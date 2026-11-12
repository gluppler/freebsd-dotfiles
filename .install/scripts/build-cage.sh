#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
# SDDM's greeter kiosk links this checkout's wlroots variant. The stock cage
# package calls the X11 and XWayland functions the variant leaves out, so it
# exits before drawing and leaves SDDM on a blank console.
pkg-config --atleast-version=0.20 --max-version=0.20.99 wlroots-0.20
version=$(awk -F '|' '$1 == "cage" {sub(/^cage-/, "", $2); print $2}' "$repo/.install/sources.lock")
mkdir -p "$repo/.build/work" "$repo/.build/prefix/libexec"
work=$(mktemp -d "$repo/.build/work/cage.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" cage "$work/src"
sh "$repo/.install/scripts/stage-licenses.sh" cage "$work/src" "$repo/.build/prefix"
cd "$work/src"
# Upstream builds with -Werror; a new compiler warning must not stop the install.
CC=/usr/bin/clang meson setup "$work/build" . --prefix="$repo/.build/prefix" \
    --buildtype=release --wrap-mode=nofallback -Dwerror=false -Dman-pages=disabled
meson compile -C "$work/build"
# Bind every symbol before main runs: an unresolved one fails here, not at login.
[ "$(LD_BIND_NOW=1 "$work/build/cage" -v)" = "Cage version $version" ]
install -m 755 "$work/build/cage" "$repo/.build/prefix/libexec/nostromo-cage"
