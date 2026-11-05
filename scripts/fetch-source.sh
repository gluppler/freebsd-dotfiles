#!/bin/sh
# Fetch one pinned archive into a fresh build directory. Never run as root.
set -eu
[ "$(id -u)" != 0 ] || {
    echo 'Fetch/build sources as the ordinary account.' >&2
    exit 1
}
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
[ "$#" = 2 ] || {
    echo 'Usage: fetch-source.sh name new-destination' >&2
    exit 2
}
name=$1 destination=$2
case $name in '' | *[!a-z0-9-]*) exit 2 ;; esac
case $destination in /*) ;; *)
    echo 'Destination must be absolute.' >&2
    exit 2
    ;;
esac
[ ! -e "$destination" ] && [ ! -L "$destination" ] || {
    echo 'Build destination already exists.' >&2
    exit 1
}
record=$(awk -F '|' -v name="$name" '$1 == name {print; n++} END {if (n != 1) exit 1}' "$repo/sources.lock")
IFS='|' read -r component archive_root expected url <<EOF
$record
EOF
case $component:$archive_root:$expected:$url in *' '* | *'	'*)
    echo 'Invalid source record.' >&2
    exit 1
    ;;
esac
case $url in https://*) ;; *) exit 1 ;; esac
cache=$repo/.build/downloads
mkdir -p "$cache"
archive=$cache/$name.tar.gz
hash() {
    if command -v sha256 >/dev/null 2>&1; then
        sha256 -q "$1"
    else shasum -a 256 "$1" | awk '{print $1}'; fi
}
part=
work=
cleanup() {
    [ -z "$part" ] || rm -f "$part"
    [ -z "$work" ] || rm -rf "$work"
}
trap cleanup 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
if [ ! -f "$archive" ] || [ "$(hash "$archive")" != "$expected" ]; then
    part=$(mktemp "$cache/.download.XXXXXXXX")
    if command -v fetch >/dev/null 2>&1; then
        fetch -o "$part" "$url"
    else curl --fail --location --proto '=https' --tlsv1.2 -o "$part" "$url"; fi
    [ "$(hash "$part")" = "$expected" ] || {
        echo "Checksum mismatch: $name" >&2
        exit 1
    }
    mv "$part" "$archive"
    part=
fi
# libarchive extraction also protects against paths through symlinks. Confine all
# archive members to the recorded top-level directory before extracting.
work=$(mktemp -d "${TMPDIR:-/tmp}/nostromo-source.XXXXXXXX")
tar -tf "$archive" >"$work/members"
awk -v root="$archive_root" -v component="$component" '
    component=="cppreference" && /^cppreference-doxygen-(local|web)\.tag\.xml$/ {next}
    $0 != root && $0 != root "/" && index($0, root "/") != 1 {bad=1}
    /(^|\/)\.\.(\/|$)/ || /^\// {bad=1}
    END {exit bad || NR == 0}
' "$work/members" || {
    echo 'Unsafe archive member.' >&2
    exit 1
}
mkdir "$work/tree"
tar -xf "$archive" -C "$work/tree" "$archive_root/"
mkdir -p "$(dirname -- "$destination")"
mv "$work/tree/$archive_root" "$destination"
