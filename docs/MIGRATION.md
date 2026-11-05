# OpenBSD/X11 → FreeBSD/Wayland

The conversion is implemented in this standalone directory. The detailed
[coverage ledger](MIGRATION-COVERAGE.md) maps every retained workflow and separates
repository implementation from native laptop acceptance. Exact build/source
versions live in the manifests, not changing latest-branch port pages.

## Selected replacements

| Previous component | Current implementation |
| --- | --- |
| dwm / bar | Patched dwl 0.9 + wlroots 0.20, dwlb typed IPC and FreeBSD status helpers |
| st | Patched foot 1.28 with Azeret Mono, alpha controls and CWD integration |
| surf + tabbed | qutebrowser alone, native Qt Wayland, local start page and external vis editor |
| dmenu | Patched fuzzel plus POSIX action/file/content/project menus |
| picom | dwl GLES output pass, animated/static/off CRT modes and map fade |
| xenodm / xlock | Native Wayland SDDM/cage + QML login; patched gtklock/PAM for authenticated locking |
| xwallpaper / xidle / X splash | swaybg, swayidle and native layer-shell splash/lock artwork |
| X11 Dunst | Native Wayland Dunst with the retained Cairo frame/label design |
| xclip / scrot | wl-clipboard, native secret clipboard owner, grim/slurp and compositor geometry |
| xrandr / XTEST / XIM | wlr-randr/kanshi, compositor pointer keys and fcitx5 Wayland text-input |
| nsxiv | swayimg; Zathura/MuPDF and mpv retain native Wayland paths |
| OpenBSD CWD/sound/device APIs | libprocstat, FreeBSD mixer/OSS/backlight, ACPI/devd and devfs |
| doas / OpenBSD service tools | Base mdo/mac_do, sysrc/service, native pkg/base/firmware helpers |
| hostname.wgN / OpenBSD PF | Native wg(4), explicit interface/route management and selective FreeBSD PF/SSH merges |
| OpenBSD boot art | Isolated FreeBSD Lua loader module with the retained hybrid orb |

Actual oksh, vis/Lowdown/LSP, abduco/dvtm, fastfetch, zoxide, Git/lazygit, nnn and
the pass-compatible workflow are retained and ported. The developer environment
adds native Zephyr/LLVM and scoped embedded Rust.

## Why the larger integration components remain

SDDM reuses the Qt stack already required by qutebrowser and supplies a genuine
graphical PAM login with the requested font/fields. A console getty remains the
recovery path. The SDDM package has X helper/library dependencies, and some shared
Qt/GTK packages contain X support; this is disclosed in the policy. The configured
greeter and desktop run Wayland, with no Xorg/Xwayland session or browser fallback.
Dwl itself is built without XWAYLAND. Bare dependency names do not prove runtime
backends; native acceptance checks the actual processes and clients with DISPLAY
unset.

Dwl/foot/dwlb and the visual patches are pinned together. Direct native builds
retain the necessary FreeBSD API/Clang fixes. Layer-shell menus/notifications draw
their own approved frames; they cannot inherit normal-window decorations. Foot
CWD titles are bounded display text. GPU effects run in the compositor's GLES
render pass.

The upstream gtklock maintenance notice makes continued upstream monitoring part
of maintaining the authentication component. The custom PAM adapter is tested
with a host mock, but that cannot certify native authentication or secure output
coverage. [BOOT-AND-SESSION](BOOT-AND-SESSION.md) records the native acceptance path.

FreeBSD compatibility libraries such as epoll-shim/LinuxKPI do not install a Linux
userland. GNU provenance is separately controlled by the exact runtime/build
exceptions and local variants in [PACKAGES](PACKAGES.md). No blanket exception is
created for the browser's optional dependencies.
