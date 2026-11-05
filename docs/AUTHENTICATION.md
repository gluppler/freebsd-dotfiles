# Password, fingerprint and FIDO

The native password stack remains the default. FreeBSD ports provide
`libfprint` 1.94.10, `fprintd` 1.94.4 and `pam_u2f` 1.4.0 in the inspected
catalog. The laptop's **actual USB ID has not been supplied**; its BIOS reader
toggle and ThinkPad model do not identify a supported sensor.

Run `nostromo-auth` from a terminal. PROBE lists local USB devices, installed
PAM modules, enrolled fingerprints and attached FIDO authenticators. Use
`usbconfig -d ugenBUS.ADDRESS dump_device_desc` locally to read `idVendor` and
`idProduct`. Do not publish the serial descriptor. Check that pair against the
**installed release's** libfprint driver table. The upstream
[device list](https://fprint.freedesktop.org/supported-devices.html) describes the
development branch; a match there alone is not FreeBSD hardware proof.

## Fingerprint

After the optional packages pass the dependency gate, keep the system D-Bus
service available. fprintd is activated through D-Bus; do not install a Linux
service manager or run an extra polling daemon. Run ENROLL FINGERPRINT, then
VERIFY FINGERPRINT under the ordinary account. Test a wrong/unregistered finger
and reconnect the reader before enabling login authentication. If no device is
found, leave the password stack unchanged and record the USB ID/library outcome.

The native module is `/usr/local/lib/security/pam_fprintd.so`, supplied by the
[FreeBSD fprintd package](https://cgit.freebsd.org/ports/tree/security/fprintd/pkg-plist).
`system/pam.d/optional/fingerprint` is the reviewed opt-in line. It is **not
installed into an active PAM service automatically**. Preserve the stock login
account/session checks and password fallback. Existing enrollment/biometric
records belong to fprintd's local storage, never this repository.

## FIDO/U2F security key

FIDO is a separate USB/NFC authenticator workflow; it does not turn the built-in
fingerprint sensor into a FIDO device. Run ENROLL FIDO and touch the actual key.
The command uses a stable relying-party ID `pam://nostromo`, independent of a
future hostname change. Each enrollment writes a new local file and preserves
earlier credentials. It contains public credential metadata; the private key
remains in the authenticator.

Review the new file and install it as the ordinary account's line in root-owned
`/usr/local/etc/nostromo/u2f_mappings`. Keep existing users/keys. That file must
be readable by the ordinary-account locker, mode **0644**, with root-owned,
non-writable parent directories. Multiple keys for one user belong on that
user's single colon-separated mapping line; do not append duplicate user rows.
Enrollment must finish successfully before adding the opt-in line from
`system/pam.d/optional/fido`.

The native module is `/usr/local/lib/pam_u2f.so`. The template offers a touched
security key as an **alternative** to the password, retaining recovery; it is
not a claim of mandatory two-factor authentication. Do not enable `nouserok`,
`alwaysok`, `debug` or a passwordless fallback. PIN/user-verification policies
require a separate tested conversation flow. See the
[upstream PAM/FIDO configuration](https://developers.yubico.com/pam-u2f/).

## Activate one service at a time

Keep a root console open. First test the chosen module with a temporary PAM
service and a native PAM test client. Then back up the target service and add
the one chosen `auth sufficient` line **before** its existing auth include.
For SDDM the file is `/usr/local/etc/pam.d/sddm`; for the locker it is
`/usr/local/etc/pam.d/gtklock`. Do not replace `/etc/pam.d/system`, alter mdo
(which uses mac_do rather than PAM), enable autologin or change remote SSH.

Test success, failed/cancelled scan, absent hardware, expired/locked accounts,
password fallback and boot/resume with the device unplugged. The graphical
locker starts PAM after Enter in the Password field; its current conversation
handles the password and module informational messages, not an independent
multi-field PIN interface. Keep the timeout bounded. Restore the backed-up
service from the still-open root console if any recovery test fails.

The existing base OpenSSH also has `ed25519-sk` support when built with its
native FIDO provider. `ssh-keygen -t ed25519-sk` is a separate, user-initiated
SSH-key enrollment; never generate or distribute SSH credentials during setup.
