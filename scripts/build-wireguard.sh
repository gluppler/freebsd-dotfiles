#!/bin/sh
# Build wg only: no wg-quick, Bash, GNU make or userspace tunnel implementation.
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin" "$repo/.build/prefix/share/licenses/wireguard" "$repo/.build/prefix/share/man/man8"
work=$(mktemp -d "$repo/.build/work/wireguard.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/scripts/fetch-source.sh" wireguard "$work/src"
cd "$work/src/src"
/usr/bin/clang -std=gnu99 -O2 -Wall -Wextra -Wno-unused-parameter \
    -DRUNSTATEDIR='"/var/run"' -Iuapi/freebsd ./*.c -lnv -o wg
install -m 755 wg "$repo/.build/prefix/bin/wg"
install -m 644 man/wg.8 "$repo/.build/prefix/share/man/man8/wg.8"
install -m 644 ../COPYING "$repo/.build/prefix/share/licenses/wireguard/COPYING"
