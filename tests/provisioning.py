"""Selective merges and file rollback, in disposable files without root access."""
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Provisioning(unittest.TestCase):
    def test_system_helpers_fonts_login_and_loader_assets_reach_declared_paths(self):
        source = (ROOT/'scripts/configure-system.sh').read_text()
        helpers = 'sf_directory 755 /usr/local/etc/nostromo\n' + source.split(
            'sf_directory 755 /usr/local/etc/nostromo\n',1)[1].split('# This group grants',1)[0]
        assets = 'sf_put "$repo/system/nostromo-ac.conf"' + source.split(
            'sf_put "$repo/system/nostromo-ac.conf"',1)[1].split('# Keep the package',1)[0]
        block = (helpers+assets).replace('"$repo/.build/prefix/bin/wg"','"$stage/wg-fixture"')
        block = block.replace('/usr/local','$stage/usr/local').replace('/boot/','$stage/boot/')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()
            (path/'work').mkdir()
            (path/'wg-fixture').write_text('compiled binary placeholder\n')
            script = 'set -eu\nrepo='+shlex.quote(str(ROOT))+'\nstage='+shlex.quote(str(path))+'\n'
            script += '''work=$stage/work
sf_safe() { case $1 in "$stage"/*) return 0 ;; *) return 1 ;; esac; }
sf_directory() { sf_safe "$2"; mkdir -p "$2"; chmod "$1" "$2"; }
sf_put() {
    sf_safe "$2"
    mkdir -p "${2%/*}"
    cp "$1" "$2"
    chmod "$3" "$2"
    printf '%s|%s|%s\\n' "$1" "$2" "$3" >> "$stage/copied"
}
''' + block
            result = subprocess.run(['sh','-c',script],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            for row in (path/'copied').read_text().splitlines():
                original,target,mode = row.split('|')
                self.assertEqual(Path(target).read_bytes(),Path(original).read_bytes(),target)
                self.assertEqual(Path(target).stat().st_mode & 0o777,int(mode,8),target)
            expected = [
                *('usr/local/libexec/nostromo-'+name for name in
                  ('session','sddm-session','performance','wifi','wireguard','bluetooth','maintenance','device','suspend','lock-session','wg')),
                *('usr/local/etc/rc.d/'+name for name in ('nostromo_mdo','nostromo_performance','nostromo_wireguard')),
                *('usr/local/share/nostromo/'+name+'.awk' for name in ('merge-mdo','merge-block','ssid-hex')),
                'usr/local/etc/devd/nostromo-ac.conf','usr/local/etc/devd/nostromo-suspend.conf',
                'usr/local/etc/pam.d/gtklock','usr/local/etc/sddm.conf',
                'usr/local/share/nostromo/nostromo-orb.png','boot/images/nostromo-orb.png',
                'boot/lua/gfx-nostromo.lua','usr/local/share/nostromo/wayland-sessions/nostromo.desktop',
                *('usr/local/share/fonts/nostromo/'+font.name for font in (ROOT/'assets/fonts').iterdir() if font.is_file()),
                *('usr/local/share/sddm/themes/nostromo/'+file.name for file in (ROOT/'system/sddm/theme').iterdir()),
            ]
            for relative in expected:
                self.assertTrue((path/relative).is_file(),relative)

    def test_library_receipt_accepts_unversioned_sonames(self):
        # The T14's receipt at 73816d3: wlroots and Lua install libraries without a
        # version suffix, and the stricter check stopped system-configuration.
        native = '''libatk-1.0.so.0 libatk-bridge-2.0.so.0 libatspi.so.0 libbasu.so.0 libbrotlicommon.so.1
            libbrotlidec.so.1 libcairo-gobject.so.2 libcairo.so.2 libdatrie.so.1 libdbus-1.so.3 libdisplay-info.so.4
            libdrm.so.2 libEGL.so.1 libepoll-shim.so.0 libepoxy.so.0 libevdev.so.2 libexpat.so.1 libfcft.so.4
            libffi.so.8 libfontconfig.so.1 libfreetype.so.6 libfribidi.so.0 libgbm.so.1 libgdk_pixbuf-2.0.so.0
            libgdk-3.so.0 libgio-2.0.so.0 libGLdispatch.so.0 libGLESv2.so.2 libglib-2.0.so.0 libgmodule-2.0.so.0
            libgobject-2.0.so.0 libgraphite2.so.3 libgtk-3.so.0 libgtk-layer-shell.so.0 libgtk-session-lock.so.0
            libgudev-1.0.so.0 libharfbuzz.so.0 libiconv.so.2 libinput.so.10 libintl.so.8 liblcms2.so.2
            libliftoff.so.0 liblua-5.4.so libmtdev.so.1 libpango-1.0.so.0 libpangocairo-1.0.so.0 libpangoft2-1.0.so.0
            libpcre2-8.so.0 libpcsclite.so.1 libpixman-1.so.0 libpng16.so.16 libseat.so.1 libthai.so.0 libudev.so.0
            libutf8proc.so.3 libwacom.so.9 libwayland-client.so.0 libwayland-cursor.so.0 libwayland-egl.so.1
            libwayland-server.so.0 libwlroots-0.20.so libX11.so.6 libXau.so.6 libxcb-render.so.0 libxcb-shm.so.0
            libxcb.so.1 libXcomposite.so.1 libXcursor.so.1 libXdamage.so.1 libXdmcp.so.6 libXext.so.6 libXfixes.so.3
            libXi.so.6 libXinerama.so.1 libxkbcommon.so.0 libXrandr.so.2 libXrender.so.1 libXRes.so.1'''.split()
        source = (ROOT/'scripts/configure-system.sh').read_text()
        check = "awk 'NF!=1" + source.split("awk 'NF!=1",1)[1].split('sf_put "$repo/.build/local-libraries"',1)[0]
        def run(lines):
            with tempfile.TemporaryDirectory() as directory:
                receipt = Path(directory)/'local-libraries'
                receipt.write_text(''.join(line+'\n' for line in lines))
                script = 'set -eu\n' + check.replace('"$repo/.build/local-libraries"',shlex.quote(str(receipt)))
                return subprocess.run(['sh','-c',script],capture_output=True,text=True)
        self.assertEqual(len(native),78)
        result = run(native)
        self.assertEqual((result.returncode,result.stderr),(0,''))
        for bad in ('/usr/local/lib/libfoo.so.1','libfoo.so.1 extra','foo.so.1','libfoo.so.1a',
                    'libfoo.so.','libfoo.so.1.','libfoo','libfoo.a',''):
            result = run(['libgtk-3.so.0',bad])
            self.assertNotEqual(result.returncode,0,bad)
            self.assertIn('Unexpected library name: '+bad+'\n',result.stderr)
        result = run([])
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Staged validation recorded no libraries.',result.stderr)

    def test_installed_font_check_accepts_variable_font_family_lists(self):
        # Fontconfig names every instance of the variable Azeret Mono
        # "Azeret Mono,Azeret Mono Thin" (2.17.1 on the T14).
        if shutil.which('fc-match') is None:
            self.skipTest('fontconfig is not installed')
        source = (ROOT/'scripts/verify-stage.sh').read_text()
        check = 'for family in Michroma' + source.split('    for family in Michroma',1)[1].split('    nostromo-dev health',1)[0]
        def run(fonts):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                (path/'fonts.conf').write_text('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">\n'
                    f'<fontconfig><dir>{fonts}</dir><cachedir>{path}/cache</cachedir></fontconfig>\n')
                return subprocess.run(['sh','-c','set -eu\n'+check],capture_output=True,text=True,
                    env={**os.environ,'FONTCONFIG_FILE':str(path/'fonts.conf')})
        result = run(ROOT/'assets/fonts')
        self.assertEqual((result.returncode,result.stderr),(0,''))
        with tempfile.TemporaryDirectory() as fonts:
            shutil.copy(ROOT/'assets/fonts/Michroma-Regular.ttf',fonts)
            result = run(fonts)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Fontconfig does not resolve Azeret Mono to the installed font.',result.stderr)

    def installer_run(self, path, body, *, setup='', boot=1):
        source = (ROOT/'install.sh').read_text()
        lifecycle = source.split('mkdir -p /var/log/nostromo\n',1)[1].split('freebsd-version -kru',1)[0]
        script = 'set -eu\numask 077\n' + setup + '\nmkdir -p /var/log/nostromo\n' + lifecycle
        script += '''
printf '15.1-RELEASE\\n' > "$log/release-before"
printf 'uid=1000(fixture)\\n' > "$log/account-before"
''' + body
        for original, local in [('/var/log/nostromo','logs'), ('/var/run/','run/'), ('/var/tmp/','tmp/'),
                                ('/var/backups/','backups/'), ('/var/db/','db/'), ('/usr/local/share/nostromo','share'),
                                ('/usr/local/libexec','libexec'), ('/usr/local/sbin/pkg','bin/pkg'),
                                ('/usr/sbin/fwget','bin/fwget')]:
            # pathlib drops a trailing slash; keep it so run/<lock> stays inside run/.
            script = script.replace(original, str(path/local) + ('/' if local.endswith('/') else ''))
        # The console prompt writes and reads separate fixture files.
        script = script.replace('>/dev/tty', '>'+str(path/'tty-prompt')).replace('</dev/tty', '<'+str(path/'tty-answer'))
        # Root identity is modeled; filesystem modes and symlinks stay real.
        script = script.replace('-user root', '-user '+str(os.getuid()))
        (path/'run').mkdir(exist_ok=True)
        (path/'bin').mkdir(exist_ok=True)
        stat = path/'bin/stat'
        stat.write_text(f'#!{sys.executable}\n' + '''
import os, sys
s=os.stat(sys.argv[-1]); birth=getattr(s, 'st_birthtime', s.st_mtime)
print(sys.argv[-2].replace('%u','0').replace('%Lp',oct(s.st_mode & 0o777)[2:]).replace('%m',str(int(s.st_mtime))).replace('%B',str(int(birth))))
''')
        stat.chmod(0o755)
        # The boot time decides whether a lock directory predates this boot.
        sysctl = path/'bin/sysctl'
        sysctl.write_text(f"#!/bin/sh\necho '{{ sec = {boot}, usec = 0 }} Thu Jan  1 00:00:01 1970'\n")
        sysctl.chmod(0o755)
        return subprocess.run(['sh','-c',script], capture_output=True, text=True,
            env={**os.environ, 'PATH':str(path/'bin')+':'+os.environ['PATH'], 'REPO':str(ROOT)})

    def test_install_retry_keeps_only_its_own_logs_and_no_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()
            logs = path/'logs'
            logs.mkdir()
            for number in range(10):
                previous = logs/f'install-{number:08d}'
                previous.mkdir(mode=0o700)
                (previous/'release-before').write_text('15.1-RELEASE\n')
                (previous/'account-before').write_text('fixture\n')
                # Legacy runs have no result marker, only stage statuses.
                (previous/'python312-dependencies.status').write_text('1\n')
                if number==6:
                    (previous/'system-backup').mkdir()
                    (previous/'system-backup/journal').write_text('1|/etc/rc.conf|644|digest|yes\n')
                    (previous/'system-backup/1.before').write_text('original\n')
                if number==7: (previous/'policy-backup').mkdir()
                # The lock is held, so a run without a result ended without its handler.
                if number==8: (previous/'python312-dependencies.status').write_text('0\n')
                if number==9: previous.chmod(0o777)
                os.utime(previous, (number+1,number+1))
            outside = path/'outside'
            outside.mkdir()
            (outside/'keep').write_text('keep\n')
            (logs/'install-symlink1').symlink_to(outside)
            # Deleting a log's child symlink must not follow it.
            (logs/'install-00000000/link').symlink_to(outside)
            os.utime(logs/'install-00000000', (1,1))
            result = self.installer_run(path, 'run python312-dependencies sh -c "exit 7"\n')
            self.assertEqual(result.returncode, 7, result.stderr)
            self.assertFalse((path/'run/nostromo-install.lock').exists())
            retained = {p.name for p in logs.iterdir()}
            self.assertIn('install-00000009', retained)
            # Backups go with their run's logs; nothing is archived.
            self.assertFalse({f'install-{n:08d}' for n in range(9)} & retained)
            self.assertNotIn('recovery', retained)
            self.assertIn('Removed old install log:', result.stdout)
            self.assertNotIn('Archived', result.stdout)
            self.assertNotIn('unfinished', result.stdout)
            self.assertIn('Retained unrecognized or unsafe log directory:', result.stdout)
            self.assertTrue((logs/'install-symlink1').is_symlink())
            self.assertEqual((outside/'keep').read_text(), 'keep\n')
            current = next(p for p in logs.iterdir() if (p/'result').is_file())
            self.assertEqual((current/'result').read_text(), 'failed\n')
            self.assertEqual((current/'exit-status').read_text(), '7\n')
            self.assertEqual((current/'last-stage').read_text(), 'python312-dependencies\n')
            self.assertIn(str(current), result.stderr)

    def test_install_cleans_temporary_policy_and_unlocks_on_failure_or_signal(self):
        for setup, body, code in [
            ('', 'policy=$(mktemp -d "$REPO_TEMP/.policy.XXXXXXXX")\nexit 19\n', 19),
            ('', 'policy=$(mktemp -d "$REPO_TEMP/.policy.XXXXXXXX")\nkill -TERM $$\n', 143),
            ('mktemp() { return 23; }', '', 23),
        ]:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                path = Path(directory).resolve()
                result = self.installer_run(path, body, setup='REPO_TEMP='+str(path)+'\n'+setup)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertFalse(list(path.glob('.policy.*')))
                self.assertFalse((path/'run/nostromo-install.lock').exists())

    def test_install_lock_is_reclaimed_only_after_its_boot(self):
        dead = subprocess.Popen(['true'])
        dead.wait()
        later = int(time.time()) + 3600
        # Power loss leaves the lock directory; its owner cannot survive a reboot.
        for boot, owner, code in [(later, None, 0), (later, dead.pid, 0), (later, os.getpid(), 1),
                                  (1, None, 1), (1, dead.pid, 1)]:
            with self.subTest(boot=boot, owner=owner), tempfile.TemporaryDirectory() as directory:
                path = Path(directory).resolve()
                lock = path/'run/nostromo-install.lock'
                lock.mkdir(parents=True)
                if owner: (lock/'pid').write_text(f'{owner}\n')
                result = self.installer_run(path, '[ "$(cat "$lock/pid")" = "$$" ]\n', boot=boot)
                self.assertEqual(result.returncode, code, result.stderr)
                if code:
                    self.assertIn('Another install holds', result.stderr)
                    self.assertEqual(sorted(p.name for p in lock.iterdir()), ['pid'] if owner else [])
                    self.assertFalse(list((path/'logs').glob('install-*')))
                else:
                    self.assertIn('Removed the lock of an install interrupted before the last boot.', result.stdout)
                    self.assertFalse(lock.exists())

    def test_install_cleanup_removes_stale_workspaces_locks_and_old_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()
            for name in ('share/.policy.AbCd1234', 'share/policy', 'share/policy.previous.20261105-140800-34264',
                         'tmp/nostromo-system.AbCd1234', 'tmp/nostromo-maintenance.AbCd1234',
                         'run/nostromo-wifi-setup.lock', 'run/nostromo-packages.lock',
                         'logs/recovery/install-00000006/system-backup', 'backups/nostromo/wifi-20261105-140800-34264'):
                (path/name).mkdir(parents=True)
            (path/'share/.policy.AbCd1234/packages.allowed').write_text('partial\n')
            (path/'share/policy.previous.20261105-140800-34264/managed').write_text('earlier policy\n')
            (path/'logs/recovery/install-00000006/system-backup/1.before').write_text('original\n')
            (path/'backups/nostromo/wifi-20261105-140800-34264/1.before').write_text('network={}\n')
            (path/'run/nostromo-packages.lock/pid').write_text(f'{os.getpid()}\n')
            setup = 'as_user() { printf "as_user: %s\\n" "$1"; }\n'
            result = self.installer_run(path, 'run cleanup sweep\n', setup=setup, boot=int(time.time()) + 3600)
            self.assertEqual(result.returncode, 0, result.stderr)
            # The Wi-Fi lock from an earlier boot goes first, so its backups go too.
            for removed in ('share/.policy.AbCd1234', 'tmp/nostromo-system.AbCd1234', 'run/nostromo-wifi-setup.lock',
                            'share/policy.previous.20261105-140800-34264', 'logs/recovery', 'backups/nostromo'):
                self.assertFalse((path/removed).exists(), removed)
            # A running owner keeps its lock; the active policy and other tools' workspaces stay.
            for kept in ('run/nostromo-packages.lock/pid', 'share/policy', 'tmp/nostromo-maintenance.AbCd1234'):
                self.assertTrue((path/kept).exists(), kept)
            self.assertIn('as_user: sh scripts/clean-build.sh', result.stdout)
            # The preflight has just removed loose checkout modes; only final cleanup repeats it.
            self.assertNotIn('checkout-modes', result.stdout)
            log = next((path/'logs').glob('install-*'))
            text = (log/'cleanup.log').read_text()
            self.assertIn('Removed a lock left by an earlier boot:', text)
            self.assertIn('Removed an old backup: '+str(path/'logs/recovery'), text)
            self.assertEqual((log/'cleanup.status').read_text(), '0\n')
            # A lock taken during this boot may still have a running owner, and a
            # Wi-Fi setup holding its lock may still need its backup.
            for name in ('run/nostromo-bluetooth.lock', 'run/nostromo-wifi-setup.lock',
                         'backups/nostromo/wifi-20261110-172400-4242'):
                (path/name).mkdir(parents=True)
            again = self.installer_run(path, 'run cleanup sweep\n', setup=setup)
            self.assertEqual(again.returncode, 0, again.stderr)
            for kept in ('run/nostromo-bluetooth.lock', 'run/nostromo-wifi-setup.lock',
                         'backups/nostromo/wifi-20261110-172400-4242'):
                self.assertTrue((path/kept).is_dir(), kept)

    def test_clean_install_offer_removes_earlier_packages_state_and_build_output(self):
        source = (ROOT/'install.sh').read_text()
        offer = 'stage=clean-offer\n' + source.split('stage=clean-offer\n',1)[1].split('esac\n',1)[0] + 'esac\n'
        prompt = ('A clean install removes every package except pkg, base and detected firmware,\n'
                  'then the package state and build output; this run builds everything again.\n'
                  'Start with a clean install? [y/N] ')
        for answer, other, held, installed, cleaned in [('y\n', False, False, True, True), ('y\n', False, False, False, True),
                                                       ('n\n', False, False, True, False), ('', False, False, True, False),
                                                       ('y\n', True, False, True, False), ('y\n', False, True, True, False)]:
            with self.subTest(answer=answer, other=other, held=held, installed=installed), \
                    tempfile.TemporaryDirectory() as directory:
                path = Path(directory).resolve()
                (path/'tty-answer').write_text(answer)
                (path/'share/policy').mkdir(parents=True)
                (path/'db/nostromo/packages/local').mkdir(parents=True)
                (path/'db/nostromo/packages/local/python312.pkg').write_text('variant\n')
                if held: (path/'run/nostromo-packages.lock').mkdir(parents=True)
                # A staged port's read-only directory with an entry, as CUPS stages one.
                repo = path/'repo'
                certs = repo/'.build/ports-work/cups/work/stage/var/run/cups/certs'
                certs.mkdir(parents=True)
                (certs/'0').write_text('certificate\n')
                certs.chmod(0o511)
                outside = path/'outside'
                outside.mkdir()
                (outside/'keep').write_text('keep\n')
                outside.chmod(0o500)
                (repo/'.build/link').symlink_to(outside)
                shells = path/'shells'
                shells.mkdir()
                for shell in ('oksh', 'bash'): (shells/shell).write_text('shell\n')
                (path/'bin').mkdir()
                (path/'bin/fwget').write_text('#!/bin/sh\necho wifi-firmware-iwlwifi-kmod-22000\n')
                (path/'bin/fwget').chmod(0o755)
                calls = shlex.quote(str(path/'calls'))
                if installed:
                    # pkgtool clears the environment, so the stub names its files.
                    (path/'bin/pkg').write_text(f'''#!/bin/sh
[ "$1" != -C ] || shift 2
printf 'pkg %s\\n' "$*" >>{calls}
case $1:$3 in
'query:%n|%o|%k|%V') printf '%s\\n' 'pkg|ports-mgmt/pkg|0|0' 'git|devel/git|0|0' 'curl|ftp/curl|1|0' \\
    'oksh|shells/oksh|0|0' 'bash|shells/bash|0|0' 'FreeBSD-runtime|base|0|1' \\
    'wifi-firmware-iwlwifi-kmod-22000|net/wifi-firmware-iwlwifi-kmod|0|0' ;;
'query:%n|%dn') echo 'git|curl' ;;
which:{shells}/oksh) echo shells/oksh ;;
which:{shells}/bash) echo shells/bash ;;
which:*) exit 1 ;;
esac
''')
                    (path/'bin/pkg').chmod(0o755)
                # uucp keeps the shell of a port that is not installed.
                accounts = ['root:*:0:0:Charlie:/root:/bin/sh', f'fixture:*:1000:1000::/home/fixture:{shells}/oksh',
                            'uucp:*:66:66::/var/spool/uucppublic:/usr/local/libexec/uucp/uucico']
                if other: accounts.append(f'admin:*:1001:1001::/home/admin:{shells}/bash')
                setup = f'''account=fixture
as_user() {{ (cd "{repo}" && NOSTROMO_REPO="{repo}" sh -c "set -eu; $1"); }}
pw() {{
    case $* in
    'usershow -a -7') printf '%s\\n' {' '.join(shlex.quote(account) for account in accounts)} ;;
    *) printf 'pw %s\\n' "$*" >>{calls} ;;
    esac
}}
'''
                result = self.installer_run(path, offer, setup=setup)
                self.assertEqual((path/'tty-prompt').read_text(), prompt)
                made = (path/'calls').read_text().splitlines() if (path/'calls').exists() else []
                kept = [p for p in ('share/policy', 'db/nostromo/packages', 'repo/.build') if (path/p).exists()]
                if cleaned:
                    self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                    # pkg, base, vital packages and detected firmware stay; the desktop
                    # account's packaged shell is reset; locked variants are unlocked first.
                    self.assertEqual(made, ['pkg query -a %n|%o|%k|%V', 'pkg query -a %n|%dn', 'pkg which -qo /bin/sh',
                                            f'pkg which -qo {shells}/oksh', 'pw usermod fixture -s /bin/sh',
                                            'pkg unlock -y curl', 'pkg delete -y git curl oksh bash',
                                            'pkg clean -a -y'] if installed else [])
                    self.assertEqual(kept, [])
                    self.assertEqual((outside/'keep').read_text(), 'keep\n')
                    self.assertEqual(outside.stat().st_mode & 0o777, 0o500)
                    log = (next((path/'logs').glob('install-*'))/'clean-install.log').read_text()
                    self.assertIn('Removed installer state: '+str(path/'db/nostromo/packages'), log)
                    self.assertIn('Removed the build output: '+str(repo/'.build'), log)
                else:
                    self.assertEqual(kept, ['share/policy', 'db/nostromo/packages', 'repo/.build'])
                    self.assertFalse([call for call in made if 'delete' in call or 'usermod' in call], made)
                    if answer.startswith('y'):
                        self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
                        self.assertIn('Setup stopped at clean-install', result.stderr)
                        self.assertIn(f'Give admin a base login shell first; {shells}/bash goes with its package.'
                                      if other else 'nostromo-packages.lock', result.stdout)
                    else:
                        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                        self.assertFalse(list((path/'logs').glob('install-*/clean-install.log')))
                outside.chmod(0o755)
                if certs.exists(): certs.chmod(0o755)

    def test_python_requirements_check_sees_shared_system_packages(self):
        # uv pip check reads only the environment's own site-packages, so the wheels'
        # requirements met by reviewed system packages looked missing.
        source = (ROOT/'scripts/development-tools.sh').read_text()
        checker = source.split("-I - <<'EOF'\n",1)[1].split('\nEOF\n',1)[0]
        if subprocess.run([sys.executable,'-I','-c','import packaging.requirements']).returncode:
            self.skipTest('this Python lacks packaging, which the native environments share')
        with tempfile.TemporaryDirectory() as directory:
            environment = Path(directory)/'environment'
            subprocess.run([sys.executable,'-m','venv','--system-site-packages','--without-pip',str(environment)],
                           check=True)
            python = str(environment/'bin/python')
            purelib = Path(subprocess.run([python,'-I','-c','import sysconfig; print(sysconfig.get_path("purelib"))'],
                                          check=True,capture_output=True,text=True).stdout.strip())
            metadata = purelib/'fixture-1.0.dist-info/METADATA'
            metadata.parent.mkdir(parents=True)
            requirements = ['packaging>=20', 'pytest; extra == "dev"', 'tomli>=1.1.0; python_version < "3.11"']
            for extra, failures in [([], []),
                                    (['nostromo-missing-fixture', 'packaging<1'],
                                     ['fixture requires nostromo-missing-fixture; found none.',
                                      'fixture requires packaging<1; found '])]:
                with self.subTest(extra=extra):
                    metadata.write_text('Metadata-Version: 2.1\nName: fixture\nVersion: 1.0\n' +
                                        ''.join('Requires-Dist: '+line+'\n' for line in requirements+extra))
                    result = subprocess.run([python,'-I','-'],input=checker,capture_output=True,text=True)
                    self.assertEqual(result.returncode, 1 if failures else 0, result.stderr)
                    lines = result.stderr.splitlines()
                    self.assertEqual(len(lines), len(failures), result.stderr)
                    for line, expected in zip(lines, failures):
                        self.assertTrue(line.startswith(expected), line)

    def test_final_cleanup_removes_this_runs_backups_only_after_the_final_check(self):
        source = (ROOT/'install.sh').read_text()
        ending = 'run final-check final_check\n' + source.split('run final-check final_check\n',1)[1]
        setup = 'account=fixture\nas_user() { printf "as_user: %s\\n" "$1"; }\n'
        backups = 'mkdir "$log/system-backup" "$log/policy-backup"\nprintf original > "$log/system-backup/1.before"\n'
        for checks, code in [('true', 0), ('false', 1)]:
            with self.subTest(checks=checks), tempfile.TemporaryDirectory() as directory:
                path = Path(directory).resolve()
                # With an active policy, the exit handler leaves the policy backup in place.
                (path/'share/policy').mkdir(parents=True)
                (path/'tty-answer').write_text('n\n')
                body = backups + 'run cleanup sweep\nfinal_check() { ' + checks + '; }\n' + ending
                result = self.installer_run(path, body, setup=setup)
                self.assertEqual(result.returncode, code, result.stderr)
                log = next((path/'logs').glob('install-*'))
                # The first cleanup keeps this run's own rollback copies.
                self.assertEqual((log/'cleanup.status').read_text(), '0\n')
                for name in ('system-backup', 'policy-backup'):
                    self.assertEqual((log/name).exists(), bool(code), name)
                if code:
                    self.assertFalse((log/'final-cleanup.log').exists())
                else:
                    text = (log/'final-cleanup.log').read_text()
                    self.assertIn('Removed a backup: '+str(log/'system-backup'), text)
                    self.assertIn('as_user: sh scripts/checkout-modes.sh --apply', text)
                    self.assertIn('Setup completed for fixture.', result.stdout)
        # Loose modes that cannot be removed stop the run before it reports success.
        failing = 'account=fixture\nas_user() { printf "as_user: %s\\n" "$1"; case $1 in *checkout-modes*) return 1 ;; esac; }\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()
            (path/'share/policy').mkdir(parents=True)
            (path/'tty-answer').write_text('n\n')
            body = backups + 'run cleanup sweep\nfinal_check() { true; }\n' + ending
            result = self.installer_run(path, body, setup=failing)
            self.assertEqual(result.returncode, 1, result.stderr)
            log = next((path/'logs').glob('install-*'))
            self.assertEqual((log/'final-cleanup.status').read_text(), '1\n')
            self.assertNotIn('Setup completed', result.stdout)

    def test_final_check_requires_login_shell_sddm_and_current_locked_variants(self):
        def setup(shell='/usr/local/bin/oksh', sddm='YES', lock='1', recipe='current', verified='0'):
            return f'''repo=$REPO
account=fixture
as_user() {{ printf 'as_user: %s\\n' "$1"; return {verified}; }}
pw() {{ printf 'fixture:*:1000:1000::/home/fixture:{shell}\\n'; }}
sysrc() {{ printf '{sddm}\\n'; }}
pkg() {{
    case $2 in
    '%v|%k') awk -F '|' -v name="$3" '$1==name {{print $3 "|" (name=="cups" ? "{lock}" : "1")}}' "$repo/packages.local" ;;
    *) if [ "$3" = cups ]; then echo 'nostromo_recipe|{recipe}'; else echo 'nostromo_recipe|current'; fi ;;
    esac
}}
'''
        for options, message in [({}, None), ({'verified': '1'}, ''), ({'shell': '/bin/sh'}, 'The login shell is not oksh.'),
                                 ({'sddm': 'NO'}, 'SDDM is not enabled at boot.'),
                                 ({'lock': '0'}, 'The cups variant is not installed'),
                                 ({'recipe': 'earlier'}, 'The cups variant is not installed')]:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                path = Path(directory).resolve()
                (path/'share/policy').mkdir(parents=True)
                (path/'share/policy/recipe.sha256').write_text('current\n')
                result = self.installer_run(path, 'run final-check final_check\n', setup=setup(**options))
                self.assertIn("as_user: sh scripts/verify-stage.sh --installed", result.stdout)
                if message is None:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn('Final checks passed for fixture.', result.stdout)
                else:
                    self.assertEqual(result.returncode, 1, result.stdout)
                    self.assertIn(message, result.stdout)
                    self.assertIn('Setup stopped at final-check', result.stderr)

    def test_completed_install_offers_reboot_after_releasing_its_lock(self):
        for answer, rebooted in [('\n', True), ('y\n', True), ('n\n', False), ('', False)]:
            with self.subTest(answer=answer), tempfile.TemporaryDirectory() as directory:
                path = Path(directory).resolve()
                (path/'tty-answer').write_text(answer)
                setup = f'shutdown() {{ [ ! -e "{path}/run/nostromo-install.lock" ] && echo "$*" > "{path}/shutdown"; }}\n'
                result = self.installer_run(path, 'stage=reboot\n', setup=setup)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual((path/'tty-prompt').read_text(), 'Reboot into the new desktop now? [Y/n] ')
                self.assertEqual((path/'shutdown').read_text() if rebooted else (path/'shutdown').exists(),
                                 '-r now\n' if rebooted else False)
                if not rebooted: self.assertIn('Reboot when ready', result.stdout)
                log = next((path/'logs').glob('install-*'))
                self.assertEqual((log/'result').read_text(), 'completed\n')
                self.assertEqual((log/'last-stage').read_text(), 'reboot\n')
        # A failed run never asks.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()
            (path/'tty-answer').write_text('y\n')
            result = self.installer_run(path, 'stage=reboot\nexit 3\n', setup='shutdown() { exit 99; }\n')
            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertFalse((path/'tty-prompt').exists())

    def test_build_cleanup_removes_only_stale_leftovers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()
            repo = path/'repo'
            (repo/'scripts').mkdir(parents=True)
            shutil.copy(ROOT/'scripts/clean-build.sh', repo/'scripts/clean-build.sh')
            shutil.copy(ROOT/'packages.local', repo/'packages.local')
            build = repo/'.build'
            workspaces = ['work/dwl.AbCd1234', 'validation.AbCd1234', 'ports.AbCd1234/previous']
            for name in workspaces: (build/name).mkdir(parents=True)
            (build/'downloads').mkdir()
            (build/'downloads/.download.AbCd1234').write_text('partial\n')
            for name in ('downloads/ports.tar.gz', 'ports.mtree', 'ports.recipe'): (build/name).write_text('keep\n')
            (build/'ports').mkdir()
            outside = path/'outside'
            outside.mkdir()
            (outside/'keep').write_text('keep\n')
            (build/'work/link.AbCd1234').symlink_to(outside)
            logs = [f'2026110{day}-120000-{100+day}' for day in range(1, 6)]
            for name in logs: (build/'logs'/name).mkdir(parents=True)
            archives = build/'ports-packages/All'
            archives.mkdir(parents=True)
            for name in ('python312-3.12.15.pkg', 'python312-3.12.14.pkg', 'ffmpeg-9.0.2,1.pkg', 'kicad-9.0.pkg'):
                (archives/name).write_text(name)
            state = path/'home/.local/state/freebsd-dotfiles'
            (state/'backups/20261110-180000-4242').mkdir(parents=True)
            (state/'backups/20261110-180000-4242/.profile').write_text('default profile\n')
            (state/'links').write_text('home/.profile|.profile\n')
            (path/'bin').mkdir()
            def clean(boot):
                sysctl = path/'bin/sysctl'
                sysctl.write_text(f"#!/bin/sh\necho '{{ sec = {boot}, usec = 0 }} Thu Jan  1 00:00:01 1970'\n")
                sysctl.chmod(0o755)
                return subprocess.run(['sh', str(repo/'scripts/clean-build.sh')], capture_output=True, text=True,
                                      env={**os.environ, 'HOME': str(path/'home'), 'PATH': str(path/'bin')+':'+os.environ['PATH']})
            # This boot's workspaces may belong to a running build.
            first = clean(1)
            self.assertEqual(first.returncode, 0, first.stderr)
            for name in workspaces: self.assertTrue((build/name).is_dir(), name)
            self.assertTrue((build/'downloads/.download.AbCd1234').is_file())
            self.assertEqual(sorted(p.name for p in (build/'logs').iterdir()), logs[2:])
            self.assertEqual(sorted(p.name for p in archives.iterdir()), ['ffmpeg-9.0.2,1.pkg', 'python312-3.12.15.pkg'])
            # User-file backups go; the record of installed links stays.
            self.assertEqual(sorted(p.name for p in state.iterdir()), ['links'])
            self.assertIn('Removed user-file backups: '+str(state/'backups'), first.stdout)
            (state/'backups').symlink_to(outside)
            # An earlier boot's leftovers are stale; links are not followed.
            second = clean(int(time.time()) + 3600)
            self.assertEqual(second.returncode, 0, second.stderr)
            for name in ('work/dwl.AbCd1234', 'validation.AbCd1234', 'ports.AbCd1234', 'downloads/.download.AbCd1234'):
                self.assertFalse((build/name).exists(), name)
            for name in ('downloads/ports.tar.gz', 'ports.mtree', 'ports.recipe', 'ports'):
                self.assertTrue((build/name).exists(), name)
            self.assertTrue((build/'work/link.AbCd1234').is_symlink())
            self.assertTrue((state/'backups').is_symlink())
            self.assertEqual((outside/'keep').read_text(), 'keep\n')
            self.assertIn('Removed a stale build workspace:', second.stdout)
            self.assertEqual(len(list((build/'logs').iterdir())), 3)

    def test_package_policy_is_reused_and_failed_publication_restores_previous(self):
        source = (ROOT/'install.sh').read_text()
        publish = 'stage=package-policy\n' + source.split('stage=package-policy\n',1)[1].split('install -m 755 "$repo/scripts/packages.sh"',1)[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()
            setup = '''repo=$REPO
sh() { if [ "$1" = "$repo/scripts/recipe-hash.sh" ]; then printf 'current\\n'; else command sh "$@"; fi; }
'''
            first = self.installer_run(path, publish, setup=setup)
            self.assertEqual(first.returncode, 0, first.stderr)
            active = path/'share/policy'
            inode = active.stat().st_ino
            second = self.installer_run(path, publish, setup=setup)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(active.stat().st_ino, inode, 'an unchanged policy should not be republished')
            self.assertFalse(list((path/'logs').glob('install-*/policy-backup')))
            self.assertFalse(list((path/'share').glob('.policy.*')))
            (active/'packages.allowed').chmod(0o666)
            unsafe = self.installer_run(path, publish, setup=setup)
            self.assertEqual(unsafe.returncode, 1, unsafe.stderr)
            self.assertIn('Unsafe installed package policy', unsafe.stderr)
            self.assertFalse(list((path/'share').glob('.policy.*')))
            (active/'packages.allowed').chmod(0o644)
            # Force a real change, then fail only the new directory's rename.
            original = (active/'packages.allowed').read_text()+'# retained policy fixture\n'
            (active/'packages.allowed').write_text(original)
            failure = setup + '''
mv() { case $1 in */.policy.*) return 29 ;; *) command mv "$@" ;; esac; }
'''
            third = self.installer_run(path, publish, setup=failure)
            self.assertEqual(third.returncode, 1, third.stderr)
            self.assertEqual((active/'packages.allowed').read_text(), original)
            self.assertFalse(list((path/'share').glob('.policy.*')))
            fourth = self.installer_run(path, publish, setup=setup)
            self.assertEqual(fourth.returncode, 0, fourth.stderr)
            backups = list((path/'logs').glob('install-*/policy-backup'))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0]/'packages.allowed').read_text(), original)
            # A later retry removes the earlier run's logs, its policy backup included.
            for _ in range(3):
                retry = self.installer_run(path, publish, setup=setup)
                self.assertEqual(retry.returncode, 0, retry.stderr)
            self.assertFalse(list((path/'logs').glob('install-*/policy-backup')))
            self.assertFalse((path/'logs/recovery').exists())
            self.assertEqual(len(list((path/'logs').glob('install-*'))), 1)

    def merge(self, script, original, policy=None, *options):
        with tempfile.TemporaryDirectory() as work:
            path = Path(work).resolve()
            (path / "original").write_text(original)
            args = ["awk", *options, "-f", str(ROOT / "scripts" / script)]
            if policy is not None:
                (path / "policy").write_text(policy)
                args.append(str(path / "policy"))
            return subprocess.run(args + [str(path / "original")], text=True, capture_output=True)

    def test_settings_preserve_other_assignments_and_refuse_continuations(self):
        policy = 'loader_logo="nostromo"\n'
        original = '# personal\nloader_logo="orb"\nzfs_load="YES"\nloader_logo="other"\n'
        result = self.merge("merge-settings.awk", original, policy)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '# personal\nzfs_load="YES"\n' + policy)
        self.assertEqual(self.merge("merge-settings.awk", result.stdout, policy).stdout, result.stdout)
        self.assertNotEqual(self.merge("merge-settings.awk", 'loader_logo="long\\\nname"\n', policy).returncode, 0)

    def test_sddm_merge_retains_other_keys_and_does_not_grow(self):
        policy = '[General]\nDisplayServer=wayland\n[Theme]\nCurrent=nostromo\n'
        original = '[General]\n# keep\nDisplayServer = x11\nHaltCommand=/custom/halt\n[Custom]\nA=7\n'
        result = self.merge("merge-ini.awk", original, policy)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('HaltCommand=/custom/halt\n[Custom]\nA=7', result.stdout)
        self.assertNotIn('x11', result.stdout)
        self.assertEqual(self.merge("merge-ini.awk", result.stdout, policy).stdout, result.stdout)

    def test_ssh_scope_ports_includes_and_malformed_markers(self):
        policy = '# BEGIN NOSTROMO SSH\nPort 2222\nPasswordAuthentication no\n# END NOSTROMO SSH\n'
        original = ('Port 22\nListenAddress "[::1]:22"\nInclude /etc/ssh/sshd_config.d/*.conf\n'
                    'Match User somebody\n    PasswordAuthentication yes\n    Banner /etc/banner\n')
        result = self.merge("merge-ssh.awk", original, policy)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('ListenAddress "[::1]:2222"', result.stdout)
        self.assertIn('Match User somebody\n    Banner /etc/banner', result.stdout)
        self.assertIn('Include /etc/ssh/sshd_config.d/*.conf', result.stdout)
        self.assertEqual(self.merge("merge-ssh.awk", result.stdout, policy).stdout, result.stdout)
        stripped = self.merge("merge-ssh.awk", original, policy, "-v", "strip_only=1")
        self.assertNotIn('Port ', stripped.stdout)
        self.assertNotIn('PasswordAuthentication', stripped.stdout)
        self.assertNotEqual(self.merge("merge-ssh.awk", '# END NOSTROMO SSH\n', policy).returncode, 0)

    def test_ssh_include_walk_strips_managed_keys_and_rejects_unsafe_paths(self):
        # The include walk had never run: FreeBSD's awk rejected its path pattern.
        source = (ROOT/'scripts/configure-security.sh').read_text()
        walk = 'security_ssh() {' + source.split('security_ssh() {',1)[1].split('\n}\n',1)[0] + '\n}\n'
        for include, okay in [('Include sshd_config.d/*.conf\nInclude "{ssh}/extra.conf"', True),
                              ('Include ../outside.conf', False), ('Include /usr/local/etc/ssh/other.conf', False)]:
            with self.subTest(include=include), tempfile.TemporaryDirectory() as directory:
                path = Path(directory).resolve()
                ssh = path/'etc/ssh'
                (ssh/'sshd_config.d').mkdir(parents=True)
                (path/'work').mkdir()
                files = {ssh/'sshd_config': 'Port 22\n' + include.format(ssh=ssh) + '\nPasswordAuthentication yes\n',
                         ssh/'sshd_config.d/10-port.conf': 'Port 2200\nPasswordAuthentication yes\nBanner none\n',
                         ssh/'extra.conf': 'PermitRootLogin yes\nInclude extra.conf\n'}
                for file, text in files.items():
                    file.write_text(text)
                (path/'policy').write_text((ROOT/'system/sshd_config').read_text().replace('@ACCOUNT@', 'fixture'))
                script = f'''set -eu
repo={shlex.quote(str(ROOT))}; work={shlex.quote(str(path/'work'))}; stage={shlex.quote(str(path))}
sf_safe() {{ case $1 in "$stage"/*) ;; *) return 1 ;; esac; }}
sf_put() {{ sf_safe "$2"; cp "$1" "$2"; chmod "$3" "$2"; }}
''' + walk.replace('/etc/ssh', str(ssh)) + 'security_ssh sshd "$stage/policy"\n'
                result = subprocess.run(['sh','-c',script], capture_output=True, text=True)
                if not okay:
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    for file, text in files.items():
                        self.assertEqual(file.read_text(), text, file)
                    continue
                self.assertEqual(result.returncode, 0, result.stderr)
                main = (ssh/'sshd_config').read_text()
                self.assertTrue(main.startswith('# BEGIN NOSTROMO SSH\nPort 2222\n'), main)
                self.assertNotIn('Port 22\n', main.split('# END NOSTROMO SSH\n',1)[1])
                self.assertNotIn('PasswordAuthentication yes', main)
                self.assertIn(f'Include "{ssh}/extra.conf"', main)
                # Included files only lose the managed keys; a self-include is read once.
                self.assertEqual((ssh/'sshd_config.d/10-port.conf').read_text(), 'Banner none\n')
                self.assertEqual((ssh/'extra.conf').read_text(), 'Include extra.conf\n')

    def test_pf_order_idempotency_and_name_collision(self):
        original = 'set skip on lo0\nblock out to 192.0.2.0/24\n'
        result = self.merge("merge-pf.awk", original)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(result.stdout.index('set skip'), result.stdout.index('pass out'))
        self.assertLess(result.stdout.index('pass out'), result.stdout.index('block out'))
        self.assertEqual(self.merge("merge-pf.awk", result.stdout).stdout, result.stdout)
        self.assertNotEqual(self.merge("merge-pf.awk", 'anchor "nostromo"\n').returncode, 0)
        self.assertNotEqual(self.merge("merge-pf.awk", 'set skip on em0\n').returncode, 0)
        self.assertNotEqual(self.merge("merge-pf.awk", 'include "/etc/private.pf"\n').returncode, 0)

    def test_file_rollback_keeps_later_edits_and_rejects_symlinks(self):
        # Only ownership and chown are modeled; real files, modes, rename and hashes run.
        with tempfile.TemporaryDirectory() as work:
            path = Path(work).resolve()
            (path / "source").write_text("new\n")
            (path / "old").write_text("old\n")
            (path / "old").chmod(0o600)
            script = r'''
set -eu
stat() {
    case $2 in
        '%u') printf '0\n' ;;
        '%u %Lp') printf '0 '; command stat -f '%Lp' "$3" ;;
        *) command stat "$@" ;;
    esac
}
install() {
    if [ "$1" = -d ]; then shift; shift 4; command install -d "$@"
    else shift 4; command install "$@"; fi
}
sha256() { shasum -a 256 "$2" | awk '{print $1}'; }
. "$REPO/scripts/system-files.sh"
sf_begin "$WORK/backup"
sf_put "$WORK/source" "$WORK/old" 644
sf_put "$WORK/source" "$WORK/new" 600
sf_put "$WORK/source" "$WORK/later" 600
printf 'administrator change\n' > "$WORK/later"
ln -s "$WORK/old" "$WORK/symlink"
if sf_put "$WORK/source" "$WORK/symlink" 644; then exit 3; fi
sf_rollback
'''
            result = subprocess.run(["sh", "-c", script], text=True, capture_output=True,
                                    env={**os.environ, "REPO": str(ROOT), "WORK": str(path)})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((path / "old").read_text(), "old\n")
            self.assertEqual((path / "old").stat().st_mode & 0o777, 0o600)
            self.assertFalse((path / "new").exists())
            self.assertEqual((path / "later").read_text(), "administrator change\n")
            self.assertTrue((path / "symlink").is_symlink())


if __name__ == "__main__":
    unittest.main(verbosity=2)
