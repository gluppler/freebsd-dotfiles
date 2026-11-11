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
sh install.sh --clean <account>
```

Replace `<account>` with the desktop account's login name, and the path if the
checkout is elsewhere. The installer has four modes:

| Mode | What it does |
| --- | --- |
| `--preview [account]` | Shows the plan on any host and changes nothing |
| `--check account` | Read-only native preflight |
| `--clean account` | Clean full install: removes earlier packages, the package state and build output, then builds and installs everything. Use it for the first install or to start again from nothing |
| `--upgrade account` | Applies what changed in the checkout to the installed environment: configuration, keys, documents, library pins and package lists. Use it after `git pull`, and to continue a run that stopped |

`--check`, `--clean` and `--upgrade` stop when no account is named; it must be a
lowercase local name (letters, digits, `_` and `-`). `--check` validates the
native release, account, checkout, source files and protected parent directories
without installing packages or writing system configuration. It does not test
network access, compile software or exercise hardware.

These three modes require native FreeBSD 15.1 amd64, matching installed/running kernels,
base mdo, an ordinary UID of at least 1000, a user-owned permanent checkout and
writable system filesystems, running devd and all source files. Nothing in the
checkout may stay writable by another account. Tools can grant group or world
write whatever the umask; uv creates its environment locks mode 0666. `--check`
lists such paths, `--clean` and `--upgrade` remove that access, and
`final-cleanup` repeats it for anything a stage left. Staged port trees under
`.build/ports-work` keep their packages' modes. Initial installation needs
neither an existing mdo rule nor doas. The installer refuses an SSH session so
network policy cannot strand its operator.

## What happens

1. Remove what earlier runs left: stale locks, workspaces, logs and backups (see
   below). Without a working connection, a default route and DNS for
   `pkg.FreeBSD.org`, set up [Wi-Fi](WIFI.md) at the console before package
   downloads. Password entry bypasses the install log. A working connection,
   wired or wireless, is kept and nothing is asked. `--clean` then performs the
   [clean install](#clean-install); `--upgrade` keeps what is there.
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
   firewall and desktop running; only the Wi-Fi setup, which runs when there is no
   connection, changes its chosen radio during installation.
8. Check the installed system again: user links, staged binaries, mdo policy,
   helpers and fonts, the oksh login shell, SDDM at boot, and all 15 variants
   installed, locked and built from the current recipe. Clean up again: remove
   every backup this run made, the package downloads and transaction receipt and
   the desktop build logs. Then remove this run's own logs, release the lock and
   ask at the console `Reboot into the new desktop now? [Y/n]`. Enter reboots;
   `n` keeps the console running. A completed install leaves no logs.

The first native build may reveal a release/port/API issue that macOS cannot
exercise. Unknown dependencies, stale recipes, missing devices and invalid files
stop the relevant stage; errors are not suppressed to reach a success message.
See [VALIDATION](VALIDATION.md) before treating the candidate as laptop-tested.

## Clean install

After the network check, `--clean` first removes:

- every package except pkg, FreeBSD base packages, packages pkg marks vital and
  the firmware `fwget` detects, with everything those depend on. Stock Git, the
  documentation packages and the built variants go too; locked variants are
  unlocked first. pkg's download cache is emptied.
- the package helper's state in `/var/db/nostromo/packages` and the published
  package policy in `/usr/local/share/nostromo/policy`.
- the checkout's `.build`: variant archives and port work, desktop programs,
  editor plugins, Python environments, the offline library, Go and uv caches and
  downloads.

The run then downloads and builds everything again, which takes hours. Merged
system settings stay, and the configuration stage merges them again. Your files,
`~/.local/state` and the saved power profile stay too. On the T14 the clean
install keeps pkg and the detected GPU and Wi-Fi firmware. The Wi-Fi driver is
part of base, so the connection keeps working.

A clean install that stops after its `clean-install` stage continues with
`--upgrade`, as the stop message says; `--clean` would remove what the stopped
run had already built. One that stops before or during that stage asks for
`--clean` again.

## Upgrade after a pull

Pull as the desktop account, then run `--check` and `--upgrade` at the root
console:

```sh
cd ~/Projects/freebsd-dotfiles
git pull --ff-only
```

```sh
sh /home/<account>/Projects/freebsd-dotfiles/install.sh --check <account>
sh /home/<account>/Projects/freebsd-dotfiles/install.sh --upgrade <account>
```

Neither mode removes configuration, and neither needs to: both install the
current configuration.

- Your configuration files are links into the checkout, listed in `.install/links.txt`.
  A pulled change to a linked file reaches it at once, and programs read it when
  they next start. An upgrade adds new links, rebuilds the desktop programs whose
  keys are compiled in and downloads offline library items whose pins changed.
  A link that has left `.install/links.txt` is removed while it still points to
  the same checkout file; anything you changed is kept. Files that a link
  replaces are backed up only for the stage's own rollback, and cleanup removes
  those backups.
- System settings are merged again from the checkout: loader, rc, sysctl, devfs,
  mdo, SSH/PF and SDDM. Only the keys and blocks the installer manages change.
  Its helpers, fonts and PAM, loader and theme files are installed again.
- Nothing records the system files that earlier versions installed. If a later
  version stops installing one, such as a font, it stays until you remove it.
- An upgrade installs every package the lists name and removes none. A package
  that a later checkout drops stays installed, since you may use it yourself.
  Remove it with Super+Ctrl+U's REMOVE, which keeps packages that others need,
  or run `--clean` to install only the lists.
- Installer tools keep their state in `.build`, not in your home. That covers
  Go's module and build caches, uv's download cache, Go's usage counters for its
  builds and the settings file from rustup's version check. Installers before
  2026-11-11 left these in your home as `~/go`, `~/.cache/go-build`,
  `~/.cache/uv`, `~/.config/go/telemetry` and `~/.rustup`. The installer cannot
  tell them from your own, so it leaves them. If you do not use those tools
  yourself, remove them as the desktop account:

  ```sh
  # Go makes its module cache read-only.
  [ ! -d ~/go ] || chmod -R u+w ~/go
  rm -rf ~/go ~/.cache/go-build ~/.cache/uv ~/.config/go/telemetry ~/.rustup
  rmdir ~/.config/go 2>/dev/null
  ```

  The project's own Rust toolchains live in `~/.local/share/nostromo/rustup`,
  not `~/.rustup`.
- The variants are reinstalled from their archives without rebuilding, unless
  their recipe changed: the ports pin, the variant list, the ports options and
  patches, or the scripts that build them. Then every variant is built again,
  which takes hours.

Without Git a stopped run could not pull fixes, so the installer installs
git-lite as soon as the reviewed curl variant is installed. If a clean run stops
before that, run `pkg install git-lite` at the root console, then pull.

A desktop account whose login shell comes from a package gets `/bin/sh` until the
login-shell stage selects oksh. Another account with a packaged login shell stops
the clean install before anything is removed; give it a base shell with `chsh`
first. A package operation still holding `/var/run/nostromo-packages.lock` stops
it too.

## Logs, reruns and recovery

During a run, root stage logs are under `/var/log/nostromo/install-*` and
native user build logs are under `.build/logs/`. A completed install removes
them all before it asks to reboot, then `/var/log/nostromo` itself once it is
empty; only the console output remains. A stopped run keeps its logs and records
`result`, `last-stage` and `exit-status`; `pkg-version` identifies the package
manager used. Read the failing stage's log, then run the command that the stop
message names. Builds print compiler and packaging warnings; a stage stops only
when its command fails.

The `cleanup` stage at the start of each run, `final-cleanup` at its end and
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
transaction receipt under `/var/db/nostromo/packages/`. During a run it also keeps
the checked package downloads in `/var/db/nostromo/packages/cache/` for the
run's later transactions, so each archive is downloaded once. The final cleanup
removes them and the receipt. A stopped run leaves them for the next run to
reuse, after checking each against the current catalogue (see PACKAGES.md). The installer's cleanup
stages remove unpublished policies, system-configuration workspaces and project
lock directories from an earlier boot. As the desktop user, they also remove
build workspaces and partial downloads from an earlier boot; during the boot that
created them, these may belong to a software-menu build that is still running.
They also keep the three newest desktop build logs, none after the final check,
and remove variant archives whose name and version are no longer in
`.install/packages.local`. Successfully installed
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
removes a listed link that has left `.install/links.txt` if it still points to the same
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

### Earlier native stops

Every earlier stop on the T14, from `python312-dependencies` to uv's lock files,
is fixed. [VALIDATION](VALIDATION.md#native-evidence-from-the-t14) records each
cause and fix. After pulling a fix, run `--check` and `--upgrade` as above.

## Source exports

From the development checkout, as its ordinary owner:

```sh
python3 .install/tests/release.py
sh .install/scripts/export.sh
```

The exporter uses Git to collect tracked and untracked files that are not
ignored, then checks paths, file permissions and common credential patterns.
It creates a fresh extraction and checks the source manifest and installer
preview before writing `.dist/freebsd-dotfiles-*.tar.gz`. A matching `.sha256`
and `.files` manifest accompany it. Export requires Git and BSD tar on FreeBSD
or macOS; Python is only needed for the separate regression test.

The archive excludes `.git`, `.build`, `.dist`, editor files and private
overrides such as `nostromo/services.local`, SVG originals and simulated
screenshots. It still contains the `.install/packages.local` policy.
Archive ownership is normalized, and extended attributes, ACLs and macOS
metadata are omitted. Source licenses and artwork attribution are retained.

An export takes the current file contents, including uncommitted changes. It
does not stage, commit or push anything. Before publishing, review `git diff`
and `git status --short`, inspect the archive's file list, and run the checks
in [VALIDATION](VALIDATION.md). Ignore rules and pattern checks cannot detect
every secret; inspect new configuration and assets before including them.
