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
# FreeBSD's NetBSD mtree exits 2 for changed content but only reports missing and
# extra files. Receipt checks must therefore treat any report as a change.
NETBSD_MTREE = f'#!{sys.executable}\n' + r'''
import hashlib, os, sys
args = sys.argv[1:]
root = args[args.index('-p') + 1]
def walk():
    found = {}
    for directory, dirs, files in os.walk(root):
        for name in dirs + files:
            path = os.path.join(directory, name)
            found[os.path.relpath(path, root)] = 'dir' if os.path.isdir(path) else \
                hashlib.sha256(open(path, 'rb').read()).hexdigest()
    return found
if '-c' in args:
    print('#\t   tree: ' + root)
    for name, value in sorted(walk().items()): print(name + '\t' + value)
    sys.exit()
spec = dict(line.rstrip('\n').split('\t') for line in open(args[args.index('-f') + 1]) if line[0] != '#')
found, status = walk(), 0
for name, value in spec.items():
    if name not in found: print(name + ' missing')
    elif found[name] != value: print(name + ': sha256digest changed'); status = 2
for name in sorted(found.keys() - spec.keys()): print('extra: ' + name)
sys.exit(status)
'''


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

    def test_complete_home_manifest_lands_at_each_declared_destination(self):
        rows = [line.split('|') for line in (ROOT/'links.txt').read_text().splitlines()
                if line and not line.startswith('#')]
        for source, _destination in rows:
            staged = self.repo/source
            staged.parent.mkdir(parents=True,exist_ok=True)
            if source.startswith('.build/'):
                # Build products are placeholders here; native ELF checks are
                # performed separately before the installer links them.
                staged.write_text('build-product fixture\n')
            elif (ROOT/source).is_dir():
                shutil.copytree(ROOT/source,staged,dirs_exist_ok=True)
            else:
                shutil.copy2(ROOT/source,staged)
        shutil.copy2(ROOT/'links.txt',self.repo/'links.txt')
        for _ in range(2):
            result = self.install('--apply')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            for source,destination in rows:
                target = self.home/destination
                self.assertTrue(target.is_symlink(),destination)
                self.assertEqual(os.readlink(target),str(self.repo.resolve()/source))
                self.assertEqual(target.resolve(),(self.repo/source).resolve())

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

    def test_links_that_leave_the_manifest_are_removed_only_while_unchanged(self):
        record = self.home / ".local/state/freebsd-dotfiles/links"
        (self.repo / "links.txt").write_text("new|.profile\nnew|.config/old\nnew|.config/kept\n")
        self.assertEqual(self.install("--apply").returncode, 0)
        self.assertEqual(record.read_text(), "new|.profile\nnew|.config/old\nnew|.config/kept\n")
        # A link the user replaced is no longer the project's file.
        (self.home / ".config/kept").unlink()
        (self.home / ".config/kept").write_text("mine")
        (self.repo / "links.txt").write_text("new|.profile\n")
        preview = self.install()
        self.assertIn("Remove former link: " + str(self.home.resolve() / ".config/old"), preview.stdout)
        self.assertTrue((self.home / ".config/old").is_symlink())
        result = self.install("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.home / ".config/old").is_symlink())
        self.assertEqual((self.home / ".config/kept").read_text(), "mine")
        self.assertIn("Retained a changed former link", result.stderr)
        self.assertTrue((self.home / ".profile").is_symlink())
        self.assertEqual(record.read_text(), "new|.profile\n")

    def test_failed_run_restores_removed_former_links(self):
        record = self.home / ".local/state/freebsd-dotfiles/links"
        (self.repo / "links.txt").write_text("new|.profile\nnew|.config/old\n")
        self.assertEqual(self.install("--apply").returncode, 0)
        tools = self.base / "tools"
        tools.mkdir()
        (tools / "ln").write_text('#!/bin/sh\ncase "$*" in *.config/new*) exit 23 ;; esac\nexec /bin/ln "$@"\n')
        (tools / "ln").chmod(0o755)
        (self.repo / "links.txt").write_text("new|.profile\nnew|.config/new\n")
        result = self.install("--apply", PATH=str(tools) + ":/usr/bin:/bin")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertEqual(os.readlink(self.home / ".config/old"), str(self.repo.resolve() / "new"))
        self.assertFalse((self.home / ".config/new").is_symlink())
        self.assertEqual(record.read_text(), "new|.profile\nnew|.config/old\n")
        self.assertEqual(sorted(p.name for p in record.parent.iterdir()), ["backups", "links"])

    def test_a_former_directory_link_can_become_a_directory_of_links(self):
        (self.repo / "tree").mkdir()
        (self.repo / "tree/rc").write_text("rc")
        (self.repo / "links.txt").write_text("tree|.config/tool\n")
        self.assertEqual(self.install("--apply").returncode, 0)
        (self.repo / "links.txt").write_text("tree/rc|.config/tool/rc\n")
        result = self.install("--apply")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.home / ".config/tool").is_symlink())
        self.assertEqual(os.readlink(self.home / ".config/tool/rc"), str(self.repo.resolve() / "tree/rc"))
        self.assertEqual((self.repo / "tree/rc").read_text(), "rc")

    def test_a_former_link_changed_after_preflight_is_never_linked_through(self):
        (self.repo / "tree").mkdir()
        (self.repo / "tree/rc").write_text("rc")
        (self.repo / "links.txt").write_text("tree|.config/tool\n")
        self.assertEqual(self.install("--apply").returncode, 0)
        # The second lookup reports another target, as if the link changed after preflight.
        tools, seen = self.base / "tools", self.base / "seen"
        tools.mkdir()
        (tools / "readlink").write_text(
            "#!/bin/sh\n"
            f'case $1 in */.config/tool) [ -e "{seen}" ] && {{ echo /elsewhere; exit; }}; : >"{seen}" ;; esac\n'
            'exec /usr/bin/readlink "$@"\n')
        (tools / "readlink").chmod(0o755)
        (self.repo / "links.txt").write_text("tree/rc|.config/tool/rc\n")
        result = self.install("--apply", PATH=str(tools) + ":/usr/bin:/bin")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Former link changed during this run", result.stderr)
        self.assertTrue((self.home / ".config/tool").is_symlink())
        self.assertFalse((self.repo / "tree/rc").is_symlink())
        self.assertEqual((self.repo / "tree/rc").read_text(), "rc")


class EditorPlugins(unittest.TestCase):
    def test_new_pins_replace_only_unedited_plugins(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            repo, tools = base / "repo", base / "bin"
            for path in (repo / "scripts", tools):
                path.mkdir(parents=True)
            shutil.copy(ROOT / "scripts/stage-licenses.sh", repo / "scripts")
            source = (ROOT / "scripts/editor-plugins.sh").read_text()
            pinned = "197cb50834c642f84b4cf99fe724932c50e6d9c92faec7ad89aa25e91df4d481"
            self.assertIn(pinned, source)
            tools.joinpath("uname").write_text("#!/bin/sh\necho FreeBSD\n")
            tools.joinpath("fetch").write_text(f'#!/bin/sh\ncp "{base}/dkjson" "$2"\n')
            tools.joinpath("sha256").write_text('#!/bin/sh\nshasum -a 256 "$2" | cut -d " " -f 1\n')
            tools.joinpath("mtree").write_text(NETBSD_MTREE)
            for tool in tools.iterdir():
                tool.chmod(0o755)
            editor = repo / ".build/editor"
            plugin, library = editor / "vis-lspc/init.lua", editor / "dkjson.lua"

            def pin(version, served=None):
                # Each version stands in for a new sources.lock or dkjson pin.
                (repo / "scripts/fetch-source.sh").write_text(
                    f'mkdir -p "$2"\nprintf "MIT\\n" >"$2/LICENSE"\nprintf -- "-- {version}\\n" >"$2/init.lua"\n')
                (base / "dkjson").write_text(served or f"-- dkjson {version}\n")
                digest = hashlib.sha256(f"-- dkjson {version}\n".encode()).hexdigest()
                (repo / "scripts/editor-plugins.sh").write_text(source.replace(pinned, digest))
                result = subprocess.run(["sh", str(repo / "scripts/editor-plugins.sh")], capture_output=True,
                                        text=True, env={**os.environ, "PATH": f"{tools}:/usr/bin:/bin"})
                self.assertEqual(list((repo / ".build/work").iterdir()), [])
                return result

            for version in ("1", "1"):
                result = pin(version)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((plugin.read_text(), library.read_text()), ("-- 1\n", "-- dkjson 1\n"))
            result = pin("2")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Replacing the unedited vis-lspc plugin", result.stdout)
            self.assertIn("Replacing the unedited dkjson.lua", result.stdout)
            self.assertEqual((plugin.read_text(), library.read_text()), ("-- 2\n", "-- dkjson 2\n"))
            # Changed and added files are both edits, under the same or a new pin.
            for edit, report in ((lambda: plugin.write_text("-- mine\n"), "init.lua: sha256digest changed"),
                                 (lambda: (editor / "vis-lspc/extra.lua").write_text("x"), "extra: extra.lua")):
                edit()
                for version in ("2", "3"):
                    result = pin(version)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(report, result.stdout)
                    self.assertIn("Staged vis-lspc has local changes", result.stderr)
                self.assertNotEqual(plugin.read_text(), "-- 3\n")
                plugin.write_text("-- 2\n")
                (editor / "vis-lspc/extra.lua").unlink(missing_ok=True)
            library.write_text("-- my dkjson\n")
            result = pin("3")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Staged dkjson.lua has local changes", result.stderr)
            self.assertEqual((plugin.read_text(), library.read_text()), ("-- 3\n", "-- my dkjson\n"))
            # A download that does not match its pin stops before anything staged changes.
            result = pin("4", served="-- dkjson tampered\n")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Checksum mismatch: dkjson", result.stderr)
            self.assertEqual((plugin.read_text(), library.read_text()), ("-- 3\n", "-- my dkjson\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
