`# Base-Setup — manual FreeBSD installation

This guide is **entirely manual**. It prepares the base OS; it is separate from
the one-command post-install setup. Do not run the older OpenBSD or X11
FreeBSD installers. The new entry point is documented in [INSTALL](INSTALL.md).

This preserves the installation split already documented in the archived
FreeBSD directory. Its detailed installer choices, root entry point, user build
stages and recovery process are the starting point for this port; its old
X11/doas/Zsh/Neovim application steps do not apply here.

Target: ThinkPad T14 Gen 2 Intel / i5-1135G7 with Iris Xe integrated graphics,
FreeBSD **15.1-RELEASE amd64**,
hostname **nostromo**, one ordinary desktop account whose name you choose.
Recommendations checked 2026-11-03;
confirm the release remains supported before a later reinstall.

## Before booting

Read [the full BIOS table](FIRMWARE.md). Keep a recovery USB and backups before
partitioning. The SN850X is reported as 2 TB; identify the actual disk by model
and capacity, never assume `nda0`, `nvd0`, `ada0` or a USB node.

Use **FreeBSD-15.1-RELEASE-amd64-dvd1.iso**, matching the user's preference.
DVD1 includes base sets, debug sets, rescue support and some packages; it is not
a complete offline Wayland/development repository. The amd64 DVD1 image may
also be written to suitable USB media. Verify the image against the official
[signed checksums](https://www.freebsd.org/releases/15.1R/signatures/), not a
checksum copied from a third-party blog. Writing an image erases the selected
USB device; verify its identity in the image-writing tool.
[Release/media details](https://www.freebsd.org/releases/15.1R/announce/).

## Installer choices

| Screen / option | Recommended choice | Meaning for this machine |
| --- | --- | --- |
| Boot | UEFI, normal multi-user installer | Keep ACPI and SMP; use safe mode only to diagnose an actual boot problem |
| Welcome | Install | Shell/Live modes are recovery/inspection alternatives |
| Keymap | **United States of America** | Matches the commands and default bindings; Japanese/Korean desktop input is configured later |
| Hostname | **nostromo** | Preserve the chosen machine identity; a real DNS domain is not required for this local setup |
| Installation type | **Distribution Sets** | Supported traditional base update path; Packages/pkgbase is a separate update model, not a desktop package option |
| base / kernel | Required | Base includes the native C/C++ toolchain; this is not an OpenBSD set-selection screen |
| base-dbg | Select | Keep base debugging symbols for diagnosis; consumes disk, not persistent idle RAM |
| kernel-dbg | Select | Keep kernel/module symbols for driver/crash investigation |
| lib32 | Select if offered | Retains the earlier selection and 32-bit FreeBSD userspace compatibility; does not install Linux |
| lib32-dbg | Optional, leave off initially | Needed only when debugging the compatibility libraries |
| src | Select | Matching base source is useful for driver/module diagnostics and supported native rebuilds |
| ports | Leave off initially | Obtain a current pinned ports tree later; avoid treating an old installation snapshot as the approved dependency graph |
| tests | Optional, leave off initially | Base test suite, not required for the dotfiles' host/native validation |

Keep base manual pages installed. The post-install stage adds C++ library pages,
language references and the English Handbook for the **DOCS** menu; DVD1 alone
does not provide that complete library. Download those packages during setup,
then use the [offline reader](OFFLINE-DOCS.md) without a network connection.

The installer may label the US keymap with its encoding. Test quotes, slash,
backslash, pipe, brackets, tilde and punctuation before proceeding. A different
layout is not inherently unsupported by FreeBSD; it would require adjusting the
documented keystrokes. See [bsdinstall](https://docs.freebsd.org/en/books/handbook/bsdinstall/).

## Disk, filesystem and swap

**Recommended: Auto (ZFS), GPT/UEFI, one-disk stripe** for the single SN850X,
with the ordinary root pool layout. A one-disk stripe has no redundancy; keep
external backups. ZFS boot environments make base/custom-desktop recovery useful
for this project. Choose full-disk GELI encryption if you want protection of the
offline laptop disk and can keep its recovery material safely; a login password
alone does not encrypt storage. Leave swap encryption enabled when offered.

Use **16 GiB swap** as the requested initial allocation. It is a workload safety
margin, not a rule that swap must match RAM, and it does not enable FreeBSD
hibernation. Native sysctl confirms 16 GiB RAM and eight logical CPUs; rediscover
physical memory after any hardware change. Avoid
swap files on ZFS. Do not enable deduplication or disable sync writes for speed.

Auto (UFS) is the simpler, lower-cache-complexity alternative if boot environments
are not wanted. Manual partitioning is for a deliberate custom layout; do not
guess EFI partition or pool geometry in a script. Review the final disk/partition
summary before accepting destruction of the existing OpenBSD installation.
See [ZFS administration](https://docs.freebsd.org/en/books/handbook/zfs/).

The Auto ZFS menu choices retained from the archived guide are:

| ZFS menu item | Choice | Meaning |
| --- | --- | --- |
| Pool type / disks | `stripe`, only the verified internal SN850X | One drive, no redundancy; do not select the installer USB |
| Pool name | `zroot` | Pool identifier; it is unrelated to hostname or username |
| Partition scheme | GPT / UEFI | Match the firmware boot mode |
| Force 4K sectors | Yes | 4 KiB allocation alignment |
| Encrypt disks | Yes for the portable personal laptop | GELI unlock at boot; retain the passphrase and recovery material separately |
| Swap size | `16g` | Requested disk-backed memory overflow allocation, not a hibernation promise |
| Mirror swap | No | There is only one selected SSD |
| Encrypt swap | Yes | Protects swapped memory contents |
| Install / Proceed | After reviewing the final disk summary | This is the destructive partitioning confirmation |

Auto UFS uses the traditional filesystem; Manual and Shell require your own
partition plan. Neither the current nor archived post-install script performs
these steps. GELI disk encryption and native ZFS encryption have different
recovery procedures; keep the method actually selected by bsdinstall.

## Network, accounts, time and services

Use the installer's network selection and scan first. The previous installation
used `iwlwifi0` with a cloned `wlan0`, but **rediscover** the current interface.
Use a suitable wired connection if Wi-Fi firmware is initially missing. Select
the actual country/regulatory domain; do not copy a US radio domain because the
keyboard is US. Keep DHCP for the initial LAN and use its DNS configuration.
Enable IPv6 when the local network supplies it; no blanket IPv6-disable tuning.

Set a root password for local recovery. Create the desktop account with a
lowercase login name (letters, digits, `_` and `-`), ordinary UID assigned
by the installer, home under `/home`, and supplementary **wheel** membership for
initial `su` recovery. Use `/bin/sh` initially; actual `/usr/local/bin/oksh` is
selected only after installation/verification. The later mdo rule gives this
account limited ACPI group access and no root transition. Administrative menus
use base su/PAM, so retain the root password and wheel membership. No password is
stored in the dotfiles.

Set the hardware clock/timezone correctly; use **Asia/Kuala_Lumpur** if this is
the laptop's intended local timezone. Check the displayed date/time before TLS
downloads. Do not configure timezone by sending the public IP to a web service.

| Service | Choice | Why |
| --- | --- | --- |
| sshd | On, retaining your explicit selection in the archived guide | Inbound SSH is separate from the client; later managed hardening uses port 2222 and tested keys |
| ntpd | On | Native clock synchronization |
| ntpd_sync_on_start | On | Correct initial clock drift at startup |
| local_unbound | Off initially | Matches the previous preference; use the supplied DNS path |
| powerd | Off initially on this Intel HWP machine | Detect hwpstate_intel first; do not run competing frequency policy loops |
| moused | Off initially | Desktop libinput is separate; enable only for required console-pointer behavior after testing |
| dumpdev | AUTO if crash dumps are wanted | Useful for driver/suspend diagnosis; consider the privacy/storage implications of dumps |

## Hardening choices

| Checkbox | Choice | Meaning / compatibility |
| --- | --- | --- |
| hide_uids | Select | Restricts other-user process visibility; verify the selected login service still works |
| hide_gids | Select | Restricts other-group process visibility |
| hide_jail | Select | Hides jail processes; does not install or enable jails |
| read_msgbuf | Select | Kernel logs then require root/mdo |
| **proc_debug** | **Leave unchecked** | Checking it disables unprivileged debugging and can break LLDB, procstat and pane-directory inspection |
| random_pid | Select | PID randomization, without treating it as a speed improvement |
| clear_tmp | Select | Clears temporary files at boot; do not store projects there |
| disable_syslogd | Select | Stops the network socket, not local logging |
| secure_console | Select | Requires root authentication for single-user recovery |
| disable_ddtrace | Select | Disables destructive DTrace operations; normal development does not need them |

When Add User asks for details, enter that login name, accept the assigned UID and
primary group, add supplementary `wheel`, keep the default login class and
`/bin/sh`, and record the proposed home. Use home permissions `700`, password
authentication enabled, no empty/random password, and leave the account
unlocked. Review the summary. The later installer discovers these values and
selects oksh only after it is installed; it never assumes UID 1000.

Keep kernel/browser mitigations at their release defaults. Any change later
needs a concrete compatibility or measured-performance finding. User willingness
to trade security for speed is not evidence that every protection costs useful
performance.

## First boot: inspect and establish networking

Choose **Boot Multi User** for ordinary setup. Single-user mode is for recovery;
it can leave root read-only and other filesystems/services unavailable. Being root
does not bypass a read-only mount. If you deliberately entered single-user mode
and need no repair, type `exit` to continue booting, then log in locally and use
`su -`.

If you must edit a file during recovery, first inspect `mount`. Remount the
installed root writable with `mount -urw /`. For UFS, mount the remaining local
filesystems with `mount -a`; for ZFS, use `zfs mount -a`. Do not change dataset
properties or remove immutable flags blindly. If writing still fails, inspect
`mount`, `ls -lo /etc/rc.conf` and the exact error. On installer/live media, `/`
can be the live image rather than the installed system. Finish recovery and boot
multi-user before running the dotfiles installer.
[FreeBSD single-user recovery](https://docs.freebsd.org/en/books/faq/#forgot-root-pw).

The owner has confirmed **16 GiB RAM and eight logical CPUs** with native sysctl.
The i5-1135G7 has four physical cores with Hyper-Threading; eight logical CPUs is
the expected count. Resource limits use the detected values.

Run these from the normal local root console or after `su -`:

```sh
freebsd-version -kru
uname -m
sysctl hw.model hw.physmem hw.ncpu
sysctl net.wlan.devices
ifconfig -a
netstat -rn
cat /etc/resolv.conf
date
```

For firmware, first check `command -v fwget` and the installed `man fwget`.
On the selected release use the native firmware utility when present; do not
blindly run `pkg install fwget` as a fallback. If firmware/networking fails,
capture the driver/PCI ID and error and use wired/offline bootstrap rather than
repeat the earlier failing command without diagnosis.

When there is no working connection, `install.sh --clean` and `--upgrade` start
with console Wi-Fi setup, before downloading anything. Enter the detected radio,
country if needed, exact SSID and security mode. The password prompt disables
terminal echo. The setup creates the missing WPA file, preserves unrelated
profiles and rc.conf settings, uses the native per-interface service, and saves
the new network only after successful authentication. It then checks DNS
separately. The checkout can be copied from USB if networking is needed before
Git is available.

If the base installer already configured a working connection, the installer
keeps it and asks nothing. Loading `if_iwlwifi` alone does not authenticate to an access point.
If configuring manually, and
`net.wlan.devices` lists `iwlwifi0`, the intended persistent values are
`wlans_iwlwifi0="wlan0"` and `ifconfig_wlan0="WPA DHCP"`. Create the cloned
interface only if missing; use a root-readable `/etc/wpa_supplicant.conf` with
mode 0600. The normal rc network/wpa_supplicant path should own the daemon:
do not start another background supplicant every time the network is checked.
Use the installer or edit the protected profile interactively so passwords do
not enter the repo/logs/shell history. Test IP routing and DNS separately.
[Wireless configuration](https://docs.freebsd.org/en/books/handbook/network/).

## Updates and initial Git handoff

For the recommended distribution-set install, run the base update stages
separately and inspect each result:

```sh
freebsd-update fetch
freebsd-update install
```

Reboot when the tool requires it; verify running and installed kernel versions
before adding a release-matched DRM module. If the base was installed with
pkgbase, stop and use its documented update method instead. The earlier failed
`freebsd-update fetch install` invocation is not a reason to conceal failures.

Bootstrap native `pkg` if required, preview/install the explicitly permitted Git
bootstrap, and keep normal repository signature checks. Do not install the old
desktop package list. Clone the project as the desktop account into its home and retain
that ownership; the setup entry point will separately handle root-only files.
No preinstalled doas is needed: the selected replacement is **base mdo**.

The implementation is ready for its native validation stage; the laptop has not
run it yet. Read [VALIDATION.md](VALIDATION.md), then follow [INSTALL.md](INSTALL.md)
for the preview, native preflight and root-console apply. Keep the manual OS install and
its console recovery available throughout.
