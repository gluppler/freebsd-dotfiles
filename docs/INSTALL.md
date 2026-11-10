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
2. Build the 15 pinned library/package variants as the ordinary user, run ports
   staging checks, import their archives into a private signed transaction repo,
   and retain matching recipe receipts and locks. Build jobs use detected RAM/CPUs.
3. Install desktop/development roots and detected firmware/DRM through the same
   gate. Remove only listed, automatic, unlocked GNU bootstrap leftovers with no
   consumers; preserve manually installed/locked packages and report conflicts.
4. Build patched native desktop programs, tpass and rustup; install pinned editor
   plugins, native Go/Python tooling and offline C/C++ references. No source build
   runs as root.
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
are under `.build/logs/`. Each finished run records `result`, `last-stage` and
`exit-status`; `pkg-version` identifies the package manager used. Read the
failing stage's log before rerunning the same command.

When `--apply` starts and again on exit, the installer removes earlier finished
diagnostic-only runs, so only the current run's logs remain: read or copy a failed
run's logs before rerunning. It recognizes older failed runs through their nonzero
`*.status` files. Finished runs containing `system-backup/` or `policy-backup/`
move to `/var/log/nostromo/recovery/` instead. Unfamiliar, unsafe or unfinished
directories are retained and reported. Cleanup runs under the
installer lock and does not follow directory symlinks. An unchanged package
policy is reused; a changed policy's previous version goes in that run's
`policy-backup/`. Older `policy.previous.*` directories are left for manual review.
Interrupted publication restores the old policy if the active path is missing.

Temporary package downloads/private repositories and unpublished policy directories
are removed on ordinary failures and handled signals. Successfully installed
packages, manually installed Python, source caches and build work remain available
for a retry. Removing them automatically could damage working software or discard
hours of compilation. SIGKILL or power loss cannot run shell cleanup handlers.

Generated ports trees have an mtree receipt. After a recipe change,
`prepare-ports` regenerates an unedited `.build/ports` tree from the cached,
checksum-verified archive and discards the old recipe's build work. A changed,
added or missing file stops the stage instead: edits are never reset.
Do not remove an installation/package lock until confirming its process ended.

User-file backups are under `~/.local/state/freebsd-dotfiles/backups/`, and
`~/.local/state/freebsd-dotfiles/links` lists the links last applied. A later run
removes a listed link that has left `links.txt` if it still points to the same
checkout file; anything you changed is kept.
System backups and a file/mode/hash journal are in the install log's
`system-backup/`, under `/var/log/nostromo/recovery/` after a later run. Failed
system-file provisioning restores files only if they
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

### Recover from a stop at python312-dependencies

This is the first stage that runs the package helper, so its errors appear here.
Neither error below installs or removes a package before stopping.

- The first installer printed empty `Unreviewed package: ... ()` messages and
  incomplete/unresolved dependencies for `libedit`, `pkgconf`, `indexinfo`,
  `mpdecimal` and `expat`. pkg prints an owner-only row for a package with no
  dependencies. The corrected reader removes only those empty-list placeholders,
  then checks every actual dependency against its declared count and identity.
- Commit `faef848` passes that audit, then previews and installs with
  `--no-remove`. pkg 2.8.4 has no such option, so the stage stops with
  `pkg: unrecognized option` for it; that dry run also lacked the `-y` pkg needs
  to report success. The helper now reviews pkg's dry-run plan, stops on any
  removal or unrecognized plan, and approves that command exactly once.

Later stages needed two related corrections. The audit now accepts
architecture-independent packages (`FreeBSD:15:*`), such as `public_suffix_list`
for the libpsl build and Python modules. When a transaction contains pkg itself,
pkg's own upgrade is reviewed and approved before the rest; `cmake-core` links
pkg's library.
Manually installing Python fixes none of these; removing Python is unnecessary.

To confirm the second error, run this from the root console before rerunning
`--apply`, which removes earlier diagnostic-only logs:

```sh
grep -h -e '--no-remove' /var/log/nostromo/install-*/python312-dependencies.log
```

Push the corrected checkout, then update the laptop copy **as gluppler**:

```sh
cd /home/gluppler/freebsd-dotfiles
git pull --ff-only
```

From the laptop's root console:

```sh
sh /home/gluppler/freebsd-dotfiles/install.sh --check gluppler
sh /home/gluppler/freebsd-dotfiles/install.sh --apply gluppler
```

Adjust the path if the checkout is elsewhere. Skip the optional Wi-Fi setup when
the current connection works. The retry installs the corrected package helper.
This update also removes the KiCad workflow, which changes the pinned ports
recipe, so `prepare-ports` replaces the failed run's unedited tree from the
cached archive; no manual cleanup is needed. A fresh clone downloads the archive
and prepares its first tree instead. The package policy changes too: the retry
publishes it and keeps the previous copy in that run's `policy-backup/`.
Existing `FreeBSD-ports`, `FreeBSD-ports-kmods` and disabled `FreeBSD-base`
definitions need no edits for these errors; the helper uses private signed
upstream definitions without replacing those system files.

### Recover from a stop at python312-build

Commit `15bb0b4` passes `python312-dependencies`; its build then stops linking
two Python modules:

```text
ld: error: unable to find library -lmpdec
*** [Modules/_decimal.cpython-312.so] Error code 1
ld: error: unable to find library -lexpat
*** [Modules/pyexpat.cpython-312.so] Error code 1
```

Python's libedit patch removed `USES=readline`, which also added the
`/usr/local` include and library search paths; the system libmpdec and expat are
installed there. The patch now keeps those paths. Variant builds also report
pkg's advisories instead of stopping: once the nightly security run downloads its
advisory file, the ports framework would refuse Python 3.12, whose two listed
advisories have no fixed version yet.

Pull and rerun `--check` and `--apply` as above. Both changes alter the ports
recipe, so `prepare-ports` replaces the unedited generated tree and discards the
failed build work; no manual cleanup is needed.

### Recover from a stop at libxslt-dependencies

With the build fixed, python312, cmake-core and libxml2 build, install and lock.
libxslt's dependency stage then stops:

```text
libxml2-2.15.4 is locked and may not be modified
```

Variants are locked after installation, and libxslt's dependency list names
libxml2 again. pkg refuses any request that names a locked package, even one
identical to the reviewed archive. The package helper now leaves installed,
locked variants out of install, preview and update requests, which they already
satisfy. The desktop list, which names fcitx5 and wlroots020, and the software
menu's update needed the same change.

Pull and rerun `--check` and `--apply` as above. The ports recipe is unchanged,
so the three finished variants are not rebuilt: their completed port work is
checked again, reinstalled from its archive and locked before libxslt continues.

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
