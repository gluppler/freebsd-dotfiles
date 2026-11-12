"""Behavior checks for native-helper boundaries using disposable command stand-ins."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]


class Display(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.bin = self.work / "bin"
        self.bin.mkdir()
        self.output = {"name": "eDP-1", "enabled": True, "scale": 1, "transform": "normal",
                       "position": {"x": 0, "y": 0},
                       "modes": [{"width": 1920, "height": 1080, "refresh": 59.95, "current": True}]}
        (self.work / "outputs").write_text(json.dumps([self.output]))
        (self.work / "choices").write_text("[]")
        self.stub("wlr-randr", """
if sys.argv[1:] == ['--json']: print((root/'outputs').read_text())
else:
    with (root/'calls').open('a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')
""")
        self.stub("nostromo-picker", """
sys.stdin.read()
choices=json.loads((root/'choices').read_text())
if not choices: sys.exit(1)
print(choices.pop(0)); (root/'choices').write_text(json.dumps(choices))
""")
        self.stub("nostromo-wallpaper", "(root/'wallpaper').touch()")
        self.stub("timeout", "os.execvp(sys.argv[2],sys.argv[2:])")
        self.env = {**os.environ, "PATH": str(self.bin) + ":/opt/homebrew/bin:/usr/bin:/bin",
                    "TEST_ROOT": str(self.work), "TMPDIR": str(self.work)}

    def stub(self, name, body):
        script = self.bin / name
        script.write_text(f"#!{sys.executable}\nimport json,os,sys\nfrom pathlib import Path\nroot=Path(os.environ['TEST_ROOT'])\n" + body + "\n")
        script.chmod(0o755)

    def run_menu(self, choices):
        (self.work / "choices").write_text(json.dumps(choices))
        return subprocess.run(["sh", str(ROOT / "bin/nostromo-display")],
                              env=self.env, text=True, capture_output=True)

    def calls(self):
        path = self.work / "calls"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def test_refresh_kept_in_hertz_and_cancel_restores(self):
        result = self.run_menu(["eDP-1", "MODE / RATE", "1920x1080@59.95Hz", "REVERT"])
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        self.assertEqual(len(calls), 3)
        self.assertIn("1920x1080@59.95Hz", calls[0])
        self.assertIn("1920x1080@59.95Hz", calls[-1])
        self.assertIn("--pos", calls[-1])
        self.assertFalse((self.work / "wallpaper").exists())
        self.assertEqual(list(self.work.glob("nostromo-display.*")), [])

    def test_no_confirmation_restores_and_keep_does_not(self):
        result = self.run_menu(["eDP-1", "SCALE", "2"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 3)
        (self.work / "calls").unlink()
        result = self.run_menu(["eDP-1", "SCALE", "2", "KEEP"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls()), 2)
        self.assertTrue((self.work / "wallpaper").exists())

    def test_last_output_and_unoffered_selection_rejected(self):
        result = self.run_menu(["eDP-1", "DISABLE"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("last active output", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.run_menu(["--output hacked"]).returncode, 2)
        self.assertEqual(self.calls(), [])


class Parsers(unittest.TestCase):
    def test_usb_mount_list_excludes_internal_cam_disks(self):
        source = (ROOT / 'system/nostromo-device').read_text()
        parser = source.split("camcontrol devlist -v | awk '\n",1)[1].split("' | while",1)[0]
        records = '''scbus0 on ahcich0 bus 0:
<Internal SATA> at scbus0 target 0 lun 0 (pass0,ada0)
scbus1 on mps0 bus 0:
<Internal SCSI> at scbus1 target 0 lun 0 (pass1,da0)
scbus2 on umass-sim0 bus 0:
<USB Flash> at scbus2 target 0 lun 0 (da1,pass2)
scbus3 on umass-sim1 bus 0:
<USB Disk> at scbus3 target 0 lun 0 (pass3,da2)
scbus4 on nvme0 bus 0:
<Internal NVMe> at scbus4 target 0 lun 0 (nda0,pass4)
'''
        result = subprocess.run(['awk',parser], input=records, capture_output=True, text=True, check=True)
        self.assertEqual(result.stdout.splitlines(), ['da1','da2'])

    def test_device_arguments_reject_paths_options_and_invalid_modes(self):
        source = (ROOT / 'system/nostromo-device').read_text()
        body = source.split('case ${1:-} in\n',1)[1]
        # Exact command dispatch, with an empty CAM inventory; no real devices used.
        script = 'set -eu\ncamcontrol() { :; }\ncase ${1:-} in\n' + body
        for args in [('probe','../usb/0.1'), ('probe','--help'), ('mount','nvme0ns1','rw'),
                     ('mount','da0;touch injected','rw'), ('mount','da0','other'),
                     ('unmount','../../etc'), ('unmount','-a')]:
            result = subprocess.run(['sh','-c',script,'device-test',*args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)

    def test_ssid_bytes_are_not_shell_escape_sequences(self):
        script = ROOT / ".install/scripts/ssid-hex.awk"
        for source, expected in [(r"a\x20b", "612062"), (r"dollar$(id)", "646f6c6c61722428696429"),
                                 (r"slash\\name", "736c6173685c6e616d65"),
                                 (r"\xe6\x97\xa5", "e697a5"), (r"line\nend", "6c696e650a656e64")]:
            process = subprocess.run(["awk", "-f", str(script)], input=source+"\n",
                                     capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"})
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stdout.strip(), expected)
        for source in [r"bad\c", r"bad\xzz", "x"*33, "a\nb"]:
            self.assertNotEqual(subprocess.run(["awk", "-f", str(script)], input=source+"\n",
                                              text=True, capture_output=True).returncode, 0)

    def test_managed_merge_preserves_other_networks_and_rejects_bad_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            block = Path(directory) / "block"
            block.write_text("new content\n")
            args = ["awk", "-v", "name=WIFI 6162", "-v", "replacement="+str(block),
                    "-f", str(ROOT / ".install/scripts/merge-block.awk")]
            original = 'ctrl_interface=/var/run/wpa_supplicant\n# comment\nnetwork={\n ssid="leave me"\n}\n'
            result = subprocess.run(args, input=original, text=True, capture_output=True, check=True).stdout
            self.assertTrue(result.startswith(original))
            second = subprocess.run(args, input=result, text=True, capture_output=True, check=True).stdout
            self.assertEqual(second, result)
            for bad in [original+"# BEGIN NOSTROMO WIFI 6162\n", result+"# END NOSTROMO WIFI 6162\n"]:
                self.assertNotEqual(subprocess.run(args, input=bad, text=True, capture_output=True).returncode, 0)

    def test_forgotten_network_is_the_one_wpa_supplicant_reads(self):
        script = str(ROOT / ".install/scripts/forget-network.awk")
        def run(source, name, *mode):
            return subprocess.run(["awk", "-v", "ssid=" + name.hex(), *mode, "-f", script], input=source,
                                  capture_output=True, env={**os.environ, "LC_ALL": "C"})
        header = b'ctrl_interface=/var/run/wpa_supplicant\neapol_version=2\n# home network={\n'
        other = b'network={\n\tssid="Homer"\n\tpsk="other-secret"\n}\n'
        # Every spelling of "Home" that wpa_supplicant accepts, bsdinstall's first.
        for block in [b'network={\n\tssid="Home"\n\tpsk="secret"\n\tpriority=5\n}\n',
                      b'  network={ # bsdinstall\r\n ssid=486F6D65\r\n}\r\n', b'network={\nssid=P"H\\x6fm\\145"\n}\n',
                      b'network={\nssid=P"\\110o\\me"\n}\n', b'network={\nssid="Other"\nssid="Home" # renamed\n}\n']:
            with self.subTest(block=block):
                self.assertEqual(run(header + block + other, b"Home").stdout, header + other)
                self.assertEqual(run(header + block + other, b"Home", "-v", "mode=find").returncode, 0)
        # Other names, a cleared name, comments and other block types stay byte for byte.
        for block in [b'network={\n ssid="Home "\n}\n', b'network={\n ssid="home"\n}\n',
                      b'network={\n ssid="Home"\n ssid=NULL\n}\n', b'#network={\n# ssid="Home"\n#}\n',
                      b'cred={\n realm="Home"\n}\n', b'network={\n key_mgmt=NONE\n}\n']:
            with self.subTest(block=block):
                self.assertEqual(run(header + block, b"Home").stdout, header + block)
                self.assertEqual(run(header + block, b"Home", "-v", "mode=find").returncode, 1)
        # A quoted name ends at the last quote, # starts a comment only outside quotes and
        # P"" decodes as printf_decode() does; bytes stay bytes.
        for name, line in [(b'Lab #1', b'ssid="Lab #1" # comment'), (b'a', b'ssid="a"#b"'), (b'x"y', b'ssid="x"y"'),
                           ("café".encode(), 'ssid="café"'.encode()), (b'\n\x1b', b'ssid=P"\\n\\e"'),
                           (b'\xff', b'ssid=P"\\xff"'), (b'\x0f', b'ssid=P"\\xf"'), (b'z', b'ssid=P"\\xz"'),
                           (b'q', b'ssid=P"\\q"'), (b'\xff', b'ssid=P"\\777"'), (b'ab', b'ssid=P"ab\\"')]:
            with self.subTest(line=line):
                self.assertEqual(run(b'network={\n ' + line + b'\n}\n' + other, name).stdout, other)
        # Managed markers stay for merge-block.awk; every earlier profile goes.
        managed = b'# BEGIN NOSTROMO WIFI 486f6d65\nnetwork={\n ssid=486f6d65\n}\n# END NOSTROMO WIFI 486f6d65\n'
        self.assertEqual(run(header + managed + other + b'network={\n ssid="Home"\n}\n', b"Home").stdout,
                         header + b'# BEGIN NOSTROMO WIFI 486f6d65\n# END NOSTROMO WIFI 486f6d65\n' + other)
        # A name wpa_supplicant would reject, or an unterminated block, stops the change.
        for source in [b'network={\n ssid="Home\n}\n', b'network={\n ssid=486\n}\n', b'network={\n ssid=zz\n ssid="Home"\n}\n',
                       b'network={\n ssid="' + b'x' * 33 + b'"\n}\n', b'network={\n ssid=P"Home\n}\n', b'network={\n ssid="Home"\n']:
            with self.subTest(source=source):
                self.assertEqual(run(source, b"Home").returncode, 2)
        for args in [["-v", "ssid=486F6D65"], ["-v", "ssid=486"], ["-v", "ssid=486f6d65", "-v", "mode=list"]]:
            self.assertEqual(subprocess.run(["awk", *args, "-f", script], input=b"", capture_output=True).returncode, 2)


class Wallpaper(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.directory = self.work / "data/nostromo/wallpapers"
        self.directory.mkdir(parents=True)
        for prefix in ("nostromo", "nostromo-ship"):
            for size in ("1920x1080", "2560x1440", "3840x2160", "7680x4320"):
                (self.directory / f"{prefix}-{size}.png").touch()
        self.state = self.work / "state/nostromo"
        tools = self.work / "bin"
        tools.mkdir()
        output = [{"name": "eDP-1", "enabled": True, "modes": [{"width": 1920, "height": 1080, "current": True}]}]
        (tools / "wlr-randr").write_text(f"#!/bin/sh\nprintf '%s\\n' '{json.dumps(output)}'\n")
        # swaybg records its arguments, then stays alive like a running background.
        # It releases the captured output so each run returns without waiting for it.
        (tools / "swaybg").write_text('#!/bin/sh\nprintf "%s\\n" "$@" >"$TEST_ROOT/swaybg"\n'
                                      'echo $$ >>"$TEST_ROOT/pids"\nexec sleep 30 >/dev/null 2>&1\n')
        for tool in tools.iterdir():
            tool.chmod(0o755)
        self.addCleanup(self.stop_backgrounds)
        self.env = {**os.environ, "PATH": str(tools) + ":/opt/homebrew/bin:/usr/bin:/bin",
                    "TEST_ROOT": str(self.work), "XDG_DATA_HOME": str(self.work / "data"),
                    "XDG_STATE_HOME": str(self.work / "state")}

    def stop_backgrounds(self):
        pids = self.work / "pids"
        for pid in pids.read_text().split() if pids.exists() else []:
            try:
                os.kill(int(pid), 15)
            except ProcessLookupError:
                pass

    def wallpaper(self, *args):
        return subprocess.run(["sh", str(ROOT / "bin/nostromo-wallpaper"), *args],
                              env=self.env, text=True, capture_output=True)

    def test_saved_selection_without_exports_falls_back_to_the_default(self):
        result = self.wallpaper("ship")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(self.directory / "nostromo-ship-1920x1080.png"), (self.work / "swaybg").read_text())
        self.assertEqual((self.state / "wallpaper").read_text(), "ship\n")
        # Archiving a variant leaves the saved selection without exports.
        for path in self.directory.glob("nostromo-ship-*"):
            path.unlink()
        result = self.wallpaper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Saved wallpaper is unavailable; using the default.", result.stderr)
        arguments = (self.work / "swaybg").read_text().splitlines()
        self.assertEqual(arguments.count(str(self.directory / "nostromo-1920x1080.png")), 2)
        self.assertEqual((self.state / "wallpaper").read_text(), "default\n")
        # An explicit request still names only an available wallpaper.
        result = self.wallpaper("ship")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unknown wallpaper selection.", result.stderr)
        self.assertEqual((self.state / "wallpaper").read_text(), "default\n")
        self.assertEqual(sorted(path.name for path in self.state.iterdir()), ["wallpaper", "wallpaper.pid"])


class Autostart(unittest.TestCase):
    """dwl's startup script. An optional step that failed used to end it, and its
    trap then stopped the bar and services: the session looked like bare dwl."""

    def test_failed_optional_steps_keep_the_services_until_logout(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        work = Path(temp.name)
        tools = work / "bin"
        tools.mkdir()
        services = ("dwlb", "dunst", "pipewire", "wireplumber", "fcitx5", "swayidle",
                    "nostromo-status", "nostromo-output-watch")
        for name in services:
            (tools / name).write_text(f'#!/bin/sh\necho {name} $$ >>"$TEST_ROOT/started"\nexec sleep 30\n')
        optional = ("dbus-update-activation-environment", "nostromo-crt", "nostromo-wallpaper", "nostromo-splash")
        for name in optional:
            (tools / name).write_text(f'#!/bin/sh\necho {name} >>"$TEST_ROOT/failed"\nexit 1\n')
        for tool in tools.iterdir():
            tool.chmod(0o755)
        env = {"PATH": f"{tools}:/usr/bin:/bin", "HOME": str(work), "TEST_ROOT": str(work),
               "WAYLAND_DISPLAY": "wayland-1", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent"}
        log = (work / "session.log").open("w")
        self.addCleanup(log.close)
        # dash is the closest shell to FreeBSD's sh; stdin stands in for dwl's status pipe.
        process = subprocess.Popen(["dash", str(ROOT / "bin/nostromo-autostart")], stdin=subprocess.PIPE,
                                   stdout=log, stderr=log, env=env)
        pids = []

        def alive(pid):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return False
            return True

        def until(condition):
            deadline = time.monotonic() + 5
            while not condition():
                self.assertLess(time.monotonic(), deadline, (work / "session.log").read_text())
                time.sleep(.05)
        try:
            until(lambda: "nostromo-splash" in (work / "failed").read_text().split()
                  if (work / "failed").exists() else False)
            time.sleep(.3)
            self.assertIsNone(process.poll(), (work / "session.log").read_text())
            started = dict(line.split() for line in (work / "started").read_text().splitlines())
            self.assertEqual(sorted(started), sorted(services))
            pids = [int(pid) for pid in started.values()]
            self.assertTrue(all(map(alive, pids)))
            self.assertEqual((work / "failed").read_text().split(), list(optional))
            text = (work / "session.log").read_text()
            for message in ("D-Bus activation environment not updated.", "CRT unavailable",
                            "Wallpaper unavailable", "Splash unavailable."):
                self.assertIn(message, text)
            # dwl's logout stops the script; its trap stops each owned service.
            process.send_signal(15)
            self.assertEqual(process.wait(timeout=5), 0)
            until(lambda: not any(map(alive, pids)))
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdin.close()
            for pid in pids:
                if alive(pid):
                    os.kill(pid, 9)


class Clipboard(unittest.TestCase):
    """The viewers' y keys and foot's scrollback copy mode."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.bin = self.work / "bin"
        self.bin.mkdir()
        record = "with (root/'calls').open('a') as f: f.write(json.dumps([Path(sys.argv[0]).name, sys.argv[1:], {}])+'\\n')"
        self.stub("wl-copy", record.format("sys.stdin.buffer.read().decode('latin-1')"))
        self.stub("notify-send", record.format("''"))
        self.stub("nostromo-copy-editor", record.format("sys.stdin.read()"))
        self.stub("file", "print((root/'type').read_text())")
        self.stub("mutool", record.format("''") + "\nPath(sys.argv[sys.argv.index('-o')+1]).write_text((root/'page').read_text())"
                  "\nsys.exit(int((root/'status').read_text()))")
        self.stub("foot", "assert sys.argv[1] == '-e'\nos.execvp(sys.argv[2], sys.argv[2:])")
        (self.work / "type").write_text("image/png")
        (self.work / "status").write_text("0")
        self.document = self.work / "it's a PDF 日本語.pdf"
        self.document.write_bytes(b"%PDF")
        self.env = {**os.environ, "PATH": f"{self.bin}:/usr/bin:/bin", "TEST_ROOT": str(self.work),
                    "TMPDIR": str(self.work)}

    stub = Display.stub

    def run_helper(self, name, *args, **options):
        return subprocess.run(["sh", str(ROOT / "bin" / name), *args],
                              env=self.env, text=True, capture_output=True, **options)

    def calls(self, name):
        path = self.work / "calls"
        rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        return [row[1:] for row in rows if row[0] == name]

    def test_image_bytes_and_type_reach_the_clipboard(self):
        image = self.work / "shot $(x) 日本語.png"
        image.write_bytes(b"\x89PNG\r\n\x1a\n\xff")
        result = self.run_helper("nostromo-clipboard", "image", str(image))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls("wl-copy"), [[["--type", "image/png"], "\x89PNG\r\n\x1a\n\xff"]])
        self.assertEqual(self.calls("notify-send"), [[["CLIPBOARD", f"Image copied: {image.name}"], ""]])
        # A relative path is resolved against the working directory.
        result = self.run_helper("nostromo-clipboard", "image", image.name, cwd=self.work)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.calls("wl-copy")), 2)

    def test_non_images_and_bad_arguments_copy_nothing(self):
        (self.work / "type").write_text("application/pdf")
        self.assertEqual(self.run_helper("nostromo-clipboard", "image", str(self.document)).returncode, 1)
        for args in (["image"], ["image", "a", "b"], ["bogus"], ["menu", "extra"],
                     ["image", str(self.work / "missing.png")]):
            with self.subTest(args=args):
                self.assertNotEqual(self.run_helper("nostromo-clipboard", *args).returncode, 0)
        self.assertEqual(self.calls("wl-copy"), [])

    def test_page_text_without_mupdf_form_feeds(self):
        (self.work / "page").write_text("Heading\n\n  indented code\n\f\n")
        result = self.run_helper("nostromo-clipboard", "page", str(self.document), "12")
        self.assertEqual(result.returncode, 0, result.stderr)
        (arguments, _), = self.calls("mutool")
        self.assertEqual(arguments[:4], ["draw", "-q", "-F", "txt"])
        self.assertEqual(arguments[-2:], [str(self.document), "12"])
        self.assertEqual(self.calls("wl-copy"), [[["--type", "text/plain;charset=utf-8"], "Heading\n\n  indented code\n\n"]])
        self.assertEqual(list(self.work.glob("nostromo-clipboard.*")), [])

    def test_pages_without_text_or_readable_input_copy_nothing(self):
        (self.work / "page").write_text(" \n\f\n")
        self.assertEqual(self.run_helper("nostromo-clipboard", "page", str(self.document), "1").returncode, 1)
        (self.work / "status").write_text("1")
        self.assertEqual(self.run_helper("nostromo-clipboard", "page", str(self.document), "1").returncode, 1)
        for page in ("0", "01", "1a", "-1", ""):
            with self.subTest(page=page):
                self.assertEqual(self.run_helper("nostromo-clipboard", "page", str(self.document), page).returncode, 2)
        self.assertEqual(self.run_helper("nostromo-clipboard", "page", self.document.name, "1").returncode, 2)
        self.assertEqual(len(self.calls("mutool")), 2)
        self.assertEqual(self.calls("wl-copy"), [])
        self.assertEqual(list(self.work.glob("nostromo-clipboard.*")), [])

    def test_scrollback_opens_the_copy_editor_and_leaves_no_file(self):
        history = "$ make\n`not run` $(not run either) 日本語\n"
        result = self.run_helper("nostromo-scrollback", input=history)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls("nostromo-copy-editor"), [[[], history]])
        self.assertEqual(list(self.work.glob("nostromo-scrollback.*")), [])


class Projects(unittest.TestCase):
    """Super+P's project picker and its abduco sessions."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name).resolve()
        self.bin = self.work / "bin"
        self.bin.mkdir()
        home = self.work / "home"
        (home / ".config/nostromo").mkdir(parents=True)
        self.saved = home / "Projects/saved"
        self.saved.mkdir(parents=True)
        (home / ".config/nostromo/projects").write_text(f"# Pinned projects\n{self.saved}\n")
        self.running = self.work / "running"
        self.running.mkdir()
        (self.work / "sessions").write_text("")
        self.stub("abduco", """
if not sys.argv[1:]:
    print('Active sessions (on host t14)')
    for name in (root/'sessions').read_text().split():
        print('* Wed    2026-11-11 10:00:00    ' + name)
    sys.exit(0)
with (root/'calls').open('a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')
""")
        self.stub("fzf", """
entries = sys.stdin.read().splitlines()
(root/'offered').write_text(json.dumps(entries))
print(entries[0])
""")
        self.env = {**os.environ, "PATH": f"{self.bin}:/usr/bin:/bin", "TEST_ROOT": str(self.work),
                    "HOME": str(home), "XDG_STATE_HOME": str(self.work / "state")}
        self.env.pop("ABDUCO_SESSION", None)

    stub = Display.stub

    def pick(self, *args):
        result = subprocess.run(["sh", str(ROOT / "bin/nostromo-project"), *args],
                                env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        offered = self.work / "offered"
        entries = json.loads(offered.read_text()) if offered.exists() else None
        offered.unlink(missing_ok=True)
        return entries, json.loads((self.work / "calls").read_text().splitlines()[-1])

    def test_running_sessions_come_first_so_enter_reattaches(self):
        _, (_, session, command) = self.pick(str(self.running))
        self.assertEqual(command, "nostromo-mux")
        # A session without a recorded directory and one that is not a project are left out.
        (self.work / "sessions").write_text(f"scratch project-99 {session}\n")
        offered, call = self.pick()
        self.assertEqual(offered, [str(self.running), str(self.saved)])
        self.assertEqual(call, ["-A", session, "nostromo-mux"])
        offered, call = self.pick("--sessions")
        self.assertEqual(offered, ["project-99\tproject-99", f"{self.running}\t{session}"])
        self.assertEqual(call, ["-a", "project-99"])
        # Without running sessions, the pinned projects lead.
        (self.work / "sessions").write_text("")
        offered, _ = self.pick()
        self.assertEqual(offered, [str(self.saved)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
