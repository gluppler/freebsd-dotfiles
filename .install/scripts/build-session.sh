#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
mkdir -p "$repo/.build/prefix/bin"
mkdir -p "$repo/.build/work"
work=$(mktemp -d "$repo/.build/work/control.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
cc -std=c11 -O2 -Wall -Wextra -Werror "$repo/session/terminal-idle.c" \
    -o "$repo/.build/prefix/bin/nostromo-terminal-idle"
wayland-scanner client-header "$repo/dwl/nostromo-control-v1.xml" "$work/nostromo-control-v1-client.h"
wayland-scanner private-code "$repo/dwl/nostromo-control-v1.xml" "$work/nostromo-control-v1.c"
protocols=$(pkg-config --variable=pkgdatadir wayland-protocols)
wayland-scanner client-header "$protocols/staging/ext-data-control/ext-data-control-v1.xml" "$work/ext-data-control-v1-client.h"
wayland-scanner private-code "$protocols/staging/ext-data-control/ext-data-control-v1.xml" "$work/ext-data-control-v1.c"
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Werror -Wno-unused-parameter -I"$work" \
    $(pkg-config --cflags wayland-client) "$repo/session/secret-copy.c" "$work/ext-data-control-v1.c" \
    $(pkg-config --libs wayland-client) -o "$repo/.build/prefix/bin/nostromo-secret-copy"
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Werror -Wno-unused-parameter -I"$work" \
    $(pkg-config --cflags wayland-client) "$repo/session/control.c" "$work/nostromo-control-v1.c" \
    $(pkg-config --libs wayland-client) -o "$repo/.build/prefix/bin/nostromo-control"
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Werror -Wno-unused-parameter \
    $(pkg-config --cflags wayland-client) "$repo/session/events.c" \
    $(pkg-config --libs wayland-client) -o "$repo/.build/prefix/bin/nostromo-output-watch"
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Werror -Wno-unused-parameter \
    $(pkg-config --cflags gtk+-3.0 gtk-layer-shell-0) "$repo/session/splash.c" \
    $(pkg-config --libs gtk+-3.0 gtk-layer-shell-0) -lm -o "$repo/.build/prefix/bin/nostromo-splash"
