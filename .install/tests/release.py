#!/usr/bin/env python3
"""Exercise source exports in disposable Git repositories; never stage this tree."""
import hashlib
import os
from pathlib import Path
import pwd
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class Release(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="nostromo-release-")
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name) / "checkout"
        self.repo.mkdir()
        self.env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull}
        for name in (".install/scripts", "bin", "oksh", "system"):
            shutil.copytree(ROOT / name, self.repo / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in (".gitignore", ".gitattributes", "install.sh", ".install/packages.local"):
            shutil.copy2(ROOT / name, self.repo / name)
        (self.repo / ".install/links.txt").write_text("oksh/profile|.profile\n")
        (self.repo / "README.md").write_text("Disposable export fixture.\n")
        self.git("init", "-q")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=self.env,
                              check=True, text=True, capture_output=True)

    def export(self):
        return subprocess.run(["sh", ".install/scripts/export.sh"], cwd=self.repo,
                              env=self.env, text=True, capture_output=True)

    def test_archive_includes_dotfiles_and_excludes_private_files(self):
        excluded = (".build/cache", ".env", "docs/key.pem",
                    "nostromo/services.local",
                    "vis/local.lua", "ssh/id_ed25519")
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
        self.assertIn("bin/nostromo-menu", files)
        self.assertIn(".install/packages.local", files)
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
            helper = source.getmember("freebsd-dotfiles/bin/nostromo-menu")
            self.assertTrue(helper.mode & 0o111)
        self.assertEqual(self.git("diff", "--cached", "--name-only").stdout,
                         "README.md\n")
        self.assertFalse(any((self.repo / ".dist").glob(".export.*")))

    def test_rejects_tracked_private_and_generated_files(self):
        for name in ("nostromo/services.local", "docs/key.pem",
                     "docs/editor.swp", ".build/cache", "art/orb.svg",
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
        path.symlink_to(".install/links.txt")
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
        def installer(*args):
            return subprocess.run(["sh", "install.sh", *args], cwd=self.repo, capture_output=True, text=True)
        for args in (("--preview",), ("--help",), ("--preview", "alice")):
            result = installer(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("setup for the desktop account:", installer("--preview").stdout)
        self.assertIn("setup for alice:", installer("--preview", "alice").stdout)
        self.assertFalse((self.repo / ".build").exists())
        # Only the four modes exist; anything else shows them.
        for args in ((), ("--apply", "alice"), ("--wifi",), ("--dry-run",), ("alice",), ("--check", "alice", "bob")):
            result = installer(*args)
            self.assertEqual(result.returncode, 2, args)
            self.assertIn("--preview [account] | --check account | --clean account | --upgrade account", result.stderr)
        # No account is built in: each mode that acts names its own before anything else runs.
        for flag in ("--check", "--clean", "--upgrade"):
            result = installer(flag)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Name the desktop account:", result.stderr)
        for args in (("--check", "root"), ("--clean", "Alice"), ("--upgrade", "-x"), ("--preview", "../x")):
            result = installer(*args)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Use an ordinary local account name.", result.stderr)
        if os.uname().sysname != "FreeBSD" or os.getuid() != 0:
            for flag in ("--check", "--clean", "--upgrade"):
                result = installer(flag, "alice")
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
        for mode, expected in (("check", 0), ("clean", 99), ("upgrade", 99)):
            with self.subTest(mode=mode):
                result = subprocess.run(["sh", "-eu"], text=True, capture_output=True,
                                        input=f"mode={mode}\naccount=fixture\n" + stat + block + "exit 99\n")
                self.assertEqual(result.returncode, expected, result.stderr)
                if mode == "check":
                    self.assertIn("No installation performed", result.stdout)

    def test_preflight_checks_ownership_then_lists_or_removes_loose_modes(self):
        script = (ROOT / "install.sh").read_text()
        start = script.index("as_user '{ [") + len("as_user '")
        end = script.index("'\n# Check lists what clean and upgrade remove", start)
        self.assertIn("\nif [ \"$mode\" = check ]; then\n    as_user 'sh .install/scripts/checkout-modes.sh --check'\nelse\n"
                      "    as_user 'sh .install/scripts/checkout-modes.sh --apply'\nfi\numask 077\nfor path in", script[end:])
        checkout = self.repo.parent.resolve() / "owned"
        checkout.mkdir()
        env = {"PATH": os.environ["PATH"], "HOME": str(checkout), "USER": pwd.getpwuid(os.getuid()).pw_name,
               "NOSTROMO_REPO": str(checkout), "NOSTROMO_UID": str(os.getuid())}
        result = subprocess.run(["sh", "-c", 'set -eu; umask 022; cd "$NOSTROMO_REPO"; ' + script[start:end]],
                                env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_checkout_modes_are_listed_by_check_and_removed_by_apply(self):
        checkout = self.repo.parent.resolve() / "modes"
        (checkout / ".install/scripts").mkdir(parents=True)
        shutil.copy2(ROOT / ".install/scripts/checkout-modes.sh", checkout / ".install/scripts")
        tool = checkout / ".install/scripts/tool.sh"
        tool.write_text("#!/bin/sh\n")
        port = checkout / ".build/ports-work" / str(checkout).lstrip("/") / ".build/ports/print/cups"
        # CUPS stages these package modes; a flavored port stages under work-<flavor>.
        staged = {}
        for relative, mode in (("work/stage/var/spool/cups/tmp", 0o1770), ("work/stage/var/cache/cups", 0o770),
                               ("work/stage/var/cache/cups/rss", 0o775), ("work-py312/stage/var/tmp", 0o1777)):
            (port / relative).mkdir(parents=True)
            (port / relative).chmod(mode)
            staged[port / relative] = mode
        def modes(flag):
            return subprocess.run(["sh", str(checkout / ".install/scripts/checkout-modes.sh"), flag],
                                  text=True, capture_output=True)
        for flag in ("--check", "--apply"):
            result = modes(flag)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        # uv 0.12.19 created its environment locks mode 0666 on the T14 (2026-11-11).
        lock = checkout / ".build/python-lsp/.lock"
        lock.parent.mkdir(parents=True)
        lock.touch()
        build = port / "work/cups-2.4.20"
        build.mkdir()
        loose = {tool: 0o664, build: 0o775, lock: 0o666}
        for path, mode in loose.items():
            path.chmod(mode)
        # chmod would follow a link out of the checkout; a link's own mode grants nothing.
        outside = self.repo.parent.resolve() / "outside"
        outside.write_text("another file\n")
        outside.chmod(0o666)
        link = checkout / ".build/link"
        link.symlink_to(outside)
        if hasattr(os, "lchmod"):
            os.lchmod(link, 0o777)
        result = modes("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("install.sh --clean and --upgrade remove group/world write from the paths above.", result.stdout)
        self.assertNotIn("./.build/link\n", result.stdout)
        for path, mode in loose.items():
            self.assertIn("./" + str(path.relative_to(checkout)) + "\n", result.stdout)
            self.assertEqual(path.stat().st_mode & 0o7777, mode, path)
        result = modes("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Removed group/world write from the paths above.", result.stdout)
        for path, mode in {**loose, **staged}.items():
            self.assertEqual(path.stat().st_mode & 0o7777, mode & 0o7755 if path in loose else mode, path)
        self.assertEqual(outside.stat().st_mode & 0o777, 0o666)
        self.assertEqual(modes("--check").stdout, "")
        # Apply stops on a mode it cannot change and names the path. FreeBSD's tmpfs has no file flags.
        with self.subTest(flags="immutable"):
            tool.chmod(0o664)
            try:
                os.chflags(tool, stat.UF_IMMUTABLE)
            except (AttributeError, OSError):
                self.skipTest("this filesystem cannot mark a file immutable")
            self.addCleanup(os.chflags, tool, 0)
            result = modes("--apply")
            self.assertEqual(result.returncode, 1)
            self.assertIn("./.install/scripts/tool.sh\n", result.stderr)
            self.assertIn("Group/world write remains on the paths above", result.stderr)


if __name__ == "__main__":
    unittest.main()
