#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || {
    echo 'Build gtklock as the ordinary account on FreeBSD.' >&2
    exit 1
}
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/gtklock.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" gtklock "$work/src"
sh "$repo/.install/scripts/stage-licenses.sh" gtklock "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p0 <"$repo/gtklock/freebsd.patch"
patch -s -F 0 -p1 <"$repo/gtklock/nostromo.patch"
patch -s -F 0 -p1 <"$repo/gtklock/ack.patch"
cp "$repo/gtklock/auth.c" src/auth.c
cp "$repo/gtklock/theme.h" "$repo/gtklock/art.h" "$repo/session/space-dots.h" include/
# English is the project language. Compiling English strings needs no msgfmt.
# The local patch uses plain English literals; no gettext tooling is invoked.
sed 's/ preprocess="xml-stripblanks"//' res/ui.gresource.xml >res/nostromo.gresource.xml
glib-compile-resources --generate-source --c-name=ui --sourcedir=res \
    --target=ui-resources.c res/nostromo.gresource.xml
set -- gtk+-3.0 gtk-session-lock-0 gmodule-export-2.0
pkg-config --exists "$@"
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Wno-unused-parameter \
    -Werror=implicit-function-declaration -Werror=incompatible-pointer-types \
    -Iinclude -DGETTEXT_PACKAGE='"gtklock"' -DLOCALEDIR='"/usr/local/share/locale"' \
    -DLIBDIR=/usr/local/lib -DMAJOR_VERSION=5 -DMINOR_VERSION=0 -DMICRO_VERSION=0 \
    $(pkg-config --cflags "$@") src/*.c ui-resources.c \
    $(pkg-config --libs "$@") -lpam -lm -o gtklock
install -m 755 gtklock "$repo/.build/prefix/bin/gtklock"
mkdir -p "$repo/.build/prefix/share/man/man1"
scdoc <man/gtklock.1.scd >"$repo/.build/prefix/share/man/man1/gtklock.1"
# PAM policy is a separate root installer step, never setuid the graphical UI.
