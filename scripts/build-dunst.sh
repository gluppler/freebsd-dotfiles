#!/bin/sh
# Direct Clang build of the native Wayland backend and shared Cairo theme.
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/dunst.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/scripts/fetch-source.sh" dunst "$work/src"
sh "$repo/scripts/stage-licenses.sh" dunst "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p1 <"$repo/src/dunst/nostromo.patch"
patch -s -F 0 -p1 <"$repo/src/dunst/freebsd.patch"
cp "$repo/src/dunst/nostromo.h" src/
protocols=$(pkg-config --variable=pkgdatadir wayland-protocols)
scanner=$(pkg-config --variable=wayland_scanner wayland-scanner)
for spec in \
    "xdg-shell|$protocols/stable/xdg-shell/xdg-shell.xml" \
    "cursor-shape-v1|$protocols/staging/cursor-shape/cursor-shape-v1.xml" \
    "tablet-unstable-v2|$protocols/unstable/tablet/tablet-unstable-v2.xml" \
    "ext-idle-notify-v1|$protocols/staging/ext-idle-notify/ext-idle-notify-v1.xml" \
    'idle|src/wayland/protocols/idle.xml' \
    'wlr-foreign-toplevel-management-unstable-v1|src/wayland/protocols/wlr-foreign-toplevel-management-unstable-v1.xml' \
    'wlr-layer-shell-unstable-v1|src/wayland/protocols/wlr-layer-shell-unstable-v1.xml'; do
    name=${spec%%|*} file=${spec#*|}
    "$scanner" client-header "$file" "src/wayland/protocols/$name-client-header.h"
    "$scanner" private-code "$file" "src/wayland/protocols/$name.h"
done
set -- gio-2.0 gdk-pixbuf-2.0 glib-2.0 pangocairo wayland-client wayland-cursor
pkg-config --exists "$@"
# Fixed pkg-config paths contain no shell data; split the compiler flag list.
# shellcheck disable=SC2046
cc -std=gnu11 -O2 -Wall -Wextra -Wno-unused-parameter -DENABLE_WAYLAND \
    -DHAVE_WL_CURSOR_SHAPE -DHAVE_WL_EXT_IDLE_NOTIFY \
    '-DVERSION="1.13.2-nostromo"' '-DSYSCONFDIR="/usr/local/etc/xdg"' \
    $(pkg-config --cflags "$@") src/*.c src/wayland/*.c \
    $(pkg-config --libs "$@") -lm -o dunst
install -m 755 dunst dunstctl "$repo/.build/prefix/bin/"
mkdir -p "$repo/.build/prefix/share/man/man1" "$repo/.build/prefix/share/man/man5"
sed 's|@sysconfdir@|/usr/local/etc/xdg|g' docs/dunst.1.pod.in >docs/dunst.1.pod
pod2man --section=1 docs/dunst.1.pod "$repo/.build/prefix/share/man/man1/dunst.1"
pod2man --section=1 docs/dunstctl.pod "$repo/.build/prefix/share/man/man1/dunstctl.1"
pod2man --section=5 docs/dunst.5.pod "$repo/.build/prefix/share/man/man5/dunst.5"
