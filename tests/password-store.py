#!/usr/bin/env python3
"""Real disposable OpenPGP/pass interoperability test; GnuPG is HOST TEST ONLY.

Usage: python3 tests/password-store.py /path/to/built/tpass /path/to/built/tcli
Never reads an existing password store or keyring. Clipboard transport is mocked.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def main():
    tpass, tcli = (str(Path(p).resolve()) for p in sys.argv[1:])
    gpg = shutil.which('gpg')
    assert gpg, 'Host-only GnuPG is needed for interoperability testing'
    with tempfile.TemporaryDirectory(prefix='nostromo-pass-', dir='/tmp') as directory:
        root = Path(directory)
        home = root / 'home'; home.mkdir(mode=0o700)
        keys = root / 'keys'; keys.mkdir(mode=0o700)
        store = root / 'store'
        scratch = root / 'tmp'; scratch.mkdir(mode=0o700)
        commands = root / 'bin'; commands.mkdir()
        clipboard = root / 'clipboard'
        env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'), XDG_STATE_HOME=str(home / '.local/state'), GNUPGHOME=str(keys), PASSWORD_STORE_DIR=str(store),
                   TUMPA_KEYSTORE=str(root / 'keys.db'), TUMPA_PASSPHRASE='test-only',
                   PASSWORD_STORE_UMASK='077', PASSWORD_STORE_ENABLE_EXTENSIONS='false',
                   TMPDIR=str(scratch), WAYLAND_DISPLAY='wayland-test-only', PASSWORD_STORE_CLIP_TIME='1',
                   PASSWORD_STORE_X_SELECTION='clipboard', CLIPBOARD_TEST_FILE=str(clipboard),
                   PATH=str(commands) + os.pathsep + os.environ['PATH'])
        def run(*args, data=None, ok=True, extra=None):
            result = subprocess.run(args, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    env=dict(env, **(extra or {})), timeout=45)
            assert (result.returncode == 0) == ok, (args, result.stderr.decode(errors='replace'))
            return result.stdout
        gp = [gpg, '--batch', '--pinentry-mode', 'loopback', '--passphrase', 'test-only']
        try:
            fingerprints = []
            for n in (1, 2):
                uid = f'Nostromo test {n} <nostromo-{n}@invalid.example>'
                run(*gp, '--quick-generate-key', uid, 'ed25519', 'sign', '1d')
                data = run(*gp, '--with-colons', '--list-keys', uid).decode()
                fp = next(line.split(':')[9] for line in data.splitlines() if line.startswith('fpr:'))
                run(*gp, '--quick-add-key', fp, 'cv25519', 'encr', '1d')
                run(tcli, 'import', '-', data=run(*gp, '--armor', '--export-secret-keys', fp))
                fingerprints.append(fp)
            run(tpass, 'init', fingerprints[0])
            before_ids = (store / '.gpg-id').read_bytes()
            run(tpass, 'init', 'missing-key@invalid.example', ok=False)
            assert (store / '.gpg-id').read_bytes() == before_ids
            outside_ids = root / 'external-ids'; outside_ids.write_bytes(b'keep')
            (store / '.gpg-id').unlink(); (store / '.gpg-id').symlink_to(outside_ids)
            run(tpass, 'init', fingerprints[0], ok=False)
            assert outside_ids.read_bytes() == b'keep'
            (store / '.gpg-id').unlink(); (store / '.gpg-id').write_bytes(before_ids)
            secret = 'fixture $() apostrophe\' Unicode 日本語\nsecond line\n'.encode()
            run(tpass, 'insert', '-m', 'sites/example', data=secret)
            assert run(tpass, 'show', 'sites/example') == secret
            assert run(*gp, '--decrypt', str(store / 'sites/example.gpg')) == secret
            legacy = run(*gp, '--trust-model', 'always', '--encrypt', '-r', fingerprints[0], data=secret)
            (store / 'legacy.gpg').write_bytes(legacy)
            assert run(tpass, 'show', 'legacy') == secret
            # Also cover RFC 4880 MDC packets, independent of host GPG defaults.
            mdc = run(*gp, '--rfc4880', '--trust-model', 'always', '--encrypt',
                      '-r', fingerprints[0], data=secret)
            (store / 'mdc.gpg').write_bytes(mdc)
            assert run(tpass, 'show', 'mdc') == secret
            for name, ciphertext in [('legacy', legacy), ('mdc', mdc)]:
                corrupt = bytearray(ciphertext); corrupt[-1] ^= 1
                (store / 'corrupt.gpg').write_bytes(corrupt)
                assert run(tpass, 'show', 'corrupt', ok=False) == b''
                (store / 'corrupt.gpg').write_bytes(ciphertext[:-8])
                assert run(tpass, 'show', 'corrupt', ok=False) == b''
            (store / 'corrupt.gpg').unlink()
            run(tpass, 'init', '-p', 'team', fingerprints[1])
            run(tpass, 'cp', 'legacy', 'team/copy')
            assert run(tpass, 'show', 'team/copy') == secret
            assert run(*gp, '--decrypt', str(store / 'team/copy.gpg')) == secret
            run(tpass, 'mv', 'team/copy', 'team/moved')
            assert not (store / 'team/copy.gpg').exists()
            assert run(tpass, 'show', 'team/moved') == secret
            run(tpass, 'generate', '-n', 'generated', '32')
            generated = run(tpass, 'show', 'generated').strip()
            assert len(generated) == 32 and generated.isalnum()
            run(tpass, 'show', 'legacy', ok=False, extra={'TUMPA_PASSPHRASE': 'wrong'})
            run(tpass, 'show', 'legacy', ok=False, extra={'TUMPA_KEYSTORE': str(root / 'wrong.db')})
            run(tpass, 'insert', '-m', '../outside', data=secret, ok=False)
            (store / 'linked').symlink_to(root, target_is_directory=True)
            run(tpass, 'insert', '-m', 'linked/outside', data=secret, ok=False)
            # Mock only the Wayland transport; test real encryption and Rust pipe handling.
            mock = commands / 'nostromo-secret-copy'
            mock.write_text("#!/usr/bin/env python3\nimport os,sys,time\nfrom pathlib import Path\nassert len(sys.argv)==3 and sys.argv[2]=='clipboard'\np=Path(os.environ['CLIPBOARD_TEST_FILE']); data=sys.stdin.buffer.read()\np.write_bytes(data)\nif os.fork(): sys.exit(0)\nnull=os.open('/dev/null',os.O_RDWR)\nfor fd in (0,1,2): os.dup2(null,fd)\ntime.sleep(int(sys.argv[1]))\nif p.read_bytes()==data: p.write_bytes(b'')\n")
            mock.chmod(0o755)
            run(tpass, 'show', '-c', 'legacy', ok=False, extra={'PASSWORD_STORE_X_SELECTION': 'secondary'})
            run(tpass, 'show', '-c', 'legacy', ok=False, extra={'PASSWORD_STORE_CLIP_TIME': '0'})
            run(tpass, 'show', '-c', 'legacy')
            assert clipboard.read_bytes() == secret.splitlines()[0]
            time.sleep(1.5)
            assert clipboard.read_bytes() == b''
            run(tpass, 'show', '-c', 'legacy')
            clipboard.write_bytes(b'new clipboard')
            time.sleep(1.5)
            assert clipboard.read_bytes() == b'new clipboard'
            # Force encryption failure AFTER editing; RAII must remove plaintext.
            editor = commands / 'failed-editor'
            editor.write_text('#!/bin/sh\nprintf "changed" > "$1"\n'
                              'mv "$TUMPA_KEYSTORE" "$TUMPA_KEYSTORE.saved"\n')
            editor.chmod(0o755)
            before = (store / 'legacy.gpg').read_bytes()
            run(tpass, 'edit', 'legacy', ok=False, extra={'EDITOR': str(editor)})
            assert (store / 'legacy.gpg').read_bytes() == before
            assert not list(scratch.glob('tpass.*')), 'Plaintext temporary files survived failure'
            assert not (root / 'outside.gpg').exists()
            for path in store.rglob('*.gpg'):
                assert secret not in path.read_bytes()
            print('PASS: OpenPGP round trips, per-directory recipients, generation, wrong-key/passphrase, '
                  'path/recipient rejection, ciphertext authentication, clipboard expiry and edit-failure cleanup')
        finally:
            subprocess.run(['gpgconf', '--homedir', str(keys), '--kill', 'gpg-agent'],
                           env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
