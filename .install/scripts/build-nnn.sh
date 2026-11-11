#!/bin/sh
# Native curses input and libarchive tar; no Readline/atool/GNU sed dependency.
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/nnn.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" nnn "$work/src"
sh "$repo/.install/scripts/stage-licenses.sh" nnn "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p1 <"$repo/nnn/freebsd.patch"
cc -std=c11 -O2 -Wall -Wextra -DNORL -DDIM_FILTERED src/nnn.c -lncursesw -lpthread -o nnn
install -m 755 nnn "$repo/.build/prefix/bin/nnn"
mkdir -p "$repo/.build/prefix/share/man/man1"
install -m 644 nnn.1 "$repo/.build/prefix/share/man/man1/"
