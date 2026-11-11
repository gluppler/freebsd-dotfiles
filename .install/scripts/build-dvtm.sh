#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || {
    echo 'Build dvtm as the ordinary account on FreeBSD.' >&2
    exit 1
}
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin" "$repo/.build/prefix/share/terminfo"
work=$(mktemp -d "$repo/.build/work/dvtm.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" dvtm "$work/src"
sh "$repo/.install/scripts/stage-licenses.sh" dvtm "$work/src" "$repo/.build/prefix"
cd "$work/src"
cp "$repo/dvtm/freebsd-cwd.h" .
sed -f "$repo/dvtm/freebsd.sed" dvtm.c >dvtm.c.new
mv dvtm.c.new dvtm.c
sed '/^static Row \*buffer_row_last(/,/^}/d; /^static Row \*buffer_row_prev(/,/^}/d' vt.c >vt.c.new
mv vt.c.new vt.c
for change in cwd panes editor; do patch -s -F 0 -p1 <"$repo/dvtm/$change.patch"; done
sed -f "$repo/dvtm/config.sed" config.def.h >config.h
# Direct Clang uses the base wide-character curses and libprocstat, not GNU make.
cc -std=c99 -O2 -Wall -Wextra -Wno-unused-parameter -DNDEBUG \
    -D_XOPEN_SOURCE_EXTENDED '-DVERSION="0.15-311a8c0-nostromo"' \
    dvtm.c vt.c -lncursesw -lutil -lprocstat -o dvtm
cc -std=c99 -O2 -Wall -Wextra -D_POSIX_C_SOURCE=200809L dvtm-editor.c -o dvtm-editor
install -m 755 dvtm dvtm-editor dvtm-pager "$repo/.build/prefix/bin/"
mkdir -p "$repo/.build/prefix/share/man/man1"
install -m 644 dvtm.1 "$repo/.build/prefix/share/man/man1/"
tic -x -o "$repo/.build/prefix/share/terminfo" dvtm.info
