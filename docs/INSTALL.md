# Post-install setup and recovery

Complete [Base-Setup](BASE-SETUP.md) manually first. Keep the permanent checkout
inside the ordinary account's home, owned by that account, with no whitespace in
its path (the ports framework cannot use whitespace in its build paths). Example:
`/home/<account>/Projects/freebsd-dotfiles`, where `<account>` is the desktop
account's login name. No account is built in.

## Obtain the source

Once published, clone the repository as the desktop account:

```sh
mkdir -p "$HOME/Projects"
git clone https://github.com/gluppler/freebsd-dotfiles.git "$HOME/Projects/freebsd-dotfiles"
cd "$HOME/Projects/freebsd-dotfiles"
sh install.sh --preview
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
cd /home/<account>/Projects/freebsd-dotfiles
sh install.sh --check <account>
sh install.sh --apply <account>
```

Replace `<account>` with the desktop account's login name, and the path if the
checkout is elsewhere. Check and apply stop when no account is named; it must be
a lowercase local name (letters, digits, `_` and `-`). Preview works on another host
and performs no installation. `--check` validates the native release, account,
checkout, source files and protected parent directories without installing
packages or writing system configuration. It does not test network access,
compile software or exercise hardware.

Check and apply require native FreeBSD 15.1 amd64, matching installed/running kernels,
base mdo, an ordinary UID of at least 1000, a user-owned permanent checkout and
writable system filesystems, running devd and all source files. Nothing in the
checkout may stay writable by another account. Tools can grant group or world
write whatever the umask; uv creates its environment locks mode 0666. `--check`
lists such paths and `--apply` removes that access, and `final-cleanup` repeats
it for anything a stage left. Staged port trees under `.build/ports-work` keep
their packages' modes. Initial installation needs neither an existing mdo rule nor doas.
The installer refuses an SSH session so network policy cannot strand its operator.

## What happens

1. Remove what earlier runs left: stale locks, workspaces, logs and backups (see
   below). Offer console Wi-Fi setup before package downloads. Password entry
   bypasses the install log. Skip this when the current connection already works.
   Then offer a [clean install](#clean-install); the default keeps what is there.
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
   radio during installation.
8. Check the installed system again: user links, staged binaries, mdo policy,
   helpers and fonts, the oksh login shell, SDDM at boot, and all 15 variants
   installed, locked and built from the current recipe. Clean up again and remove
   every backup this run made. Record the result, release the lock, then ask at the console
   `Reboot into the new desktop now? [Y/n]`. Enter reboots; `n` keeps the
   console running.

The first native build may reveal a release/port/API issue that macOS cannot
exercise. Unknown dependencies, stale recipes, missing devices and invalid files
stop the relevant stage; errors are not suppressed to reach a success message.
See [VALIDATION](VALIDATION.md) before treating the candidate as laptop-tested.

## Clean install

After the Wi-Fi offer, `--apply` asks `Start with a clean install? [y/N]`. Enter
continues as an ordinary rerun. `y` first removes:

- every package except pkg, FreeBSD base packages, packages pkg marks vital and
  the firmware `fwget` detects, with everything those depend on. Stock Git, the
  documentation packages and the built variants go too; locked variants are
  unlocked first. pkg's download cache is emptied.
- the package helper's state in `/var/db/nostromo/packages` and the published
  package policy in `/usr/local/share/nostromo/policy`.
- the checkout's `.build`: variant archives and port work, desktop programs,
  editor plugins, Python environments and downloads.

The run then downloads and builds everything again, which takes hours. Merged
system settings stay, and the configuration stage merges them again. Your files,
`~/.local/state` and the saved power profile stay too. On the T14 the clean
install keeps pkg and the detected GPU and Wi-Fi firmware. The Wi-Fi driver is
part of base, so the connection keeps working.

Without Git a stopped run could not pull fixes, so the installer installs
git-lite as soon as the reviewed curl variant is installed. If a clean run stops
before that, run `pkg install git-lite` at the root console, then pull.

A desktop account whose login shell comes from a package gets `/bin/sh` until the
login-shell stage selects oksh. Another account with a packaged login shell stops
the clean install before anything is removed; give it a base shell with `chsh`
first. A package operation still holding `/var/run/nostromo-packages.lock` stops
it too.

## Logs, reruns and recovery

Root stage logs are under `/var/log/nostromo/install-*`; native user build logs
are under `.build/logs/`. Each finished run records `result`, `last-stage` and
`exit-status`; `pkg-version` identifies the package manager used. Read the
failing stage's log before rerunning the same command. Builds print compiler and
packaging warnings; a stage stops only when its command fails.

The `cleanup` stage at the start of `--apply`, `final-cleanup` at its end and
the exit handler prune logs under the installer lock. No other run can be active
then, so every earlier run has ended, including one that power loss left
without a result. Each earlier run's log directory is removed with everything in
it, so only the current run's logs remain: read or copy a failed run's logs
before rerunning. Unfamiliar or unsafe directories are retained and reported.
Cleanup does not follow directory symlinks.

The installer keeps no recovery archive. A run backs up what it replaces only
for its own rollback: system files in its log's `system-backup/`, the replaced
package policy in `policy-backup/`, user files under
`~/.local/state/freebsd-dotfiles/backups/` and Wi-Fi settings under
`/var/backups/nostromo/`. `final-cleanup` removes them all once the final check
passes; after a failed run, the next run's cleanup removes them. A Wi-Fi setup
still holding its lock keeps its backup. Cleanup also removes the
`/var/log/nostromo/recovery/` directory and the
`/usr/local/share/nostromo/policy.previous.*` copies that earlier installers
kept. A completed install therefore leaves no copy of the files it replaced. An
unchanged package policy is reused. Interrupted publication restores the old
policy if the active path is missing.

Temporary package downloads/private repositories and unpublished policy directories
are removed on ordinary failures and handled signals. SIGKILL or power loss cannot
run shell cleanup handlers, so later runs remove what they leave. The package
helper removes its stale workspaces under its own lock and keeps only its latest
transaction receipt under `/var/db/nostromo/packages/`. The installer's cleanup
stages remove unpublished policies, system-configuration workspaces and project
lock directories from an earlier boot. As the desktop user, they also remove
build workspaces and partial downloads from an earlier boot; during the boot that
created them, these may belong to a software-menu build that is still running.
They also keep the three newest desktop build logs and remove variant archives
whose name and version are no longer in `packages.local`. Successfully installed
packages, manually installed Python, source caches and port build work remain
available for a retry. Removing them automatically could damage working software
or discard hours of compilation.

Generated ports trees have an mtree receipt. After a recipe change,
`prepare-ports` regenerates an unedited `.build/ports` tree from the cached,
checksum-verified archive and discards the old recipe's build work. A changed,
added or missing file stops the stage instead: edits are never reset.

Install and package locks record their process ID. A lock from an earlier boot
is removed automatically unless a process with that ID is running. A lock from
the current boot stops the run even after its process has ended, because a stage
it started may still be running. Reboot, or confirm with `ps -ax` that no install
or build remains, then remove the directory the message names.

`~/.local/state/freebsd-dotfiles/links` lists the links last applied. A later run
removes a listed link that has left `links.txt` if it still points to the same
checkout file; anything you changed is kept. A failed link stage restores the
files it replaced. Failed system-file provisioning restores files from its
journal only if they
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

Push the corrected checkout, then update the laptop copy as the desktop account:

```sh
cd ~/freebsd-dotfiles
git pull --ff-only
```

From the laptop's root console, with `<account>` replaced by that account's
login name:

```sh
sh /home/<account>/freebsd-dotfiles/install.sh --check <account>
sh /home/<account>/freebsd-dotfiles/install.sh --apply <account>
```

Adjust the path if the checkout is elsewhere. Skip the optional Wi-Fi setup when
the current connection works. The retry installs the corrected package helper.
This update also removes the KiCad workflow, which changes the pinned ports
recipe, so `prepare-ports` replaces the failed run's unedited tree from the
cached archive; no manual cleanup is needed. A fresh clone downloads the archive
and prepares its first tree instead. The package policy changes too, and the
retry publishes it.
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

### Recover from a stop at ffmpeg-dependencies

With that fixed, libxslt, libpsl, curl, CUPS and Imath build, install and lock.
FFmpeg's dependency stage then stops before installing anything:

```text
Unreviewed package: frei0r. No packages installed.
```

The ports framework computes each variant's dependency list on FreeBSD. FFmpeg's
default frei0r effects need the frei0r header to build. No reviewed package
depends on frei0r, so resolving the stock packages never showed it. Python ECDSA,
the last variant, would have stopped the same way on the framework's wheel
tools: py312-build, py312-installer and py312-pyproject-hooks. All four are now
reviewed stock packages. The 15 dependency lists recorded on the T14 are in
`tests/variant-deps.txt`, and host tests check them against the reviewed list.

Pull and rerun `--check` and `--apply` as above. The ports recipe is unchanged,
so the eight finished variants are not rebuilt. The package policy changed, and
the retry publishes it.

### Recover from a group/world-writable checkout stop

`--check` on commit `26cb970` stopped before installing anything:

```text
The checkout has group/world-writable files. Review their permissions before installing.
```

Your own files were not the problem. The check also scanned `.build/ports-work`,
where the CUPS build staged three directories with the modes its package
installs: `var/spool/cups/tmp` (1770), `var/cache/cups` (770) and
`var/cache/cups/rss` (775). CUPS is the first variant to stage group-writable
modes, so the stop appeared on the first check after it was built. Leave those
modes alone; the staged tree matches what its package records. The check now
skips staged port trees and still covers port build directories and the rest of
the checkout, listing every path it finds. Since the
[lock-file stop](#recover-from-a-stop-on-uvs-lock-files), `--apply` removes
that access instead of stopping. The ownership check still covers the whole checkout.

Pull and rerun `--check` and `--apply` as above. The ports recipe is unchanged,
so the eight finished variants are not rebuilt; the frei0r policy change above
is published as described there. This update also adds the cleanup, final check
and reboot prompt described above. Its cleanup removes the `policy.previous.*`
copies and recovery archives that earlier installers kept.

### Recover from a stop at fcitx5-build

With those fixes, the first 11 variants, through hunspell, were built, installed
and locked. fcitx5's packaging check then stopped:

```text
Error : Missing : etc/xdg/Xwayland-session.d/20-fcitx-x11
Error : Missing : lib/fcitx5/libxcb.so
Error : Missing : lib/fcitx5/libxim.so
Error : Missing : %%DATADIR%%/addon/xcb.conf
Error : Missing : %%DATADIR%%/addon/xim.conf
Error : Plist issues found.
```

The reviewed options build fcitx5 without X11, but the port's file list named its
X11 session script and XCB/XIM add-ons as unconditional files.
`src/ports/fcitx-x11.patch` marks those five entries X11-only, so the list matches
the Wayland-only build.

The stages after fcitx5 were then checked on the T14 before rerunning (see
[VALIDATION](VALIDATION.md#native-evidence-from-the-t14)). That found three more
stops, now fixed:

- `development-tools`: `uv pip check` reads only the environment's own
  packages, so it would reject the wheels that use reviewed system packages. A
  check that reads both replaces it.
- `staged-validation`: FreeBSD's LLVM ports install `llvm-mc.1` as
  `llvm-mc21.1`, so `nostromo-docs --check` could not find the manual.
- `system-configuration`: FreeBSD's awk rejected the pattern that validates SSH
  `Include` paths.

Desktop packages also replace stock Git with the reviewed git-lite flavor.

The patch changes the ports recipe, so the next run regenerates the tree and
rebuilds all 15 variants, whether or not you choose a clean install. Pull and
rerun `--check` and `--apply` as above.

### Recover from a stop at system-configuration

Commit `73816d3` rebuilt all 15 variants with that patch, installed and locked
them, and passed every stage through `user-files`. `system-configuration` then
stopped with exit 1 and no message, and rolled back the files it had installed.

Staged validation records the `/usr/local` libraries that the desktop programs
link. This stage checks each name before giving the list to the package helper.
The check required a version after `.so`, but wlroots 0.20 and Lua 5.4 install
`libwlroots-0.20.so` and `liblua-5.4.so`. It now accepts names without a version
and prints each line it rejects. Installed packages provide all 78 recorded
libraries.

A check of the rest of the stage on the T14 found one more stop. The installed
check compared fontconfig's family list with one name, and every instance of the
variable Azeret Mono reports `Azeret Mono,Azeret Mono Thin`. It now accepts any
listed family.

Neither fix changes the ports recipe, so the next run reinstalls the 15 variants
from their archives without rebuilding them. Answer no to the clean install
offer, which would remove them and rebuild everything. Pull and rerun `--check`
and `--apply` as above.

### Recover from a stop on uv's lock files

With those fixes pulled (`e32612f`), `--check` stopped before installing anything:

```text
./.build/python-lsp/.lock
./.build/embedded-python/.lock
The checkout has the group/world-writable paths above. Review their permissions before installing.
```

The previous run's `development-tools` stage created both files: uv 0.12.19
makes its environment lock files mode 0666 whatever the umask. The paths are
relative to the checkout, so removing them from another directory changes
nothing. Any tool can leave such modes, so `--check` now lists group/world-writable
paths and `--apply` removes that access before installing; `final-cleanup`
repeats it for anything a stage leaves. Staged port trees keep their packages'
modes, and a path owned by another account still stops the run.

No manual step is needed. Pull and rerun `--check` and `--apply` as above, and
answer no to the clean install offer. `--check` and `--apply` now require the
account name; none is built in.

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
