# Validation and native acceptance

Updated **2026-11-05**. The first reported native attempt stopped at
`python312-dependencies`: the installer misread pkg's empty dependency rows.
The error has a source fix and regression coverage below; a native rerun of that
fix is still pending. Host checks pass for the listed scopes. The full native
FreeBSD package build/install, first login/reboot and hardware acceptance remain
**incomplete**. The installer performs
additional native stage/ABI/configuration checks before enabling SDDM; that is
not a substitute for testing the actual session. No zero-error, all-board or
measured battery-performance claim is made.

## Audit fixes

- Dependency records now handle pkg's owner-only rows for packages without
  dependencies. Regression inputs reproduce all five reported leaf-package
  errors; the corrected resolver accepts empty lists while still rejecting
  missing edges, wrong origins, partial records and query failures. Kernel
  modules use the release-specific signed kmods repository, separate from the
  ordinary quarterly packages and pkgbase.
- Retries bound diagnostic-only logs and preserve recovery backups. Unchanged
  package policies are reused; failed publication restores the previous policy.
  Failure/signal tests cover temporary downloads, unpublished policy cleanup and
  lock release, including log allocation failure and legacy failed-run retention.
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
| `python3 tests/check.py` | 18 passed: links/assets/fonts, manifest coverage, browser arguments/schema, CWD encoding, shell syntax, user-link preflight/rollback/idempotency |
| `python3 tests/helpers.py` | 7 passed: display-mode/scale rollback and last-output protection, SSID bytes/managed blocks, USB CAM filtering and unsafe argument rejection |
| `python3 tests/package-policy.py` | 16 passed: reported empty-list failure and actual resolver/query handling, kmods selection/catalogue, failure/signal cleanup, graph/identity/ABI/receipt validation, exact GNU roles/versions, stock conversion/cleanup, pkgbase separation, protected removal, native upgrade dispatch, pending versions and preserved automatic/build-protection flags |
| `python3 tests/provisioning.py` | 8 passed: selective settings/SDDM/SSH/PF merges, ambiguous input rejection, idempotency, rollback preserving later edits, bounded legacy/current logs, signal cleanup, lock release and policy reuse/recovery |
| `python3 tests/network-menus.py` | 9 passed: actual fuzzel managers, byte-safe SSIDs, masked secrets, cancellation, scan recovery, phone/open/OWE hotspots, unprivileged portal dispatch, Bluetooth initialization/pairing, persistent WireGuard selection and status without authentication |
| `python3 tests/bootstrap.py` | 8 passed: actual console/helper transactions with simulated native commands; missing WPA profile, hidden input, failed-auth rollback, DNS-failure retention, later rc overrides, open/OWE profiles, unsupported security rejection, unsafe paths and supported Intel Bluetooth initialization |
| `python3 tests/eda.py` | 3 passed: ERC/DRC before fabrication, failed-check stop, literal paths, fresh output directories, unchanged sources, preserved library tables and generated native CLI reference |
| `python3 tests/security.py` | 8 passed: mdo migration, terminal/GUI authenticated command transport, failure/cancellation, all-socket lock checks, suspend cancellation/deadline, installed mergers/SSID decoder and native event dispatch/resume debounce |
| `python3 tests/embedded.py` | 3 passed: scoped Rust dispatch, Zephyr architecture/word-size/float-ABI guards, real ARM compiler-rt bare-metal ELF link |
| `python3 tests/offline-docs.py` | 7 passed: literal/invalid topics, Go offline environment, pager cleanup, Python text lookup, encoded local language-book URLs, examples, cancellation and separate-window dispatch |
| `python3 tests/release.py` | 7 passed: complete home dotfiles in exports, private/generated file exclusions even when tracked, credential-pattern rejection without disclosure, file modes, symlink parents, installer host guards and the read-only preflight stop point |
| `python3 tests/terminal-idle.py` | 4 passed: clock cleanup/static mode, actual PTY viewer scrolling/resizing/control filtering/signal restoration, bounded vis pages with pending-key/edit guards, and unchanged plain/JSON fetch dispatch |
| `python3 tests/reference-examples.py` | C syntax, C++/Rust compilation and execution, Go example test, Python/shell/Lua syntax, x86-64/Thumb/AArch64 assembly passed with host tools; this host Clang lacks MIPS, and Zephyr requires a real board build |
| Offline package contents | Checked quarterly stdman archive renders its C++ examples through mandoc; Python pathlib text retains example blocks; the four added documentation packages have no dependencies |
| POSIX shfmt + ShellCheck | 101 operational/build/source/config files clean at style severity; interactive oksh checked separately with ksh mode and `/bin/ksh -n` |
| Fastfetch | Exact 2.69.0 parser accepts the detailed configuration; plain-output CLI flags checked with the host build. This does not verify FreeBSD sensor detection |
| KiCad source recipes | All seven ports patches apply to the pinned tree with zero fuzz. OpenCASCADE packing-list commands retain staged headers/libraries/symlinks/empty resources and framework records. Full native builds have not run |
| New reference sources | cppreference snapshot and InteractiveHtmlBom archives match pinned hashes; cppreference extraction confines files to its declared directory. ngspice's relocated release URL retains the original distinfo checksum |
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

The twelve Python suites total **98 passing cases**. They use real local code and
small disposable command stand-ins where native devices/package managers are
unavailable. They do not execute a root installer or alter this macOS machine.
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
**79 cases**, including the export and terminal-idle regressions. They require
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
python3 tests/provisioning.py
python3 tests/network-menus.py
python3 tests/bootstrap.py
python3 tests/eda.py
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
12. Open KiCad's standard libraries and a real design; check simulation, ERC/DRC,
    Gerbers/drills/BOM/positions, GerbView/3D/STEP and the interactive assembly page.
13. Check the original 2D orb's idle cycle in native vis and the complete Fastfetch
    view, including static/off, resizing, keyboard navigation, closing and sensor
    availability. Host Lua tests use an API stand-in, not a running native editor.

The user is waiting to install until the configuration is ready. No native
laptop checks have been performed in this pass, and no zero-error guarantee is
made for a machine that has not booted this environment.
