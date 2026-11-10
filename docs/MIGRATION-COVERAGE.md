# Complete migration scope

Updated 2026-11-04. **All implemented OpenBSD workflows and its unfinished plans
remain in scope.** The old PLANS, DESKTOP, DEVELOPMENT, audit and source/helper
inventory were reviewed. The new directory is standalone; neither installation
nor runtime reads the old tree.

“Implemented” means the repository contains the configuration/build/helper path,
with the host evidence in [VALIDATION](VALIDATION.md). It does **not** mean the
FreeBSD laptop has booted it. Hardware-conditional features are documented rather
than enabled against guessed devices. The installer runs its native stage gates
before enabling graphical login.

| Old component / workflow | FreeBSD / Wayland destination | Current state |
| --- | --- | --- |
| dwm tags, random floating, explicit tiling, focus, resize, monitor movement | `src/dwl/`, no Xwayland | Implemented: full bindings, scratchpad, gaps and typed IPC; native behavior pending |
| dwm white outline, terminal CWD rail, blank app top rail; new viewer bottom rail | dwl scene buffers and validated OSC-title path | Implemented: scene decorations, bounded encoded CWD, centered top-to-bottom text, square outer corners, 80% recess/10% end caps, body-only outlines and viewer bottom title rail; native mixed-DPI/hotplug pending |
| slstatus and clickable readings | dwlb + FreeBSD status producer | Implemented: active tag fill, scale-aware bar, allowlisted actions and detected readings; hardware pending |
| dmenu combined app/action/file/content search and project selector | fuzzel + POSIX helpers, no resident index | Implemented: combined search/project helpers and content-sized native cut/wedge panel |
| st typography, alpha, scrolling, selection, URL actions, CWD | foot config, OSC 7, Wayland clipboard | Implemented: native config plus alpha controls and literal line picker; native terminfo/IME pending |
| vis dashboard, file/recent/window pickers, bookmarks, saved sessions | retained Lua configuration and native vis | Implemented: dashboard/workflows, pinned vis-lspc/dkjson and native LSP tools; native editor acceptance pending |
| unsaved Markdown preview; PDF reading | retained vis/Lowdown module; Zathura/MuPDF on GTK Wayland | Implemented: unsaved-buffer Lowdown split and Zathura/MuPDF config; native interaction pending |
| abduco/dvtm layout, Ctrl+B, connected dividers, copy and CWD | patched dvtm with libprocstat, foot and wl-copy | Implemented: FreeBSD libprocstat, connected dividers, copy integration and project layout; native sessions pending |
| oksh prompt/history/completion, zoxide and aliases | actual oksh, `.profile`, `okshrc` | Implemented: actual oksh, aliases/history/completion, zoxide and tested helper argument boundaries |
| surf/tabbed, start page, remote service placeholders | qutebrowser only, Qt Wayland, same local page | Implemented: qutebrowser config and local start page; real QtWebEngine page preview, native browser pending |
| Fastfetch orb and full laptop information | detailed detected hardware/environment profile and icon legends | Implemented: 64 report entries, original 2D idle logo, keyboard-scrollable view and plain/JSON output, no public-IP request; native sensor readings pending |
| xwallpaper exports/selector, default orb and all retained variants | swaybg per output; same default artwork | Implemented: default orb, selector, per-output exports and event-triggered refresh; other variants archived outside this repository |
| picom CRT and animations | compositor render path plus native client effects | Implemented: dwl GLES CRT pass, animated/static/off modes and shared-timer map fades; native GPU pending |
| space_dots reference | pinned MIT source, monochrome and resolution-aware adaptation | Implemented: pinned monochrome shader adaptation plus shared splash/login/lock motion and static/off checks; native GPU pending |
| xenodm native graphical login | SDDM Wayland greeter under cage, Qt theme and PAM | Implemented: SDDM/cage session, native PAM integration checks and QML theme; actual QML mock tests, native login pending |
| xlock masked input, orb, idle bounce, focus brackets | gtklock ext-session-lock + FreeBSD PAM | Implemented: native art, PAM helper, compositor lock acknowledgement and sleep guard; native authentication pending |
| X11 splash / motion helper | native Wayland space_dots-style overlay after authenticated login | Implemented: native layer-shell 2.4-second arrival/CRT/fade splash after login; actual shared painter GIF rendered |
| dunst frames, overlapping source label, actions/history/quiet | native Wayland Dunst, shared Cairo patch | Implemented: native Wayland build/Cairo patch and queue/history/actions; painter preview rendered |
| X11 clipboard, screenshots and pointer keys | wl-clipboard, grim/slurp, compositor pointer controls | Implemented: clipboard/region/full/focused capture and compositor pointer bindings; native protocol behavior pending |
| xrandr, docking and clamshell | wlr-randr, kanshi and FreeBSD ACPI/devd policy | Implemented: output menu/rollback, watcher, portable/docked policy and optional actual kanshi profiles; hardware pending |
| sndio, brightness and hardware keys | FreeBSD mixer/OSS, backlight and discovered device permissions | Implemented: detected FreeBSD controls and managed device permissions; actual controls/capture pending |
| XIM/UIM US → JP → KR, direct picker | fcitx5 Wayland, Anthy/Hangul, text-input protocols | Implemented: fcitx5 without X, Anthy/Hangul and text-input paths; actual composition in each client pending |
| Wi-Fi scans, hidden/saved profiles, secret handling and rollback | net80211 + wpa_supplicant, root-owned POSIX helper | Implemented: console bootstrap, phone/open/OWE hotspot profiles with capability checks, browser portal action, protected secrets and rollback; radio tests pending |
| WireGuard up/down/status, SSH/SFTP shortcuts | native wg(4), wg-only tools, FreeBSD rc and OpenSSH | Implemented: native wg-only build, own-interface rc/helper, status and local placeholders; real peers remain user configuration |
| SSH/PF managed edits, inbound port 2222 | preserve unrelated settings, native syntax checks and rollback | Implemented: selective include-aware SSH merges, PF anchor, native parser gates and file rollback; live native acceptance pending |
| tpass/pass-compatible encrypted store and clipboard expiry | pass-compatible OpenPGP store; pure Rust crypto and native Wayland clipboard | Implemented: tpass/wecanencrypt OpenPGP, pure Rust crypto and native expiring clipboard; host interoperability/tamper tests pass |
| nnn files, archives, Open With, image/video/PDF integration | NORL nnn, base archive tools, swayimg, mpv, Zathura | Implemented: NORL nnn, archive/Open With helpers, swayimg/mpv/Zathura configs; native clients pending |
| removable media, camera/mic, external keyboards, print/scan | discovered FreeBSD devices and explicit optional workflows | Implemented: explicit USB mount/probe and serial access, audio/input controls; camera/print/scan depend on identified devices |
| software menu: search/install/details/update/**remove**, ports, base/firmware | pkg/ports gate, local ABI retention, native base-update method | Implemented: signed package gate, 15 variants, protected uninstall, reviewed ports and native maintenance; native complete graph pending |
| root installer, user builds, file links, logs, recovery | archived FreeBSD stage structure plus OpenBSD audit fixes | Implemented: root pipeline, ordinary-user builds, stage gates, selective files/logs/recovery; full native run pending |
| manual Base-Setup, firmware choices, DVD1 and console recovery | separate FreeBSD manual and retained T14 firmware profile | Updated: separate complete manual setup, supplied firmware choices and actual installer handoff |
| adaptive CPU, resource limits, efficient idle, maximum load performance | detected HWP/devd, fallback powerd, measured limits | Implemented: HWP/devd profiles, powerd fallback and bounded build jobs; measured idle/load/battery results pending |
| C/C++, Rust, Go, Python/uv, POSIX shell, multi-architecture assembly | native LLVM and native tools in retained editor workflow | Implemented: pinned native tool provisioning and editor/build/test/lint/debug helpers; native project acceptance pending |
| **Unfinished old Zephyr plan**: west, all requested board families, flash/debug | native FreeBSD CLI workflow and exact board/toolchain matrix | Implemented: native CLI, pinned workspace/tools/runtime, board-family matrix; exact native builds/flash/probes pending, Xtensa unsupported |
| **New embedded Rust request** | per-project no_std targets, linker/probe/serial/rust-analyzer | Implemented: scoped Rust toolchain/no_std targets and Zephyr Rust module; real ARM runtime host link check, hardware pending |
| Offline manuals and formatted code examples while editing | DOCS launcher, vis Space od, dvtm Ctrl+B d, man/Lowdown/local HTML | Implemented: C/C++/Rust/Go/Python/LLVM/system references, nine template topics, data-only documentation packages and an installation gate; native installed library check pending |
| **New fingerprint/PAM/FIDO request** | FreeBSD driver/USB-ID check, supported PAM path, enrollment guide | Implemented: actual device discovery, optional module paths, local enrollment and recovery guide; reader/FIDO hardware pending |
| **New Bluetooth request** | native controller/profile discovery, status icon, connect menu | Implemented: controller discovery, status icon, native classic HID scan/pair/connect; BLE/audio limits documented, hardware pending |
| current desktop/browser/menu/workspace/login/lock renders and GIFs | render from migrated implementation and actual fonts | Generated: current shared-painter compositions/GIFs and actual QML/HTML renders with bundled fonts; native screenshots pending |

Only explicit later choices remove old components: FreeBSD replaces OpenBSD;
Wayland replaces X11/Xenocara; dwl/foot/qutebrowser replace dwm/st/surf/tabbed;
base mdo replaces doas; Bluetooth is restored. Email/Tuta were cancelled and
Tailscale remains excluded. Older Neovim/tmux/Zsh/pfetch choices remain superseded,
while their useful editing/session/navigation workflows are retained above.

Native package closure, login/lock/resume, mixed-DPI docking, fingerprint support,
IME and measured performance are acceptance tasks. Full Zephyr/all-board support
cannot be inferred from a successful compiler build; unsupported toolchains are
explicit in [EMBEDDED](EMBEDDED.md). Endpoints, keys, enrollment, actual monitor
profiles, printers and probes remain local inputs. No server/router/container
provisioning belongs to this laptop repository.
