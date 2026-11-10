#!/usr/bin/env python3
"""Exercise source exports in disposable Git repositories; never stage this tree."""
import hashlib
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Release(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="nostromo-release-")
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name) / "checkout"
        self.repo.mkdir()
        self.env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull}
        for name in ("scripts", "home", "system"):
            shutil.copytree(ROOT / name, self.repo / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in (".gitignore", ".gitattributes", "install.sh", "packages.local"):
            shutil.copy2(ROOT / name, self.repo / name)
        (self.repo / "links.txt").write_text("home/.profile|.profile\n")
        (self.repo / "README.md").write_text("Disposable export fixture.\n")
        self.git("init", "-q")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=self.env,
                              check=True, text=True, capture_output=True)

    def export(self):
        return subprocess.run(["sh", "scripts/export.sh"], cwd=self.repo,
                              env=self.env, text=True, capture_output=True)

    def test_archive_includes_dotfiles_and_excludes_private_files(self):
        excluded = (".build/cache", ".env", "docs/key.pem",
                    "home/.config/nostromo/services.local",
                    "home/.config/vis/local.lua", "home/.ssh/id_ed25519")
        for name in excluded:
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("not for publication\n")
        self.git("add", "README.md")  # Include both indexed and new source files.
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        archives = list((self.repo / ".dist").glob("*.tar.gz"))
        self.assertEqual(len(archives), 1)
        archive = archives[0]
        expected = hashlib.sha256(archive.read_bytes()).hexdigest()
        self.assertEqual(Path(str(archive) + ".sha256").read_text(),
                         f"SHA256 ({archive.name}) = {expected}\n")
        files = Path(str(archive) + ".files").read_text().splitlines()
        self.assertIn("home/.local/bin/nostromo-menu", files)
        self.assertIn("packages.local", files)
        self.assertIn("README.md", files)
        self.assertTrue(set(files).isdisjoint(excluded))
        with tarfile.open(archive) as source:
            members = source.getmembers()
            self.assertEqual([m.name for m in members],
                             ["freebsd-dotfiles/" + f for f in files])
            for member in members:
                self.assertTrue(member.isfile(), member.name)
                self.assertEqual((member.uid, member.gid), (0, 0))
                self.assertFalse(member.mode & 0o6022, member.name)
                self.assertFalse(member.pax_headers, member.name)
            helper = source.getmember("freebsd-dotfiles/home/.local/bin/nostromo-menu")
            self.assertTrue(helper.mode & 0o111)
        self.assertEqual(self.git("diff", "--cached", "--name-only").stdout,
                         "README.md\n")
        self.assertFalse(any((self.repo / ".dist").glob(".export.*")))

    def test_rejects_tracked_private_and_generated_files(self):
        for name in ("home/.config/nostromo/services.local", "docs/key.pem",
                     "docs/editor.swp", ".build/cache", "assets/orb.svg",
                     "docs/assets/desktop.png"):
            with self.subTest(name=name):
                path = self.repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("private fixture\n")
                self.git("add", "-f", "--", name)
                result = self.export()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(name, result.stderr)
                self.git("rm", "--cached", "--", name)
                path.unlink()
        self.assertFalse(any((self.repo / ".dist").glob("*.tar.gz")))

    def test_rejects_credentials_without_echoing_them(self):
        values = ["-----BEGIN " + "PRIVATE KEY-----",
                  "ghp_" + "a" * 36, "github_pat_" + "b" * 40,
                  "AKIA" + "C" * 16, "xoxb-" + "d" * 30,
                  "https://example.invalid/?token=" + "e" * 32,
                  "PrivateKey = " + "f" * 43 + "=",
                  "https://" + "user:password@example.invalid/",
                  "/" + "Users" + "/example/private-file"]
        path = self.repo / "docs" / "private.txt"
        path.parent.mkdir(exist_ok=True)
        for value in values:
            with self.subTest(kind=values.index(value)):
                path.write_text(value + "\n")
                result = self.export()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("docs/private.txt", result.stderr)
                self.assertNotIn(value, result.stderr + result.stdout)
        self.assertFalse(any((self.repo / ".dist").glob("*.tar.gz")))

    def test_rejects_unsafe_modes_and_symlinks(self):
        path = self.repo / "README.md"
        for mode in (0o664, 0o646, 0o666):
            with self.subTest(mode=oct(mode)):
                path.chmod(mode)
                self.assertIn("Unsafe source permissions", self.export().stderr)
        path.chmod(0o644)
        path.unlink()
        path.symlink_to("links.txt")
        self.assertIn("regular source file", self.export().stderr)

    def test_rejects_symlinked_parent_of_tracked_file(self):
        directory = self.repo / "docs"
        directory.mkdir()
        (directory / "example.md").write_text("fixture\n")
        self.git("add", "docs/example.md")
        outside = self.repo.parent / "outside"
        directory.rename(outside)
        directory.symlink_to(outside, target_is_directory=True)
        with (self.repo / ".gitignore").open("a") as ignore:
            ignore.write("\n/docs\n")
        self.assertIn("Symlinked export directory", self.export().stderr)

    def test_installer_preview_and_host_guard(self):
        for flag in ("--preview", "--help"):
            result = subprocess.run(["sh", "install.sh", flag], cwd=self.repo,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.repo / ".build").exists())
        if os.uname().sysname != "FreeBSD" or os.getuid() != 0:
            for flag in ("--check", "--apply", "--wifi"):
                result = subprocess.run(["sh", "install.sh", flag], cwd=self.repo,
                                        capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("root console on the FreeBSD", result.stderr)
        (self.repo / 'system/nostromo-suspend').unlink()
        result = self.export()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing system install source: system/nostromo-suspend', result.stderr)
        self.assertFalse(any((self.repo / '.dist').glob('*.tar.gz')))

    def test_readonly_preflight_stops_before_installation(self):
        script = (ROOT / "install.sh").read_text()
        start = script.index("umask 077\nfor path in")
        end = script.index("mkdir -p /var/log/nostromo\n", start)
        block = script[start:end]
        for original, name in (("/var/log/nostromo", "logs"),
                               ("/usr/local/share/nostromo", "share")):
            path = self.repo.parent.resolve() / name
            path.mkdir()
            block = block.replace(original, str(path))
        # macOS has different owners; keep the real directory and branch checks.
        stat = "stat() { case $2 in %u) echo 0 ;; %Lp) echo 755 ;; *) return 1 ;; esac; }\n"
        for mode, expected in (("check", 0), ("apply", 99)):
            with self.subTest(mode=mode):
                result = subprocess.run(["sh", "-eu"], text=True, capture_output=True,
                                        input=f"mode={mode}\naccount=fixture\n" + stat + block + "exit 99\n")
                self.assertEqual(result.returncode, expected, result.stderr)
                if mode == "check":
                    self.assertIn("No installation performed", result.stdout)

    def test_preflight_mode_check_exempts_only_staged_ports(self):
        script = (ROOT / "install.sh").read_text()
        start = script.index("as_user '{ [") + len("as_user '")
        command = script[start:script.index("'\numask 077\n", start)]
        checkout = self.repo.parent.resolve() / "modes"
        (checkout / "scripts").mkdir(parents=True)
        tool = checkout / "scripts/tool.sh"
        tool.write_text("#!/bin/sh\n")
        port = checkout / ".build/ports-work" / str(checkout).lstrip("/") / ".build/ports/print/cups"
        # CUPS stages these package modes; a flavored port stages under work-<flavor>.
        for relative, mode in (("work/stage/var/spool/cups/tmp", 0o1770), ("work/stage/var/cache/cups", 0o770),
                               ("work/stage/var/cache/cups/rss", 0o775), ("work-py312/stage/var/tmp", 0o1777)):
            (port / relative).mkdir(parents=True)
            (port / relative).chmod(mode)
        env = {"PATH": os.environ["PATH"], "HOME": str(checkout), "USER": pwd.getpwuid(os.getuid()).pw_name,
               "NOSTROMO_REPO": str(checkout), "NOSTROMO_UID": str(os.getuid())}
        def check():
            return subprocess.run(["sh", "-c", 'set -eu; umask 022; cd "$NOSTROMO_REPO"; ' + command],
                                  env=env, text=True, capture_output=True)
        result = check()
        self.assertEqual(result.returncode, 0, result.stderr)
        build = port / "work/cups-2.4.20"
        build.mkdir()
        for path, mode in ((tool, 0o664), (build, 0o775)):
            with self.subTest(path=path):
                path.chmod(mode)
                result = check()
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("./" + str(path.relative_to(checkout)) + "\n", result.stderr)
                self.assertIn("group/world-writable paths above", result.stderr)
                path.chmod(mode & 0o755)


if __name__ == "__main__":
    unittest.main()
