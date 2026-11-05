# Research sources and provenance

Updated **2026-11-04**. Primary project documentation/FreeBSD ports were used for
the migration decisions. URLs following main/latest may change; locally saved
research files are evidence snapshots, not an install lock or approval of their
whole dependency closure. Exact source/ports pins are in `sources.lock` and `ports.lock`; runtime package
transactions independently verify signatures, policy and native ABI.

## Platform and hardware

- [FreeBSD 15.1 release/media](https://www.freebsd.org/releases/15.1R/announce/)
- [Release support](https://www.freebsd.org/security/)
- [Manual installation](https://docs.freebsd.org/en/books/handbook/bsdinstall/)
- [Wayland](https://docs.freebsd.org/en/books/handbook/wayland/)
- [Power management](https://docs.freebsd.org/en/books/handbook/config/)
- [Package/ports management](https://docs.freebsd.org/en/books/handbook/ports/)
- [Base updates](https://docs.freebsd.org/en/books/handbook/cutting-edge/)
- [Wireless networking](https://docs.freebsd.org/en/books/handbook/network/)
- [HWP manual source, releng/15.1](https://github.com/freebsd/freebsd-src/blob/releng/15.1/share/man/man4/hwpstate_intel.4)
- [mdo manual source, releng/15.1](https://github.com/freebsd/freebsd-src/blob/releng/15.1/usr.bin/mdo/mdo.1)
- [mac_do manual source, releng/15.1](https://github.com/freebsd/freebsd-src/blob/releng/15.1/share/man/man4/mac_do.4)
- [Lenovo T14 Gen 2 Intel specifications](https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_T14_Gen_2_Intel/ThinkPad_T14_Gen_2_Intel_Spec.pdf)
- Lenovo BIOS option definitions are linked next to the tables in [FIRMWARE](FIRMWARE.md).

## Desktop and editor

- [dwl FreeBSD recipe](https://cgit.freebsd.org/ports/tree/x11-wm/dwl): checked 0.9 / wlroots 0.20, downstream Clang fix, default X11 option to disable.
- [dwlb recipe](https://cgit.freebsd.org/ports/tree/x11/dwlb): checked snapshot s20250520 / upstream 48dbe00; status stdin vs optional IPC explained in the saved upstream README.
- [foot recipe](https://cgit.freebsd.org/ports/tree/x11/foot) and [foot 1.28 config manual](https://codeberg.org/dnkl/foot/src/tag/1.28.0/doc/foot.ini.5.scd): use colors-dark, not an obsolete colors section.
- [fuzzel recipe](https://cgit.freebsd.org/ports/tree/x11/fuzzel) and [upstream](https://codeberg.org/dnkl/fuzzel).
- [Dunst recipe](https://cgit.freebsd.org/ports/tree/sysutils/dunst): checked native WAYLAND option, existing X dependencies and build tools.
- [qutebrowser recipe](https://cgit.freebsd.org/ports/tree/www/qutebrowser): checked 3.7.0, Qt6/PyQt6/WebEngine.
- [qutebrowser 3.7 settings source](https://github.com/qutebrowser/qutebrowser/blob/v3.7.0/qutebrowser/config/configdata.yml): native backend, fonts, colors and editor settings.
- [SDDM recipe](https://cgit.freebsd.org/ports/tree/x11/sddm): Qt6, FreeBSD PAM files, ConsoleKit and unconditional X helper dependencies; native Wayland integration still needs proof.
- [gtklock recipe](https://cgit.freebsd.org/ports/tree/x11/gtklock) and [upstream](https://github.com/jovanlanik/gtklock): version 5 uses ext-session-lock; upstream's maintenance notice is recorded in MIGRATION.
- [Ly recipe](https://cgit.freebsd.org/ports/tree/x11/ly): considered as terminal recovery, not selected as the graphical theme.
- [seatd rc script](https://cgit.freebsd.org/ports/tree/sysutils/seatd/files/seatd.in): default video-group socket access.
- [vis recipe](https://cgit.freebsd.org/ports/tree/editors/vis): native executable vise, WL_COPY option and NLS/TRE choices.
- [Zephyr guide](https://docs.zephyrproject.org/latest/develop/getting_started/index.html) and [host toolchains](https://docs.zephyrproject.org/latest/develop/toolchains/host.html): FreeBSD host/all-board support is not established by these guides.

## Artwork/effects

The retained asset licenses are under assets/licenses and assets/fonts.
The original [Omarchy shader reference](https://github.com/abaidan/omarchy-weyland-yutani-theme/blob/c88479a05e208acca0725a640ffb280e8ce26a7a/crt.glsl)
and user-supplied [Cyberpunk](https://www.cyberpunk.net/en) styling reference
remain design context, not runtime dependencies.

New reference: [space_dots](https://github.com/vdawg-git/space_dots), local revision
`c7775088bdb07824aeaaf41f25308c71b1f98996`. Inspected `.other/orig.frag`,
hypr/theme.conf, readme and local screenshot; did not execute reference scripts
or view its linked video. Copied shader SHA256:
`f5b7d8fbd29f5a697b99ee5a6522578d80688a97628b9b6f9817edbeb6c4ef17`.
The file's MIT header identifies Maxim Samoliuk (2023) and is retained.

The new directory's assets/configuration are adapted from the current local
OpenBSD project for visuals and portable tools. The archived FreeBSD installer
and manual setup guides are the explicitly requested installation starting point;
their obsolete application stages have been replaced by the current native pipeline.
Historical renders and SVG source art are archived outside this repository;
the retained PNG artwork keeps the same attribution and usage terms.

## Native provisioning and embedded additions

- [pkg query fields](https://github.com/freebsd/pkg/blob/main/docs/pkg-query.8): automatic/locked/vital/reverse-dependency guards for bootstrap cleanup.
- [FreeBSD PF](https://man.freebsd.org/cgi/man.cgi?query=pf.conf&sektion=5): anchor quick-rule semantics and native syntax validation.
- [FreeBSD sshd](https://man.freebsd.org/cgi/man.cgi?query=sshd&sektion=8): command-line precedence over configuration files.
- [USB storage](https://docs.freebsd.org/en/books/handbook/disks/#usb-disks) and [mount_msdosfs](https://man.freebsd.org/cgi/man.cgi?query=mount_msdosfs&sektion=8): explicit device/mount permissions.
- [Zephyr 4.5.0 source](https://github.com/zephyrproject-rtos/zephyr/tree/v4.5.0) and [custom CMake toolchains](https://docs.zephyrproject.org/latest/develop/toolchains/custom_cmake.html): matching compiler/linker/bintools roots and per-target configuration.
- [Zephyr Rust](https://docs.zephyrproject.org/latest/develop/languages/rust/index.html): optional module/target boundaries.
- [Rust 1.98.1 distribution manifest](https://static.rust-lang.org/dist/channel-rust-1.98.1.toml): verified FreeBSD host archive and bare-metal target availability.
- [LLVM compiler-rt builtins](https://llvm.org/docs/HowToCrossCompileBuiltinsOnArm.html): freestanding runtime/archive/link requirements.

- [Swayimg 5.6 API](https://github.com/artemsen/swayimg/blob/v5.6/extra/swayimg.lua): current Lua theme/keyboard configuration and app ID for bottom-rail matching.
- [Zathura application ID](https://github.com/pwmt/zathura/blob/develop/zathura/zathura.c): `org.pwmt.zathura` for the document-viewer rail, with legacy `zathura` also recognised.

## Offline references and package maintenance

- [pkg 2.8.4 command restart](https://github.com/freebsd/pkg/blob/2.8.4/src/main.c),
  [upgrade](https://github.com/freebsd/pkg/blob/2.8.4/docs/pkg-upgrade.8),
  [delete](https://github.com/freebsd/pkg/blob/2.8.4/docs/pkg-delete.8) and
  [dependency checking](https://github.com/freebsd/pkg/blob/2.8.4/src/check.c):
  self-upgrade replay, preserved automatic flags, consumer removal and read-only checks.
- [stdman](https://github.com/jeaye/stdman),
  [Python 3.12 offline formats](https://docs.python.org/3.12/download.html),
  [Rust components](https://rust-lang.github.io/rustup/concepts/components.html)
  and [Go toolchain selection](https://go.dev/doc/toolchain): local references and
  disabled documentation-time downloads.
- The checked quarterly documentation archives were stdman 2024.07.05,
  python-doc-text/python-doc-html 3.12.15 and en-freebsd-doc 20260814,1. Their
  manifests had no package dependencies. Checksums were verified against the
  cached catalog; the native installer repeats signed archive/graph checks.
- [Intel graphics](https://docs.freebsd.org/en/books/handbook/x11/#x-graphic-card-drivers)
  and [Wayland setup](https://docs.freebsd.org/en/books/handbook/wayland/):
  i915kms, firmware discovery, seatd and video-group access for the confirmed Iris Xe GPU.
