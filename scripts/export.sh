#!/bin/sh
# Export tracked and new source files, without build caches or private settings.
set -eu
LC_ALL=C
export LC_ALL
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
[ "$#" = 0 ] || {
    echo 'Usage: sh scripts/export.sh' >&2
    exit 2
}
[ "$(id -u)" != 0 ] || {
    echo 'Export as the ordinary account.' >&2
    exit 1
}
[ "$(git -C "$repo" rev-parse --show-toplevel)" = "$repo" ] || exit 1
cd "$repo"
umask 077
[ ! -L .dist ] || exit 1
mkdir -p .dist
work=$(mktemp -d "$repo/.dist/.export.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
git -c core.quotePath=false ls-files --cached --others --exclude-standard >"$work/unsorted"
sort -u "$work/unsorted" >"$work/files"

while IFS= read -r file; do
    case $file in
    '' | /* | *[!A-Za-z0-9_./+-]* | ../* | */../* | */..)
        echo 'Export contains an unsupported filename.' >&2
        exit 1
        ;;
    .gitattributes | .gitignore | README.md | PLANS.md | COPYING.md | install.sh | \
        links.txt | packages.txt | packages.allowed | packages.local | ports.lock | sources.lock | \
        home/* | system/* | src/* | scripts/* | tests/* | docs/* | assets/* | LICENSES/*) ;;
    *)
        echo "Unexpected export path: $file" >&2
        exit 1
        ;;
    esac
    # Check even tracked files: .gitignore does not remove them from an index.
    case $file in
    */.env | */.env.* | */.ssh/* | */.gnupg/* | */.password-store/* | \
        *.pem | *.key | *.p12 | *.pfx | *.kdbx | */id_rsa* | */id_ecdsa* | */id_ed25519* | \
        home/*.local | home/*/local.lua | */.DS_Store | */._* | */__pycache__/* | \
        */.build/* | */.dist/* | docs/assets/* | *.svg | *.pyc | *.o | *.core | *.log | *.swp | *.swo | *~)
        echo "Private or generated file in export: $file" >&2
        exit 1
        ;;
    esac
    [ -f "$file" ] && [ ! -L "$file" ] || {
        echo "Export requires a regular source file: $file" >&2
        exit 1
    }
    parent=${file%/*}
    if [ "$parent" != "$file" ]; then
        while [ "$parent" != . ]; do
            [ ! -L "$parent" ] || {
                echo "Symlinked export directory: $parent" >&2
                exit 1
            }
            case $parent in */*) parent=${parent%/*} ;; *) parent=. ;; esac
        done
    fi
    mode=$(stat -f '%Lp' "$file")
    [ "$((0$mode & 06022))" = 0 ] || {
        echo "Unsafe source permissions: $file" >&2
        exit 1
    }
    case $file in *.png | *.gif | *.ttf) continue ;; esac
    awk '
        /-----BEGIN ([A-Z0-9]+ )*PRIVATE KEY( BLOCK)?-----/ ||
        /(^|[^A-Za-z0-9_])(ghp_|github_pat_)[A-Za-z0-9_]{20,}/ ||
        /(^|[^A-Za-z0-9])(AKIA|ASIA)[A-Z0-9]{16}([^A-Za-z0-9]|$)/ ||
        /xox[baprs]-[A-Za-z0-9-]{20,}/ ||
        /[?&](access_token|api_key|api_token|client_secret|password|token)=[A-Za-z0-9_-]{16,}/ ||
        /^[[:space:]]*(PrivateKey|PresharedKey)[[:space:]]*=[[:space:]]*[A-Za-z0-9+\/]{43}=/ ||
        /https?:\/\/[^\/@[:space:]]+:[^\/@[:space:]]+@/ ||
        /\/(Users|private\/var)\// {bad=1}
        END {exit bad}
    ' "$file" || {
        echo "Review possible credentials or a private host path in: $file" >&2
        exit 1
    }
done <"$work/files"

COPYFILE_DISABLE=1 tar --format=ustar --no-xattrs --no-acls --no-fflags \
    --no-mac-metadata --uid 0 --gid 0 --uname root --gname wheel --no-recursion \
    -cf "$work/source.tar" -s ',^,freebsd-dotfiles/,' -T "$work/files"
mkdir "$work/unpacked"
tar -xf "$work/source.tar" -C "$work/unpacked"
sh "$work/unpacked/freebsd-dotfiles/scripts/verify-stage.sh" --sources
sh "$work/unpacked/freebsd-dotfiles/install.sh" --preview >/dev/null
gzip -n -c "$work/source.tar" >"$work/source.tar.gz"
if command -v sha256 >/dev/null 2>&1; then
    digest=$(sha256 -q "$work/source.tar.gz")
else
    digest=$(shasum -a 256 "$work/source.tar.gz" | awk '{print $1}')
fi
name=freebsd-dotfiles-$(date +%Y%m%d-%H%M%S)-${work##*.export.}.tar.gz
printf 'SHA256 (%s) = %s\n' "$name" "$digest" >"$work/SHA256"
chmod 644 "$work/source.tar.gz" "$work/SHA256" "$work/files"
mv "$work/source.tar.gz" "$repo/.dist/$name"
mv "$work/SHA256" "$repo/.dist/$name.sha256"
mv "$work/files" "$repo/.dist/$name.files"
printf 'Source archive: %s/.dist/%s\nSHA256: %s\n' "$repo" "$name" "$digest"
