#!/bin/sh
# Validate staged binaries and configuration on FreeBSD.
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
mode=${1:---stage}
case $mode in --sources | --stage | --installed) ;; *) exit 2 ;; esac
[ "$#" -le 1 ] || exit 2
for script in configure-system configure-security configure-devices setup-wifi editor-plugins development-tools docs-library build-desktop link-home clean-build checkout-modes; do
    [ -s "$repo/.install/scripts/$script.sh" ] || {
        echo "Missing implementation: $script" >&2
        exit 1
    }
    sh -n "$repo/.install/scripts/$script.sh"
done
for file in .install/scripts/merge-mdo.awk .install/scripts/merge-block.awk .install/scripts/ssid-hex.awk .install/scripts/forget-network.awk \
    system/nostromo-suspend system/nostromo-lock-session system/nostromo-suspend.conf; do
    [ -s "$repo/$file" ] || {
        echo "Missing system install source: $file" >&2
        exit 1
    }
done
for helper in nostromo-admin nostromo-menu nostromo-software nostromo-crt nostromo-profile nostromo-lock \
    nostromo-wifi nostromo-vpn nostromo-bluetooth nostromo-display nostromo-output-change nostromo-docs; do
    [ -x "$repo/bin/$helper" ] || {
        echo "Missing executable helper: $helper" >&2
        exit 1
    }
done
while IFS='|' read -r source destination; do
    case $source in '' | '#'*) continue ;; .build/*) [ "$mode" != --sources ] || continue ;; esac
    [ -e "$repo/$source" ] || {
        echo "Missing install source: $source" >&2
        exit 1
    }
    if [ "$mode" = --installed ]; then
        [ -L "$HOME/$destination" ] && [ "$(realpath "$HOME/$destination")" = "$(realpath "$repo/$source")" ] || {
            echo "Missing/changed user link: $destination" >&2
            exit 1
        }
    fi
done <"$repo/.install/links.txt"
[ "$mode" != --sources ] || exit 0
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
prefix=$repo/.build/prefix
PATH=$prefix/bin:$repo/bin:/usr/local/bin:/usr/local/sbin:/bin:/usr/bin:/sbin:/usr/sbin
export PATH
umask 077
work=$(mktemp -d "$repo/.build/validation.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
: >"$work/local-libraries"
for binary in dwl dwlb foot dvtm dvtm-editor gtklock fuzzel dunst nnn wg nostromo-output-watch nostromo-splash nostromo-control nostromo-secret-copy nostromo-terminal-idle tpass tcli tclig rustup efm-langserver; do
    file=$prefix/bin/$binary
    [ -x "$file" ] || {
        echo "Missing compiled program: $binary" >&2
        exit 1
    }
    file -b "$file" | grep -q ELF || {
        echo "Not a native executable: $binary" >&2
        exit 1
    }
    if [ "$binary" = efm-langserver ]; then continue; fi # Static Go binary.
    ldd "$file" >"$work/ldd"
    if grep -q 'not found' "$work/ldd"; then
        cat "$work/ldd" >&2
        exit 1
    fi
    awk '$2=="=>" && $3 ~ /^\/usr\/local\// {print $1}' "$work/ldd" >>"$work/local-libraries"
done
sort -u "$work/local-libraries" >"$repo/.build/local-libraries"
for tool in vise vis-menu oksh foot qutebrowser fcitx5 uv rustc cargo rustfmt cargo-clippy \
    rust-analyzer go gofmt gopls python3 ruff asm-lsp shellcheck shfmt cmake ninja dbus-run-session \
    seatd cage sddm swayidle swaybg wlr-randr wl-copy wl-paste grim slurp zathura mpv; do
    command -v "$tool" >/dev/null || {
        echo "Missing runtime tool: $tool" >&2
        exit 1
    }
done
for tool in clangd clang-format clang-tidy lldb llvm-mc llvm-objdump; do nostromo-tool --path "$tool"; done
foot --check-config --config="$repo/foot/foot.ini"
fuzzel --check-config --config="$repo/fuzzel/fuzzel.ini"
fastfetch --config "$repo/fastfetch/config.jsonc" --gen-config "$work/fastfetch.jsonc" >/dev/null
oksh -n "$repo/oksh/okshrc"
"$repo/.build/python-lsp/bin/python" -c 'import pylsp, pylsp_ruff, cattrs, lsprotocol'
"$repo/.build/embedded-python/bin/west" --version
"$repo/.build/embedded-python/bin/python" -c 'import yaml, jsonschema, pykwalify, elftools, serial, intelhex, esptool'
test -s "$repo/.build/editor/vis-lspc/init.lua"
test -s "$repo/.build/editor/dkjson.lua"
# Its Go queries keep their cache and usage counters in this workspace.
NOSTROMO_DOCS_ROOT="$repo/docs/reference" NOSTROMO_CPPREFERENCE_ROOT="$repo/.build/docs/cppreference-20250209" \
    NOSTROMO_LIBRARY_ROOT="$repo/.build/docs/library" MANPATH="$prefix/share/man:" \
    XDG_CACHE_HOME="$work/cache" XDG_CONFIG_HOME="$work/config" nostromo-docs --check
if [ "$mode" = --installed ]; then
    if /usr/bin/mdo -i -u root -- /usr/bin/id -u >/dev/null 2>&1 ||
        /usr/bin/mdo -u root -- /usr/bin/id -u >/dev/null 2>&1; then
        echo 'An existing mdo rule still grants this account root; review that policy.' >&2
        exit 1
    fi
    [ "$(/usr/bin/mdo -k -g nostromo_power -- /usr/bin/id -u)" = "$(id -u)" ]
    [ "$(/usr/bin/mdo -k -g nostromo_power -- /usr/bin/id -gn)" = nostromo_power ]
    for group in wheel video dialer; do id -Gn | tr ' ' '\n' | grep -Fxq "$group"; done
    for helper in merge-mdo merge-block ssid-hex forget-network; do
        file=/usr/local/share/nostromo/$helper.awk
        [ -f "$file" ] && [ ! -L "$file" ] && [ "$(stat -f '%u %Lp' "$file")" = '0 644' ]
        cmp -s "$repo/.install/scripts/$helper.awk" "$file"
    done
    for helper in suspend lock-session; do
        file=/usr/local/libexec/nostromo-$helper
        [ -f "$file" ] && [ ! -L "$file" ] && [ "$(stat -f '%u %Lp' "$file")" = '0 755' ]
        cmp -s "$repo/system/nostromo-$helper" "$file"
    done
    cmp -s "$repo/system/nostromo-suspend.conf" /usr/local/etc/devd/nostromo-suspend.conf
    # Every instance of the variable Azeret Mono reports "Azeret Mono,Azeret Mono Thin".
    for family in Michroma 'Azeret Mono'; do
        fc-match -f '%{family}\n' "$family" | tr ',' '\n' | grep -Fxq "$family" || {
            echo "Fontconfig does not resolve $family to the installed font." >&2
            exit 1
        }
    done
    nostromo-dev health
fi
printf 'Native stage checks passed; login, rendering and hardware acceptance still require the laptop session.\n'
