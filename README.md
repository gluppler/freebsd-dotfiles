# Nostromo

FreeBSD **15.1-RELEASE amd64** dotfiles for a keyboard-driven Wayland desktop on
the ThinkPad T14 Gen 2 Intel: Core i5-1135G7, Iris Xe graphics and NVMe storage.
The default hostname is `nostromo`. No account is built in; the installer sets up
the one you name.

The desktop uses **dwl, foot, qutebrowser, oksh, vis and abduco/dvtm**, with
fuzzel, fastfetch, zoxide, nnn, Git/lazygit, LLVM, uv and native WireGuard.
Michroma and Azeret Mono, monochrome artwork, custom window bars and adjustable
CRT effects are animated by default. Development tools cover C/C++, Rust, Go, Python,
shell, assembly and the documented Zephyr/Rust embedded workflows. Offline
references include an illustrated electronics guide to circuits, robotics, PCBs
and badges.

The installer has completed natively on the T14. First reboot, login and
hardware acceptance are still pending; see [validation](docs/VALIDATION.md). Simulated screenshots and SVG
originals are archived outside this repository. Installed artwork uses PNG.

## Install

Install the OS manually using [Base-Setup](docs/BASE-SETUP.md), including the
[firmware settings](docs/FIRMWARE.md). Keep a complete checkout or extracted
source archive under the desktop account's home, owned by that account.

Review the plan as the ordinary user:

```sh
sh install.sh --preview
```

Then, from a local root console in the same directory, replacing `<account>`
with the desktop account's login name:

```sh
sh install.sh --check <account>
sh install.sh --clean <account>
```

After a `git pull`, `sh install.sh --upgrade <account>` applies what changed.

Boot normally into multi-user mode first. `--check` performs read-only native
preflight. `--clean` is a clean full install: it removes earlier packages and
build output, installs packages, builds as the ordinary user and enables login
after validation. `--upgrade` applies the checkout's changed configuration,
documents and pins to the installed environment, and continues a run that
stopped. Both report whether `pkg.FreeBSD.org` is reachable and ask
`Configure a Wi-Fi connection now? [y/N]` before downloading; without a
connection, declining stops the run. They keep backups of replaced files only until the final check
passes, and logs only when a stage stops. Base `mdo` grants limited ACPI access; administrative changes use
base `su`/PAM authentication. No existing privilege wrapper is needed.
It does not partition disks; after a final check it asks before rebooting.
Read the [installation and recovery
guide](docs/INSTALL.md) before applying it. Keep this checkout in place: installed
user files and built programs link into it.

## Layout

Each program has its own folder: its configuration, and for the programs built
here, the patches and headers that build them. `.install/links.txt` names where
each file is linked in your home, for example `foot/foot.ini` at
`~/.config/foot/foot.ini` and `bin/` in `~/.local/bin`.

| Path | Contents |
| --- | --- |
| `install.sh` | Root installer and read-only preview/preflight |
| `dwl/`, `foot/`, `vis/`, `qutebrowser/`, … | One program each: configuration, patches and its upstream license |
| `oksh/` | Interactive shell and the login profile |
| `bin/` | Desktop helpers and toolchain wrappers |
| `session/` | Small session programs: splash, idle viewer, clipboard, events and control |
| `sddm/` | Login greeter theme and settings |
| `system/` | System settings, privileged helpers and boot files |
| `embedded/` | Zephyr and bare-metal toolchain files |
| `fonts/`, `wallpapers/`, `art/` | Typefaces, wallpapers, the orb and their attribution |
| `docs/` | Guides, the offline references and design notes |
| `.install/` | The installer's scripts, tests and generators, the link manifest, package policy and pinned sources |

Build output stays in `.build/`. `sh .install/scripts/export.sh` creates a checked source
archive under `.dist/`, with a SHA256 checksum and file list. Both directories
are excluded from Git. The archive contains everything needed from this project;
installation still downloads native packages and pinned sources. No archived
dotfiles tree is required. See [source exports](docs/INSTALL.md#source-exports).

Keep credentials and personal overrides outside the checkout. The shipped
WireGuard, SSH and service settings contain no enrolled keys or real endpoints;
local setup is covered in the relevant guides. Review [security](docs/SECURITY.md)
and [licenses and attribution](COPYING.md) before publishing changes.

## Guides

- [Keyboard controls](docs/KEYBINDINGS.md), [editor and development](docs/DEVELOPMENT.md), [embedded Rust/Zephyr](docs/EMBEDDED.md)
- [First-run requirements](docs/FIRST-RUN.md), [full laptop information](docs/SYSTEM-INFO.md)
- [Offline manuals, formatted examples and the electronics guide](docs/OFFLINE-DOCS.md), [password store](docs/PASSWORDS.md)
- [Packages and GNU exceptions](docs/PACKAGES.md), [boot and session](docs/BOOT-AND-SESSION.md)
- [Hardware](docs/HARDWARE.md), [performance](docs/PERFORMANCE.md), [fingerprint/FIDO](docs/AUTHENTICATION.md)
- [Wi-Fi](docs/WIFI.md), [WireGuard](docs/WIREGUARD.md), [Bluetooth](docs/BLUETOOTH.md)
- [Requirements](docs/PLANS.md), [migration coverage](docs/MIGRATION-COVERAGE.md), [validation](docs/VALIDATION.md)
