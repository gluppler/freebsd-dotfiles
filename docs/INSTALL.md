# Post-install setup and recovery

Complete [Base-Setup](BASE-SETUP.md) manually first. Keep the permanent checkout
inside the ordinary account's home, owned by that account, with no whitespace in
its path (the ports framework cannot use whitespace in its build paths). Example:
`/home/gluppler/Projects/freebsd-dotfiles`.

## Obtain the source

Once published, clone the repository **as gluppler**:

```sh
mkdir -p "$HOME/Projects"
git clone https://github.com/gluppler/freebsd-dotfiles.git "$HOME/Projects/freebsd-dotfiles"
cd "$HOME/Projects/freebsd-dotfiles"
sh install.sh --preview gluppler
```

Alternatively, transfer the source archive and its `.sha256` file to the laptop.
Run `sha256` on the archive and compare it with that file; obtain the expected
checksum through a trusted channel. Extract with `tar -xzf` under `~/Projects`
as the ordinary account. Do not overlay an existing checkout. The extracted
`freebsd-dotfiles` directory works without Git metadata. Transfer the source
archive rather than the development machine's `.build/` directory, which contains
host-specific binaries and caches. Installation requires working networking for
the signed package repositories and pinned source downloads.

## Run the installer

From the laptop's local console, switch to root and enter the permanent checkout:

```sh
su -
cd /home/gluppler/Projects/freebsd-dotfiles
sh install.sh --check gluppler
sh install.sh --apply gluppler
```

Replace the path and account argument if needed. Preview works on another host
and performs no installation. `--check` validates the native release, account,
checkout, source files and protected parent directories without installing
packages or writing system configuration. It does not test network access,
compile software or exercise hardware.

Check and apply require native FreeBSD 15.1 amd64, matching installed/running kernels,
base mdo, an ordinary UID of at least 1000, a user-owned permanent checkout and
writable system filesystems, running devd and all source files. The checkout must not contain group/world-writable files.
Initial installation needs neither an existing mdo rule nor doas.
The installer refuses an SSH session so network policy cannot strand its operator.

## What happens

1. Offer console Wi-Fi setup before package downloads. Password entry bypasses
   the install log. Skip this when the current connection already works.
   Bootstrap pkg with FreeBSD's signature verification and publish the root-owned
   package policy. Resolve and audit the complete requested dependency closure.
2. Build the 21 pinned library/package variants as the ordinary user, run ports
   staging checks, import their archives into a private signed transaction repo,
   and retain matching recipe receipts and locks. Build jobs use detected RAM/CPUs.
3. Install desktop/development roots and detected firmware/DRM through the same
   gate. Remove only listed, automatic, unlocked GNU bootstrap leftovers with no
   consumers; preserve manually installed/locked packages and report conflicts.
4. Build patched native desktop programs, tpass and rustup; install pinned editor
   plugins, native Go/Python tooling, KiCad libraries/assembly workflow and offline
   C/C++ references. No source build runs as root.
5. Validate staged ELF binaries, linked libraries, configuration syntax, helper
   availability, plugins and offline documentation. `nostromo-docs --check`
   requires the installed language manuals, books and examples before proceeding.
   Back up user files and install explicit links.
6. Back up and selectively merge loader, rc, sysctl, devfs, mdo, SSH/PF and SDDM
   settings. Install root-owned helpers, fonts, PAM/loader/theme files. Validate
   native SSH/PF syntax, denial of direct mdo root access, limited ACPI group access
   and the final fresh-user environment. Install and check the Wi-Fi/Bluetooth
   merger and SSID decoder along with the suspend guard.
7. Select actual oksh and enable SDDM **last**. Provisioning leaves the current
   firewall and desktop running; only the explicit Wi-Fi setup changes its chosen
   radio during installation. No automatic reboot.

The first native build may reveal a release/port/API issue that macOS cannot
exercise. Unknown dependencies, stale recipes, missing devices and invalid files
stop the relevant stage; errors are not suppressed to reach a success message.
See [VALIDATION](VALIDATION.md) before treating the candidate as laptop-tested.

## Logs, reruns and recovery

Root stage logs are under `/var/log/nostromo/install-*`; native user build logs
are under `.build/logs/`. Read the failing stage's log before rerunning the same
command. Generated ports trees have an mtree receipt: preserve a modified/stale
`.build/ports` tree before rebuilding it, rather than resetting user edits.
Do not remove an installation/package lock until confirming its process ended.

User-file backups are under `~/.local/state/freebsd-dotfiles/backups/`.
System backups and a file/mode/hash journal are in the install log's
`system-backup/`. Failed system-file provisioning restores files only if they
still match what that transaction wrote; later administrator edits are retained.
Group memberships, ACPI settings and active mdo policy introduced by that failed stage are
restored where safe. Package transactions, previously completed user links,
created directories and loaded kernel modules are not one atomic OS rollback.

For a graphical boot failure, use another virtual console (`Ctrl+Alt+F2`) and
log in as root. `sysrc sddm_enable=NO` restores console boot; inspect the session
log at `~/.local/state/nostromo/session.log` and SDDM's logs. Do not delete the
permanent checkout: user links and compiled binaries point into it. On ZFS,
create a boot environment with `bectl create before-nostromo` before applying
changes and keep the loader's boot-environment/recovery options available.

Optional fingerprint/FIDO enrollment, WireGuard keys/peers, SSH authorized keys,
Bluetooth PINs, printer/scanner models and board memory maps are local inputs.
The installer creates none of these credentials and never invents device support.

## Source exports

From the development checkout, as its ordinary owner:

```sh
python3 tests/release.py
sh scripts/export.sh
```

The exporter uses Git to collect tracked and untracked files that are not
ignored, then checks paths, file permissions and common credential patterns.
It creates a fresh extraction and checks the source manifest and installer
preview before writing `.dist/freebsd-dotfiles-*.tar.gz`. A matching `.sha256`
and `.files` manifest accompany it. Export requires Git and BSD tar on FreeBSD
or macOS; Python is only needed for the separate regression test.

The archive excludes `.git`, `.build`, `.dist`, editor files and private
overrides, SVG originals and simulated screenshots. It contains the real
`home/.local` tree and `packages.local` policy.
Archive ownership is normalized, and extended attributes, ACLs and macOS
metadata are omitted. Source licenses and artwork attribution are retained.

An export takes the current file contents, including uncommitted changes. It
does not stage, commit or push anything. Before publishing, review `git diff`
and `git status --short`, inspect the archive's file list, and run the checks
in [VALIDATION](VALIDATION.md). Ignore rules and pattern checks cannot detect
every secret; inspect new configuration and assets before including them.
