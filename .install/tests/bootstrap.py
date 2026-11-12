"""Console Wi-Fi transactions against a disposable filesystem and fake radio."""
import fcntl
import json
import os
from pathlib import Path
import pty
import re
import select
import subprocess
import sys
import tempfile
import termios
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]


class Bootstrap(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nostromo-bootstrap-')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name).resolve()
        for name in ('bin', 'etc', 'var/run', 'var/backups', '.install/scripts', 'system'):
            (self.work / name).mkdir(parents=True, exist_ok=True)
        self.env = {**os.environ, 'TEST_ROOT': str(self.work),
                    'PATH': str(self.work/'bin') + ':/usr/bin:/bin'}
        self.rc = self.work/'etc/rc.conf'
        self.rc.write_text('hostname="fixture"\nsshd_enable="YES"\n')
        self.state = self.work/'radio.json'
        self.state.write_text(json.dumps({'exists': False, 'up': False, 'country': 'US', 'domain': 'FCC'}))
        for name in ('.install/scripts/setup-wifi.sh', '.install/scripts/system-files.sh', 'system/nostromo-wifi'):
            source = (ROOT/name).read_text()
            source = '\n'.join(line for line in source.splitlines() if not line.startswith('PATH='))+'\n'
            source = re.sub('/etc|/var', lambda m: str(self.work/m[0][1:]), source)
            (self.work/name).write_text(source)
        for name in ('merge-block.awk', 'forget-network.awk'):
            (self.work/'.install/scripts'/name).write_bytes((ROOT/'.install/scripts'/name).read_bytes())
        self.stub('uname', 'print("FreeBSD")')
        self.stub('id', 'print("0")')
        self.stub('sleep', 'pass')
        self.stub('netstat', 'print("fixture routing table")')
        # Like the T14's router, which answers DNS only over UDP: getent hosts uses TCP.
        self.stub('getent', 'sys.exit(2)')
        self.stub('fetch', '''
with (root/'fetch-calls').open('a') as out: out.write(sys.argv[-1]+'\\n')
sys.exit(1 if (root/'offline').exists() else 0)
''')
        self.stub('route', '''
if (root/'no-route').exists(): sys.exit(1)
print('   route to: default\\ninterface: em0')
''')
        self.stub('sysctl', 'print("iwlwifi0")')
        self.stub('sha256', 'import hashlib; print(hashlib.sha256(Path(sys.argv[-1]).read_bytes()).hexdigest())')
        self.stub('stat', '''
p=Path(sys.argv[-1]); mode=oct(p.stat().st_mode & 0o777)[2:]
if p != root and root not in p.parents: mode='755'
print(sys.argv[-2].replace('%u','0').replace('%Lp',mode))
''')
        self.stub('install', '''
import subprocess
args=sys.argv[1:]
for flag in ('-o','-g'):
    if flag in args:
        i=args.index(flag);del args[i:i+2]
sys.exit(subprocess.call(['/usr/bin/install',*args]))
''')
        self.stub('sysrc', '''
import re
args=sys.argv[1:]; file=root/'etc/rc.conf'
if args[:1]==['-f']: file=Path(args[1]);args=args[2:]
text=file.read_text(); rows=dict(re.findall(r'^([A-Za-z0-9_]+)="(.*)"$',text,re.M))
if args[:1]==['-n']:
    if args[1]=='wpa_supplicant_conf_file': print(root/'etc/wpa_supplicant.conf')
    elif args[1]=='ifconfig_wlan0' and (root/'override').exists(): print('DHCP')
    elif args[1] in rows: print(rows[args[1]])
    else: sys.exit(1)
else:
    key,value=args[0].split('=',1)
    if key.endswith('+'):
        key=key[:-1]; value=' '.join(dict.fromkeys((rows.get(key,'')+' '+value).split()))
    line=f'{key}="{value}"'
    if key in rows: text=re.sub(r'^'+key+r'=".*"$',lambda _:line,text,flags=re.M)
    else: text+=line+'\\n'
    file.write_text(text)
''')
        self.stub('ifconfig', '''
args=sys.argv[1:]; path=root/'radio.json'; state=json.loads(path.read_text())
with (root/'ifconfig-calls').open('a') as out: out.write(json.dumps(args)+'\\n')
if args==['-g','wlan']: print('wlan0' if state['exists'] else '')
elif args==['wlan0','create','wlandev','iwlwifi0']: state['exists']=True
elif not state['exists'] or args[0]!='wlan0': sys.exit(1)
elif len(args)==1:
    print('wlan0: flags=1<'+('UP,RUNNING' if state['up'] else 'RUNNING')+'>')
    print(' parent interface: iwlwifi0')
    print(' regdomain '+state['domain']+' country '+state['country'])
elif args[1]=='list': print('Fixture radio information')
elif args[1]=='destroy': state['exists']=False
elif args[1] in ('up','down'): state['up']=args[1]=='up'
else:
    for i in range(1,len(args),2): state[{'regdomain':'domain','country':'country'}[args[i]]]=args[i+1]
path.write_text(json.dumps(state))
''')
        # rc.subr refuses to start a running daemon or stop a stopped one; restart does both.
        self.stub('service', '''
name,action,*args=sys.argv[1:]; running=root/('running-'+name)
with (root/'service-calls').open('a') as out: out.write(' '.join(sys.argv[1:])+'\\n')
if action=='onestatus': sys.exit(0 if running.exists() else 1)
if action=='onestart' and running.exists(): sys.exit(name+' already running?')
if action=='onestop' and not running.exists(): sys.exit(name+' not running?')
if action=='onestop': running.unlink()
else: running.touch()
''')
        # Reads the profile as wpa_supplicant does (src/utils/config.c and common.c), so the
        # helper's own check sees the supplicant's view rather than the awk program's.
        self.stub('wpa_cli', r'''
import re
args=sys.argv[sys.argv.index('-i')+2:]; action=args[0]
def effective(raw):
    pos=raw.lstrip(b' \t\r')
    if pos[:1] in (b'', b'#'): return b''
    end=pos.find(b'#'); start=0
    while end>=0:
        start=pos.find(b'"',start)
        if start<0 or start>end: break
        start=pos.find(b'"',start+1)
        if start<0: break
        start+=1
        if start>end: end=pos.find(b'#',start)
    return (pos[:end] if end>=0 else pos).rstrip(b' \t\r')
def decode(text):
    out=bytearray(); i=0
    while i<len(text):
        c=text[i:i+1]; i+=1
        if c!=b'\\': out+=c; continue
        c=text[i:i+1]; simple={b'\\':b'\\',b'"':b'"',b'n':b'\n',b'r':b'\r',b't':b'\t',b'e':b'\x1b'}
        if c in simple: out+=simple[c]; i+=1
        elif c==b'x':
            i+=1; digits=re.match(rb'[0-9a-fA-F]{1,2}',text[i:])
            if digits: out.append(int(digits[0],16)); i+=len(digits[0])
        elif c and c in b'01234567':
            digits=re.match(rb'[0-7]{1,3}',text[i:]); out.append(int(digits[0],8)%256); i+=len(digits[0])
    return bytes(out)
def string(value):
    if value==b'NULL': return None
    if value[:1]==b'"' and len(value)>1 and value.endswith(b'"'): return value[1:-1]
    if value[:2]==b'P"' and len(value)>2 and value.endswith(b'"'): return decode(value[2:-1])
    if re.fullmatch(rb'([0-9a-fA-F]{2})*',value): return bytes.fromhex(value.decode())
    sys.exit('failed to parse '+value.decode(errors='replace'))
def networks():
    blocks=[]; block=None; path=root/'etc/wpa_supplicant.conf'
    for raw in path.read_bytes().split(b'\n') if path.exists() else []:
        line=effective(raw)
        if block is None:
            if line==b'network={': block={}
        elif line==b'}': blocks.append(block); block=None
        elif b'=' in line:
            key,value=line.split(b'=',1); block[key]=value
    # A profile only the supplicant reads, as if the awk program had missed one.
    if (root/'phantom').exists(): blocks.append({b'ssid':(root/'phantom').read_bytes()})
    return blocks
if action=='ping': print('PONG')
elif action=='get_capability': print('WPA-PSK NONE' if (root/'no-sae').exists() else 'WPA-PSK SAE OWE NONE')
elif action=='status':
    blocks=networks(); current=int((root/'selected').read_text()) if (root/'selected').exists() else -1
    if 0<=current<len(blocks):
        block=blocks[current]; security={b'WPA-PSK':'WPA2-PSK',b'NONE':'NONE'}.get(block.get(b'key_mgmt',b'WPA-PSK'),'OTHER')
        print(f'id={current}\nssid={string(block[b"ssid"]).decode(errors="backslashreplace")}\nkey_mgmt={security}')
        print('wpa_state='+('DISCONNECTED' if (root/'auth-fail').exists() else 'COMPLETED'))
elif action=='list_networks':
    print('network id / ssid / bssid / flags')
    for number,_ in enumerate(networks()): print(f'{number}\tfixture\tany\t')
elif action=='get_network':
    value=networks()[int(args[1])].get(args[2].encode())
    text=string(value) if value is not None else None
    # wpa_config_write_string(): a printable name is quoted, any other written in hex.
    if text is None: print('FAIL')
    elif all(32<=byte<127 for byte in text): sys.stdout.buffer.write(b'"'+text+b'"')
    else: print(text.hex())
elif action=='select_network': (root/'selected').write_text(args[1]); print('OK')
else: print('OK')
''')

    def stub(self, name, body):
        path = self.work/'bin'/name
        path.write_text(f'#!{sys.executable}\nimport json,os,sys\nfrom pathlib import Path\n'
                        'root=Path(os.environ["TEST_ROOT"])\n'+body)
        path.chmod(0o755)

    def console(self, *answers, offer=False):
        master, slave = pty.openpty()
        def terminal():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        process = subprocess.Popen(['sh', str(self.work/'.install/scripts/setup-wifi.sh'), *(['--offer'] if offer else [])],
                                   stdin=slave, stdout=slave, stderr=slave, env=self.env, preexec_fn=terminal)
        os.close(slave)
        output = b''
        try:
            for prompt, answer in answers:
                deadline = time.monotonic()+10
                while prompt.encode() not in output:
                    if process.poll() is not None: self.fail(output.decode())
                    if time.monotonic()>deadline: self.fail('Prompt missing: '+prompt+'\n'+output.decode())
                    if select.select([master], [], [], .1)[0]:
                        try: output += os.read(master, 65536)
                        except OSError: self.fail(output.decode())
                os.write(master, answer.encode()+b'\n')
            deadline=time.monotonic()+15
            while time.monotonic()<deadline:
                if select.select([master], [], [], .1)[0]:
                    try: data=os.read(master,65536)
                    except OSError: break
                    if not data: break
                    output+=data
                elif process.poll() is not None: break
            return process.wait(timeout=2), output.decode()
        finally:
            if process.poll() is None: process.kill(); process.wait()
            os.close(master)

    def connect(self):
        return self.console(('Radio to configure:', 'iwlwifi0'), ('Country code', 'MY'),
                            ('Network name (SSID):', 'Lab$(id) WiFi'), ('Security [', 'wpa2'),
                            ('Wi-Fi password (hidden):', 'fixture"secret\\$(id)'))

    def existing_profile(self, *blocks):
        # A laptop set up by bsdinstall: wlan0 associated through a running supplicant.
        self.state.write_text(json.dumps({'exists': True, 'up': True, 'country': 'US', 'domain': 'FCC'}))
        (self.work/'running-wpa_supplicant').touch()
        (self.work/'selected').write_text('0')
        self.rc.write_text(self.rc.read_text()+'wlans_iwlwifi0="wlan0"\nifconfig_wlan0="WPA DHCP"\n')
        profile=self.work/'etc/wpa_supplicant.conf'
        profile.write_bytes(b'ctrl_interface='+bytes(self.work/'var/run/wpa_supplicant')+b'\neapol_version=2\n'+b''.join(blocks))
        profile.chmod(0o600)
        return profile

    def test_saved_profile_for_the_same_network_is_replaced(self):
        old=b'network={\n\tssid="Lab$(id) WiFi"\n\tpsk="old-secret"\n\tpriority=5\n}\n'
        neighbour=b'# The flat upstairs.\nnetwork={\n\tssid="Neighbour"\n\tpsk="their-secret"\n}\n'
        profile=self.existing_profile(old, neighbour)
        original, rc=profile.read_bytes(), self.rc.read_text()
        answers=(('Radio to configure:', 'iwlwifi0'), ('Country code', ''),
                 ('Network name (SSID):', 'Lab$(id) WiFi'), ('Security [', 'open'))
        # A change that fails to associate leaves every byte as it was.
        (self.work/'auth-fail').touch()
        code, output=self.console(*answers)
        self.assertNotEqual(code, 0, output)
        self.assertEqual((profile.read_bytes(), self.rc.read_text()), (original, rc))
        (self.work/'auth-fail').unlink()
        code, output=self.console(*answers)
        self.assertEqual(code, 0, output)
        for line in ('Connected to Lab$(id) WiFi with WPA2-PSK.',
                     'This network has a saved profile; the new settings replace it once they connect.',
                     'The new profile replaced the one saved earlier for this network.'):
            self.assertIn(line, output)
        text=profile.read_bytes()
        self.assertNotIn(b'old-secret', text)
        self.assertIn(neighbour, text)
        self.assertEqual(text.count(b'ssid='+b'Lab$(id) WiFi'.hex().encode()), 1)
        self.assertIn(b'key_mgmt=NONE', text)

    def test_unavailable_security_is_named_before_any_password(self):
        profile=self.existing_profile(b'network={\n\tssid="Home"\n\tpsk="old-secret"\n}\n')
        original, rc=profile.read_bytes(), self.rc.read_text()
        (self.work/'no-sae').touch()
        code, output=self.console(('Radio to configure:', 'iwlwifi0'), ('Country code', ''),
                                  ('Network name (SSID):', 'Home'), ('Security [wpa2/open; default wpa2]:', 'wpa3'))
        self.assertNotEqual(code, 0)
        self.assertIn('Not available with this Wi-Fi driver and supplicant: wpa3 owe.', output)
        self.assertIn('wpa3 is not available with this Wi-Fi driver and supplicant.', output)
        self.assertNotIn('Wi-Fi password (hidden)', output)
        self.assertEqual((profile.read_bytes(), self.rc.read_text()), (original, rc))
        # The connection in use was never restarted.
        self.assertNotIn('wpa_supplicant onerestart wlan0', (self.work/'service-calls').read_text())

    def test_profile_the_supplicant_still_reads_undoes_the_change(self):
        profile=self.existing_profile(b'network={\n\tssid="Home"\n\tpsk="old-secret"\n}\n')
        original=profile.read_bytes()
        (self.work/'phantom').write_bytes(b'"Home"')
        code, output=self.console(('Radio to configure:', 'iwlwifi0'), ('Country code', ''),
                                  ('Network name (SSID):', 'Home'), ('Security [', 'wpa2'),
                                  ('Wi-Fi password (hidden):', 'new-secret'))
        self.assertNotEqual(code, 0)
        self.assertIn('Another saved profile still names this network', output)
        self.assertEqual(profile.read_bytes(), original)

    def test_missing_profile_is_created_and_secret_never_echoed(self):
        code, output = self.connect()
        self.assertEqual(code, 0, output)
        self.assertNotIn('fixture"secret', output)
        profile=self.work/'etc/wpa_supplicant.conf'
        self.assertEqual(profile.stat().st_mode & 0o777, 0o600)
        self.assertIn('ssid='+b'Lab$(id) WiFi'.hex(), profile.read_text())
        self.assertIn(r'psk="fixture\"secret\\$(id)"', profile.read_text())
        self.assertIn('sshd_enable="YES"', self.rc.read_text())
        self.assertIn('ifconfig_wlan0="WPA DHCP"', self.rc.read_text())
        self.assertEqual(list((self.work/'var/run').glob('*.lock')), [])

    def test_failed_auth_restores_files_and_existing_radio(self):
        original={'exists':True,'up':False,'country':'US','domain':'FCC'}
        self.state.write_text(json.dumps(original))
        before=self.rc.read_text()
        (self.work/'auth-fail').touch()
        code, output=self.connect()
        self.assertNotEqual(code, 0, output)
        self.assertEqual(self.rc.read_text(), before)
        self.assertFalse((self.work/'etc/wpa_supplicant.conf').exists())
        self.assertEqual(json.loads(self.state.read_text()), original)

    def test_unreachable_package_server_keeps_successful_profile(self):
        (self.work/'offline').touch()
        code, output=self.connect()
        self.assertNotEqual(code, 0)
        self.assertIn('profile is saved, but pkg.FreeBSD.org is not reachable', output)
        self.assertTrue((self.work/'etc/wpa_supplicant.conf').exists())
        self.assertTrue(json.loads(self.state.read_text())['exists'])

    def test_running_supplicant_is_restarted_not_started_twice(self):
        # A configured laptop: wlan0 exists, is associated and its supplicant runs.
        self.state.write_text(json.dumps({'exists': True, 'up': True, 'country': 'US', 'domain': 'FCC'}))
        (self.work/'running-wpa_supplicant').touch()
        code, output=self.connect()
        self.assertEqual(code, 0, output)
        calls=(self.work/'service-calls').read_text().splitlines()
        self.assertNotIn('wpa_supplicant onestart wlan0', calls)
        self.assertIn('wpa_supplicant onerestart wlan0', calls)
        self.assertIn('ssid='+b'Lab$(id) WiFi'.hex(), (self.work/'etc/wpa_supplicant.conf').read_text())

    def test_later_rc_override_fails_before_claiming_persistence(self):
        (self.work/'override').touch()
        before=self.rc.read_text()
        code, output=self.connect()
        self.assertNotEqual(code,0)
        self.assertIn('overrides this interface',output)
        self.assertEqual(self.rc.read_text(),before)
        self.assertFalse((self.work/'etc/wpa_supplicant.conf').exists())

    def test_open_hotspot_needs_no_password(self):
        for mode in ('open','owe'):
            with self.subTest(mode=mode):
                code, output=self.console(('Radio to configure:', 'iwlwifi0'), ('Country code',''),
                                          ('Network name (SSID):','Public hotspot'), ('Security [',mode))
                self.assertEqual(code,0,output)
                profile=(self.work/'etc/wpa_supplicant.conf').read_text()
                self.assertIn('key_mgmt='+('NONE' if mode=='open' else 'OWE'),profile)
                self.assertNotIn('psk=',profile)
                if mode=='owe': self.assertIn('owe_only=1',profile)
                self.assertNotIn('password (hidden)',output)
                self.assertIn('PORTAL',output)

    def test_unsupported_security_does_not_replace_configuration(self):
        (self.work/'no-sae').touch()
        before=self.rc.read_text()
        code, output=self.console(('Radio to configure:', 'iwlwifi0'), ('Country code',''),
                                  ('Network name (SSID):','Phone hotspot'), ('Security [','wpa3'),
                                  ('Wi-Fi password (hidden):','fixture-secret'))
        self.assertNotEqual(code,0)
        self.assertIn('wpa3 is not available with this Wi-Fi driver and supplicant. Available: wpa2 open.',output)
        self.assertEqual(self.rc.read_text(),before)
        self.assertFalse((self.work/'etc/wpa_supplicant.conf').exists())

    def test_offer_reports_the_connection_unknown_radio_and_unsafe_profile_do_not_change_rc(self):
        before=self.rc.read_text()
        offer='Configure a Wi-Fi connection now? [y/N]'
        # The installer asks every time; declining keeps a reachable connection as it is.
        for answer in ('', 'n', 'N'):
            with self.subTest(answer=answer):
                code, output=self.console((offer, answer), offer=True)
                self.assertEqual(code, 0, output)
                self.assertIn('pkg.FreeBSD.org is reachable through em0.', output)
                self.assertFalse((self.work/'ifconfig-calls').exists())
        self.assertIn('https://pkg.FreeBSD.org/FreeBSD:15:amd64/quarterly/meta.conf', (self.work/'fetch-calls').read_text())
        # Declining without the package server stops before a clean install removes anything.
        (self.work/'offline').touch()
        code, output=self.console((offer, 'n'), offer=True)
        self.assertNotEqual(code, 0)
        self.assertIn('pkg.FreeBSD.org is not reachable.', output)
        self.assertIn('Connect a cable or set up Wi-Fi, then rerun.', output)
        self.assertFalse((self.work/'ifconfig-calls').exists())
        # Accepting starts the console setup, connected or not.
        for offline in (True, False):
            with self.subTest(offline=offline):
                if not offline: (self.work/'offline').unlink()
                code, output=self.console((offer, 'y'), ('Radio to configure:', 'wlan999'), offer=True)
                self.assertNotEqual(code, 0)
        code, _=self.console(('Radio to configure:', 'wlan999'))
        self.assertNotEqual(code, 0)
        (self.work/'etc/wpa_supplicant.conf').symlink_to(self.rc)
        code, _=self.console(('Radio to configure:', 'iwlwifi0'))
        self.assertNotEqual(code, 0)
        self.assertEqual(self.rc.read_text(), before)


    def test_bluetooth_bootstrap_uses_supported_usb_ids_and_keeps_live_hci(self):
        source=(ROOT/'system/nostromo-bluetooth').read_text()
        source='\n'.join(line for line in source.splitlines() if not line.startswith('PATH='))+'\n'
        source=source.replace('/usr/local/libexec/nostromo-packages','package-helper').replace('/usr/sbin/iwmbtfw','iwmbtfw')
        script=self.work/'bluetooth';script.write_text(source)
        self.stub('usbconfig', '''
if sys.argv[1:]==['list']:print('ugen0.3: unrelated device\\nugen0.4: Intel Bluetooth')
else:print(' idVendor = '+('0x8087' if sys.argv[2]=='ugen0.4' else '0x1234')+'\\n idProduct = 0x0026')
''')
        self.stub('hccontrol', "\nif (root/'hci').exists():print('ubt0hci')\nelse:sys.exit(1)")
        self.stub('pkg', 'sys.exit(1)')
        for name in ['package-helper','iwmbtfw','kldload']:
            self.stub(name, "\nwith (root/'bt-calls').open('a') as out:out.write(json.dumps([Path(sys.argv[0]).name,sys.argv[1:]])+'\\n')")
        self.stub('kldstat', 'sys.exit(1)')
        self.stub('sysctl', "print('dev.ubt.0.%driver')")
        self.stub('service', "assert sys.argv[1:]==['bluetooth','onestart','ubt0']; (root/'hci').touch()")
        first=subprocess.run(['sh',str(script),'setup'],env=self.env,text=True,capture_output=True)
        self.assertEqual(first.returncode,0,first.stderr)
        calls=(self.work/'bt-calls').read_text()
        self.assertIn('["install", "iwmbt-firmware"]',calls)
        self.assertIn('ugen0.4',calls)
        self.assertNotIn('ugen0.3',calls)
        second=subprocess.run(['sh',str(script),'setup'],env=self.env,text=True,capture_output=True)
        self.assertEqual(second.returncode,0,second.stderr)
        self.assertEqual((self.work/'bt-calls').read_text(),calls)


if __name__ == '__main__': unittest.main(verbosity=2)
