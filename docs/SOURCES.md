# Research sources and provenance

Updated **2026-11-04**. Primary project documentation/FreeBSD ports were used for
the migration decisions. URLs following main/latest may change; locally saved
research files are evidence snapshots, not an install lock or approval of their
whole dependency closure. Exact source/ports pins are in `.install/sources.lock` and `.install/ports.lock`; runtime package
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

The orb's FreeBSD glyph comes from Font Logos (Nerd Fonts 3.0.2, U+F30C); its
public-domain notice and the FreeBSD trademark statement are in
`art/licenses/font-logos.txt`. The fonts keep their OFL licenses in `fonts/`.
The user-supplied [Cyberpunk](https://www.cyberpunk.net/en) styling reference
is design context, not a runtime dependency.

New reference: [space_dots](https://github.com/vdawg-git/space_dots), local revision
`c7775088bdb07824aeaaf41f25308c71b1f98996`. Inspected `.other/orig.frag`,
hypr/theme.conf, readme and local screenshot; did not execute reference scripts
or view its linked video. Copied shader SHA256:
`f5b7d8fbd29f5a697b99ee5a6522578d80688a97628b9b6f9817edbeb6c4ef17`.
The file's MIT header identifies Maxim Samoliuk (2023) and is retained.

The new directory's artwork and configuration are adapted from the current local
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
  python-doc-text/python-doc-html 3.12.15, en-freebsd-doc 20260814,1 and
  cmake-man 3.31.12. Their manifests had no package dependencies. Checksums were
  verified against the cached catalog; the native installer repeats signed
  archive/graph checks.
- Offline library, reviewed 2026-11-11 and pinned by SHA256 in `.install/sources.lock`:
  [C23 draft N3220](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n3220.pdf),
  [C++23 draft N4950](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2023/n4950.pdf),
  [POSIX.1-2024](https://pubs.opengroup.org/onlinepubs/9799919799/),
  [Arm ABI 2026Q3](https://github.com/ARM-software/abi-aa/releases/tag/2026Q3),
  [C++ Core Guidelines](https://github.com/isocpp/CppCoreGuidelines),
  [Go by Example](https://github.com/mmcgrana/gobyexample),
  [Google style guides](https://github.com/google/styleguide),
  [System Design Primer](https://github.com/donnemartin/system-design-primer),
  [Awesome Scalability](https://github.com/binhnguyennus/awesome-scalability),
  [HTTP/2 explained](https://github.com/bagder/http2-explained),
  [HTTP/3 explained](https://github.com/bagder/http3-explained),
  [What happens when](https://github.com/alex/what-happens-when),
  [Let's Build a Simple Database](https://github.com/cstack/db_tutorial),
  [Kubernetes the Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way),
  [The Art of Command Line](https://github.com/jlevy/the-art-of-command-line) and
  [pure sh bible](https://github.com/dylanaraps/pure-sh-bible). Each archive
  passed the fetcher's member rule and the library's link and special-file rule,
  and every catalogue entry and Go by Example program resolved, on the Mac.
- Electronics library, reviewed 2026-11-11 and pinned the same way:
  [MIT 6.002 lecture notes](https://ocw.mit.edu/courses/6-002-circuits-and-electronics-spring-2007/pages/lecture-notes/),
  [Lessons in Electric Circuits](https://www.ibiblio.org/kuphaldt/electricCircuits/),
  the guide inside [Logisim 2.7.1](https://cburch.com/logisim/index.html)'s jar,
  [Feedback Systems](https://www.cds.caltech.edu/~murray/books/AM08/pdf/fbs-public_24Jul2020.pdf),
  [A Mathematical Introduction to Robotic Manipulation](https://www.cds.caltech.edu/~murray/books/MLS/pdf/mls94-complete.pdf),
  [Introduction to Autonomous Robots 3.0](https://github.com/Introduction-to-Autonomous-Robots/Introduction-to-Autonomous-Robots/releases/tag/v3.0),
  [Planning Algorithms](https://lavalle.pl/planning/),
  [PCB Design Tutorial](https://www.alternatezone.com/electronics/files/PCBDesignTutorialRevA.pdf),
  the [Tildagon documentation](https://github.com/emfcamp/badge-2024-documentation) at `da28c27669cc`,
  the [2025 Communicator badge](https://github.com/Hack-a-Day/2025-Communicator_Badge) at `6e923e9074f1`
  and the [Vectorscope badge](https://github.com/Hack-a-Day/Vectorscope) at `ea5fab24017a`.
  The electronics guide's SAO pinout follows the Communicator schematic's
  `Simple_Addon_v2` connector; its hexpansion shape, pins, power, EEPROM header
  and rules follow the Tildagon hexpansion documentation, and its header code
  reproduces that documentation's example bytes. The Art of Electronics was not
  added: it is in print, and the archive.org copy offered is a user upload.
  `www.cds.caltech.edu` leaves its intermediate certificate out of its TLS chain,
  which browsers complete and FreeBSD's fetch(1) does not. `.install/intermediates.crt`
  holds that certificate, InCommon RSA Server CA 2, from the leaf's CA Issuers
  URL; it was checked against the USERTrust root before it was committed.
  `docs-library.sh` adds it to the base system's roots, so chains still end there.
- [The Book of Secret Knowledge](https://github.com/trimstray/the-book-of-secret-knowledge)
  at commit `7d37069a361d`: `.install/scripts/import-secret-knowledge.py` regenerates the
  committed chapters from a local clone, and every link was compared with the source.
- [Intel graphics](https://docs.freebsd.org/en/books/handbook/x11/#x-graphic-card-drivers)
  and [Wayland setup](https://docs.freebsd.org/en/books/handbook/wayland/):
  i915kms, firmware discovery, seatd and video-group access for the confirmed Iris Xe GPU.
