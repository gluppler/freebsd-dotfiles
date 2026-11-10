#!/bin/sh
# Group/world write in the checkout would let another account change what root
# later runs or installs from it. Tools can grant it whatever the umask: uv 0.12
# creates its environment locks mode 0666. The desktop account owns every path
# here (checked first), so removing that access loses nothing.
set -eu
case ${1:-} in --check | --apply) mode=$1 ;; *) exit 2 ;; esac
[ "$#" = 1 ] || exit 2
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
cd "$repo"
# A staged port keeps its package's modes: CUPS stages group-writable spool
# directories. chmod would follow a symlink, and a link's own mode grants nothing.
loose() {
    find . \( -path './.build/ports-work/*/work/stage' -o -path './.build/ports-work/*/work-*/stage' \) -prune -o \
        ! -type l \( -perm -0020 -o -perm -0002 \) "$@"
}
found=$(loose -print)
[ -n "$found" ] || exit 0
printf '%s\n' "$found" | head -n 20
if [ "$mode" = --check ]; then
    echo 'Apply removes group/world write from the paths above.'
    exit 0
fi
# The second scan names whatever chmod could not change.
loose -exec chmod go-w {} + || :
remaining=$(loose -print)
[ -z "$remaining" ] || {
    printf '%s\n' "$remaining" | head -n 20 >&2
    echo 'Group/world write remains on the paths above; check their file flags.' >&2
    exit 1
}
echo 'Removed group/world write from the paths above.'
