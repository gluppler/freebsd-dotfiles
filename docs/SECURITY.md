# Privileges, SSH and PF

## Base mdo

FreeBSD 15.1 provides `/usr/bin/mdo` and `mac_do`. The desktop account receives
**no root transition**. Its rule is
`uid=DETECTED_UID>uid=.,gid=POWER_GID,!gid=.`: keep the same user and supplementary
groups, and temporarily select the dedicated `nostromo_power` primary group.
Devfs grants that group access only to `/dev/acpi`. The installer does not add
the account to `operator`, whose access would include system disks.

Administrative menu operations use `nostromo-admin`: base `su`/PAM asks for the
root password, then base mdo executes the selected helper with root's groups and
a clean environment. GUI operations open a themed foot authentication prompt;
terminal operations use their existing terminal. There is no authentication
cache, new setuid program, or root GUI. Input/output cross the GUI prompt through
private FIFOs; Wi-Fi passwords and Bluetooth PINs are not put in argv or ordinary
user-owned temporary files. Cancelling or failing authentication executes no helper.
PAM owns the terminal streams during authentication; the helper's original
streams are restored afterward so password prompts cannot pollute captured data.
No doas/sudo configuration is installed. Base PAM still governs authentication;
keep a working root password and the account's wheel membership.

The installer removes only its former exact `uid=DETECTED_UID>uid=0` grant and
preserves unrelated administrator rules. It refuses an unmanaged collision with
the power group and checks both root denial and the limited group transition
under a fresh user process. If another existing rule still grants root, the
stage stops for policy review. File changes and live policy have conditional
rollback; unrelated MAC policies and securelevels are retained.

```sh
id
mdo -i -u root -- /usr/bin/id -u
mdo -k -g nostromo_power -- /usr/bin/id
nostromo-admin performance status
```

The root request must fail. The group request must retain your ordinary UID.
The last command asks for the root password. Initial installation still runs
from the root console and does not need an already configured mdo rule.

ACPI group access is a power-control capability, not a command allowlist: programs
under your account can request power-state changes. They do not gain root, raw
disk access or permission to change system configuration. Keep this group reserved
for the installed ACPI rule.

## Suspend locking

Automatic lid/sleep-button suspension is disabled in the native ACPI settings;
their events go to the logged-in session, which locks before requesting S3.
A priority-100 devd Suspend handler also checks the existing Wayland sockets as
the ordinary user before running native `/etc/rc.suspend`. A failed lock or a
four-second timeout sends `acpiconf -k 1` to cancel the pending request, rather
than relying on an rc hook's exit code. FreeBSD's kernel otherwise forces a
pending request after ten seconds. Unknown or absent sessions are refused.

The helper reads the live `pam_xdg` prefix to find the existing runtime directory;
it does not create a second session directory. Password prompts, compositor
acknowledgement, sleep-button wake events and resume still require native testing.
This does not prevent a root administrator from bypassing the configured hooks
or a compromised desktop account from changing its own session. The standard
devd rules must remain enabled and custom higher-priority suspend rules require review.

## SSH

The laptop is primarily an SSH client. User keys, known hosts and real endpoint
aliases stay local. `server` uses the chosen local alias; no server/router setup
is performed. Login/authentication secrets are never generated into the checkout.

The selective server policy sets port **2222**, public-key authentication, no
root/password/keyboard-interactive login and no forwarding. Existing sshd enablement
is preserved. The installer requires the laptop console, so it can safely stage
this policy without depending on a still-working remote session. Incoming SSH is
blocked by the default empty allowed-peer table; add an authorized key and an
explicit WireGuard peer before expecting inbound access. Password login at the
local graphical/console session remains separate and available.

The merge follows supported `/etc/ssh` includes, preserves unrelated directives
and Match blocks, and removes/replaces only listed managed keys. It refuses
complex/outside include paths and nonempty custom `sshd_flags`, which can override
config-file settings. It preserves or
creates native host keys, runs `sshd -t`, checks `sshd -T -C` for the selected
account and validates the client with `ssh -G`. It does not restart the active
SSH service during installation. Port 2222 reduces default-port scans; keys and
firewall rules provide the actual access controls.

## PF

The FreeBSD-specific rules live in `/usr/local/etc/nostromo/pf.conf`, loaded from
a namespaced parent anchor. The parent merge preserves unrelated macros, rules
and anchors. It rejects ambiguous top-level includes, unsafe `set skip` bypasses
and custom `pf_flags`, and validates the complete candidate with native
`pfctl -nf` before writing it. It does not flush live state or load new rules over
the current connection during installation; rc applies the enabled policy at boot.

The anchor permits stateful outgoing traffic, loopback, DHCP and essential
ICMP/IPv6 behavior, and blocks unsolicited inbound traffic. Incoming TCP 2222 is
allowed only on project WireGuard interfaces from addresses explicitly listed
in root-owned `/usr/local/etc/nostromo/ssh-peers`. The default empty file permits
none. Configure that file and the local authorized key deliberately; WireGuard
setup alone does not expose SSH. Existing unrelated rules remain on disk, but
this project's quick policy intentionally determines filtering for its traffic.

## Ownership and recovery

System helpers, PAM policy, loader assets and package policy are root-owned.
Builds, user links, project environments and secrets belong to the desktop user.
System-file transactions reject unsafe symlink parents, keep numbered backups
until the run's final check passes, and restore only files whose content/mode
still match the transaction's write;
later administrator edits are preserved. The install is not an atomic rollback
of packages, compiled outputs, group memberships or created directories. See
[INSTALL](INSTALL.md) before applying or recovering it.

Native PAM checks passwords. Fingerprint/FIDO stay optional until supported
hardware is identified and enrolled; see [AUTHENTICATION](AUTHENTICATION.md).
Performance profiles retain NX, ASLR, browser sandboxing, TLS checking and kernel
protections. They do not weaken unrelated security settings for an unmeasured gain.

## Repository contents

Keep SSH and WireGuard keys, passwords, tokens, device identifiers and real
service endpoints outside the checkout. Use the documented local overrides;
the shipped files contain placeholders. `.gitignore` excludes common private
files, overrides, build caches and exports. The source exporter also checks
tracked files, since ignore rules cannot remove a file already in Git.

Export checks cover private-key blocks, several token formats, credential URLs,
WireGuard key assignments, local host paths and unsafe file permissions. These
are limited checks, not a complete secret scanner. Review the file list and diff
before publishing. If a credential was committed, revoke it and remove it from
history before sharing the repository; deleting the current file is insufficient.

Sources: [mdo](https://man.freebsd.org/cgi/man.cgi?query=mdo&sektion=1),
[mac_do](https://man.freebsd.org/cgi/man.cgi?query=mac_do&sektion=4),
[su](https://man.freebsd.org/cgi/man.cgi?query=su&sektion=1&manpath=FreeBSD+15.1-RELEASE),
[ACPI suspend requests and cancellation](https://github.com/freebsd/freebsd-src/blob/releng/15.1/sys/dev/acpica/acpi.c),
[sshd](https://man.freebsd.org/cgi/man.cgi?query=sshd&sektion=8),
[PF](https://man.freebsd.org/cgi/man.cgi?query=pf.conf&sektion=5).
