"""Run the actual terminal viewer in a disposable PTY; no laptop devices needed."""
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import signal
import struct
import subprocess
import tempfile
import termios
import time
import unittest

ROOT=Path(__file__).resolve().parents[2]


class Idle(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='nostromo-idle-')
        self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name)
        self.binary=self.work/'idle'
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(ROOT/'session/terminal-idle.c'),'-o',str(self.binary)],check=True)
        self.env={**os.environ,'HOME':str(self.work),'NOSTROMO_EFFECTS':'animated','LC_ALL':'en_US.UTF-8'}

    def test_clock_closes_with_parent_and_static_emits_once(self):
        process=subprocess.Popen([str(self.binary),'--ticks'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,env=self.env)
        try:
            self.assertEqual(process.stdout.readline(),b'0\n')
            self.assertEqual(process.stdout.readline(),b'1\n')
            process.stdin.close()
            self.assertEqual(process.wait(timeout=2),0)
        finally:
            if process.poll() is None: process.kill(); process.wait()
            process.stdout.close()
        result=subprocess.run([str(self.binary),'--ticks'],input=b'',capture_output=True,env={**self.env,'NOSTROMO_EFFECTS':'static'},check=True)
        self.assertEqual(result.stdout,b'0\n')

    def test_viewer_scroll_resize_controls_and_signal_restore(self):
        report=self.work/'report'
        report.write_text('Unsafe \x1b]52;c;fixture\x07 text\n'+''.join(f'Metric {n:03d}  日本語  '+('value '*25)+'\n' for n in range(80)))
        for mode in ('animated','static'):
            with self.subTest(mode=mode):
                master,slave=pty.openpty()
                fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,120,0,0))
                original=termios.tcgetattr(slave)
                process=subprocess.Popen([str(self.binary),'--report',str(report),'--art',str(ROOT/'art/nostromo-orb-idle.txt')],
                                         stdin=slave,stdout=slave,stderr=slave,env={**self.env,'NOSTROMO_EFFECTS':mode})
                output=b''
                def until(needle):
                    nonlocal output
                    deadline=time.monotonic()+4
                    while needle not in output:
                        if time.monotonic()>deadline: self.fail('Missing terminal output: '+repr(needle))
                        if select.select([master],[],[],.1)[0]: output+=os.read(master,65536)
                try:
                    until(b'1/81')
                    self.assertNotIn(b'\x1b]52',output)
                    self.assertNotIn(b'52;c;fixture',output)
                    self.assertIn(b'Unsafe  text',output)
                    if mode=='animated':
                        initial=output.count(b'\x1b[H')
                        time.sleep(.6)
                        until(b'\x1b[H'+b'\x1b[2K')
                        if select.select([master],[],[],1)[0]: output+=os.read(master,65536)
                        self.assertGreater(output.count(b'\x1b[H'),initial)
                    os.write(master,b'G'); until(b'Metric 079')
                    fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',30,70,0,0))
                    output=b'';process.send_signal(signal.SIGWINCH)
                    until(b'q close')
                    process.send_signal(signal.SIGTERM)
                    deadline=time.monotonic()+2
                    while process.poll() is None and time.monotonic()<deadline:
                        if select.select([master],[],[],.05)[0]: output+=os.read(master,65536)
                    self.assertEqual(process.wait(timeout=2),0)
                    restored=termios.tcgetattr(slave)
                    # BSD may set PENDIN while re-enabling canonical input.
                    restored[3] &= ~getattr(termios,'PENDIN',0)
                    original[3] &= ~getattr(termios,'PENDIN',0)
                    self.assertEqual(restored,original)
                finally:
                    if process.poll() is None: process.kill(); process.wait()
                    os.close(master);os.close(slave)

    def view(self, report, keys=b''):
        # One static frame per key at 120x24, where the report starts in column 34.
        master,slave=pty.openpty()
        fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,120,0,0))
        process=subprocess.Popen([str(self.binary),'--report',str(report),'--art',str(ROOT/'art/nostromo-orb-idle.txt')],
                                 stdin=slave,stdout=slave,stderr=slave,env={**self.env,'NOSTROMO_EFFECTS':'static'})
        frames=[]
        try:
            for key in [None,*keys]:
                if key is not None: os.write(master,bytes([key]))
                output=b'';deadline=time.monotonic()+4
                while b'q close' not in output:
                    if time.monotonic()>deadline: self.fail('Missing terminal output')
                    if select.select([master],[],[],.1)[0]: output+=os.read(master,65536)
                frames.append(output)
            os.write(master,b'q')
            self.assertEqual(process.wait(timeout=2),0)
        finally:
            if process.poll() is None: process.kill(); process.wait()
            os.close(master);os.close(slave)
        return frames

    def test_viewer_aligns_fastfetch_columns_and_drops_controls(self):
        # fastfetch --pipe still aligns values with ESC[18G; the viewer printed "[18G".
        report=self.work/'report'
        report.write_text('◆ OS  \x1b[18GFreeBSD 15.1-RELEASE amd64\nBLUETOOTH DEVICES  \x1b[18Gnone\n'
                          'tab\there\nbold \x1b[1mtext\x1b[0m end\n')
        first,scrolled=self.view(report,b'l')
        self.assertNotIn(b'[18G',first)
        self.assertIn(('◆ OS'+' '*13+'FreeBSD 15.1-RELEASE').encode(),first)
        self.assertIn(b'BLUETOOTH DEVICES  none',first)
        self.assertIn(b'tab     here',first)
        self.assertIn(b'bold text end',first)
        # Eight columns scrolled: the key is gone and the value keeps its column.
        self.assertNotIn('◆ OS'.encode(),scrolled)
        self.assertIn(b'\x1b[34G'+b' '*9+b'FreeBSD',scrolled)

    def test_viewer_shows_real_fastfetch_output_without_controls(self):
        fastfetch=ROOT/'.build/fastfetch-check/fastfetch'
        if not fastfetch.is_file():
            self.skipTest('the host fastfetch 2.69.0 build is not cached')
        report=self.work/'report'
        with report.open('wb') as stream:
            subprocess.run([str(fastfetch),'--config',str(ROOT/'fastfetch/config.jsonc'),'--logo','none','--pipe','true'],
                           stdout=stream,stderr=subprocess.DEVNULL,check=True,timeout=60,
                           env={'HOME':str(self.work),'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8'})
        self.assertIn(b'\x1b[18G',report.read_bytes())
        frame,=self.view(report)
        self.assertNotIn(b'[18G',frame)
        self.assertRegex(frame.decode(),r'◆ OS {13}\S')
        # The native stage check only parses the JSON; fastfetch skips an unknown
        # module silently and names it only in its JSON report.
        result=subprocess.run([str(fastfetch),'--config',str(ROOT/'fastfetch/config.jsonc'),'--format','json'],
                              capture_output=True,text=True,check=True,timeout=60,
                              env={'HOME':str(self.work),'PATH':'/usr/bin:/bin','LANG':'en_US.UTF-8'})
        modules=json.loads(result.stdout)
        self.assertEqual([module['type'] for module in modules if module.get('error')=='Unknown module type'],[])
        self.assertEqual(len(modules),68)

    def test_console_output_uses_glyphs_the_console_fonts_have(self):
        # FreeBSD 15.1's built-in vt font (sys/dev/vt/font/vt_font_default.c) and the
        # loader's 16x32 Terminus on the T14 (contrib/terminus/ter-u32n.bdf) both have
        # these. Neither has ◈ ▣ ▤ ▰, which fastfetch's keys showed broken on the console.
        console=set('↑›◆■≡▬▀▄█')
        for name in ('fastfetch/config.jsonc','art/nostromo-orb-small.txt','art/nostromo-orb-idle.txt'):
            text=(ROOT/name).read_text()
            self.assertEqual({ch for ch in text if ord(ch)>0x7e}-console,set(),name)

    def test_dashboard_animation_does_not_accumulate_edits(self):
        data=self.work/'share/nostromo';data.mkdir(parents=True)
        for name in ('nostromo-orb-small.txt','nostromo-orb-idle.txt'):
            (data/name).symlink_to(ROOT/'art'/name)
        subprocess.run(['lua','.install/tests/dashboard-idle.lua'],cwd=ROOT,env={**self.env,'XDG_DATA_HOME':str(data.parent)},check=True)

    def test_redirected_fetch_preserves_plain_or_json_output(self):
        binary=self.work/'bin';binary.mkdir()
        fetch=binary/'fastfetch'
        fetch.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
        fetch.chmod(0o755)
        for options in ([],['--format','json'],['--plain']):
            result=subprocess.run([str(ROOT/'bin/nostromo-fetch'),*options],input='untouched input',text=True,
                                  capture_output=True,env={**self.env,'PATH':str(binary)+':/usr/bin:/bin'},check=True)
            self.assertIn('--config\n',result.stdout)
            self.assertNotIn('--report\n',result.stdout)
            self.assertNotIn('--plain\n',result.stdout)
            if options==['--format','json']: self.assertTrue(result.stdout.endswith('--format\njson\n'))


if __name__=='__main__':unittest.main(verbosity=2)
