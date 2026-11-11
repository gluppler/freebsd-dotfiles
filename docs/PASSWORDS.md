# Pass-compatible passwords

`pass` is an explicit POSIX wrapper for the pinned **tpass 0.6.4** build; it is
not the GNU/Bash `pass` program. Entries keep the `.password-store/name.gpg`
OpenPGP layout and per-directory `.gpg-id` recipients. `tcli` manages its own
OpenPGP key database; `tclig` provides supported GPG-style commands. No GNU
GnuPG, pinentry, RNP or Botan package is required. Bash pass extensions are
deliberately rejected, not silently executed through another shell.

Run these in foot, as your ordinary account:

```sh
tcli --help
tcli import /path/to/your/private-key.asc
tcli list
pass init YOUR_ENCRYPTION_KEY_FINGERPRINT
pass insert sites/example
pass generate sites/another 24
pass show --clip sites/example
pass edit sites/example
```

Use the exact fingerprint printed by your key-management tool. Import your own
keys locally; no default key, password or account is shipped. Keep an encrypted
offline recovery copy. `tcli` uses a separate key store, so importing an existing
password directory alone does not import its decryption keys. Use `tcli --help`
for key creation/export and supported smart cards. Enrollment is never automated.
FreeBSD prompts for the key passphrase invisibly in the terminal. An explicitly
configured `PINENTRY_PROGRAM` remains possible; none is installed or started.

The PASSWORDS menu (Super+Shift+P) lists names without decrypting previews and copies one chosen
entry. `nostromo-secret-copy` stores at most 1 MiB in memory, advertises a
password-manager sensitivity hint and releases its **own** Wayland selection
after 45 seconds by default (`PASSWORD_STORE_CLIP_TIME`, 1–3600 seconds).
It never writes the password to a temporary file or puts it in command arguments.
Copying something else cancels the old owner; expiry cannot clear the new item.
`PASSWORD_STORE_X_SELECTION=primary` is supported for compatibility with pass;
Wayland has no secondary selection. No persistent clipboard-history daemon is
started. Other applications can still read the active clipboard, and third-party
clipboard managers may ignore sensitivity hints.

Encrypted-entry updates use a complete, synced temporary ciphertext and atomic
rename. Decryption verifies the whole authenticated message before output;
unauthenticated legacy SED packets are rejected. Editing necessarily creates
plaintext for the editor, removed on normal success and returned errors. A power
failure or forced kill can leave that edit file: use a private RAM-backed TMPDIR
when that matters. Secure erasure on an SSD is not promised.

Host tests use disposable keys and a host-only GnuPG installation to check
interoperability, tampering, bad credentials, recipient/path rejection, generation
and edit failure. They do not install GnuPG on FreeBSD. Clipboard transport and
native USB/OpenPGP-card operation require the laptop acceptance test.

Sources: [tumpa-cli](https://github.com/tumpaproject/tumpa-cli),
[Wayland data control](https://wayland.app/protocols/ext-data-control-v1).
