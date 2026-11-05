#!/usr/bin/env python3
"""Host checks for migrated files; does not claim a native Wayland session."""
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class Migration(unittest.TestCase):
    def test_document_links(self):
        missing = []
        for doc in [ROOT / "README.md", ROOT / "PLANS.md", ROOT / "COPYING.md", *ROOT.glob("docs/**/*.md")]:
            if "research" in doc.parts:
                continue
            for target in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
                if target.startswith(("https:", "http:", "#", "mailto:")):
                    continue
                if not (doc.parent / unquote(target.split("#")[0])).exists():
                    missing.append(f"{doc.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])

    def test_fonts(self):
        directory = ROOT / "assets/fonts"
        for line in (directory / "SHA256").read_text().splitlines():
            match = re.fullmatch(r"SHA256 \((.+)\) = ([a-f0-9]{64})", line)
            self.assertIsNotNone(match, line)
            name, expected = match.groups()
            self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected)

    def test_install_manifest_covers_runtime_files_and_small_orb(self):
        rows=[line.split('|') for line in (ROOT/'links.txt').read_text().splitlines() if line and not line.startswith('#')]
        targets=[row[1] for row in rows]
        self.assertEqual(len(targets),len(set(targets)))
        sources={row[0] for row in rows}
        for path in (ROOT/'home').rglob('*'):
            if path.is_file() and path.suffix!='.pyc':self.assertIn(str(path.relative_to(ROOT)),sources)
        self.assertIn('assets/nostromo-orb-small.txt',sources)

    def test_reference_shader(self):
        shader = ROOT / "assets/references/space-dots-original.frag"
        self.assertEqual(hashlib.sha256(shader.read_bytes()).hexdigest(),
                         "f5b7d8fbd29f5a697b99ee5a6522578d80688a97628b9b6f9817edbeb6c4ef17")
        self.assertIn("Copyright 2023 Maxim Samoliuk", shader.read_text())

    def test_start_page_assets(self):
        self.assertEqual((ROOT / "assets/nostromo-orb.png").read_bytes(),
                         (ROOT / "home/.local/share/nostromo/nostromo-orb.png").read_bytes())
        page = ROOT / "home/.local/share/nostromo/start/index.html"
        for resource in re.findall(r'src="([^"]+)"', page.read_text()):
            self.assertTrue((page.parent / resource).is_file(), resource)

    def test_shell_syntax(self):
        files = [ROOT / "home/.profile", *ROOT.glob("*.sh"), *ROOT.glob("scripts/*.sh"),
                 *ROOT.glob("home/.local/bin/*"),
                 *ROOT.glob("home/.config/nostromo/*.conf")]
        for script in files:
            with self.subTest(script=script.name):
                subprocess.run(["/bin/sh", "-n", str(script)], check=True, capture_output=True)

    def test_no_x11_or_doas_runtime(self):
        for path in (ROOT / "home").rglob("*"):
            if not path.is_file() or path.suffix in (".pyc", ".png"):
                continue
            text = path.read_text()
            self.assertIsNone(re.search(r"\b(?:doas|tailscale|tailscaled|xclip|xrandr|xdotool|xenodm|picom|surf|tabbed)\b", text), str(path))
            self.assertNotIn("/usr/X11R6", text, str(path))

    def test_foot_config(self):
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(ROOT / "home/.config/foot/foot.ini")
        self.assertEqual(cfg["main"]["shell"], "/usr/local/bin/oksh")
        self.assertNotIn("colors", cfg)  # Obsolete on the checked foot version.
        self.assertEqual(cfg["colors-dark"]["alpha"], "0.90")
        self.assertEqual(cfg["colors-dark"]["alpha-mode"], "default")
        self.assertEqual(cfg["csd"]["preferred"], "server")
        combos = [key for value in cfg["key-bindings"].values() for key in value.split()]
        self.assertEqual(len(combos), len(set(combos)))

    def test_qutebrowser_option_names(self):
        options, bindings = {}, {}

        class Node:
            def __init__(self, prefix=""):
                object.__setattr__(self, "prefix", prefix)

            def __getattr__(self, name):
                return Node(self.prefix + name + ".")

            def __setattr__(self, name, value):
                options[self.prefix + name] = value

        class Config:
            def load_autoconfig(self):
                pass

            def set(self, name, value):
                options[name] = value

            def bind(self, key, command):
                bindings[key] = command

        with patch.dict(os.environ, {"XDG_DATA_HOME": "/tmp/home space/#data"}):
            runpy.run_path(str(ROOT / "home/.config/qutebrowser/config.py"),
                           init_globals={"config": Config(), "c": Node()})
        known = set(re.findall(r"^([a-z][a-z0-9_.]+):", (ROOT / "docs/research/qutebrowser-configdata.yml").read_text(), re.M))
        self.assertTrue(known)
        self.assertEqual(set(options) - known, set())
        self.assertEqual(options["qt.force_platform"], "wayland")
        self.assertEqual(options["url.start_pages"], ["file:///tmp/home%20space/%23data/nostromo/start/index.html"])
        self.assertEqual(options["editor.command"][:3], ["foot", "-e", "vis"])
        self.assertNotIn("j", bindings)  # Keep normal web navigation.


class Browser(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nostromo-test-")
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.home = self.directory / "home space # unicode-日"
        self.page = self.home / ".local/share/nostromo/start/index.html"
        self.page.parent.mkdir(parents=True)
        self.page.write_text("start")
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        fake = self.bin / "qutebrowser"
        fake.write_text(f"#!{sys.executable}\nimport json, os, sys\nprint(json.dumps([sys.argv[1:], os.environ['QT_QPA_PLATFORM']]))\n")
        fake.chmod(0o755)
        self.env = {**os.environ, "HOME": str(self.home), "PATH": f"{self.bin}:/usr/bin:/bin",
                    "XDG_DATA_HOME": str(self.home / ".local/share"),
                    "XDG_CONFIG_HOME": str(self.home / ".config"), "QT_QPA_PLATFORM": "xcb"}

    def launch(self, *args, **env):
        return subprocess.run(["/bin/sh", str(ROOT / "home/.local/bin/nostromo-browser"), *args],
                              env={**self.env, **env}, text=True, capture_output=True)

    def test_default_local_url(self):
        proc = self.launch()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        args, platform = json.loads(proc.stdout)
        self.assertEqual(args[0], "--")
        self.assertEqual(platform, "wayland")
        self.assertEqual(unquote(urlsplit(args[1]).path), str(self.page))

    def test_literal_multiple_arguments(self):
        urls = ["https://example.invalid/?a='quoted'&b=$(touch nope)", "words with spaces"]
        proc = self.launch(*urls)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)[0], ["--", *urls])

    def test_reject_options_and_qute_commands(self):
        for value in ("--no-sandbox", ":spawn sh", ""):
            with self.subTest(value=value):
                proc = self.launch(value)
                self.assertEqual(proc.returncode, 2)
                self.assertEqual(proc.stdout, "")

    def test_missing_page_and_relative_data(self):
        self.page.unlink()
        self.assertNotEqual(self.launch().returncode, 0)
        self.assertEqual(self.launch(XDG_DATA_HOME="relative").returncode, 2)

    def test_discord_only_real_http_url(self):
        config = self.home / ".config/nostromo"
        config.mkdir(parents=True)
        (config / "services.conf").write_text("DISCORD_URL=\n")
        self.assertEqual(self.launch("--discord").returncode, 1)
        (config / "services.local").write_text("DISCORD_URL='https://example.invalid/remote?x=1&y=2'\n")
        proc = self.launch("--discord")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)[0], ["--", "https://example.invalid/remote?x=1&y=2"])
        self.assertEqual(self.launch("--discord", "ignored").returncode, 2)

    def test_cwd_bytes_are_encoded(self):
        proc = subprocess.run(["/bin/sh", str(ROOT / "home/.local/bin/nostromo-cwd")],
                              cwd=self.home, capture_output=True, check=True)
        self.assertTrue(proc.stdout.startswith(b"\x1b]2;NOSTROMO_CWD:file:///"))
        self.assertTrue(proc.stdout.endswith(b"\x07"))
        uri = proc.stdout.split(b"\x1b]7;", 1)[1][:-1].decode("ascii")
        self.assertEqual(Path(unquote(urlsplit(uri).path)), self.home.resolve())


@unittest.skipIf(os.geteuid() == 0, "user file installation intentionally refuses root")
class UserInstaller(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="nostromo-install-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "checkout with spaces"
        self.home = self.base / "home"
        self.repo.mkdir()
        self.home.mkdir()
        (self.repo / "scripts").mkdir()
        shutil.copy(ROOT / "scripts/link-home.sh", self.repo / "scripts/link-home.sh")
        ((self.repo / "new").resolve()).write_text("new content")
        (self.repo / "links.txt").write_text("new|.profile\n")
        (self.home / ".profile").write_text("keep my original")

    def install(self, *args, **env):
        return subprocess.run(["sh", str(self.repo / "scripts/link-home.sh"), "--target", str(self.home), *args],
                              env={**os.environ, **env}, capture_output=True, text=True)

    def test_preview_backup_and_retry(self):
        self.assertEqual(self.install().returncode, 0)
        self.assertFalse((self.home / ".profile").is_symlink())
        result = self.install("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list(self.home.glob(".local/state/freebsd-dotfiles/backups/*/.profile"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "keep my original")
        self.assertEqual((self.home / ".profile").resolve(), (self.repo / "new").resolve())
        self.assertEqual(self.install("--apply").returncode, 0)
        self.assertEqual(len(list(self.home.glob(".local/state/freebsd-dotfiles/backups/*/.profile"))), 1)

    def test_preflight_stops_before_any_writes(self):
        (self.repo / "links.txt").write_text("new|.profile\nmissing|.config/fail\n")
        self.assertNotEqual(self.install("--apply").returncode, 0)
        self.assertEqual((self.home / ".profile").read_text(), "keep my original")
        (self.repo / "links.txt").write_text("new|.profile\nnew|.config/fail\n")
        (self.home / ".config").symlink_to(self.base, target_is_directory=True)
        self.assertNotEqual(self.install("--apply").returncode, 0)
        self.assertFalse((self.home / ".profile").is_symlink())

    def test_failed_link_restores_replaced_files(self):
        tools = self.base / "tools"
        tools.mkdir()
        bad = tools / "ln"
        bad.write_text("#!/bin/sh\nexit 23\n")
        bad.chmod(0o755)
        result = self.install("--apply", PATH=str(tools) + ":/usr/bin:/bin")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertEqual((self.home / ".profile").read_text(), "keep my original")
        self.assertFalse((self.home / ".profile").is_symlink())


if __name__ == "__main__":
    unittest.main(verbosity=2)
