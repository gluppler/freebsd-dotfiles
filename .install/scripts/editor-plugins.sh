#!/bin/sh
# Stage the pinned Lua dependencies during installation as the ordinary account.
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
mkdir -p "$repo/.build/editor" "$repo/.build/work"
work=$(mktemp -d "$repo/.build/work/editor.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" vis-lspc "$work/vis-lspc"
fetch -o "$work/dkjson.lua" https://dkolf.de/dkjson-lua/dkjson-2.11.lua
[ "$(sha256 -q "$work/dkjson.lua")" = 197cb50834c642f84b4cf99fe724932c50e6d9c92faec7ad89aa25e91df4d481 ] || {
    echo 'Checksum mismatch: dkjson' >&2
    exit 1
}
# Receipts identify an unedited earlier pin, which a new pin replaces. Local
# edits are preserved: the stage stops instead.
destination=$repo/.build/editor/vis-lspc
receipt=$repo/.build/editor/vis-lspc.mtree
library=$repo/.build/editor/dkjson.lua
library_receipt=$repo/.build/editor/dkjson.sha256
# Native mtree exits 0 for missing and extra files, so any report is an edit.
unedited() {
    [ -f "$receipt" ] || return 1
    report=$(mtree -f "$receipt" -p "$destination") && [ -z "$report" ] && return
    [ -z "$report" ] || printf '%s\n' "$report"
    return 1
}
if [ -L "$destination" ] || { [ -e "$destination" ] && [ ! -d "$destination" ]; }; then
    echo 'Staged vis-lspc is not a plain directory; preserve it, then rerun.' >&2
    exit 1
fi
if [ ! -e "$destination" ]; then
    mv "$work/vis-lspc" "$destination"
elif ! diff -qr "$work/vis-lspc" "$destination" >/dev/null; then
    unedited || {
        echo 'Staged vis-lspc has local changes: preserve them, then rerun.' >&2
        exit 1
    }
    echo 'Replacing the unedited vis-lspc plugin with its new pin.'
    mv "$destination" "$work/previous"
    mv "$work/vis-lspc" "$destination"
fi
mtree -c -k type,link,sha256digest -p "$destination" >"$work/vis-lspc.mtree"
mv "$work/vis-lspc.mtree" "$receipt"
if [ -L "$library" ] || { [ -e "$library" ] && [ ! -f "$library" ]; }; then
    echo 'Staged dkjson.lua is not a plain file; preserve it, then rerun.' >&2
    exit 1
fi
if [ ! -e "$library" ] || ! cmp -s "$work/dkjson.lua" "$library"; then
    if [ -e "$library" ]; then
        [ -f "$library_receipt" ] && [ "$(sha256 -q "$library")" = "$(cat "$library_receipt")" ] || {
            echo 'Staged dkjson.lua has local changes: preserve them, then rerun.' >&2
            exit 1
        }
        echo 'Replacing the unedited dkjson.lua with its new pin.'
    fi
    install -m 644 "$work/dkjson.lua" "$library"
fi
sha256 -q "$library" >"$work/dkjson.sha256"
mv "$work/dkjson.sha256" "$library_receipt"
sh "$repo/.install/scripts/stage-licenses.sh" vis-lspc "$destination" "$repo/.build/prefix"
# dkjson carries its MIT license in the source file itself.
mkdir -p "$repo/.build/prefix/share/licenses/dkjson"
install -m 644 "$work/dkjson.lua" "$repo/.build/prefix/share/licenses/dkjson/dkjson.lua"
