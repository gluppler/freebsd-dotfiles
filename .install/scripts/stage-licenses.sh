#!/bin/sh
set -eu
[ "$#" = 3 ] || exit 2
component=$1
source=$2
prefix=$3
case $component in '' | *[!a-z0-9-]*) exit 2 ;; esac
destination=$prefix/share/licenses/$component
mkdir -p "$destination"
found=no
for file in "$source"/LICENSE* "$source"/COPYING* "$source"/LICENCE*; do
    [ -f "$file" ] || continue
    install -m 644 "$file" "$destination/${file##*/}"
    found=yes
done
[ "$found" = yes ] || {
    printf 'Missing upstream license: %s\n' "$component" >&2
    exit 1
}
