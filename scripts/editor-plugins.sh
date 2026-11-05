#!/bin/sh
# Stage the pinned Lua dependencies during installation as the ordinary account.
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
mkdir -p "$repo/.build/editor" "$repo/.build/work"
work=$(mktemp -d "$repo/.build/work/editor.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/scripts/fetch-source.sh" vis-lspc "$work/vis-lspc"
fetch -o "$work/dkjson.lua" https://dkolf.de/dkjson-lua/dkjson-2.11.lua
[ "$(sha256 -q "$work/dkjson.lua")" = 197cb50834c642f84b4cf99fe724932c50e6d9c92faec7ad89aa25e91df4d481 ] || exit 1
# Preserve local edits in an existing plugin tree.
destination=$repo/.build/editor/vis-lspc
if [ -e "$destination" ]; then
    if [ -L "$destination" ] || ! diff -qr "$work/vis-lspc" "$destination"; then
        echo 'Staged vis-lspc differs; preserve it before replacing the plugin.' >&2
        exit 1
    fi
else mv "$work/vis-lspc" "$destination"; fi
if [ -e "$repo/.build/editor/dkjson.lua" ]; then
    cmp -s "$work/dkjson.lua" "$repo/.build/editor/dkjson.lua" || exit 1
else install -m 644 "$work/dkjson.lua" "$repo/.build/editor/dkjson.lua"; fi
sh "$repo/scripts/stage-licenses.sh" vis-lspc "$destination" "$repo/.build/prefix"
# dkjson carries its MIT license in the source file itself.
mkdir -p "$repo/.build/prefix/share/licenses/dkjson"
install -m 644 "$work/dkjson.lua" "$repo/.build/prefix/share/licenses/dkjson/dkjson.lua"
