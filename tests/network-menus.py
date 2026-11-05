"""Exercise the actual POSIX panel scripts; substitute hardware commands only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Menus(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.bin = self.work / 'bin'
        self.bin.mkdir()
        self.env = {**os.environ, 'HOME': str(self.work), 'TEST_ROOT': str(self.work),
                    'XDG_DATA_HOME': str(ROOT / 'home/.local/share'),
                    'XDG_CONFIG_HOME': str(self.work / 'config'),
                    'XDG_STATE_HOME': str(self.work / 'state'),
                    'PATH': str(self.bin) + ':/opt/homebrew/bin:/usr/bin:/bin',
                    'TMPDIR': str(self.work)}
        (self.work / 'choices').write_text('[]')
        (self.work / 'fail').write_text('')
        for name in ('wifi', 'vpn', 'bluetooth'):
            text = (ROOT / 'home/.local/bin' / ('nostromo-' + name)).read_text()
            text = text.replace('nostromo-admin ', 'network-control ')
            text = text.replace('/usr/local/share/nostromo/ssid-hex.awk', str(ROOT / 'scripts/ssid-hex.awk'))
            (self.bin / ('nostromo-' + name)).write_text(text)
            (self.bin / ('nostromo-' + name)).chmod(0o755)
        (self.bin / 'nostromo-picker').symlink_to(ROOT / 'home/.local/bin/nostromo-picker')
        self.stub('ifconfig', "\nif sys.argv[1:]==['-g','wlan']: print('wlan0')\nelse: sys.exit(1)")
        self.stub('sysctl', "print('dev.ubt.0.%driver')")
        self.stub('notify-send', 'pass')
        self.stub('qutebrowser', "(root/'browser').write_text(json.dumps(sys.argv[1:]))")
        self.stub('fuzzel', r'''
rows=sys.stdin.read().splitlines()
with (root/'panels').open('a') as out:
    out.write(json.dumps({'argv':sys.argv[1:],'rows':rows})+'\n')
choices=json.loads((root/'choices').read_text())
if not choices: sys.exit(1)
choice=choices.pop(0); (root/'choices').write_text(json.dumps(choices))
if choice is None: sys.exit(1)
if '--index' in sys.argv:
    if isinstance(choice,int): print(choice)
    else: print(next(i for i,row in enumerate(rows) if choice in row))
else: print(choice)
''')
        self.stub('network-control', r'''
name,action,*args=sys.argv[1:]
stdin=sys.stdin.read() if action in ('connect','select','pair') and name!='bluetooth' or action=='pair' else ''
with (root/'calls').open('a') as out: out.write(json.dumps([name,action,args,stdin])+'\n')
if (root/'fail').read_text()==name+':'+action:
    print('Simulated hardware failure',file=sys.stderr); sys.exit(1)
if name=='wifi':
    if action=='scan': print('00:11:22:33:44:55\t2412\t-42\t[WPA2-PSK-CCMP][ESS]\tLab$(id)\\x20WiFi')
    elif action=='saved': print('7\tExisting network\tany\t[CURRENT]')
    elif action=='status': print('wpa_state=COMPLETED')
elif name=='bluetooth':
    if action=='nodes' and not (root/'no-hci').exists(): print('ubt0hci')
    elif action=='setup': (root/'no-hci').unlink(); print('ubt0hci')
    elif action=='scan': print('BD_ADDR: 00:11:22:33:44:55')
    elif action=='status': print('00:11:22:33:44:55 12 ACL OPEN')
elif name=='wireguard':
    if action=='profiles': print('wg0\nwg2')
    elif action=='brief': print('OFF')
    elif action=='status': print('No recent handshake')
''')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(f'#!{sys.executable}\nimport json,os,sys\nfrom pathlib import Path\nroot=Path(os.environ["TEST_ROOT"])\n'+body+'\n')
        path.chmod(0o755)

    def run_menu(self, name, choices, *args):
        (self.work / 'choices').write_text(json.dumps(choices))
        result = subprocess.run([str(self.bin / ('nostromo-' + name)), *args],
                                env=self.env, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.work.glob('nostromo-picker.*')), [])
        if os.environ.get('NOSTROMO_MENU_PREVIEWS'):
            for panel in self.records('panels'):
                prefix={'wifi':'Wi-Fi /','vpn':'WireGuard /','bluetooth':'Bluetooth /'}[name]
                prompt=next((a[9:] for a in panel['argv'] if a.startswith('--prompt='+prefix)),None)
                if prompt:
                    target=Path(os.environ['NOSTROMO_MENU_PREVIEWS'])/(name+'-menu.txt')
                    target.write_text(prompt+'\n'+'\n'.join(panel['rows'])+'\n')
                    break
        return result

    def records(self, name):
        path=self.work/name
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_wifi_scan_connect_preserves_bytes_and_masks_secret(self):
        secret='not-a-real-password$(id)'
        self.run_menu('wifi',['wlan0','SCAN','00:11', 'wpa2',secret,None,'EXIT'])
        connect=[c for c in self.records('calls') if c[1]=='connect']
        self.assertEqual(connect,[['wifi','connect',['wlan0'],
            'Lab$(id) WiFi'.encode().hex()+'\nwpa2\n'+secret+'\n']])
        panels=self.records('panels')
        password=next(p for p in panels if '--password' in p['argv'])
        self.assertIn('--cache=/dev/null',password['argv'])
        self.assertIn('--log-level=none',password['argv'])
        self.assertEqual(password['rows'],[])
        self.assertNotIn(secret,json.dumps(panels))

    def test_wifi_cancel_secret_and_invalid_selection_do_not_connect(self):
        self.run_menu('wifi',['wlan0','HIDDEN','Hidden AP','wpa3',None,'EXIT'])
        self.assertEqual(self.records('calls'),[])
        self.run_menu('wifi',['wlan0',999])
        self.assertEqual(self.records('calls'),[])

    def test_wifi_public_networks_skip_password_and_portal_is_unprivileged(self):
        for mode in ('open','owe'):
            with self.subTest(mode=mode):
                self.run_menu('wifi',['wlan0','HIDDEN','Public hotspot',mode,None,'PORTAL','EXIT'])
                connect=[c for c in self.records('calls') if c[1]=='connect'][-1]
                self.assertEqual(connect,['wifi','connect',['wlan0'],b'Public hotspot'.hex()+'\n'+mode+'\n\n'])
        self.assertFalse(any('--password' in p['argv'] for p in self.records('panels')))
        # The menu launches the existing browser without a root operation or waiting for it to close.
        import time
        for _ in range(50):
            if (self.work/'browser').exists(): break
            time.sleep(.02)
        self.assertEqual(json.loads((self.work/'browser').read_text()),['--target','window','http://neverssl.com/'])
        self.assertEqual([c[1] for c in self.records('calls')],['connect','connect'])

    def test_wifi_phone_hotspot_uses_personal_security(self):
        self.run_menu('wifi',['wlan0','HIDDEN','Phone hotspot','wpa3','fixture-secret',None,'EXIT'])
        self.assertEqual(self.records('calls'),[['wifi','connect',['wlan0'],b'Phone hotspot'.hex()+'\nwpa3\nfixture-secret\n']])

    def test_scan_failure_is_visible_and_saved_selection_survives(self):
        (self.work/'fail').write_text('wifi:scan')
        self.run_menu('wifi',['wlan0','SCAN',None,'SAVED','Existing network',None,'EXIT'])
        self.assertTrue(any('Simulated hardware failure' in p['rows'] for p in self.records('panels')))
        selected=[c for c in self.records('calls') if c[1]=='select']
        self.assertEqual(selected,[['wifi','select',['wlan0'],'7\n']])

    def test_bluetooth_scan_pair_then_disconnect_without_a_terminal(self):
        self.run_menu('bluetooth',['ubt0','SCAN','00:11','PAIR CLASSIC PIN','1234',None,
                                   'DISCONNECT','00:11',None,'EXIT'])
        actions=[c for c in self.records('calls') if c[1] in ('pair','disconnect')]
        self.assertEqual(actions,[['bluetooth','pair',['ubt0hci','00:11:22:33:44:55'],'1234\n'],
                                  ['bluetooth','disconnect',['ubt0hci','12'],'']])
        self.assertNotIn('1234',json.dumps(self.records('panels')))

    def test_bluetooth_initialization_then_controller_selection(self):
        (self.work/'no-hci').touch()
        self.run_menu('bluetooth',['INITIALIZE',None,'ubt0','EXIT'])
        self.assertEqual([c[1] for c in self.records('calls')], ['nodes','setup','nodes'])

    def test_vpn_selection_persists_for_the_bar_and_status_uses_no_panel(self):
        self.run_menu('vpn',['TUNNEL','wg2','UP',None,'STATUS',None,'DOWN',None,'EXIT'],'menu')
        actions=[c for c in self.records('calls') if c[1] in ('up','down','status')]
        self.assertEqual([c[2] for c in actions],[['wg2'],['wg2'],['wg2']])
        before=len(self.records('panels'))
        self.assertEqual(self.run_menu('vpn',[],'brief').stdout,'OFF\n')
        self.assertEqual(len(self.records('panels')),before)
        self.assertEqual(len(self.records('calls')),len(actions)+1)  # Profiles + explicit actions only.

    def test_status_bar_does_not_request_root_authentication(self):
        self.assertEqual(self.run_menu('bluetooth',[],'status').stdout,'HCI\n')
        self.assertEqual(self.run_menu('vpn',[],'brief').stdout,'OFF\n')
        self.stub('ifconfig', "print('wg0: flags=8041<UP,RUNNING,MULTICAST> mtu 1420')")
        self.assertEqual(self.run_menu('vpn',[],'brief').stdout,'UP\n')
        self.stub('ifconfig', "print('wg0: flags=8000<MULTICAST> mtu 1420')")
        self.assertEqual(self.run_menu('vpn',[],'brief').stdout,'DOWN\n')
        self.assertEqual(self.records('calls'),[])


if __name__=='__main__': unittest.main(verbosity=2)
