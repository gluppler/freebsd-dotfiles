"""Selective merges and file rollback, in disposable files without root access."""
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Provisioning(unittest.TestCase):
    def installer_run(self, path, body, *, setup=''):
        source = (ROOT/'install.sh').read_text()
        lifecycle = source.split('mkdir -p /var/log/nostromo\n',1)[1].split('freebsd-version -kru',1)[0]
        script = 'set -eu\numask 077\n' + setup + '\nmkdir -p /var/log/nostromo\n' + lifecycle
        script += '''
printf '15.1-RELEASE\\n' > "$log/release-before"
printf 'uid=1000(fixture)\\n' > "$log/account-before"
''' + body
        for original, local in [('/var/log/nostromo','logs'), ('/var/run/','run/'),
                                ('/usr/local/share/nostromo','share'), ('/usr/local/libexec','libexec')]:
            script = script.replace(original, str(path/local))
        # Root identity is modeled; filesystem modes and symlinks stay real.
        script = script.replace('-user root', '-user '+str(os.getuid()))
        (path/'run').mkdir(exist_ok=True)
        (path/'bin').mkdir(exist_ok=True)
        stat = path/'bin/stat'
        stat.write_text(f'#!{sys.executable}\n' + '''
import os, sys
s=os.stat(sys.argv[-1]); print(sys.argv[-2].replace('%u','0').replace('%Lp',oct(s.st_mode & 0o777)[2:]).replace('%m',str(int(s.st_mtime))))
''')
        stat.chmod(0o755)
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
                if number==6: (previous/'system-backup').mkdir()
                if number==7: (previous/'policy-backup').mkdir()
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
            self.assertTrue({f'install-{n:08d}' for n in range(4,10)} <= retained)
            self.assertFalse({f'install-{n:08d}' for n in range(4)} & retained)
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
            self.assertTrue(backups[0].is_dir())
            self.assertEqual(len(list((path/'logs').glob('install-*'))), 4)

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
