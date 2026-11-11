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

ROOT = Path(__file__).resolve().parents[2]
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


# foot 1.28's built-in key bindings, from foot.ini(5).
FOOT_DEFAULTS = {
    "scrollback-up-page": "Shift+Page_Up Shift+KP_Page_Up",
    "scrollback-down-page": "Shift+Page_Down Shift+KP_Page_Down",
    "clipboard-copy": "Control+Shift+c XF86Copy",
    "clipboard-paste": "Control+Shift+v XF86Paste",
    "primary-paste": "Shift+Insert",
    "search-start": "Control+Shift+r",
    "font-increase": "Control+plus Control+equal Control+KP_Add",
    "font-decrease": "Control+minus Control+KP_Subtract",
    "font-reset": "Control+0 Control+KP_0",
    "spawn-terminal": "Control+Shift+n",
    "show-urls-launch": "Control+Shift+o",
    "prompt-prev": "Control+Shift+z",
    "prompt-next": "Control+Shift+x",
    "unicode-input": "Control+Shift+u",
}


def foot_combo(text):
    *mods, key = text.split("+")
    mods = {{"Mod1": "Alt", "Mod4": "Super", "Control": "Ctrl"}.get(mod, mod) for mod in mods}
    # Like foot, treat Control+C and Control+Shift+c as the same key press.
    if len(key) == 1 and key.isupper():
        mods.add("Shift")
        key = key.lower()
    return frozenset(mods), key


def link_rows():
    """The manifest's (source, destination) pairs."""
    return [tuple(line.split("|")) for line in (ROOT / ".install/links.txt").read_text().splitlines()
            if line and not line.startswith("#")]


def glob_pattern(path):
    """A "$repo/..." argument as a regular expression: variables and * stay in one directory."""
    parts = re.split(r"(\$\{?\w+\}?|\*)", path)
    return re.compile("".join("[^/]*" if i % 2 else re.escape(part) for i, part in enumerate(parts)))


def dwl_bindings():
    """Every dwl keys[] entry as (modifiers, keysym, function, argument), macros expanded."""
    text = (ROOT / "dwl/config.h").read_text()
    body = text.split("static const Key keys[] = {", 1)[1].split("\n};", 1)[0]
    mods = lambda value: frozenset(value.split("|")) - {"0"}
    keys = [(mods(m), sym, function, argument) for m, sym, function, argument in re.findall(
        r'\{\s*([\w|]+),\s*XKB_KEY_(\w+),\s*(\w+),\s*(\{[^}]*\}|SHCMD\("[^"]*"\))\s*\}', body)]
    tagkeys = re.search(r"#define TAGKEYS\(KEY,TAG\)((?:.*\\\n)*.*)", text).group(1)
    for sym, tag in re.findall(r"TAGKEYS\(XKB_KEY_(\w+), (\d+)\)", body):
        keys += [(mods(m), sym, function, tag) for m, function in re.findall(r"\{\s*([\w|]+),\s*KEY,\s*(\w+),", tagkeys)]
    m, function = re.search(r"#define CHVT\(n\) \{ ([\w|]+), XKB_KEY_F##n, (\w+),", body).groups()
    keys += [(mods(m), "F" + n, function, n) for n in re.findall(r"\bCHVT\((\d+)\)", body)]
    return keys


class Migration(unittest.TestCase):
    def test_document_links(self):
        missing = []
        for doc in [ROOT / "README.md", ROOT / "COPYING.md", *ROOT.glob("art/*.md"), *ROOT.glob("docs/**/*.md")]:
            if "research" in doc.parts:
                continue
            for target in re.findall(r"\]\(([^)]+)\)", doc.read_text()):
                if target.startswith(("https:", "http:", "#", "mailto:")):
                    continue
                if not (doc.parent / unquote(target.split("#")[0])).exists():
                    missing.append(f"{doc.relative_to(ROOT)} -> {target}")
        self.assertEqual(missing, [])

    def test_fonts(self):
        directory = ROOT / "fonts"
        for line in (directory / "SHA256").read_text().splitlines():
            match = re.fullmatch(r"SHA256 \((.+)\) = ([a-f0-9]{64})", line)
            self.assertIsNotNone(match, line)
            name, expected = match.groups()
            self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected)

    def test_install_manifest_covers_runtime_files_and_small_orb(self):
        rows = link_rows()
        targets = [destination for _, destination in rows]
        self.assertEqual(len(targets), len(set(targets)))
        for source, _ in rows:
            if not source.startswith(".build/"):
                self.assertTrue((ROOT / source).exists(), source)
        self.assertIn(("art/nostromo-orb-small.txt", ".local/share/nostromo/nostromo-orb-small.txt"), rows)

    def test_every_program_file_has_a_reader(self):
        # A program folder holds what the home links, the installer, a helper or a test
        # reads, and license text. A leftover that nothing reads fails here.
        readers = [ROOT / "install.sh", *ROOT.glob(".install/scripts/*"), *ROOT.glob(".install/tests/*"),
                   *ROOT.glob("bin/**/*")]
        text = "\n".join(path.read_text() for path in readers if path.is_file())
        covered, patterns = {source for source, _ in link_rows()}, []
        for path in re.findall(r'\$repo"?/([\w.$/{}*-]+)', text):
            if not re.search(r"[$*]", path):
                covered.add(path.rstrip("/"))
            elif not path.startswith(("$", "*")):
                patterns.append(glob_pattern(path))
        unread = []
        for folder in sorted(ROOT.iterdir()):
            if not folder.is_dir() or folder.name.startswith(".") or folder.name == "docs":
                continue
            for path in sorted(folder.rglob("*")):
                relative = path.relative_to(ROOT).as_posix()
                parts = relative.split("/")
                if path.is_dir() or path.name.startswith(".") or "__pycache__" in parts:
                    continue
                if ({"/".join(parts[:i]) for i in range(1, len(parts) + 1)} & covered
                        or any(pattern.fullmatch(relative) for pattern in patterns)
                        or re.search(r"(?<![\w.-])" + re.escape(relative) + r"(?![\w.-])", text)
                        or re.search(r"LICENSE|COPYING|README", path.name) or "licenses" in parts
                        or any(f'#include "{path.name}"' in other.read_text()
                               for other in path.parent.glob("*.[ch]") if other != path)):
                    continue
                unread.append(relative)
        self.assertEqual(unread, [])

    def test_every_user_guide_reaches_the_docs_reader(self):
        # nostromo-docs offers the guides, chapters and library it finds beside its examples.
        pairs = set(link_rows())
        internal={'DESIGN','MIGRATION','MIGRATION-COVERAGE','PLANS','SOURCES','VALIDATION'}
        for guide in sorted(ROOT.glob('docs/*.md')):
            if guide.stem not in internal:
                self.assertIn((f'docs/{guide.name}',f'.local/share/nostromo/{guide.name}'),pairs)
        for source,name in [('docs/reference','reference'),('docs/secret-knowledge','secret-knowledge'),
                            ('docs/electronics','electronics'),('.build/docs/library','library')]:
            self.assertIn((source,f'.local/share/nostromo/{name}'),pairs)

    def test_reference_shader(self):
        shader = ROOT / "docs/design/space-dots-original.frag"
        self.assertEqual(hashlib.sha256(shader.read_bytes()).hexdigest(),
                         "f5b7d8fbd29f5a697b99ee5a6522578d80688a97628b9b6f9817edbeb6c4ef17")
        self.assertIn("Copyright 2023 Maxim Samoliuk", shader.read_text())

    def test_start_page_assets(self):
        # The browser resolves the page's resources beside its link in the home.
        links = {destination: source for source, destination in link_rows()}
        page = ".local/share/nostromo/start/index.html"
        for resource in re.findall(r'src="([^"]+)"', (ROOT / links[page]).read_text()):
            destination = os.path.normpath(os.path.join(os.path.dirname(page), resource))
            self.assertIn(destination, links, resource)
            self.assertTrue((ROOT / links[destination]).is_file(), resource)

    def test_shell_syntax(self):
        files = [ROOT / "oksh/profile", *ROOT.glob("*.sh"), *ROOT.glob(".install/scripts/*.sh"),
                 *(path for path in ROOT.glob("bin/**/*") if path.is_file()),
                 *ROOT.glob("nostromo/*.conf")]
        for script in files:
            with self.subTest(script=script.name):
                subprocess.run(["/bin/sh", "-n", str(script)], check=True, capture_output=True)

    def test_awk_programs_parse(self):
        # sh -n cannot see inside quoted awk programs. FreeBSD's awk ended an Include
        # pattern at a slash inside brackets, which stopped every system configuration.
        programs = []
        for directory, dirs, names in os.walk(ROOT):
            dirs[:] = [name for name in dirs if Path(directory, name).relative_to(ROOT).as_posix()
                       not in (".git", ".build", "docs/research", "tests")]
            for name in names:
                path = Path(directory, name)
                if path.suffix == ".awk":
                    programs.append((path, path.read_text()))
                    continue
                if path.is_symlink() or not (path.suffix == ".sh" or path.read_bytes()[:9] == b"#!/bin/sh"):
                    continue
                text = path.read_text()
                for match in re.finditer(r"(?<![\w./-])awk(?![\w.-])((?:\s+-[Fv](?:\s*(?:'[^']*'|\"[^\"]*\"|[^\s'\"])+))*)\s+'", text):
                    if text[text.rfind("\n", 0, match.start()) + 1:match.start()].lstrip().startswith("#"):
                        continue
                    start, parts = match.end(), []
                    while True:
                        end = text.index("'", start)
                        parts.append(text[start:end])
                        if not text.startswith("\\''", end + 1):
                            break
                        parts.append("'")
                        start = end + 4
                    programs.append((path, "".join(parts)))
        self.assertGreater(len(programs), 100)
        with tempfile.TemporaryDirectory() as directory:
            for path, program in programs:
                (Path(directory) / "program.awk").write_text(program)
                result = subprocess.run(["awk", "-f", "program.awk"], cwd=directory, stdin=subprocess.DEVNULL,
                                        capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"})
                self.assertIsNone(re.search(r"syntax error|nonterminated|unterminated|illegal|bailing out|fatal",
                                            result.stderr), f"{path.relative_to(ROOT)}: {result.stderr}")

    def test_llvm_paths_name_the_installed_llvm(self):
        # rustup's libclang and the embedded runtime use fixed LLVM prefixes.
        packages = set((ROOT / ".install/packages.txt").read_text().split())
        used = {}
        for script in ROOT.glob(".install/scripts/*.sh"):
            for version in re.findall(r"/usr/local/llvm(\d+)\b", script.read_text()):
                used.setdefault(f"llvm{version}", []).append(script.name)
        self.assertIn("build-rustup.sh", used.get("llvm21", []))
        self.assertEqual({name: files for name, files in used.items() if name not in packages}, {})

    def test_installer_tool_state_stays_in_the_build_output(self):
        # The home keeps only what its user creates; a clean install removes .build.
        tools = (ROOT / ".install/scripts/development-tools.sh").read_text()
        exports = dict(re.findall(r"\b(GOPATH|GOCACHE|UV_CACHE_DIR|GOFLAGS)=(\"[^\"]*\"|\S+)", tools))
        for name in ("GOPATH", "GOCACHE", "UV_CACHE_DIR"):
            self.assertTrue(exports.get(name, "").startswith('"$repo/.build/'), name)
        # Go makes its module cache read-only, which would stop that removal.
        self.assertEqual(exports.get("GOFLAGS"), "-modcacherw")
        # Go's usage counters follow XDG_CONFIG_HOME; every go command runs in this subshell.
        block = re.search(r"\n\(\n(.*?)\n\)\n", tools, re.S).group(1)
        self.assertIn('XDG_CONFIG_HOME="$work/config"', block)
        self.assertEqual(tools.count('"$go" '), block.count('"$go" '))
        self.assertGreater(block.count('"$go" '), 0)
        # Any rustup command writes settings to its RUSTUP_HOME.
        runs = [line for line in (ROOT / ".install/scripts/build-rustup.sh").read_text().splitlines()
                if "bin/rustup" in line and not line.startswith(("install ", "#"))]
        self.assertTrue(runs)
        for line in runs: self.assertTrue(line.startswith('RUSTUP_HOME="$work/'), line)
        check = re.search(r"NOSTROMO_DOCS_ROOT=.*?nostromo-docs --check", (ROOT / ".install/scripts/verify-stage.sh").read_text(), re.S)
        for name in ("XDG_CACHE_HOME", "XDG_CONFIG_HOME"):
            self.assertIn(f'{name}="$work/', check.group(0))

    def test_no_x11_or_doas_runtime(self):
        linked = [ROOT / source for source, _ in link_rows() if not source.startswith((".build/", "docs/"))]
        for path in (found for source in linked for found in [source, *source.rglob("*")]):
            if not path.is_file() or path.suffix in (".pyc", ".png", ".ttf"):
                continue
            text = path.read_text()
            self.assertIsNone(re.search(r"\b(?:doas|tailscale|tailscaled|xclip|xrandr|xdotool|xenodm|picom|surf|tabbed)\b", text), str(path))
            self.assertNotIn("/usr/X11R6", text, str(path))

    def test_foot_config(self):
        cfg = configparser.ConfigParser(interpolation=None)
        cfg.read(ROOT / "foot/foot.ini")
        self.assertEqual(cfg["main"]["shell"], "/usr/local/bin/oksh")
        self.assertNotIn("colors", cfg)  # Obsolete on the checked foot version.
        self.assertEqual(cfg["colors-dark"]["alpha"], "0.90")
        self.assertEqual(cfg["colors-dark"]["alpha-mode"], "default")
        self.assertEqual(cfg["csd"]["preferred"], "server")
        # Overriding an action replaces only its own defaults, and foot refuses a
        # configuration in which two actions share a combination.
        bindings = {**FOOT_DEFAULTS, **cfg["key-bindings"]}
        owners = {}
        for action, value in bindings.items():
            for combo in re.sub(r"\[[^]]*\]", "", value).split():
                if combo != "none":
                    owners.setdefault(foot_combo(combo), []).append(action)
        self.assertEqual({combo: names for combo, names in owners.items() if len(names) > 1}, {})
        for helper in re.findall(r"\[([^] ]+)\]", "".join(cfg["key-bindings"].values())):
            self.assertTrue((ROOT / "bin" / helper).is_file(), helper)

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
            runpy.run_path(str(ROOT / "qutebrowser/config.py"),
                           init_globals={"config": Config(), "c": Node()})
        known = set(re.findall(r"^([a-z][a-z0-9_.]+):", (ROOT / "docs/research/qutebrowser-configdata.yml").read_text(), re.M))
        self.assertTrue(known)
        self.assertEqual(set(options) - known, set())
        self.assertEqual(options["qt.force_platform"], "wayland")
        self.assertEqual(options["url.start_pages"], ["file:///tmp/home%20space/%23data/nostromo/start/index.html"])
        self.assertEqual(options["editor.command"][:3], ["foot", "-e", "vis"])
        self.assertNotIn("j", bindings)  # Keep normal web navigation.


class Keyboard(unittest.TestCase):
    """Every desktop feature has a key, and no key shadows another."""
    # Reached inside a bound panel, or through the keys for each of its steps.
    WITHIN = {"BRIGHTNESS": "nostromo-brightness up", "SCREENSHOT WINDOW": "nostromo_capture",
              **dict.fromkeys(["INSTALL PACKAGES", "REMOVE PACKAGES", "PORTS", "BASE PATCHES", "FIRMWARE"],
                              "foot -e nostromo-software")}
    # Occasional settings stay in the Super+X menu instead of taking arbitrary chords.
    MENU_ONLY = {"WALLPAPER", "CRT STATIC", "AUTHENTICATION", "EMBEDDED"}

    @classmethod
    def setUpClass(cls):
        cls.keys = dwl_bindings()
        cls.bound = {argument[7:-2] for _, _, function, argument in cls.keys if argument.startswith("SHCMD(")}
        cls.bound |= {function for _, _, function, _ in cls.keys}
        cls.actions = subprocess.run(["sh", str(ROOT / "bin/nostromo-menu"), "--list"],
                                     check=True, capture_output=True, text=True).stdout.splitlines()

    def test_dwl_chords_are_unique(self):
        # dwl tries the unshifted keysym first, so Shift+p and Shift+P are one chord.
        chords = [(mods, sym.lower() if len(sym) == 1 else sym) for mods, sym, _, _ in self.keys]
        self.assertGreater(len(chords), 150)
        seen, repeated = set(), []
        for chord in chords:
            if chord in seen:
                repeated.append(chord)
            seen.add(chord)
        self.assertEqual(repeated, [])

    def test_every_menu_and_bar_action_has_a_key(self):
        menu = (ROOT / "bin/nostromo-menu").read_text()
        commands = {name.strip("'"): command for name, command in
                    re.findall(r"^('[^'\n]+'|[A-Z]+)\) exec (.+) ;;$", menu, re.M)}
        self.assertEqual(set(commands), set(self.actions))
        self.assertLessEqual(set(self.WITHIN) | self.MENU_ONLY, set(self.actions))
        for action in self.actions:
            if action not in self.MENU_ONLY:
                with self.subTest(action=action):
                    self.assertIn(self.WITHIN.get(action, commands[action]), self.bound)
        bar = (ROOT / "dwlb/controls.patch").read_text().split("*actions[] = {", 1)[1].split("};", 1)[0]
        self.assertLessEqual(set(re.findall(r'"([^"]+)"', bar)), set(self.actions) - self.MENU_ONLY)

    def test_mouse_actions_have_keys(self):
        dunst = {"close_current": "dunstctl close", "close_all": "dunstctl close-all",
                 "do_action": "dunstctl context", "context": "dunstctl context",
                 "context_all": "dunstctl context", "open_url": "dunstctl context"}
        clicks = re.findall(r"^\s*mouse_\w+_click\s*=\s*(\w+)", (ROOT / "dunst/dunstrc").read_text(), re.M)
        self.assertEqual(len(clicks), 3)
        for click in clicks:
            self.assertIn(dunst[click], self.bound, click)
        config = (ROOT / "dwl/config.h").read_text()
        buttons = {("moveresize", ".ui = CurMove"): "nostromo_shift", ("moveresize", ".ui = CurResize"): "nostromo_resize",
                   ("togglefloating", "0"): "togglefloating"}
        found = re.findall(r"\{\s*MODKEY,\s*BTN_\w+,\s*(\w+),\s*\{([^}]*)\}\s*\}", config)
        self.assertEqual(len(found), 3)
        for button in found:
            self.assertIn(buttons[button], self.bound, button)
        for command in re.findall(r'\{\s*MODKEY,\s*Axis\w+,\s*spawn,\s*SHCMD\("([^"]*)"\)\s*\}', config):
            self.assertIn(command, self.bound)

    def test_reference_lists_every_menu_action(self):
        reference = (ROOT / "docs/KEYBINDINGS.md").read_text()
        section = reference.split("\n## Every menu action\n", 1)[1].split("\n## ", 1)[0]
        listed = re.findall(r"^\| ([A-Z][A-Z ]*[A-Z]) \|", section, re.M)
        self.assertEqual(sorted(listed), sorted(self.actions))


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
        return subprocess.run(["/bin/sh", str(ROOT / "bin/nostromo-browser"), *args],
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
        proc = subprocess.run(["/bin/sh", str(ROOT / "bin/nostromo-cwd")],
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
        (self.repo / ".install/scripts").mkdir(parents=True)
        shutil.copy(ROOT / ".install/scripts/link-home.sh", self.repo / ".install/scripts/link-home.sh")
        ((self.repo / "new").resolve()).write_text("new content")
        (self.repo / ".install/links.txt").write_text("new|.profile\n")
        (self.home / ".profile").write_text("keep my original")

    def install(self, *args, **env):
        return subprocess.run(["sh", str(self.repo / ".install/scripts/link-home.sh"), "--target", str(self.home), *args],
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
        rows = link_rows()
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
        shutil.copy2(ROOT/'.install/links.txt',self.repo/'.install/links.txt')
        for _ in range(2):
            result = self.install('--apply')
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            for source,destination in rows:
                target = self.home/destination
                self.assertTrue(target.is_symlink(),destination)
                self.assertEqual(os.readlink(target),str(self.repo.resolve()/source))
                self.assertEqual(target.resolve(),(self.repo/source).resolve())

    def test_preflight_stops_before_any_writes(self):
        (self.repo / ".install/links.txt").write_text("new|.profile\nmissing|.config/fail\n")
        self.assertNotEqual(self.install("--apply").returncode, 0)
        self.assertEqual((self.home / ".profile").read_text(), "keep my original")
        (self.repo / ".install/links.txt").write_text("new|.profile\nnew|.config/fail\n")
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
        (self.repo / ".install/links.txt").write_text("new|.profile\nnew|.config/old\nnew|.config/kept\n")
        self.assertEqual(self.install("--apply").returncode, 0)
        self.assertEqual(record.read_text(), "new|.profile\nnew|.config/old\nnew|.config/kept\n")
        # A link the user replaced is no longer the project's file.
        (self.home / ".config/kept").unlink()
        (self.home / ".config/kept").write_text("mine")
        (self.repo / ".install/links.txt").write_text("new|.profile\n")
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
        (self.repo / ".install/links.txt").write_text("new|.profile\nnew|.config/old\n")
        self.assertEqual(self.install("--apply").returncode, 0)
        tools = self.base / "tools"
        tools.mkdir()
        (tools / "ln").write_text('#!/bin/sh\ncase "$*" in *.config/new*) exit 23 ;; esac\nexec /bin/ln "$@"\n')
        (tools / "ln").chmod(0o755)
        (self.repo / ".install/links.txt").write_text("new|.profile\nnew|.config/new\n")
        result = self.install("--apply", PATH=str(tools) + ":/usr/bin:/bin")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertEqual(os.readlink(self.home / ".config/old"), str(self.repo.resolve() / "new"))
        self.assertFalse((self.home / ".config/new").is_symlink())
        self.assertEqual(record.read_text(), "new|.profile\nnew|.config/old\n")
        self.assertEqual(sorted(p.name for p in record.parent.iterdir()), ["backups", "links"])

    def test_a_former_directory_link_can_become_a_directory_of_links(self):
        (self.repo / "tree").mkdir()
        (self.repo / "tree/rc").write_text("rc")
        (self.repo / ".install/links.txt").write_text("tree|.config/tool\n")
        self.assertEqual(self.install("--apply").returncode, 0)
        (self.repo / ".install/links.txt").write_text("tree/rc|.config/tool/rc\n")
        result = self.install("--apply")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.home / ".config/tool").is_symlink())
        self.assertEqual(os.readlink(self.home / ".config/tool/rc"), str(self.repo.resolve() / "tree/rc"))
        self.assertEqual((self.repo / "tree/rc").read_text(), "rc")

    def test_a_former_link_changed_after_preflight_is_never_linked_through(self):
        (self.repo / "tree").mkdir()
        (self.repo / "tree/rc").write_text("rc")
        (self.repo / ".install/links.txt").write_text("tree|.config/tool\n")
        self.assertEqual(self.install("--apply").returncode, 0)
        # The second lookup reports another target, as if the link changed after preflight.
        tools, seen = self.base / "tools", self.base / "seen"
        tools.mkdir()
        (tools / "readlink").write_text(
            "#!/bin/sh\n"
            f'case $1 in */.config/tool) [ -e "{seen}" ] && {{ echo /elsewhere; exit; }}; : >"{seen}" ;; esac\n'
            'exec /usr/bin/readlink "$@"\n')
        (tools / "readlink").chmod(0o755)
        (self.repo / ".install/links.txt").write_text("tree/rc|.config/tool/rc\n")
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
            for path in (repo / ".install/scripts", tools):
                path.mkdir(parents=True)
            shutil.copy(ROOT / ".install/scripts/stage-licenses.sh", repo / ".install/scripts")
            source = (ROOT / ".install/scripts/editor-plugins.sh").read_text()
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
                (repo / ".install/scripts/fetch-source.sh").write_text(
                    f'mkdir -p "$2"\nprintf "MIT\\n" >"$2/LICENSE"\nprintf -- "-- {version}\\n" >"$2/init.lua"\n')
                (base / "dkjson").write_text(served or f"-- dkjson {version}\n")
                digest = hashlib.sha256(f"-- dkjson {version}\n".encode()).hexdigest()
                (repo / ".install/scripts/editor-plugins.sh").write_text(source.replace(pinned, digest))
                result = subprocess.run(["sh", str(repo / ".install/scripts/editor-plugins.sh")], capture_output=True,
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
