#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || {
    echo 'Build dwlb as the ordinary account on FreeBSD.' >&2
    exit 1
}
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/dwlb.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" dwlb "$work/src"
sh "$repo/.install/scripts/stage-licenses.sh" dwlb "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p1 <"$repo/dwlb/nostromo.patch"
patch -s -F 0 -p1 <"$repo/dwlb/scale.patch"
patch -s -F 0 -p1 <"$repo/dwlb/controls.patch"
patch -s -F 0 -p1 <"$repo/dwlb/reparse.patch"
cp "$repo/dwlb/config.h" .
protocols=$(pkg-config --variable=pkgdatadir wayland-protocols)
scanner=$(pkg-config --variable=wayland_scanner wayland-scanner)
for entry in \
    "xdg-shell|$protocols/stable/xdg-shell/xdg-shell.xml" \
    "xdg-output-unstable-v1|$protocols/unstable/xdg-output/xdg-output-unstable-v1.xml" \
    'wlr-layer-shell-unstable-v1|protocols/wlr-layer-shell-unstable-v1.xml' \
    'dwl-ipc-unstable-v2|protocols/dwl-ipc-unstable-v2.xml'; do
    name=${entry%%|*} file=${entry#*|}
    "$scanner" client-header "$file" "$name-protocol.h"
    "$scanner" private-code "$file" "$name-protocol.c"
done
# No GNU make or Linux memfd dependency; shm_open(SHM_ANON) is native FreeBSD.
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Wno-unused-parameter \
    $(pkg-config --cflags wayland-client wayland-cursor fcft pixman-1) \
    dwlb.c ./*-protocol.c $(pkg-config --libs wayland-client wayland-cursor fcft pixman-1) \
    -o dwlb
install -m 755 dwlb "$repo/.build/prefix/bin/dwlb"
mkdir -p "$repo/.build/prefix/share/man/man1"
install -m 644 dwlb.1 "$repo/.build/prefix/share/man/man1/"
