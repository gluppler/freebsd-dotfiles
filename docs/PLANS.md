# Nostromo — active FreeBSD / Wayland plan

Updated **2026-11-11**. This document supersedes the active platform decisions
in `openbsd-dotfiles/PLANS.md` and the older archived FreeBSD/X11 project.
Earlier user requirements continue unless explicitly superseded below.
All user-facing configuration, documentation and menus remain in English.

Native attempts first stopped at `python312-dependencies`, the first package transaction.
The first exposed an empty-list parsing error. With that fixed, the stage reaches
its transaction, where `pkg install --no-remove` fails: pkg 2.8.4 has no such
option. Both are reproduced and fixed in source; the transaction failure was
reproduced with the real pkg 2.8.4 binary. The helper now reviews pkg's dry-run plan and
approves it once. The audit also accepts architecture-independent `FreeBSD:15:*`
packages that later stages need, and pkg's own upgrade is approved separately.
Retries now keep only the current run's logs and reuse an unchanged package
policy. Kernel modules use FreeBSD's release-specific quarterly
repository. The KiCad PCB workflow is removed: PCB design runs on a separate
server. That changes the pinned ports recipe; `prepare-ports` now replaces an
unedited generated tree from an earlier recipe and stops on edits. Commit
`15bb0b4` passes that stage natively and stops in `python312-build`: the libedit
patch dropped Readline's `/usr/local` search paths, so two Python modules could
not link libmpdec and expat. The patch keeps them now. Variant builds also report
pkg's advisories instead of stopping, since the framework would refuse Python
3.12 once the nightly audit fetches its advisory file. Commit `7f3f3ee` then
built, installed and locked three variants natively and stopped at
`libxslt-dependencies`: pkg refuses any request naming a locked package, and
libxslt's dependency list names libxml2. The helper now keeps installed, locked
variants out of install, preview and update requests. Commit `d8f1ac5` passed
that stage, built five more variants and stopped at `ffmpeg-dependencies` on the
unreviewed frei0r, a build dependency only the ports framework lists. It and
the wheel tools py312-ecdsa needs are now reviewed, and the 15 dependency lists
recorded on the T14 are checked on the host. `--check` on commit `26cb970` then
stopped on the group-writable directories CUPS stages; the mode check now skips
staged port trees. Reruns also clean up stale locks, workspaces, logs and
backups, keeping no recovery archive, and a final check precedes a reboot prompt.
Commit `8bf9f2b` built eleven variants and stopped at `fcitx5-build`: the port's
file list named X11 files that the Wayland-only build omits, and a ports patch now
marks them X11-only. A check of every later stage on the T14 then found three
more stops, now fixed: an awk pattern FreeBSD rejects in the SSH merge, the LLVM
ports' versioned manual name and a Python requirements check that ignored system
packages. Desktop packages replace stock Git with git-lite, and a clean install
became available. Commit `73816d3` rebuilt, installed and locked all 15 variants,
passed every stage through `user-files` and stopped at `system-configuration`:
the library receipt check rejected `libwlroots-0.20.so` and `liblua-5.4.so`,
which have no version suffix. It accepts them now, and the installed font check
now accepts fontconfig's family list for the variable Azeret Mono, which would
have stopped the same stage. The next `--check` stopped on the two environment
lock files uv creates mode 0666; installing runs and `final-cleanup` now remove
group/world write from the checkout, which `--check` lists. No account name is
built in any more: every native mode requires one. Commit `17fb366` then completed
every stage on the T14 in one run, through the final check and cleanup. A
completed run now removes its own logs, the desktop build logs and the package
receipt before the reboot prompt, and installer tools keep their caches in
`.build` instead of the home. The reboot into the desktop, first login and
hardware acceptance still need confirming. The installer now has four modes:
`--preview`, `--check`, `--clean` for a clean full install and `--upgrade` to
apply a pulled checkout; both installing modes report whether
`pkg.FreeBSD.org` is reachable and offer console Wi-Fi setup [y/N] first. The [native evidence](VALIDATION.md#native-evidence-from-the-t14)
records each earlier stop's cause and fix.

**Latest scope clarification:** migrate every implemented workflow **and every
unfinished future plan** from the OpenBSD tree. The [coverage ledger](MIGRATION-COVERAGE.md)
maps that complete scope to the new platform and keeps missing implementation
visible. A stock application replacement does not retire the previous features.

## Confirmed changes

| Decision | Current requirement |
| --- | --- |
| Platform | FreeBSD 15.1-RELEASE amd64; use the current supported production release, not the now-EOL 15.0 |
| Workspace | New `freebsd-dotfiles/`; preserve both earlier trees as references |
| Display system | Native Wayland, **dwl** replacing dwm; no Xorg/Xwayland fallback session |
| Terminal | **foot**, explicitly selected by the user |
| Browser | **qutebrowser**, explicitly permitted to replace surf + tabbed; sole browser |
| Privileges | **base mdo + mac_do** for limited ACPI group access; base su/PAM authenticates root operations; no doas/sudo |
| Retained core | Actual oksh, vis, abduco/dvtm, fastfetch, zoxide, nnn, Git/lazygit, uv, LLVM and WireGuard |
| Theme | Current black/white CRT/cyberpunk corporate design; Michroma GUI and Azeret Mono terminal/code |
| Logo | Current FreeBSD-orb/pufferfish hybrid; moving OS does not authorize redesigning it |
| Install split | Entirely manual Base-Setup, followed by one root-run POSIX `install.sh` |

The archived FreeBSD `installer.sh`, `install.sh`, `bootstrap.sh`,
`docs/BASE-SETUP.md` and `docs/INSTALL.md` are the installation starting point,
as explicitly clarified by the user. Reuse their preview → root system stage →
ordinary-user builds/files → final login activation structure, logs and recovery.
Port and audit it here; do not invent a second installation process or require
the archived directory at runtime. Its X11/doas/Zsh/Neovim steps are superseded.

The earlier requests for Neovim/LazyVim, tmux, Zsh, Firefox/LibreWolf, pfetch,
Tailscale, LightDM and Xenocara are superseded. Do not reintroduce
them just because they appeared in an older FreeBSD checkout. Preserve their
requested useful workflows through the selected replacements.

## Hardware and scope

- Lenovo ThinkPad T14 Gen 2 Intel, model 20W1S4F61C, Core i5-1135G7.
- **Intel Iris Xe integrated graphics**, confirmed by the user on 2026-11-04.
  Use the native Intel i915kms/Mesa path and detected Tiger Lake firmware.
- Native sysctl confirms **16 GiB RAM and eight logical CPUs** (four physical
  cores). Detect actual usable RAM and CPUs at install time; never bake these
  observations into allocation limits.
- WD BLACK SN850X 2 TB NVMe; actual disk node and capacity must be discovered.
- Reported BIOS N34ET71W 1.71 (2026-05-09), EC N34HT46W 1.46,
  ME 15.0.55.2751. These are observations, not a claim that firmware is latest.
- Hostname `nostromo`; the ordinary account is named when installing, never
  built in; discover UID/home, never hardcode UID 1000. No unit/board serial, UUID, MAC or license IDs in the repo.
- Laptop is the daily driver and local development client. SSH/SFTP and browser
  bookmarks reach separately managed services. No Ubuntu/router provisioning,
  local AI service, Docker, Kubernetes, jails, VMs or Linux compatibility runtime.
  The supplied router model/no-CGNAT information does not authorize port forwards.

## Philosophy and performance

- Mostly suckless: native FreeBSD facilities, small focused tools, little idle
  work and POSIX sh glue. Feature completeness matters; a stock minimal config
  does not satisfy the earlier editor/multiplexer requirements.
- Native LLVM/Clang first. Retain stock base; audit added packages, transitive
  libraries and build tools for GNU components. Git remains an explicit exception.
  Necessary added GNU dependencies need an exact documented finding after checking
  workable alternatives; previous OpenBSD graph approval is not FreeBSD approval.
- Interactive shell is **oksh itself**. Operational scripts use `/bin/sh` and
  POSIX syntax; application-required Lua/Python/QML/C are not shell scripts.
- Resource availability under load plus efficient idle is the goal. Use Intel
  HWP where attached; no OpenBSD `hw.perfpolicy`, blanket fixed clocks, custom
  kernel, mitigation-disable bundle or speculative loader/sysctl list.
- Keep SMT available, working graphics acceleration and per-device power controls.
  Measure build times, temperatures, idle redraw and battery drain with effects
  animated/static/off. Battery improvement from Wayland is a hypothesis.
- A whole kernel/GPU/Wayland/browser desktop cannot be expected to use
  only a few MiB. Distinguish idle helper memory from total resident memory, GPU
  buffers and reclaimable filesystem cache. Do not fake status figures.

## Desktop replacement decisions

See [MIGRATION.md](MIGRATION.md) for native support and dependencies.

| Role | Selected direction |
| --- | --- |
| Compositor | dwl, FreeBSD port-compatible source/config, XWAYLAND disabled |
| Bar | dwlb with matching dwl status/IPC version and our geometry patch |
| Launcher | fuzzel plus existing app/action/file/content workflow ported to POSIX helpers |
| Terminal | foot, 90% background opacity, Azeret Mono, native Wayland clipboard |
| Notifications | Dunst native Wayland backend, retaining its shared Cairo drawing customization |
| Wallpaper | swaybg with existing exports, one coherent per-output selection policy |
| Idle/lock | swayidle + gtklock using ext-session-lock and native FreeBSD PAM |
| Graphical login | SDDM Wayland greeter under cage, built here against the wlroots variant; the stock cage failed at the first boot (2026-11-12) |
| Clipboard/capture | wl-clipboard; grim + slurp; no X selection or XTEST helpers |
| Displays | wlr-randr for manual modes; kanshi for hotplug profiles after output discovery |
| Images/PDF/media | swayimg; Zathura/MuPDF with GTK Wayland; mpv with native Wayland output |
| Input languages | fcitx5 with native text-input-v3/input-method-v2, Anthy and Hangul |
| Hardware | FreeBSD devd/ACPI, mixer/OSS, backlight, net80211/wpa_supplicant, native wg |

SDDM/cage is chosen to retain the requested **graphical** login and real font
rendering while reusing Qt already required by qutebrowser. A text-mode ly/getty
screen is a recovery route, not a substitute for the accepted visual design.
Stock dwl has no picom/Hyprland shader setting: the full CRT renderer and custom
window rails require compositor work, not renamed X11 configuration.

## Visual requirements carried forward exactly

1. Keep Michroma GUI and Azeret Mono terminal/code; preserve fallback glyphs and
   plain console recovery. No switch back to red or decorative text/slogans.
2. The centered hybrid orb is the only wallpaper. The monochrome reference ports
   and NOSTROMO ship/abstract wordmark variants are archived outside this
   repository. Do not resurrect the removed Arasaka texture. Keep 1080p, 1440p,
   4K and 8K exports; center per physical output without stretching.
3. Workspace tabs: **only bottom-left corner cut**; active tab filled white with
   black text. The selected tag, not the entire workspace, is inverted.
4. Statuses: **no angular frames**, 10.5-point Michroma (the accepted 5% increase),
   the accepted roughly 5% separation with a font-sized minimum, consistent in
   every render. Show CPU temperature, VPN, battery, Wi-Fi, sound, brightness,
   language and date/time, plus **Bluetooth** under the latest request. Unknown
   readings display unavailable; a Bluetooth icon must expose the connection menu.
5. Every normal window body has a continuous white outline; attached bars have
   no separate outline/highlights. New windows float at
   moderate randomized positions, prefer free space and use least-overlap when
   needed. Tiling/monocle/fullscreen are explicit keys; do not swallow GUI apps.
6. Foot windows alone have an attached white **right** directory rail with black
   text, square outer edge corners and the reference's recessed edge across the
   middle 80% of its length, leaving 10% end caps. Keep depth modest, about 30%
   of the bar thickness, with short diagonal shoulders and scalable geometry.
   Center the path on the divot midpoint and inside its white spine. Home/`~/`
   starts at the top, with the current project at the bottom; active dvtm pane CWD
   must drive it. A Wayland title is not a trustworthy filesystem path.
7. PDF and image viewers (Zathura/swayimg) have a white **bottom** title bar with
   the same long, shallow recess and square outer edge corners. Other normal apps retain
   a blank, uncut white **top** bar. Fuzzel has a centered content-sized panel,
   **left** white rail with the same 80% recess/10% end caps and one
   **bottom-right** panel-body cut. Square only the outer bar corners: preserve
   the approved divot geometry. No extra rail highlights or full-width dmenu strip.
8. Every application panel uses **90% opacity**, including the browser, PDF/image
   viewers, launcher, network menus and notifications. Foot, vis, abduco/dvtm,
   fuzzel and Dunst use background alpha with solid text/highlights. Other GUI
   clients supply a finished surface, so dwl blends their whole content at 90%.
   Never multiply foot's native alpha again. Compositor rails/outlines stay solid;
   no opaque black dvtm panes. Preserve this in animated/static/off CRT modes.
9. Notifications: only bottom-right frame cut; compact white source/NOTIF label
   overlaps the top frame, offset 3.5% from the left. The label itself has a
   bottom-right cut and a smaller left wedge; arbitrary app names are plain,
   bounded text. Keep actions, history, dismissal, quiet mode and persistent
   critical notifications.
10. Login: only logo plus Login and Password inputs; lock: logo plus masked
    Password input. Textboxes cut only at bottom-right. Animated focus overlay
    sits **outside and larger than** the textbox. Join top-left and bottom-left
    segments along the left side, and top-right/bottom-right along the right
    side: **two distinct side-bracket highlights**, not diagonal connections.
11. Apply the **space_dots** motion/effects to splash, login and lock: the
    reference's 1.2-second arrival curve, restrained white phosphor glow, rolling
    scan phase, grain and slight analog drift. Splash lasts 2.4 seconds on every
    successful desktop login, including after boot. Idle logo bounces like a TV/DVD idle
    screen; the password input stays stationary. Neither overlay is itself a lock.
12. CRT effects follow the **space_dots / Golden Era** shader and the
    Cyberpunk border/motion direction. Preserve readable monochrome
    scanlines/sweep, brief fades and animated/static/off controls.
    Damage/redraw accounting must remain efficient.
    The inspected space_dots source is pinned and documented in DESIGN; its
    orange tint, hardcoded resolution, expensive bloom and Linux startup scripts
    are not runtime configuration for this project.
13. Vis dashboard stays the original aligned 2D orb and **plain** menu, without
    angular frames. Vis and the interactive Fastfetch view use a restrained 2D
    floating idle cycle. Respect static/off mode and stop the clock when the view
    closes or the user is editing. The wallpaper keeps the original 2D design.
14. Preserve connected dvtm horizontal/vertical dividers and reserved pane column.
    Export current desktop/login/lock/menu/browser/workspace renders and splash/
    idle GIFs, plus login/lock animations and the three network panels. Clearly
    separate compositions from actual native screenshots.

The exact visual source and wedge reference are recorded in
[DESIGN.md](DESIGN.md). Existing X11 renders are reference evidence only.

## Keyboard and daily-use requirements

- Super desktop layer; Ctrl+B multiplexer prefix; ordinary Vim/vis motions and
  Space-leader project/development actions. Preserve the earlier command map
  where possible and document genuine tool differences rather than claim parity.
- Every feature is reachable from the keyboard: each menu, bar, notification-click
  and mouse action has a key or, for the four rare settings (WALLPAPER, CRT STATIC,
  AUTHENTICATION, EMBEDDED), Super+X. Super opens and focuses; Shift acts on the
  window or takes the key's alternative; Ctrl opens system panels and resizes;
  Super+Alt drives the pointer. Super+F1–F7 mirror the T14's F-row icons because
  the firmware profile makes F1–F12 primary. Copy works without a mouse in foot,
  dvtm, vis, swayimg, Zathura and qutebrowser. `.install/tests/check.py` keeps chords unique,
  every action bound and docs/KEYBINDINGS.md complete.
- Unified launcher: apps, actions, files, contents, project sessions, settings,
  package search/install/update/details/**uninstall**, ports catalog and base/
  firmware maintenance. No resident content indexer; Escape must cancel safely.
- Scan/connect Wi-Fi including phone hotspots, open/Enhanced Open public networks,
  hidden/saved networks and explicit browser-based captive-portal sign-in; protect credentials,
  preserve a working connection, change a saved network's security or password
  and roll back failed profile changes.
- US English → Japanese → Korean cycle plus direct chooser and extensible engines.
  XKB keymaps alone are not Japanese/Korean conversion; validate terminal,
  GTK and Qt text-input paths. No silent English-only fallback called complete.
- Native keyboard volume, mute, mic mute, output/input routing and brightness;
  headset/USB device detection, external keyboard/TrackPoint/touchpad behavior.
- External display scaling/rotation/modes, hotplug, multi-monitor wallpaper,
  lid/clamshell rules and safe undock recovery. Do not suspend a docked active
  session or turn off its last usable output.
- Manual/idle locking, lock-before-suspend with acknowledgement, resume, clear
  logout/reboot/shutdown confirmation. FreeBSD hibernation is not promised.
- nnn files, archive operations, explicit MIME/open rules, mount/unmount/eject
  for actual media, screenshots to file/clipboard, keyboard image/PDF/video use.
- Native WireGuard client and OpenSSH/SFTP; no Tailscale. Status distinguishes
  interface existence/up, peer handshake age and actual reachability.
- SSH/PF managed changes preserve unrelated directives, Match blocks, includes,
  anchors and state. Retain the requested SSH port **2222** when inbound sshd is
  enabled; do not change an unrelated remote server's SSH port.
- Pass-compatible OpenPGP workflow remains required. tpass is the existing
  candidate, not permission to substitute a different store. Port clipboard
  behavior to Wayland, test GnuPG interoperability without installing it as the
  default, and keep all secrets/enrollment outside the repo.
- Fastfetch uses the full laptop/environment profile requested on 2026-11-05,
  with icon legends, runtime detection and no public-IP request. Root filesystem usage is not installed RAM or total NVMe capacity.
- Preserve browser start-page placeholders for Containers, Pods, Files, AI,
  Discord and Services. Add no actual server/router configuration.
- After the current work, investigate **FreeBSD fingerprint drivers, PAM and FIDO**
  and implement supported paths, including enrollment instructions outside the
  repository. Detect the actual USB ID/driver/PAM path; a BIOS toggle is not
  evidence of support. Keep working password authentication and console recovery.
- The latest request supersedes the earlier Bluetooth exclusion: add the icon,
  discovery/pair/connect/disconnect workflow and persistent per-device setup where
  FreeBSD supports the controller and profile. Check Intel firmware, HID versus
  BLE and audio-profile support separately. Do not label unsupported hardware as
  connected, or copy Linux BlueZ commands into this environment.

## Development and multiplexer acceptance

Retain vis dashboard, fuzzy/recent/working files, bookmarks, saved project editor
sessions, splits, native motions/registers/macros, LSP navigation/completion/
diagnostics/rename, format/lint/build/test/debug and unsaved live Markdown preview.
Offline references are part of the installation: C/system man pages, stdman C++,
Rust books/API docs, Go documentation/example sources, Python text/HTML manuals,
LLVM/shell/desktop manuals and the FreeBSD Handbook. DOCS in the launcher,
Space od in vis and Ctrl+B d in dvtm open them alongside code. Shipped Markdown
templates cover functions, callbacks, vis hooks, four assembly architectures and
Zephyr GPIO. Display examples without executing them or downloading dependencies.
The installer checks the reference library before enabling graphical login.
The full cppreference snapshot supplies C/C++ syntax and standard-library pages;
Go's installed specification, expanded Rust books and Python's complete HTML
manual tree are selectable too. Report actual versions and snapshot dates.
An illustrated electronics guide draws each schematic symbol and circuit with
its laws, equations and current flow, from DC circuits through signals, control
and robotics to PCBs and badges; the library holds the circuits, robotics and
board books it summarizes.
PCB design (KiCad) runs on a separate server and is not part of this laptop setup.
Keep uv project Python, LLVM C/C++, Rust, Go, POSIX shell and cross-architecture
assembly (ARM/Thumb/AArch64, x86/x86-64, MIPS variants). No Mason binary downloads.

Abduco owns attach/detach; dvtm supplies the familiar Ctrl+B workflow and 65%
editor + shell/Git layout, scroll/copy, tag/focus/resize/zoom, current-directory
inheritance and divider geometry. It is not tmux's independent split-tree/plugin
API. Sessions survive detaching, not a reboot. Port process CWD inspection using
FreeBSD APIs, not Linux procfs or OpenBSD KERN_PROC_CWD.

Zephyr remains terminal-first with west, native Python/uv, CMake/Ninja, devicetree,
Kconfig, toolchains, serial, flashing and debugging. Scope includes NXP, STM32,
ESP32 Xtensa and RISC-V, Raspberry Pi MCU/full-size families and extensibility.
Exact boards/probes/releases must have a support matrix. FreeBSD host support,
LLVM target coverage and vendor runtimes must be established separately; no
Linux SDK, VM or container workaround. See [DEVELOPMENT.md](DEVELOPMENT.md).

The same embedded workflow now includes **embedded Rust**:
per-project targets/linkers, `no_std`, rust-analyzer target settings, Cargo build,
native probe/flash/debug and serial, with separate ARM/RISC-V/Xtensa support
findings. Do not set an embedded target globally or claim every board is supported.
The later proposed Tuta/suckless email-client addition was explicitly **cancelled**;
add no email client, Tuta integration or account placeholders.

## Installer contract

- Separate manual Base-Setup explains DVD1 verification, US keymap, installation
  type/sets, disk/encryption/swap, services/hardening and initial network/Git.
- Normal multi-user boot and writable system filesystems are required. Offer
  console Wi-Fi setup [y/N] with hidden input before downloads, with backups and
  failed-connection rollback; keep a working connection, and stop when the
  package server is unreachable and the setup is declined. Bluetooth offers explicit HCI/firmware setup.
  Remaining account/device/credential requirements are in [FIRST-RUN](FIRST-RUN.md).
- One root entry point previews account/packages/files/builds/services,
  discovers hardware, boot/update method, home and group membership, then applies
  only validated changes. Initial setup does not require an already working mdo.
- Configure mac_do for the detected account's ACPI group capability only; no
  desktop-to-root grant. Base su/PAM authenticates administrative changes.
  Explain that mdo controls credentials, not a command allowlist.
- Build and create user configs as the user; keep privileged policy/helpers owned
  by root. Use fixed trusted paths and a clean privileged environment.
- Idempotent, backed-up, transactional file updates with logs and rollback;
  preserve unrelated settings and credentials. Backups last only until the
  final check passes: a completed install leaves no archive on the laptop. Do not replace whole rc.conf,
  loader.conf, sysctl.conf, PF/SSH or user config files blindly.
- Native signed package/ABI checks precede installation; unreviewed dependencies
  stop the transaction. Updates/removal share this gate, protected roots and
  locally linked library ABI checks. Never auto-delete an arbitrary dependency.
- Boot/login activation comes only after native build/session/auth checks, with
  local console and boot-environment recovery. Do not run an old installer.
- Shell syntax, shellcheck, meaningful host regressions and real FreeBSD checks
  are separate evidence. No promise of zero errors before hardware testing.

## Implementation status — 2026-11-10

| Area | Repository state | Remaining native evidence |
| --- | --- | --- |
| Source/package policy | Pinned 2026Q4 ports tree, 15 variants, complete closure gate, signed transaction repo and protected removal/update paths | Actual FreeBSD ports stage/check-plist/link results and repository changes |
| dwl/dwlb/foot | Placement, layouts, full bindings, IPC, scaling, frames/CWD, CRT GPU pass, brief map fade and foot opacity/line picker implemented | GPU rendering, output scale/hotplug and input latency |
| Login/lock/notifications | SDDM/cage QML, FreeBSD PAM, acknowledged gtklock, splash/idle, native Dunst drawing implemented | Login/logout, actual PAM, every-output lock, suspend/resume |
| Daily helpers | Menus, Wi-Fi, WireGuard, Bluetooth, IME, audio/display/lid, files/media/probe access, packages and tpass implemented | Detected hardware, supported profiles and real connectivity |
| Editor/development | Pinned vis plugins, dashboard, Markdown, LSP/tool workflows, dvtm CWD/dividers, native west and project Rust | Native project execution and exact board build/flash/debug |
| Installer | Root entry point, user build stages, selective file merges/backups/rollback and final activation gate implemented | Full native provisioning/reboot/repeat run |
| Visual assets | Current QML and code-derived host compositions, splash/idle GIFs, default wallpaper/fonts | Native screenshots and GPU CRT capture |
| Documentation/audit | Current install instructions, dependency exceptions, keyboard map and source/host checks | Hardware acceptance is recorded separately in VALIDATION |

[Coverage](MIGRATION-COVERAGE.md) preserves all prior and unfinished workflows.
[Validation](VALIDATION.md) states exactly what has run. Unsupported Xtensa
host toolchains, vendor-only runners, unidentified fingerprint hardware and
Bluetooth profile limits are explicit capability boundaries, not fabricated tests.

## Latest visual and manager changes — implemented 2026-11-03

- Outer rail corners are square; the approved 80% recess, 10% end caps and
  shallow depth are unchanged. Terminal labels center on the divot, read home
  to project from top to bottom, and ellipsize in the middle when necessary.
- Wi-Fi, native WireGuard and classic Bluetooth use the same styled fuzzel
  panel directly. Esc cancels, operation results return to the manager, and
  passwords/PINs use masked input with no history. Existing privileged helpers
  still own validation and selective configuration/rollback.
- Splash, SDDM login and authenticated gtklock share the space_dots-derived
  motion vocabulary. Static/off stop their motion; lock and splash honor the
  saved CRT mode even when launched directly. Input geometry stays stationary.
- Current PNGs and splash/login/lock/idle GIFs are regenerated from shipped
  painters/QML. Hardware, authentication, radio support and battery measurements
  remain the native acceptance work in VALIDATION, not claimed host results.

- Panel sizing is now native: fuzzel measures shaped text and the prompt, sizes
  to the item count, and fits/paginates within the active output at its scale.
  Shell character-count estimates and fixed preview rectangles are removed.
- PDF/image filenames belong **inside the bottom extended bar**, centered at
  the divot in black Michroma text. They update on document/image changes;
  other nonterminal top bars remain blank. The divot shape stays unchanged.

## Final preparation — 2026-11-04

- Application panels use 90% opacity. Foot retains solid text with its native
  background alpha; the compositor blends other client surfaces once. Layer-shell
  menus and notifications use their own background alpha. Rails stay solid.
- DOCS, vis Space od and dvtm Ctrl+B d provide the offline reference library and
  formatted examples. The installer checks documents and local tool manuals.
- Package updates use native `pkg upgrade`, keep dependency flags and verify
  pending versions after pkg's own restart. Removal explicitly protects consumers,
  pkg/base, locks, vital entries and local library providers. Optional applications
  stay removable after an update.
- Comments and guides have been shortened and stale command references corrected.
  Upstream licenses, source snapshots and useful security explanations remain.
- Refreshed previews include the DOCS menu and code/reference windows. Host tests
  and compiler checks are recorded in VALIDATION; native installation, hardware,
  authentication and reboot acceptance remain required.
- The repository has one public `install.sh`; build and user-link stages live
  under `.install/scripts/`. Read-only native preflight precedes apply. Source exports
  exclude caches and private settings, retain notices, and validate a fresh
  extraction without either archived project. Git publication is a separate step.
- SVG originals and `docs/assets/` simulations are archived outside this
  repository. Runtime logos/textures use PNG; future previews go under `.build/`.
  Animations default to animated mode across the desktop, login, lock, idle and
  splash, with saved static/off overrides. Idle retains its bouncing movement.
- Audit fixes remove the desktop's root grant, authenticate administrative changes
  through base su/PAM, retain mdo only for the ACPI group capability, and cancel
  suspend when the session lock cannot be verified. The installer provisions and
  checks the network merger and SSID decoder. Host regressions cover these paths;
  native authentication and sleep/resume acceptance remain pending.
