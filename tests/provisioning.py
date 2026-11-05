"""Selective merges and file rollback, in disposable files without root access."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Provisioning(unittest.TestCase):
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
