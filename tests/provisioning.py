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

    def installer_run(self, path, body, *, setup='', boot=1):
        source = (ROOT/'install.sh').read_text()
        lifecycle = source.split('mkdir -p /var/log/nostromo\n',1)[1].split('freebsd-version -kru',1)[0]
        script = 'set -eu\numask 077\n' + setup + '\nmkdir -p /var/log/nostromo\n' + lifecycle
        script += '''
printf '15.1-RELEASE\\n' > "$log/release-before"
printf 'uid=1000(fixture)\\n' > "$log/account-before"
''' + body
        for original, local in [('/var/log/nostromo','logs'), ('/var/run/','run/'), ('/var/tmp/','tmp/'),
                                ('/usr/local/share/nostromo','share'), ('/usr/local/libexec','libexec')]:
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

    def test_install_retry_bounds_logs_and_preserves_recovery_data(self):
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
                if number in (5,6):
                    (previous/'system-backup').mkdir()
                    (previous/'system-backup/journal').touch()
                if number==6:
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
            self.assertFalse({f'install-{n:08d}' for n in range(9)} & retained)
            self.assertEqual((logs/'recovery/install-00000006/system-backup/1.before').read_text(), 'original\n')
            self.assertTrue((logs/'recovery/install-00000007/policy-backup').is_dir())
            # A backup with an empty journal holds no original file.
            self.assertEqual(sorted(p.name for p in (logs/'recovery').iterdir()),
                             ['install-00000006', 'install-00000007'])
            self.assertIn('Removed old install log:', result.stdout)
            self.assertIn('Archived recovery data:', result.stdout)
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

    def test_install_cleanup_removes_stale_workspaces_and_locks_and_archives_old_policies(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()
            for name in ('share/.policy.AbCd1234', 'share/policy', 'share/policy.previous.20261105-140800-34264',
                         'tmp/nostromo-system.AbCd1234', 'tmp/nostromo-maintenance.AbCd1234',
                         'run/nostromo-wifi-setup.lock', 'run/nostromo-packages.lock'):
                (path/name).mkdir(parents=True)
            (path/'share/.policy.AbCd1234/packages.allowed').write_text('partial\n')
            (path/'share/policy.previous.20261105-140800-34264/managed').write_text('earlier policy\n')
            (path/'run/nostromo-packages.lock/pid').write_text(f'{os.getpid()}\n')
            setup = 'as_user() { printf "as_user: %s\\n" "$1"; }\n'
            result = self.installer_run(path, 'run cleanup sweep\n', setup=setup, boot=int(time.time()) + 3600)
            self.assertEqual(result.returncode, 0, result.stderr)
            for removed in ('share/.policy.AbCd1234', 'tmp/nostromo-system.AbCd1234', 'run/nostromo-wifi-setup.lock'):
                self.assertFalse((path/removed).exists(), removed)
            # A running owner keeps its lock; the active policy and other tools' workspaces stay.
            for kept in ('run/nostromo-packages.lock/pid', 'share/policy', 'tmp/nostromo-maintenance.AbCd1234'):
                self.assertTrue((path/kept).exists(), kept)
            self.assertEqual((path/'logs/recovery/policy.previous.20261105-140800-34264/managed').read_text(),
                             'earlier policy\n')
            self.assertFalse(list((path/'share').glob('policy.previous.*')))
            self.assertIn('as_user: sh scripts/clean-build.sh', result.stdout)
            log = next((path/'logs').glob('install-*'))
            self.assertIn('Removed a lock left by an earlier boot:', (log/'cleanup.log').read_text())
            self.assertEqual((log/'cleanup.status').read_text(), '0\n')
            # A lock taken during this boot may still have a running owner.
            (path/'run/nostromo-bluetooth.lock').mkdir()
            again = self.installer_run(path, 'run cleanup sweep\n', setup=setup)
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertTrue((path/'run/nostromo-bluetooth.lock').is_dir())

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
            (path/'bin').mkdir()
            def clean(boot):
                sysctl = path/'bin/sysctl'
                sysctl.write_text(f"#!/bin/sh\necho '{{ sec = {boot}, usec = 0 }} Thu Jan  1 00:00:01 1970'\n")
                sysctl.chmod(0o755)
                return subprocess.run(['sh', str(repo/'scripts/clean-build.sh')], capture_output=True, text=True,
                                      env={**os.environ, 'PATH': str(path/'bin')+':'+os.environ['PATH']})
            # This boot's workspaces may belong to a running build.
            first = clean(1)
            self.assertEqual(first.returncode, 0, first.stderr)
            for name in workspaces: self.assertTrue((build/name).is_dir(), name)
            self.assertTrue((build/'downloads/.download.AbCd1234').is_file())
            self.assertEqual(sorted(p.name for p in (build/'logs').iterdir()), logs[2:])
            self.assertEqual(sorted(p.name for p in archives.iterdir()), ['ffmpeg-9.0.2,1.pkg', 'python312-3.12.15.pkg'])
            # An earlier boot's leftovers are stale; links are not followed.
            second = clean(int(time.time()) + 3600)
            self.assertEqual(second.returncode, 0, second.stderr)
            for name in ('work/dwl.AbCd1234', 'validation.AbCd1234', 'ports.AbCd1234', 'downloads/.download.AbCd1234'):
                self.assertFalse((build/name).exists(), name)
            for name in ('downloads/ports.tar.gz', 'ports.mtree', 'ports.recipe', 'ports'):
                self.assertTrue((build/name).exists(), name)
            self.assertTrue((build/'work/link.AbCd1234').is_symlink())
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
            # A later retry must retain recovery data while rotating ordinary logs.
            for _ in range(3):
                retry = self.installer_run(path, publish, setup=setup)
                self.assertEqual(retry.returncode, 0, retry.stderr)
            archived = path/'logs/recovery'/backups[0].parent.name/'policy-backup'
            self.assertTrue(archived.is_dir())
            self.assertEqual((archived/'packages.allowed').read_text(), original)
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
