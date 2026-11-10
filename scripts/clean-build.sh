#!/bin/sh
# Remove leftovers as the checkout owner: build workspaces and partial downloads
# from an earlier boot, old desktop build logs, superseded variant archives and
# user-file backups.
set -eu
LC_ALL=C
export LC_ALL
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
[ "$(id -u)" != 0 ] || {
    echo 'Clean the checkout as its ordinary owner.' >&2
    exit 1
}
build=$repo/.build
boot=$(sysctl -n kern.boottime | sed -n 's/^{ sec = \([0-9][0-9]*\),.*/\1/p')
[ -n "$boot" ] || exit 1
# Exit handlers remove these unless SIGKILL or power loss stopped the build. The
# software menu can build ports at any time, so only an earlier boot's copies go.
for stale in "$build"/work/*.???????? "$build"/validation.???????? "$build"/ports.???????? \
    "$build"/downloads/.download.????????; do
    # mktemp makes directories here, except for partial downloads.
    case $stale in */.download.*) [ -f "$stale" ] ;; *) [ -d "$stale" ] ;; esac && [ ! -L "$stale" ] || continue
    [ "$(stat -f %B "$stale")" -lt "$boot" ] || continue
    # Staged ports can leave read-only directories; chmod -R follows no symlinks.
    chmod -R u+w "$stale"
    rm -rf "$stale"
    printf 'Removed a stale build workspace: %s\n' "$stale"
done
# Keep the three newest desktop build logs; their names sort by start time.
set -- "$build"/logs/[0-9]*-[0-9]*-[0-9]*
[ -e "$1" ] || set --
while [ "$#" -gt 3 ]; do
    if [ -d "$1" ] && [ ! -L "$1" ]; then
        rm -rf "$1"
        printf 'Removed an old desktop build log: %s\n' "$1"
    fi
    shift
done
# The installer imports each variant's current name-version archive only.
for archive in "$build"/ports-packages/All/*.pkg; do
    [ -f "$archive" ] && [ ! -L "$archive" ] || continue
    awk -F '|' -v file="${archive##*/}" '!/^#/ && NF==3 && $1 "-" $3 ".pkg"==file {found=1} END {exit !found}' \
        "$repo/packages.local" && continue
    rm -f "$archive"
    printf 'Removed a superseded variant archive: %s\n' "$archive"
done
# The link stage restores from these only when it fails itself.
backups=$HOME/.local/state/freebsd-dotfiles/backups
if [ -d "$backups" ] && [ ! -L "$backups" ]; then
    rm -rf "$backups"
    printf 'Removed user-file backups: %s\n' "$backups"
fi
