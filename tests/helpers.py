"""Behavior checks for native-helper boundaries using disposable command stand-ins."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


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
        return subprocess.run(["sh", str(ROOT / "home/.local/bin/nostromo-display")],
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
        script = ROOT / "scripts/ssid-hex.awk"
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
                    "-f", str(ROOT / "scripts/merge-block.awk")]
            original = 'ctrl_interface=/var/run/wpa_supplicant\n# comment\nnetwork={\n ssid="leave me"\n}\n'
            result = subprocess.run(args, input=original, text=True, capture_output=True, check=True).stdout
            self.assertTrue(result.startswith(original))
            second = subprocess.run(args, input=result, text=True, capture_output=True, check=True).stdout
            self.assertEqual(second, result)
            for bad in [original+"# BEGIN NOSTROMO WIFI 6162\n", result+"# END NOSTROMO WIFI 6162\n"]:
                self.assertNotEqual(subprocess.run(args, input=bad, text=True, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
