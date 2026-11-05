#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
mkdir -p "$repo/.build/work" "$repo/.build/prefix"
work=$(mktemp -d "$repo/.build/work/foot.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/scripts/fetch-source.sh" foot "$work/src"
sh "$repo/scripts/stage-licenses.sh" foot "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p1 <"$repo/src/foot/nostromo.patch"
# Stock foot supplies matching terminfo; retain FreeBSD's base ulog helper.
CC=/usr/bin/clang meson setup "$work/build" . --prefix="$repo/.build/prefix" \
    --buildtype=release --wrap-mode=nofallback -Ddocs=enabled -Dthemes=false \
    -Dterminfo=disabled -Dutmp-default-helper-path=/usr/libexec/ulog-helper
meson compile -C "$work/build"
meson test -C "$work/build" --print-errorlogs
meson install -C "$work/build" --no-rebuild
