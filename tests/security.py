"""Privilege and suspend regressions with disposable native-command stand-ins."""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import shlex
import socket
import subprocess
import sys
import tempfile
import termios
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Security(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='nostromo-security-')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.bin = self.work / 'bin'
        self.bin.mkdir()
        self.env = {**os.environ, 'HOME': str(self.work), 'XDG_RUNTIME_DIR': str(self.work),
                    'WAYLAND_DISPLAY': 'wayland-0', 'PATH': str(self.bin) + ':/usr/bin:/bin'}

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(f'#!{sys.executable}\nimport os,sys,json,subprocess,hashlib\nfrom pathlib import Path\n'
                        f'work=Path({str(self.work)!r})\n' + body + '\n')
        path.chmod(0o755)
        return path

    def run_script(self, script, *args, **kwargs):
        return subprocess.run(['sh', str(script), *args], env=self.env, text=True,
                              capture_output=True, timeout=10, **kwargs)

    def records(self, name):
        path = self.work / name
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_mdo_migration_removes_root_grant_preserves_other_accounts(self):
        command = ['awk', '-v', 'uid=1001', '-v', 'gid=1008', '-f', str(ROOT/'scripts/merge-mdo.awk')]
        old = 'uid=9000>uid=9001; uid = 1001 > uid = 0 ;gid=777>uid=778;uid=1001>uid=0\n'
        result = subprocess.run(command, input=old, text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout, 'uid=9000>uid=9001;gid=777>uid=778;uid=1001>uid=.,gid=1008,!gid=.\n')
        self.assertEqual(subprocess.check_output(command, input=result.stdout, text=True), result.stdout)
        for uid, gid in [('0','1008'), ('1001','0'), ('1001','wheel'), ('1001','')]:
            args = ['awk','-v',f'uid={uid}','-v',f'gid={gid}','-f',str(ROOT/'scripts/merge-mdo.awk')]
            self.assertNotEqual(subprocess.run(args, input='', text=True, capture_output=True).returncode, 0)

    def admin(self):
        su = self.stub('su', r'''
with (work/'auth').open('a') as out: out.write(json.dumps([sys.argv[1:],dict(os.environ)])+'\n')
if (work/'reject').exists(): sys.exit(1)
assert os.isatty(0) and os.isatty(1)
print('Password prompt fixture',flush=True)
sys.exit(subprocess.call(['/bin/sh','-c',sys.argv[-1]],pass_fds=(3,4)))
''')
        mdo = self.stub('mdo', r'''
assert sys.argv[1:4]==['-u','root','--']
with (work/'mdo').open('a') as out: out.write(json.dumps(sys.argv[1:])+'\n')
os.execv(sys.argv[4],sys.argv[4:])
''')
        helper = self.stub('root-helper', r'''
data=sys.stdin.buffer.read()
with (work/'calls').open('a') as out:
    out.write(json.dumps([sys.argv[1:],hashlib.sha256(data).hexdigest(),dict(os.environ)])+'\n')
print('reply from helper',flush=True)
sys.exit(42 if '--fail' in sys.argv else 0)
''')
        self.stub('foot', r'''
with (work/'foot').open('a') as out: out.write(json.dumps('prompt')+'\n')
if (work/'cancel').exists(): sys.exit(130)
at=sys.argv.index('-e')+1
import pty,fcntl,termios,select
master,slave=pty.openpty()
child=os.fork()
if not child:
    os.close(master)
    os.setsid()
    fcntl.ioctl(slave,termios.TIOCSCTTY,0)
    for fd in (0,1,2): os.dup2(slave,fd)
    if slave>2: os.close(slave)
    os.execv(sys.argv[at],sys.argv[at:])
os.close(slave)
finished=0
with (work/'prompt').open('ab',buffering=0) as out:
    while True:
        if select.select([master],[],[],0.05)[0]:
            try: data=os.read(master,4096)
            except OSError: break
            if not data: break
            out.write(data)
        finished,status=os.waitpid(child,os.WNOHANG)
        if finished: break
    if not finished: _,status=os.waitpid(child,0)
os.close(master)
sys.exit(os.WEXITSTATUS(status) if os.WIFEXITED(status) else 128+os.WTERMSIG(status))
''')
        source = (ROOT/'home/.local/bin/nostromo-admin').read_text()
        source = source.replace('/usr/bin/su',str(su)).replace('/usr/bin/mdo',str(mdo))
        source = source.replace('helper=/usr/local/libexec/nostromo-$1',f'helper={helper}')
        path = self.work/'admin'
        path.write_text(source)
        return path

    def test_admin_quotes_arguments_authenticates_and_keeps_secrets_in_pipes(self):
        script = self.admin()
        argument = "space ' ; $(touch " + str(self.work/'injected') + ") `id` *"
        secret = 'fixture-password$(id)\n'
        self.env.update(ENV='/tmp/not-an-env', BASH_ENV='/tmp/not-bash', NOSTROMO_UNTRUSTED='bad')
        result = self.run_script(script,'wifi','connect',argument,input=secret)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout,'reply from helper\n')
        args,digest,environment = self.records('calls')[0]
        self.assertEqual(args,['connect',argument])
        self.assertEqual(digest,hashlib.sha256(secret.encode()).hexdigest())
        self.assertFalse((self.work/'injected').exists())
        for name in ('ENV','BASH_ENV','NOSTROMO_UNTRUSTED','WAYLAND_DISPLAY'):
            self.assertNotIn(name,environment)
            self.assertNotIn(name,self.records('auth')[0][1])
        self.assertEqual(environment['HOME'],'/root')
        self.assertNotIn(secret,json.dumps(self.records('auth')+self.records('mdo')))
        self.assertIn('Password prompt fixture',(self.work/'prompt').read_text())
        self.assertEqual(list(self.work.glob('nostromo-admin.*')),[])
        # Existing terminals use su directly and still authenticate each operation.
        master,slave=pty.openpty()
        stopped=threading.Event()
        def drain_terminal():
            while not stopped.is_set():
                if select.select([master],[],[],0.05)[0]:
                    try: data=os.read(master,4096)
                    except OSError: return
                    if not data: return
        reader=threading.Thread(target=drain_terminal)
        reader.start()
        def terminal_session():
            os.setsid()
            fcntl.ioctl(2,termios.TIOCSCTTY,0)
        try:
            terminal=subprocess.run(['sh',str(script),'wifi','status'],input='',text=True,
                                    stdout=subprocess.PIPE,stderr=slave,env=self.env,timeout=10,
                                    preexec_fn=terminal_session)
        finally:
            stopped.set()
            reader.join(timeout=1)
            os.close(slave)
            os.close(master)
        self.assertEqual(terminal.returncode,0)
        self.assertEqual(terminal.stdout,'reply from helper\n')
        self.assertEqual(len(self.records('auth')),2)
        self.assertEqual(len(self.records('foot')),1)

    def test_admin_failed_auth_and_closed_prompt_never_execute_command(self):
        script = self.admin()
        for marker, code in [('reject',1),('cancel',130)]:
            (self.work/marker).touch()
            result = self.run_script(script,'wifi','connect',input='fixture\n')
            self.assertEqual(result.returncode,code,result.stderr)
            self.assertEqual(self.records('calls'),[])
            self.assertEqual(self.records('mdo'),[])
            self.assertEqual(list(self.work.glob('nostromo-admin.*')),[])
            (self.work/marker).unlink()

    def test_admin_command_failure_and_invalid_requests_remain_failures(self):
        script = self.admin()
        self.assertEqual(self.run_script(script,'wifi','--fail',input='').returncode,42)
        before=len(self.records('auth'))
        for args in [('shell',),('wifi','line\nbreak')]:
            self.assertEqual(self.run_script(script,*args,input='').returncode,2)
        self.assertEqual(len(self.records('auth')),before)
        self.env.pop('WAYLAND_DISPLAY')
        self.assertEqual(self.run_script(script,'wifi','scan',input='').returncode,1)

    def test_suspend_cancels_failed_or_timed_out_lock_before_native_hooks(self):
        policy=self.work/'account'
        policy.write_text('1001 gluppler\n')
        policy.chmod(0o600)
        self.stub('uname', "print('FreeBSD')")
        self.stub('id', "print('1001' if sys.argv[-1]=='gluppler' else '0')")
        self.stub('stat', "print('0 '+format(Path(sys.argv[-1]).stat().st_mode & 0o777,'o'))")
        self.stub('logger', "pass")
        su=self.stub('su', "\nwith (work/'events').open('a') as out: out.write(json.dumps('lock')+'\\n')\nsys.exit(1 if (work/'reject').exists() else 0)")
        timeout=self.stub('timeout', r'''
assert sys.argv[1:4]==['-k','1','4']
if (work/'timeout').exists(): sys.exit(124)
sys.exit(subprocess.call(sys.argv[4:]))
''')
        acpi=self.stub('acpiconf', "\nwith (work/'events').open('a') as out: out.write(json.dumps(sys.argv[1:])+'\\n')")
        rc=self.stub('rc.suspend', "\nwith (work/'events').open('a') as out: out.write(json.dumps(['native',*sys.argv[1:]])+'\\n')")
        source=(ROOT/'system/nostromo-suspend').read_text()
        source=source.replace('PATH=/sbin:/bin:/usr/sbin:/usr/bin',f'PATH={self.bin}:/usr/bin:/bin')
        for old,new in [('/usr/bin/su',su),('/usr/bin/timeout',timeout),('/usr/sbin/acpiconf',acpi),
                        ('/etc/rc.suspend',rc),('/usr/local/etc/nostromo/mdo-account',policy)]:
            source=source.replace(old,str(new))
        script=self.work/'suspend'
        script.write_text(source)
        result=self.run_script(script,'0x03')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(self.records('events'),['lock',['native','acpi','0x03']])
        for marker in ('reject','timeout'):
            (self.work/'events').unlink()
            (self.work/marker).touch()
            self.assertNotEqual(self.run_script(script,'0x03').returncode,0)
            self.assertIn(['-k','1'],self.records('events'))
            self.assertFalse(any(isinstance(e,list) and e[0]=='native' for e in self.records('events')))
            (self.work/marker).unlink()
        policy.chmod(0o644)
        self.assertNotEqual(self.run_script(script,'0x03').returncode,0)

    def test_lock_probe_uses_existing_pam_directory_and_checks_every_socket(self):
        pam=self.work/'pam-system'
        pam.write_text(f'session optional pam_xdg.so runtime_dir_prefix={self.work}/runtime\n')
        runtime=self.work/'runtime'/'gluppler'
        runtime.mkdir(parents=True,mode=0o700)
        local=self.work/'.local/bin'
        local.mkdir(parents=True)
        # Use real Unix sockets; no listener, connection or device access is needed.
        for name in ('wayland-0','wayland-1'):
            sock=socket.socket(socket.AF_UNIX)
            self.addCleanup(sock.close)
            sock.bind(str(runtime/name))
        control=self.stub('nostromo-control', r'''
assert os.environ['XDG_RUNTIME_DIR']==str(work/'runtime/gluppler')
sys.exit(0 if (work/('locked-'+os.environ['WAYLAND_DISPLAY'])).exists() else 1)
''')
        locker=self.stub('gtklock', r'''
if (work/'reject').exists(): sys.exit(1)
(work/('locked-'+os.environ['WAYLAND_DISPLAY'])).touch()
''')
        (local/'nostromo-control').symlink_to(control)
        (local/'gtklock').symlink_to(locker)
        self.stub('id', "print('gluppler' if sys.argv[1]=='-un' else str(os.getuid()))")
        # System commands still use the host's stat; only account naming is modeled.
        source=(ROOT/'system/nostromo-lock-session').read_text().replace('/etc/pam.d/system',str(pam))
        source=source.replace('PATH=$HOME/.local/bin:',f'PATH=$HOME/.local/bin:{self.bin}:')
        script=self.work/'lock-session'
        script.write_text(source)
        result=self.run_script(script)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((self.work/'locked-wayland-0').exists())
        self.assertTrue((self.work/'locked-wayland-1').exists())
        (self.work/'locked-wayland-1').unlink()
        (self.work/'reject').touch()
        self.assertNotEqual(self.run_script(script).returncode,0)
        runtime.chmod(0o755)
        self.assertNotEqual(self.run_script(script).returncode,0)
        pam.write_text('session required pam_permit.so\n')
        self.assertNotEqual(self.run_script(script).returncode,0)

    def test_runtime_mergers_are_provisioned_and_work_from_installed_paths(self):
        source=(ROOT/'scripts/configure-system.sh').read_text()
        start=source.index('for helper in merge-mdo merge-block ssid-hex; do')
        loop=source[start:source.index('\ndone',start)+len('\ndone')]
        script='set -eu\nrepo='+shlex.quote(str(ROOT))+'\nstage='+shlex.quote(str(self.work))+'\n'
        script+='sf_put() { mkdir -p "$stage${2%/*}"; cp "$1" "$stage$2"; chmod "$3" "$stage$2"; }\n'+loop
        subprocess.run(['sh','-c',script],check=True)
        merger=self.work/'usr/local/share/nostromo/merge-block.awk'
        replacement=self.work/'replacement'
        replacement.write_text('new network\n')
        result=subprocess.run(['awk','-v','name=WIFI test','-v',f'replacement={replacement}',
                               '-f',str(merger)],input='unrelated network\n',text=True,capture_output=True,check=True)
        self.assertIn('unrelated network\n',result.stdout)
        self.assertIn('new network\n',result.stdout)
        self.assertEqual(merger.stat().st_mode & 0o777,0o644)
        decoder=self.work/'usr/local/share/nostromo/ssid-hex.awk'
        self.assertEqual(subprocess.check_output(['awk','-f',str(decoder)],input='Lab\\x20WiFi\n',text=True),'4c61622057694669\n')

    def test_sleep_button_dispatch_and_resume_debounce(self):
        source=(ROOT/'src/session/events.c').read_text()
        queue=source[source.index('static void queue_action('):source.index('static void geometry(')]
        events=source[source.index('static bool has('):source.index('static int connect_devd(')]
        test=self.work/'events.c'
        test.write_text('''#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
static const char *pending;
static int64_t pending_at, resumed_until, now=1000;
static int64_t milliseconds(void) { return now; }
''' + queue + events + '''
int main(void) {
    device_event("!system=ACPI subsystem=Button notify=0x01");
    assert(pending && !strcmp(pending,"sleep") && pending_at==1200);
    device_event("!system=ACPI subsystem=Resume notify=0x03");
    assert(!pending);
    device_event("!system=ACPI subsystem=Button notify=0x01");
    assert(!pending);
    now=3000;
    device_event("!system=ACPI subsystem=Button notify=0x01");
    assert(pending && !strcmp(pending,"sleep"));
    pending=NULL;
    device_event("!system=ACPI subsystem=Button notify=0x010");
    assert(!pending);
    device_event("!system=ACPI subsystem=Button notify=0x00");
    assert(!pending);
    device_event("!system=ACPI subsystem=Lid notify=0x00");
    device_event("!system=DRM subsystem=CONNECTOR");
    assert(pending && !strcmp(pending,"closed"));
    return 0;
}
''')
        binary=self.work/'events'
        subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(test),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
