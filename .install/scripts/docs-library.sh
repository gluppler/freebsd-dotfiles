#!/bin/sh
# Install the pinned offline reference library as the desktop user: the doc-*
# records of sources.lock, archives through fetch-source.sh, and single documents
# and directories taken from larger archives by their SHA256. Only the checked
# documents are kept, not their archives.
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
export PATH=/usr/local/bin:/usr/local/sbin:/bin:/usr/bin:/sbin:/usr/sbin
# Some hosts leave an intermediate certificate out of their chain. libfetch reads
# these for every download here, fetch-source.sh's included; roots stay the base's.
export SSL_CA_CERT_FILE="$repo/.install/intermediates.crt" SSL_CA_CERT_PATH=/etc/ssl/certs
docs=$repo/.build/docs
library=$docs/library
for dir in "$repo/.build" "$docs" "$library"; do
    [ ! -L "$dir" ] || exit 1
    mkdir -p "$dir"
done
work=
trap '[ -z "$work" ] || rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
work=$(mktemp -d "$docs/.library.XXXXXXXX")
awk -F '|' '$1 ~ /^doc-/' "$repo/.install/sources.lock" >"$work/records"
[ -s "$work/records" ] || exit 1
: >"$work/items"
while IFS='|' read -r name root expected url; do
    item=${name#doc-}
    # Ranges such as a-z also match other letters in UTF-8 locales.
    case $item in '' | *[!abcdefghijklmnopqrstuvwxyz0123456789-]*) exit 1 ;; esac
    case $expected in *[!0123456789abcdef]*) exit 1 ;; esac
    [ "${#expected}" = 64 ] || exit 1
    case $url in https://*) ;; *) exit 1 ;; esac
    printf '%s\n' "$item" >>"$work/items"
    case $root in
    *.pdf | *.PDF)
        file=$library/$item.pdf
        [ ! -L "$file" ] || exit 1
        [ ! -f "$file" ] || [ "$(sha256 -q "$file")" != "$expected" ] || continue
        fetch -o "$work/download" "$url" </dev/null
        [ "$(sha256 -q "$work/download")" = "$expected" ] || {
            echo "Checksum mismatch: $name" >&2
            exit 1
        }
        rm -rf "$file"
        mv "$work/download" "$file"
        ;;
    *)
        tree=$library/$item marker=$library/.$item.sha256
        [ ! -L "$tree" ] && [ ! -L "$marker" ] || exit 1
        if [ -d "$tree" ] && [ -f "$marker" ] && [ "$(cat "$marker")" = "$expected" ]; then continue; fi
        case $root in
        */*)
            # One directory of a larger archive, such as a program's bundled
            # manual; nothing else is extracted.
            case $root in /* | -* | *..*) exit 1 ;; esac
            fetch -o "$work/download" "$url" </dev/null
            [ "$(sha256 -q "$work/download")" = "$expected" ] || {
                echo "Checksum mismatch: $name" >&2
                exit 1
            }
            mkdir "$work/archive"
            tar -xf "$work/download" -C "$work/archive" "$root"
            [ -d "$work/archive/$root" ] && [ ! -L "$work/archive/$root" ] || exit 1
            mv "$work/archive/$root" "$work/$item"
            rm -rf "$work/archive" "$work/download"
            ;;
        *)
            sh "$repo/.install/scripts/fetch-source.sh" "$name" "$work/$item" </dev/null
            rm -f "$repo/.build/downloads/$name.tar.gz"
            ;;
        esac
        # Documents are read, never run: refuse special files and links that
        # leave their own tree.
        real=$(realpath "$work/$item")
        if [ -n "$(find "$work/$item" ! -type f ! -type d ! -type l -print | head -n 1)" ] ||
            ! find "$work/$item" -type l -exec sh -c '
                for link; do
                    target=$(realpath "$link") || exit 1
                    case $target in "$0" | "$0"/*) ;; *) exit 1 ;; esac
                done' "$real" {} +; then
            echo "Unsafe link or special file in $name." >&2
            exit 1
        fi
        rm -rf "$tree" "$marker"
        mv "$work/$item" "$tree"
        printf '%s\n' "$expected" >"$marker"
        ;;
    esac
done <"$work/records"
# Items that are no longer pinned go too.
for path in "$library"/* "$library"/.*.sha256; do
    [ -e "$path" ] || [ -L "$path" ] || continue
    entry=${path##*/}
    entry=${entry#.}
    entry=${entry%.sha256}
    entry=${entry%.pdf}
    grep -Fxq -e "$entry" "$work/items" && continue
    rm -rf "$path"
    printf 'Removed an unpinned library item: %s\n' "$path"
done
