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
        (self.work/'.install/scripts/merge-block.awk').write_bytes((ROOT/'.install/scripts/merge-block.awk').read_bytes())
        self.stub('uname', 'print("FreeBSD")')
        self.stub('id', 'print("0")')
        self.stub('sleep', 'pass')
        self.stub('netstat', 'print("fixture routing table")')
        self.stub('getent', 'sys.exit(1 if (root/"dns-fail").exists() else 0)')
        self.stub('route', 'sys.exit(1 if (root/"no-route").exists() else 0)')
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
        self.stub('service', '''
name,action,*args=sys.argv[1:]; running=root/('running-'+name)
if action=='onestatus': sys.exit(0 if running.exists() else 1)
if action=='onestop': running.unlink(missing_ok=True)
else: running.touch()
''')
        self.stub('wpa_cli', '''
args=sys.argv[sys.argv.index('-i')+2:]; action=args[0]
file=root/'etc/wpa_supplicant.conf'
if action=='ping': print('PONG')
elif action=='get_capability': print('WPA-PSK NONE' if (root/'no-sae').exists() else 'WPA-PSK SAE OWE NONE')
elif action=='status':
    if (root/'selected').exists():
        print('id=0\\nwpa_state='+('DISCONNECTED' if (root/'auth-fail').exists() else 'COMPLETED'))
elif action=='list_networks': print('network id / ssid / bssid / flags\\n0\\tfixture\\tany\\t')
elif action=='get_network':
    import re
    match=re.search(r'id_str=(.*)',file.read_text())
    print(match[1] if match else 'FAIL')
elif action=='select_network': (root/'selected').touch();print('OK')
else: print('OK')
''')

    def stub(self, name, body):
        path = self.work/'bin'/name
        path.write_text(f'#!{sys.executable}\nimport json,os,sys\nfrom pathlib import Path\n'
                        'root=Path(os.environ["TEST_ROOT"])\n'+body)
        path.chmod(0o755)

    def console(self, *answers, needed=False):
        master, slave = pty.openpty()
        def terminal():
            os.setsid()
            fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        process = subprocess.Popen(['sh', str(self.work/'.install/scripts/setup-wifi.sh'), *(['--needed'] if needed else [])],
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

    def test_dns_failure_keeps_successful_profile(self):
        (self.work/'dns-fail').touch()
        code, output=self.connect()
        self.assertNotEqual(code, 0)
        self.assertIn('profile is saved', output)
        self.assertTrue((self.work/'etc/wpa_supplicant.conf').exists())
        self.assertTrue(json.loads(self.state.read_text())['exists'])

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
        self.assertIn('does not support SAE',output)
        self.assertEqual(self.rc.read_text(),before)
        self.assertFalse((self.work/'etc/wpa_supplicant.conf').exists())

    def test_working_connection_unknown_radio_and_unsafe_profile_do_not_change_rc(self):
        before=self.rc.read_text()
        # The installer keeps a working connection without asking anything.
        code, output=self.console(needed=True)
        self.assertEqual(code, 0, output)
        self.assertIn('The network is up', output)
        self.assertFalse((self.work/'ifconfig-calls').exists())
        # Without a default route or package-host DNS, it goes straight to the setup.
        for offline in ('no-route', 'dns-fail'):
            with self.subTest(offline=offline):
                (self.work/offline).touch()
                code, output=self.console(('Radio to configure:', 'wlan999'), needed=True)
                self.assertNotEqual(code, 0)
                self.assertIn('No working connection', output)
                (self.work/offline).unlink()
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
