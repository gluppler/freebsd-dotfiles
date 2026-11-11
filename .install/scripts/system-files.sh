#!/bin/sh
# Sourced by root provisioning: atomic files, backups, conditional rollback.
# No trap here: the caller also restores live service/sysctl state on failure.
sf_begin() {
    sf_backup=$1
    sf_safe "$sf_backup" || return 1
    # A backup must be new; never truncate an earlier recovery journal.
    mkdir -m 700 "$sf_backup" || return 1
    sf_number=0
    : >"$sf_backup/journal"
}
sf_safe() {
    case $1 in /*) ;; *) return 1 ;; esac
    case $1 in *'|'* | *[[:cntrl:]]* | */../* | */./* | */.. | */.) return 1 ;; esac
    sf_check=$1
    while [ "$sf_check" != / ]; do
        [ ! -L "$sf_check" ] || {
            echo "Refusing a symlink: $sf_check" >&2
            return 1
        }
        if [ -e "$sf_check" ]; then
            [ "$(stat -f '%u' "$sf_check")" = 0 ] || return 1
            sf_permissions=$(stat -f '%Lp' "$sf_check")
            [ "$((0$sf_permissions & 0022))" = 0 ] || {
                echo "Group/world-writable system path: $sf_check" >&2
                return 1
            }
        fi
        sf_check=${sf_check%/*}
        [ -n "$sf_check" ] || sf_check=/
    done
}
sf_directory() {
    sf_safe "$2" || return 1
    if [ -e "$2" ]; then
        [ -d "$2" ]
        return
    fi
    # Parent creation uses mode 755. Callers create private parents first with 700.
    sf_parents "${2%/*}" || return 1
    install -d -o root -g wheel -m "$1" "$2"
}
sf_parents() {
    [ ! -d "$1" ] || return 0
    sf_parents "${1%/*}" || return 1
    install -d -o root -g wheel -m 755 "$1"
}
sf_put() {
    sf_source=$1 sf_destination=$2 sf_mode=$3
    sf_safe "$sf_destination" || return 1
    [ ! -e "$sf_destination" ] || [ -f "$sf_destination" ] || return 1
    if [ -f "$sf_destination" ] && cmp -s "$sf_source" "$sf_destination" &&
        [ "$(stat -f '%Lp' "$sf_destination")" = "$sf_mode" ]; then return; fi
    sf_directory 755 "${sf_destination%/*}" || return 1
    sf_number=$((sf_number + 1))
    sf_existed=no
    if [ -f "$sf_destination" ]; then
        cp -p "$sf_destination" "$sf_backup/$sf_number.before" || return 1
        sf_existed=yes
    fi
    sf_temporary=$(mktemp "${sf_destination}.nostromo.XXXXXXXX") || return 1
    if ! install -o root -g wheel -m "$sf_mode" "$sf_source" "$sf_temporary"; then
        rm -f "$sf_temporary"
        return 1
    fi
    sf_digest=$(sha256 -q "$sf_temporary") || {
        rm -f "$sf_temporary"
        return 1
    }
    # Journal before rename; recovery checks the expected installed digest/mode.
    printf '%s|%s|%s|%s|%s\n' "$sf_number" "$sf_destination" "$sf_mode" "$sf_digest" "$sf_existed" >>"$sf_backup/journal"
    mv "$sf_temporary" "$sf_destination" || {
        rm -f "$sf_temporary"
        return 1
    }
}
sf_rollback() {
    awk '{row[NR]=$0} END{for(i=NR;i>0;i--) print row[i]}' "$sf_backup/journal" >"$sf_backup/reverse"
    while IFS='|' read -r sf_index sf_path sf_mode sf_digest sf_existed; do
        if [ -L "$sf_path" ] || [ ! -f "$sf_path" ] ||
            [ "$(sha256 -q "$sf_path")" != "$sf_digest" ] || [ "$(stat -f '%u %Lp' "$sf_path")" != "0 $sf_mode" ]; then
            printf 'Preserved a subsequent change at %s; backup is in %s\n' "$sf_path" "$sf_backup" >&2
            continue
        fi
        if [ "$sf_existed" = yes ]; then
            sf_temporary=$(mktemp "${sf_path}.restore.XXXXXXXX") || return 1
            cp -p "$sf_backup/$sf_index.before" "$sf_temporary" && mv "$sf_temporary" "$sf_path" || return 1
        else rm -f "$sf_path" || return 1; fi
    done <"$sf_backup/reverse"
}
