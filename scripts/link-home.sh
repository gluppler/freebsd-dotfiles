#!/bin/sh
# Link only files owned by this project; preserve every replaced destination.
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
target=$HOME
apply=no
while [ "$#" -gt 0 ]; do
    case $1 in
    --apply) apply=yes ;;
    --dry-run) apply=no ;;
    --target)
        shift
        target=${1:?--target needs an existing directory}
        ;;
    *)
        echo "Usage: $0 [--dry-run|--apply] [--target directory]" >&2
        exit 2
        ;;
    esac
    shift
done
[ -d "$target" ] || {
    echo "Target must already exist: $target" >&2
    exit 1
}
target=$(CDPATH='' cd -- "$target" && pwd -P)
[ "$target" != / ] || {
    echo 'Refusing to install into /' >&2
    exit 1
}
if [ "$apply" = yes ] && [ "$(id -u)" = 0 ]; then
    echo 'Run the user installer as your regular account.' >&2
    exit 1
fi

# A linked parent could redirect writes outside the chosen home directory.
check_parent() {
    parent=$(dirname -- "$1")
    while [ "$parent" != "$target" ]; do
        if [ -L "$parent" ] || { [ -e "$parent" ] && [ ! -d "$parent" ]; }; then
            echo "Parent is not a plain directory: $parent" >&2
            exit 1
        fi
        parent=$(dirname -- "$parent")
    done
}

valid_path() {
    case $1 in
    '' | /* | . | .. | ./* | ../* | */../* | */.. | */./* | */. | *'|'*)
        echo "Invalid manifest path: $1" >&2
        exit 1
        ;;
    esac
}

while IFS='|' read -r source destination; do
    case $source in '' | '#'*) continue ;; esac
    valid_path "$source"
    valid_path "$destination"
    [ -e "$repo/$source" ] || {
        echo "Missing $source; complete the build stages through install.sh first." >&2
        exit 1
    }
    check_parent "$target/$destination"
done <"$repo/links.txt"
# A duplicate or overlapping destination could invalidate the rollback journal.
awk -F '|' '
    /^#/ || NF == 0 {next}
    NF != 2 {bad=1}
    {
        if ($2 in seen) bad=1
        for (path in seen)
            if (index(path, $2 "/") == 1 || index($2, path "/") == 1) bad=1
        seen[$2]=1
    }
    END {exit bad}
' "$repo/links.txt" || {
    echo 'Duplicate, overlapping or malformed link destinations.' >&2
    exit 1
}
check_parent "$target/.local/state/freebsd-dotfiles/backups/check"

backup=$target/.local/state/freebsd-dotfiles/backups/$(date +%Y%m%d-%H%M%S)-$$
finish() {
    status=$?
    trap - 0
    if [ "$status" != 0 ] && [ -f "$backup/changed" ]; then
        # Reverse order supports future manifests that replace a whole subtree.
        awk '{line[NR]=$0} END {for(i=NR;i>0;i--) print line[i]}' "$backup/changed" |
            while IFS='|' read -r source destination; do
                to=$target/$destination
                if [ -L "$to" ] && [ "$(readlink "$to")" = "$repo/$source" ]; then
                    rm "$to"
                elif [ -e "$to" ] || [ -L "$to" ]; then
                    printf 'Recovery preserved a subsequently changed file: %s\n' "$to" >&2
                    continue
                fi
                if [ -e "$backup/$destination" ] || [ -L "$backup/$destination" ]; then
                    mv -- "$backup/$destination" "$to"
                fi
            done
        printf 'User file stage rolled back. Journal: %s/changed\n' "$backup" >&2
    fi
    exit "$status"
}
trap finish 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
while IFS='|' read -r source destination; do
    case $source in '' | '#'*) continue ;; esac
    from=$repo/$source
    to=$target/$destination
    if [ -L "$to" ] && [ "$(readlink "$to")" = "$from" ]; then
        printf 'Already linked: %s\n' "$destination"
        continue
    fi
    printf 'Link: %s -> %s\n' "$to" "$from"
    if [ -e "$to" ] || [ -L "$to" ]; then
        printf 'Back up: %s -> %s\n' "$to" "$backup/$destination"
    fi
    [ "$apply" = yes ] || continue
    mkdir -p "$(dirname -- "$to")"
    (
        umask 077
        mkdir -p "$backup"
    )
    printf '%s|%s\n' "$source" "$destination" >>"$backup/changed"
    if [ -e "$to" ] || [ -L "$to" ]; then
        (
            umask 077
            mkdir -p "$(dirname -- "$backup/$destination")"
        )
        mv -- "$to" "$backup/$destination"
    fi
    ln -s -- "$from" "$to"
done <"$repo/links.txt"
if [ "$apply" = no ]; then
    echo 'Preview only. Use --apply to install.'
else
    echo 'User files installed. Keep this checkout in place.'
fi
