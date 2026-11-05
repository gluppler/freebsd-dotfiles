#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || {
    echo 'Build dwl as the ordinary account on FreeBSD.' >&2
    exit 1
}
pkg-config --atleast-version=0.20 --max-version=0.20.99 wlroots-0.20
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/dwl.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/scripts/fetch-source.sh" dwl "$work/src"
sh "$repo/scripts/stage-licenses.sh" dwl "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p1 <"$repo/src/dwl/clang.patch"
patch -s -F 0 -p1 <"$repo/src/dwl/nostromo.patch"
patch -s -F 0 -p1 <"$repo/src/dwl/ipc.patch"
patch -s -F 0 -p1 <"$repo/src/dwl/controls.patch"
patch -s -F 0 -p1 <"$repo/src/dwl/crt.patch"
patch -s -F 0 -p1 <"$repo/src/dwl/animation.patch"
cp "$repo/src/dwl/config.h" "$repo/src/dwl/nostromo.h" "$repo/src/dwl/ipc.h" .
cp "$repo/src/dwl/crt.h" "$repo/src/dwl/rail.h" .
sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/^/"/' -e 's/$/\\n"/' "$repo/src/dwl/crt.frag" >crt-shader.h
protocols=$(pkg-config --variable=pkgdatadir wayland-protocols)
scanner=$(pkg-config --variable=wayland_scanner wayland-scanner)
"$scanner" enum-header "$protocols/staging/cursor-shape/cursor-shape-v1.xml" cursor-shape-v1-protocol.h
"$scanner" enum-header "$protocols/staging/ext-image-copy-capture/ext-image-copy-capture-v1.xml" ext-image-copy-capture-v1-protocol.h
"$scanner" enum-header "$protocols/unstable/pointer-constraints/pointer-constraints-unstable-v1.xml" pointer-constraints-unstable-v1-protocol.h
"$scanner" enum-header protocols/wlr-layer-shell-unstable-v1.xml wlr-layer-shell-unstable-v1-protocol.h
"$scanner" server-header protocols/wlr-output-power-management-unstable-v1.xml wlr-output-power-management-unstable-v1-protocol.h
"$scanner" server-header "$protocols/stable/xdg-shell/xdg-shell.xml" xdg-shell-protocol.h
"$scanner" server-header "$repo/src/dwl/dwl-ipc-unstable-v2.xml" dwl-ipc-unstable-v2-protocol.h
"$scanner" private-code "$repo/src/dwl/dwl-ipc-unstable-v2.xml" dwl-ipc-unstable-v2-protocol.c
"$scanner" server-header "$repo/src/dwl/nostromo-control-v1.xml" nostromo-control-v1-server.h
"$scanner" private-code "$repo/src/dwl/nostromo-control-v1.xml" nostromo-control-v1.c
# Native BSD visibility is needed for arc4random_uniform; XWAYLAND is undefined.
# pkg-config returns compiler words; splitting is intentional and never eval'd.
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Wno-unused-parameter \
    -Werror=implicit-function-declaration -Werror=incompatible-pointer-types \
    -DWLR_USE_UNSTABLE '-DVERSION="0.9-nostromo"' -I. \
    $(pkg-config --cflags wayland-server xkbcommon libinput wlroots-0.20 pangocairo libdrm egl glesv2) \
    dwl.c dwl-ipc-unstable-v2-protocol.c nostromo-control-v1.c \
    $(pkg-config --libs wayland-server xkbcommon libinput wlroots-0.20 pangocairo libdrm egl glesv2) -lm -o dwl
install -m 755 dwl "$repo/.build/prefix/bin/dwl"
mkdir -p "$repo/.build/prefix/share/man/man1"
install -m 644 dwl.1 "$repo/.build/prefix/share/man/man1/"
mkdir -p "$repo/.build/prefix/share/licenses/space-dots"
install -m 644 "$repo/src/dwl/crt.frag" "$repo/.build/prefix/share/licenses/space-dots/crt.frag"
