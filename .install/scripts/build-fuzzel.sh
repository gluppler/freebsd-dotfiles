#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
mkdir -p "$repo/.build/work" "$repo/.build/prefix"
work=$(mktemp -d "$repo/.build/work/fuzzel.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" fuzzel "$work/src"
sh "$repo/.install/scripts/stage-licenses.sh" fuzzel "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p1 <"$repo/fuzzel/nostromo.patch"
cp "$repo/fuzzel/panel.h" .
# Native Meson/Ninja. No bundled downloads and no unused icon-renderer chain.
CC=/usr/bin/clang meson setup "$work/build" . --prefix="$repo/.build/prefix" \
    --buildtype=release --wrap-mode=nofallback \
    -Denable-cairo=disabled -Dpng-backend=none -Dsvg-backend=none
meson compile -C "$work/build"
meson install -C "$work/build" --no-rebuild
