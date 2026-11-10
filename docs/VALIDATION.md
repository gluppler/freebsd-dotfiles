# Validation and native acceptance

Updated **2026-11-10**. Native attempts first stopped at `python312-dependencies`,
the first package transaction. The first misread pkg's empty dependency rows. With
that fixed, commit `faef848` reaches the transaction and passes pkg an option that
pkg 2.8.4 does not have. Both have source fixes and regression coverage below,
including real pkg 2.8.4 transactions on this host. Commit `15bb0b4` then passed
that stage on the T14 and stopped in `python312-build`. With that fixed, commit
`7f3f3ee` built, installed and locked python312, cmake-core and libxml2 natively,
then stopped at `libxslt-dependencies`. Commit `d8f1ac5` passed that stage, built
five more variants and stopped at `ffmpeg-dependencies`. With that fixed,
`--check` on commit `26cb970` stopped on the group-writable directories CUPS
stages; the check now skips staged port trees. Commit `8bf9f2b` then built,
installed and locked FFmpeg, wlroots 0.20 and Hunspell, eleven variants in all,
and stopped at `fcitx5-build` on the port's file list. Before a rerun, every
later stage was checked on the T14 or against its pinned sources, which found
three more stops. The [native evidence](#native-evidence-from-the-t14) records
each cause and fix. A native run of these fixes is pending. The KiCad PCB workflow has since been removed because PCB design
runs on a separate server: its packages, six native variants, ports patch, plugin,
helper, guide and tests are gone. Host checks pass for the listed scopes. The full native
FreeBSD package build/install, first login/reboot and hardware acceptance remain
**incomplete**. The installer performs
additional native stage/ABI/configuration checks before enabling SDDM; that is
not a substitute for testing the actual session. No zero-error, all-board or
measured battery-performance claim is made.

## Audit fixes

- fcitx5's file list named its X11 session script and XCB/XIM add-ons
  unconditionally, so the reviewed Wayland-only build stopped in `check-plist`
  with five missing files. `src/ports/fcitx-x11.patch` marks them X11-only; the
  port substitutes `%%X11%%` because it sets `OPTIONS_SUB`.
- A check of every later stage before rerunning found three more stops:
  - `system-configuration`: FreeBSD's awk ends a regular expression at any
    unescaped slash, even inside brackets, so the pattern that validates SSH
    `Include` paths was a syntax error. The slash is now escaped. A host test
    parses all 124 awk programs in the installer, and another runs the SSH merge
    with relative, quoted and self includes and with unsafe paths.
  - `staged-validation`: FreeBSD's LLVM ports install each manual under a
    versioned name, `llvm-mc21(1)` for llvm21, so `nostromo-docs --check` could
    not find the LLVM assembler manual. The reader now derives the name from the
    LLVM prefix.
  - `development-tools`: `uv pip check` reads only an environment's own
    site-packages, so it would report the reviewed system packages these wheels
    import as missing. A check that reads both replaces it.
- rustup's aws-lc-sys 0.28 has no FreeBSD bindings and generates them with
  libclang. `LIBCLANG_PATH` now names the reviewed llvm21, and a host test checks
  that fixed LLVM paths name an installed package.
- Desktop packages replace stock Git, which the base setup installs, with the
  reviewed git-lite flavor of the same port. pkg removes the conflicting flavor
  within the reviewed plan; that removal is permitted only for an unreviewed,
  unlocked, non-vital flavor with no consumers. Its unreviewed automatic
  dependencies that nothing uses any more are removed afterwards. pkgbase
  packages are now recognized by their origin, which has no category.
- `--apply` offers a [clean install](INSTALL.md#clean-install) after the Wi-Fi
  offer. It restores Git as git-lite once the curl variant is installed.
- The checkout mode check scanned staged port trees. CUPS stages its spool and
  cache directories group-writable, as its package installs them, so the first
  `--check` after CUPS was built stopped. The check now skips
  `.build/ports-work/*/work/stage` and `work-*/stage` and lists each path it
  rejects. Port build directories and the rest of the checkout are still checked,
  and so is ownership of everything. A find failure now stops the check instead
  of passing it, and the account/write test, which never stopped on its first
  two conditions, now does.
- Reruns clean up what SIGKILL or power loss leaves. Install and package locks
  record their process ID. A lock from an earlier boot is reclaimed unless that
  ID is running; one from the current boot still stops the run. Under its lock,
  the package helper removes stale workspaces. The installer's `cleanup` and
  `final-cleanup` stages remove unpublished policies, configuration workspaces,
  project lock directories from an earlier boot and, as the desktop user, build
  workspaces and partial downloads from an earlier boot. They also keep the three
  newest desktop build logs and remove superseded variant archives. Interrupted runs no longer
  accumulate as unfinished log directories.
- A completed install leaves no archive. Earlier runs' logs go with their
  system and policy backups, and `final-cleanup` removes this run's backups once
  the final check passes. Both cleanup stages also remove user-file backups and
  Wi-Fi backups; a Wi-Fi setup still holding its lock keeps its backup. The
  recovery directory and `policy.previous.*` copies from earlier installers are
  removed too. The package helper keeps only its latest transaction receipt.
- After SDDM is enabled, a final check reruns the installed-stage verification
  and confirms the oksh login shell, SDDM at boot and all 15 variants installed,
  locked and built from the current recipe. With the result recorded and the
  lock released, the installer asks before rebooting. The host harness for these
  tests had written its lock outside the fixture's `run/` directory, so earlier
  lock-release assertions passed without checking anything; that is fixed.
- Variant dependency lists come from the ports framework on FreeBSD and name
  packages that no other reviewed package depends on. `ffmpeg-dependencies` stopped on
  the unreviewed frei0r, whose header FFmpeg's default frei0r effects build
  against; py312-ecdsa would have stopped on the framework's wheel tools. frei0r,
  py312-build, py312-installer and py312-pyproject-hooks are now reviewed stock
  packages. `tests/variant-deps.txt` records all 15 lists from the T14. Host
  tests check them against the reviewed list and, with the cached catalogue,
  check every package the installer's requests depend on.
- Later dependency lists, the desktop list and updates name variants that
  earlier stages installed and locked. pkg refuses any request naming a locked
  package, even one identical to the reviewed archive, so `libxslt-dependencies`
  stopped on libxml2. The helper now leaves installed, locked variants out of
  install, preview and update requests; reinstall still unlocks its own variant
  first. Real pkg 2.8.4 reproduces the stop and passes the corrected requests.
- Python's libedit patch dropped `USES=readline`, which also added the
  `/usr/local` include and library search paths, so the T14's first variant build
  could not link `_decimal` and `pyexpat` against the system libmpdec and expat.
  The patch keeps those paths. A host test now applies every ports patch to the
  cached pinned archive with zero fuzz and checks that each port dropping
  Readline still gets the paths its libraries need.
- The ports framework refuses any port listed in pkg's advisory file, and its
  check runs on every build. Once the nightly security run downloads that file,
  every rerun would stop at python312, whose two listed advisories have no fixed
  version. Variant builds now print pkg's report for that variant, then build it
  with `DISABLE_VULNERABILITIES`; stock packages are built without the check too.
- The package transaction no longer passes `--no-remove`, which pkg 2.8.4 rejects
  as an unrecognized option, so `faef848` stopped at its first transaction. That
  dry run also lacked the `-y` pkg needs to return success for a nonempty plan.
  The helper now records pkg's dry-run plan, rejects removals and unrecognized
  plans, and approves the same command once; a conflict re-solve reads
  end-of-input and stops. When the transaction repository contains pkg, pkg's own
  upgrade and restart are approved as a separate reviewed transaction.
- The audit accepts pkg's `FreeBSD:15:*` ABI for architecture-independent packages,
  131 of the 511 reviewed repository packages in the cached 2026Q4 catalogue. Later
  variant and desktop stages would otherwise stop on fonts, headers and Python
  modules. Other releases, architectures and broader patterns still fail.
- The post-install check compares origin and ABI, not version: pkg 2.8.4 keeps an
  older installed dependency when a new package does not require its upgrade.
  A mismatch now names the package instead of failing without a message.
- Dependency records now handle pkg's owner-only rows for packages without
  dependencies. Regression inputs reproduce all five reported leaf-package
  errors; the corrected resolver accepts empty lists while still rejecting
  missing edges, wrong origins, partial records and query failures. Kernel
  modules use the release-specific signed kmods repository, separate from the
  ordinary quarterly packages and pkgbase.
- Retries keep only the current run's logs and no backups. Unchanged
  package policies are reused; failed publication restores the previous policy.
  Failure/signal tests cover temporary downloads, unpublished policy cleanup and
  lock release, including log allocation failure and legacy failed-run cleanup.
- A recipe change no longer stops `prepare-ports` with an unedited tree from the
  previous recipe. The tree is regenerated, and that recipe's build work is
  discarded, because port cookies would otherwise package objects built from the
  old patches and options. FreeBSD's mtree, built from NetBSD's sources, exits 0 for
  missing and extra files, so any receipt report now counts as an edit. Edited
  trees stop for review and are never reset.
- Reruns after an update no longer leave removed links behind or stop on an
  earlier editor-plugin pin. The link stage records the links it applied and
  removes one that leaves `links.txt` while it still points to the same checkout
  file; a failed run restores it. A new vis-lspc or dkjson pin replaces an
  unedited staged copy, checked against its receipt. Edits stop the stage. dkjson
  now explains each stop, including a download that fails its checksum.
- Only the default orb wallpaper ships; the other variants are archived outside
  this repository. A saved selection whose exports are gone now falls back to the
  default, because session startup stops when the wallpaper helper fails.
- Sleep-button events now use the session's acknowledged lock path, with automatic
  ACPI lid/button actions disabled. The devd Suspend guard checks the existing
  Wayland sockets and cancels with `acpiconf -k 1` on failure or timeout before
  native suspend hooks run. Wake-button notifications are debounced after Resume.
- The former desktop-to-root mdo grant is replaced by a non-root ACPI group
  transition. Root changes authenticate through base su/PAM and retain mdo for
  command execution. Failed authentication, cancellation, command failures,
  literal arguments, private FIFO transport and separation of PAM prompts from
  captured command output have host regressions. The native
  installed-stage gate checks root denial and the exact permitted group change.
- The Wi-Fi/Bluetooth merger and Wi-Fi SSID decoder now install root-owned with
  mode 0644. The installed-stage gate checks their permissions and contents;
  a host regression provisions and exercises the real installed copies.

The review covered installer/root helpers, package transactions, SSH/PF merging,
locker authentication, secret handling and exports for a single-user laptop.
Native PAM, suspend/resume, firewall traffic and the installed package vulnerability
database still need testing. These fixes are not a claim that every security
flaw has been eliminated. See [security policy and suspend boundaries](SECURITY.md).

## Host results

| Check | Result and scope |
| --- | --- |
| `python3 tests/check.py` | 26 passed: links/assets/fonts, manifest coverage, every declared home destination, browser arguments/schema, CWD encoding, shell syntax, all 124 awk programs parsed by the host's one-true-awk, fixed LLVM paths naming an installed package, user-link preflight/rollback/idempotency, former-link removal/restoration/directory conversion/mid-run change, receipt-checked plugin pins and dkjson checksum stops |
| `python3 tests/helpers.py` | 8 passed: display-mode/scale rollback and last-output protection, SSID bytes/managed blocks, USB CAM filtering, unsafe argument rejection and default fallback for a saved wallpaper whose exports were removed |
| `python3 tests/package-policy.py` | 27 passed: reported empty-list failure and actual resolver/query handling, kmods selection/catalogue, failure/signal cleanup, a lock reclaimed only after its boot with stale workspaces removed, only the latest transaction receipt kept, graph/identity/ABI/receipt validation including only the FreeBSD 15 `*` ABI, exact GNU roles/versions, stock conversion/cleanup, only an unreviewed, unused flavor of an audited origin replaceable, pkgbase separation, protected removal, transaction-guard dispatch, separate pkg self-upgrade, named origin/ABI mismatches, pending versions, preserved automatic/build-protection flags, stale ports-tree replacement that stops on changed, added or missing files, all seven ports patches on the cached pinned archive with search paths kept where Readline is dropped, listed advisories reported without stopping a variant build, the 15 dependency lists recorded on the T14 naming only reviewed packages and earlier variants, and the cached catalogue's dependencies of every installer request reviewed with matching origins and pinned versions |
| `PKG=… python3 tests/pkg-integration.py` | 12 passed against pkg 2.8.4 built from source on this host, with disposable signed repositories: stock Git's flavor replaced by git-lite within one reviewed plan with its unused dependencies removed, the clean install keeping pkg, base, vital and firmware packages with their dependencies, the native locked-variant stop reproduced, then install/preview/update requests that keep a locked variant while stock packages and an unlocked variant still change and reinstall unlocks its own, `--no-remove` rejected as unrecognized, the five reported leaf dependencies installed twice, preview/reinstall/upgrade, existing automatic dependencies, a file conflict denied a second approval, real removal plans rejected, a `FreeBSD:15:*` archive audited and installed, an older dependency pkg keeps, and pkg's restart failing under one approval but passing as its own transaction |
| `python3 tests/provisioning.py` | 18 passed: selective settings/SDDM/SSH/PF merges, the SSH `Include` walk over relative, quoted and self includes with unsafe paths refused, the clean-install offer removing earlier packages, package state and build output, a Python requirements check that sees system packages, helper/font/login/loader destinations, ambiguous input rejection, idempotency, rollback preserving later edits, legacy/current/interrupted log pruning that keeps no backup, signal cleanup, lock release, a lock reclaimed only after its boot, stale workspaces/locks, recovery archives, policy copies and Wi-Fi backups removed unless a setup holds its lock, this run's backups removed only after the final check, build leftovers cleaned only from an earlier boot with user-file backups removed, the final login/SDDM/variant check, the reboot prompt after the lock is released, and policy reuse/recovery |
| `python3 tests/network-menus.py` | 9 passed: actual fuzzel managers, byte-safe SSIDs, masked secrets, cancellation, scan recovery, phone/open/OWE hotspots, unprivileged portal dispatch, Bluetooth initialization/pairing, persistent WireGuard selection and status without authentication |
| `python3 tests/bootstrap.py` | 8 passed: actual console/helper transactions with simulated native commands; missing WPA profile, hidden input, failed-auth rollback, DNS-failure retention, later rc overrides, open/OWE profiles, unsupported security rejection, unsafe paths and supported Intel Bluetooth initialization |
| `python3 tests/security.py` | 8 passed: mdo migration, terminal/GUI authenticated command transport, failure/cancellation, all-socket lock checks, suspend cancellation/deadline, installed mergers/SSID decoder and native event dispatch/resume debounce |
| `python3 tests/embedded.py` | 3 passed: scoped Rust dispatch, Zephyr architecture/word-size/float-ABI guards, real ARM compiler-rt bare-metal ELF link |
| `python3 tests/offline-docs.py` | 9 passed: literal/invalid topics, Go offline environment, pager cleanup, Python text lookup, encoded local language-book URLs, the LLVM ports' versioned manual name, `--check` requiring every local reference, examples, cancellation and separate-window dispatch |
| `python3 tests/release.py` | 8 passed: complete home dotfiles in exports, private/generated file exclusions even when tracked, credential-pattern rejection without disclosure, file modes, symlink parents, installer host guards, the read-only preflight stop point and its mode check skipping only staged port trees |
| `python3 tests/terminal-idle.py` | 4 passed: clock cleanup/static mode, actual PTY viewer scrolling/resizing/control filtering/signal restoration, bounded vis pages with pending-key/edit guards, and unchanged plain/JSON fetch dispatch |
| `python3 tests/reference-examples.py` | C syntax, C++/Rust compilation and execution, Go example test, Python/shell/Lua syntax, x86-64/Thumb/AArch64 assembly passed with host tools; this host Clang lacks MIPS, and Zephyr requires a real board build |
| Offline package contents | Checked quarterly stdman archive renders its C++ examples through mandoc; Python pathlib text retains example blocks; the four added documentation packages have no dependencies |
| POSIX shfmt + ShellCheck | 99 operational/build/source scripts and the two shell configuration files they source are clean at style severity; interactive oksh checked separately with ksh mode and `/bin/ksh -n` |
| Fastfetch | Exact 2.69.0 parser accepts the detailed configuration; plain-output CLI flags checked with the host build. This does not verify FreeBSD sensor detection |
| Ports recipes | `tests/package-policy.py` applies all seven ports patches to the checksum-verified pinned archive with zero fuzz. Eleven of the 15 variants have built, installed and locked natively, and fcitx5 built before its file-list check stopped; see [native evidence](#native-evidence-from-the-t14) |
| Reference sources | cppreference snapshot matches its pinned hash; extraction confines files to its declared directory |
| `lua tests/viewer-title.lua` | Shipped Swayimg config exercises viewer/slideshow/gallery title updates, empty images and duplicate-redraw suppression with a small host API stand-in |
| Lua parsing | Eight editor/loader/image-viewer files parsed; native clients are not installed on this host |
| `tests/rail-geometry.c` | Actual right/left/bottom painters checked at 1x/2x/4x: unchanged 80% recess, square outer corners, modest depth, centered directory/title pixels, title sanitization, responsive panel dimensions, 90% panel alpha, solid rails and no doubled foot alpha |
| `python3 tests/scene-input.py` | Patched dwl hit-test function exercised with client, decorative rail and empty nodes; rails neither dereference a missing surface nor pass input to a window below |
| `tests/space-dots.c` | Shared native effect stays monochrome, animated frames change, static/off stay stable, saved modes are honored and splash finishes transparent |
| `tests/freebsd-compile.py` | Eleven component groups pass against FreeBSD 15.1 amd64 headers, including the new terminal viewer; details below |
| `tests/pam-auth.c` | Mock PAM conversation, multiple prompts, malformed requests, failed passwords, expired accounts and cleanup errors pass |
| `tests/password-store.py` | Real disposable OpenPGP round trips/interoperability, recipient/path protections, tamper rejection, wrong credentials, copy/move/edit failure and mocked clipboard expiry pass |
| Rust source builds | Pinned tpass/tcli/tclig and patched rustup built on the host; rustup warning fix verified with a locked offline rebuild |
| GLSL | `src/dwl/crt.frag` passes glslangValidator fragment validation; no native GPU execution |
| QML login | Actual theme rendered at 1080p/1440p/4K/8K plus 90-frame motion GIF; keyboard focus, masked input, dispatch, failed-login recovery and static/off pass without theme warnings |
| HTML/start page | Actual QtWebEngine local page/font render and placeholder behavior checked; not a qutebrowser process |
| Current artwork | Runtime logos/textures use PNG; native shared painters, idle bounce, QML login and browser page checked after conversion. Animated defaults and static/off overrides pass. Simulations are archived outside the source tree; regenerated previews stay in `.build/previews/` |

The eleven Python suites total **128 passing cases**. Two package-policy cases
read caches and skip without them: the checksum-verified ports archive and the
quarterly catalogue. They use real local code and
small disposable command stand-ins where native devices/package managers are
unavailable. They do not execute a root installer or alter this macOS machine.
The separate pkg integration suite runs the transaction guard with the real pkg
2.8.4 solver, signatures and database in a temporary directory, as an ordinary
user. It does not use FreeBSD's repositories, kernel or installed packages.
The console bootstrap suite uses a temporary controlling terminal; password masking
is checked against the actual prompt and input handling. Hardware, services and
root identity remain stand-ins. The security suite uses temporary Unix sockets and a PTY to exercise session
discovery and both command-transport paths; it needs host permission for those
local test endpoints. Authentication, root identity and hardware commands are
stand-ins. FreeBSD's real su/PAM, mdo kernel policy and ACPI remain native checks.
The password-store test uses a host-only GnuPG keyring under a fresh temporary
directory; no GnuPG package is added to the laptop. It required permission for a
temporary local agent socket outside this host's sandbox. The clipboard transport
in that test is mocked; native data-control ownership still needs acceptance.

QtWebEngine's macOS offscreen preview reports
upstream Skia Graphite initialization errors before falling back to its renderer;
the page renders successfully. This is not a clean native-browser GPU result.

## Source distribution

The source archive was extracted into a new temporary directory without `.git`,
`.build` or either archived project. All source files matched the working
copy byte for byte; archive ownership, permissions, metadata exclusions and
SHA256 were checked. Source-manifest validation and the installer preview passed.
The nine suites that need no prebuilt cache passed from that extraction:
**98 cases**, including the export and terminal-idle regressions. They require
host Python, Lua and a C compiler. The embedded suite retains
its separate compiler-rt/cache requirements.

The public entry point is `install.sh`; user linking and desktop builds live
under `scripts/`. A regression test checks that permission inspection cannot
overwrite the selected `--check` mode and continue into installation. The full
native preflight still requires FreeBSD and its real account/filesystem state.

Common credential patterns, private host paths, tracked private files and unsafe
source permissions are rejected during export. No credentials or unit-specific
hardware identifiers were found in the source review. Build caches, editor files
and local overrides are excluded. These checks do not certify the absence of
every security flaw or secret. Existing upstream notices and artwork attribution
remain included. No Git commit or push was performed.

## FreeBSD API and embedded evidence

`tests/freebsd-compile.py` applies pinned patches with zero fuzz and checks
x86_64-unknown-freebsd15.1 using the official base archive and 46 checksum-checked
header packages. It covers dwl/control/secret-copy, dwlb, gtklock, dvtm, nnn,
Dunst Wayland, fuzzel, session event/splash helpers, the terminal idle viewer,
wg-only and foot actions/config.
It uses `-Wall -Werror`, generally `-Wextra` with unused callbacks excepted;
fuzzel follows its upstream warning level. This is syntax/type checking, **not**
FreeBSD linking, execution, PAM authentication or GPU testing.

Base archive SHA256:
`3768988b151c20f965679062b065c63a977d6bbb9f47fd83695ec2c40790c18f`.
Header versions/checksums are in `tests/freebsd-headers.json`. The cached quarterly
catalog is research evidence, not a completed native dependency certificate.
The installer re-resolves and audits actual signed archives independently.

The ARM compiler-rt test built 139 ELF archive members and linked a real Cortex-M0
ELF with 64-bit division using LLD. This caught an empty archive produced by the
host's Apple archiver; the host check uses BSD ar-format output, while the native
builder explicitly uses LLVM ar/ranlib. The native runtime builder now requires
a nonempty member list and a successful freestanding link before publishing a
profile. No firmware was executed or flashed; other profiles need their own native
builds and exact board/probe acceptance.

## Reproduce the relevant checks

```sh
python3 tests/check.py
python3 tests/helpers.py
python3 tests/package-policy.py
PKG=/path/to/pkg-2.8.4/src/pkg python3 tests/pkg-integration.py
python3 tests/provisioning.py
python3 tests/network-menus.py
python3 tests/bootstrap.py
python3 tests/security.py
python3 tests/embedded.py
python3 tests/offline-docs.py
python3 tests/release.py
python3 tests/terminal-idle.py
python3 tests/reference-examples.py
sh scripts/verify-stage.sh --sources
sh install.sh --preview gluppler
```

Cross compilation and previews require the checksum-verified caches and native
host dependencies described by their scripts. Run the PAM mock with glib-2.0
pkg-config include/library flags; run the password-store test with paths to the
host-built tpass and tcli. Previews are development output under `.build/previews/`;
they are not included in source exports. Generate them with:

```sh
.build/qt-preview/bin/python tests/qml-preview.py
.build/qt-preview/bin/python tests/browser-preview.py
python3 tests/render-current.py
```

The renderer needs Cairo/Pango/Fontconfig, Lua, Lowdown and ffmpeg, plus the
prepared sources from the cross-compile check. Set `LOWDOWN` to its executable
if it is not on PATH. QML/HTML checks need PySide6 and QtWebEngine. These are host
test dependencies. SVG originals and earlier simulated captures are archived
outside the repository; no native laptop screenshots have been produced.
Run `python3 tests/scene-input.py` after the cross-compile step has prepared the
patched dwl source. Painter tests need their pkg-config libraries; the space_dots
test also needs `-Isrc/session`. `mandoc -Tlint -Wwarning docs/man/nostromo-docs.1`
passes for the new manual. Upstream research snapshots are excluded from the
operational ShellCheck pass: they depend on FreeBSD rc libraries absent on macOS.

On FreeBSD, `scripts/verify-stage.sh` additionally requires native ELF programs,
resolved shared libraries, all tools, foot/fuzzel config validation, actual oksh,
Python imports, pinned editor plugins and `nostromo-docs --check`. The installed pass checks links, mdo,
wheel/video/dialer membership and exact font families. Those checks are inside the
installer and have not been executed here. Real native errors must stop the stage;
no host result bypasses those gates.

## Native evidence from the T14

The installer has run natively on the T14 (FreeBSD 15.1-RELEASE amd64) through
eight variant builds. Commit `15bb0b4` passed `python312-dependencies`;
`python312-build` then stopped linking two modules with
`ld: error: unable to find library -lmpdec` and `-lexpat`, although both
libraries are installed in `/usr/local/lib`. Read-only diagnosis as the desktop
user, over SSH and with temporary files confined to `/tmp`, found:

- With the failed recipe, the pinned ports framework evaluates `LDFLAGS` to
  nothing; `-I/usr/local/include` came only from the NLS option. With the fixed
  patch, `LDFLAGS` is `-L/usr/local/lib` and reaches configure and `MAKE_ENV`.
- Both failing link commands succeed with that path. The earlier replayed steps
  (`getbuildinfo`, the LTO `_freeze_module` link and a freeze) also succeed.
- `/var/db/pkg/vuln.xml` was absent. pkg's nightly audit is enabled and cron runs.
  Real pkg 2.8.4 on this host lists python312-3.12.15 under the pinned tree's
  advisories (newest 2026-10-01: CVE-2025-15367 and CVE-2025-15366, no fixed
  version) and none of the other 14 variants. The live advisory list could not
  be downloaded here.

With that fix, commit `7f3f3ee` regenerated the tree for recipe `d486a70b…` and
built python312, cmake-core and libxml2. Each was imported, installed from the
transaction repository and locked, with that recipe's receipt. libxslt's
dependency list (`gmake`, `pkgconf`, `libxml2`) then stopped with
`libxml2-2.15.4 is locked and may not be modified`. pkg 2.8.4 returns that error
for any request naming a locked package, before comparing versions or digests;
it leaves a request's locked dependencies installed as they are.

With that fix, commit `d8f1ac5` passed `libxslt-dependencies` and built,
installed and locked libxslt, libpsl, curl, cups and Imath. All eight installed
variants carry the same recipe receipt. `ffmpeg-dependencies` then stopped with
`Unreviewed package: frei0r. No packages installed.` Read-only checks as the
desktop user found:

- The pinned ports framework lists 42 direct dependencies for FFmpeg. frei0r is
  the only one outside the reviewed list; it comes from the default FREI0R
  option's build dependency on `frei0r.h`. The stock ffmpeg package does not
  depend on frei0r.
- The lists of all 15 variants were recorded. py312-ecdsa names py312-build and
  py312-installer, and py312-build depends on py312-pyproject-hooks; none was
  reviewed. No other list names or depends on an unreviewed package.
- With both signed repository catalogues fetched into a private copy under
  `/tmp` (2026-11-10), every installer request was replayed through
  `package-policy.awk`: the 15 dependency and 15 variant requests, the desktop
  list, gperf and the detected firmware. With the four additions every audit
  passes, including the eight built variants' recorded dependency versions.
- For every variant the framework reports the package name and version in
  `packages.local`, an accepted license, a valid option set and no ignore,
  broken or forbidden mark. The fetched catalogue satisfies all 49 versioned
  dependency requirements in the 15 lists.

`--check` on commit `26cb970` then stopped with `The checkout has
group/world-writable files.` A read-only search as the desktop user found three
such directories, all in CUPS's staged package tree under `.build/ports-work` and
created when CUPS was built: `var/spool/cups/tmp` (1770), `var/cache/cups` (770)
and `var/cache/cups/rss` (775), owned by gluppler. Nothing else in the checkout,
including `.git`, is group/world-writable, and the login umask is 0022:

- Run as the desktop user against the T14's checkout, the previous check
  reproduces the stop. The corrected check passes in two seconds and skips the
  eight staged trees.
- In a private `/tmp` copy, ZFS birth times and `kern.boottime` give the
  expected lock decisions. An ownerless lock from before the boot is reclaimed,
  and so is one whose recorded process has ended. A lock from before the boot
  whose process is running is kept, as is any lock from the current boot.
- The build cleanup removed only backdated workspaces and partial downloads,
  kept the three newest desktop build logs and kept the current variant
  archives, including `ffmpeg-9.0.2,1`.

Commit `8bf9f2b` passed `--check`, built, installed and locked FFmpeg, wlroots
0.20 and Hunspell, and stopped in `fcitx5-build`: `check-plist` reported the X11
session script and the XCB/XIM add-on files missing. All eleven installed variants
carry recipe `d486a70b…`, the recipe of commits `d8f1ac5` through `8bf9f2b`.

Every later stage was then checked before a rerun, as the desktop user and
without root, in temporary directories under `/tmp` that were removed afterwards:

- System configuration was replayed against copies of the T14's own rc.conf,
  loader.conf, sysctl.conf, devfs rules, SSH configuration and PF file. The SSH
  `Include` walk stopped with FreeBSD awk's `nonterminated character class`.
  With the fix every merge succeeds. The effective sshd policy is port 2222 with
  root, password and keyboard-interactive login off, `AllowUsers gluppler` and
  public-key authentication.
- FreeBSD 15.1's mdo(1), mac_do(4) and mac_do source confirm the mdo rule. mac_do
  is not loaded yet and has no rules. The kernel returns the rule string as set,
  which the configuration stage compares. `uid=.` refuses root, and
  `gid=<nostromo_power>` with `!gid=.` allows only the change of primary group
  that the installed check runs.
- The PF anchor's keywords, ICMP types and interface negation match 15.1's
  pf.conf(5) and pfctl source. pfctl opens its netlink socket even with `-n`, so
  parsing needs root and runs only inside the installer.
- Every download host verifies with the base certificate store alone. The T14
  has no ca_root_nss package, so a clean install cannot remove its trust store.
- WireGuard's `wg`, nnn, dvtm, dwl, Dunst and the session helpers built against
  the installed packages. dwlb, foot (its meson test passing), fuzzel, gtklock
  and the splash helper built against a private copy of the reviewed packages'
  archives. Every program resolves all of its libraries. foot and fuzzel accept
  the shipped configuration, and oksh parses `okshrc`.
- A dry run of the link stage against the real home creates 147 links and backs
  up only `~/.profile`.
- llvm19, installed on the T14, documents `llvm-mc` as `llvm-mc19(1)` in
  `/usr/local/share/man`. `man -w` finds it with the MANPATH that
  `verify-stage.sh` sets.
- Fresh downloads of every pinned source the installer fetches match their pins
  (2026-11-10).
- A clean install would remove 166 of the 169 installed packages, including the
  eleven locked variants and stock Git. It keeps pkg and the detected Tiger Lake
  GPU and iwlwifi firmware; the Wi-Fi driver is in base. No account's login shell
  comes from a removed package.
- PipeWire, PyQt6 and Python ECDSA were checked against their pinned ports and
  sources. PyQt6's file list names no disabled module. PipeWire's `readline`
  option exists and leaves the file list unchanged. Of the libraries its meson
  build finds on its own, only libdrm is outside its declared dependencies, and
  only an uninstalled example links it.

tpass and rustup were not built on the T14: their builds download crates and run
the crates' build scripts, which this diagnosis did not do. Review of aws-lc-sys,
which both use, led to the `LIBCLANG_PATH` fix instead.

No package was built, installed or removed during any diagnosis. The fcitx5 patch
changes the ports recipe, so the next run rebuilds all 15 variants; these checks
do not compile them.

## Laptop acceptance after reinstall

1. Verify release/running kernel, actual RAM/CPU/NVMe and detected devices.
2. Validate graphics acceleration and native clients with DISPLAY unset; no
   Xorg/Xwayland process used as a compatibility shortcut.
3. Verify mdo retains the desktop UID with only the permitted ACPI group; direct
   root requests must fail. Test root-password prompts, cancellation and wrong
   passwords from both foot and the GUI menus, preserved policy and console recovery.
4. Test boot, login, logout, compositor crash, lock failure/success, idle,
   suspend/resume, lid/clamshell, dock/unplug and power-loss recovery.
5. Test Wi-Fi scan/connect/reconnect, phone hotspots, public-network web sign-in,
   supported authentication modes, DHCP/DNS, native WireGuard peer state,
   SSH/PF effective configuration and preserved unrelated rules.
6. Test speakers/headphones/mic mute/camera, external keyboards, display modes
   and scales, removable/serial devices and fingerprint support truthfully.
7. Test native English/Japanese/Korean conversion in foot, GTK and qutebrowser;
   clipboard, PDF/media and browser file dialogs/screensharing where required.
8. Measure settled idle and repeated build performance on AC/battery with matched
   brightness/output/network conditions and CRT animated/static/off.
9. Test native C/C++, Rust, Go, Python/uv and assembly projects. Certify Zephyr
   board/probe combinations separately through build/flash/debug evidence.
10. Verify package install/update/**uninstall**/ports workflows, base update
    method and custom desktop/ABI retention across an update/reboot.
11. Disconnect networking and read C/C++/Rust/Go/Python references and formatted
    examples through DOCS, vis and dvtm. Check MIPS assembly with native LLVM and
    the GPIO example with the selected Zephyr board.
12. Check the original 2D orb's idle cycle in native vis and the complete Fastfetch
    view, including static/off, resizing, keyboard navigation, closing and sensor
    availability. Host Lua tests use an API stand-in, not a running native editor.

The installer has not yet completed on the laptop, none of these acceptance
checks has run, and no zero-error guarantee is made for a machine that has not
booted this environment.
