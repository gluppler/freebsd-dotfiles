# POSIX functions shared by the three unprivileged native panel managers.
# Never send a password or PIN to these result/row helpers.
network_notice() {
    printf '%s\n' "$2" | LC_ALL=C awk '{gsub(/[[:cntrl:]]/, " "); print}' |
        nostromo-picker -p "$1" -l 8 >/dev/null || :
}
network_choice() {
    [ -n "$2" ] || {
        network_notice "$1" 'No entries available.'
        return 1
    }
    network_index=$(printf '%s\n' "$2" | LC_ALL=C awk '{gsub(/[[:cntrl:]]/, " "); print}' |
        nostromo-picker --index -p "$1") || return 1
    case $network_index in '' | *[!0-9]*) return 2 ;; esac
    # Use the index into the original rows, never parse an untrusted display label.
    printf '%s\n' "$2" | awk -v n="$network_index" 'NR==n+1 {print; found=1} END {exit !found}'
}
network_capture() {
    network_title=$1
    shift
    if network_result=$("$@" 2>&1); then
        printf '%s\n' "$network_result"
    else
        network_notice "$network_title failed" "$network_result"
        return 1
    fi
}
network_run() {
    network_title=$1
    shift
    if network_result=$("$@" 2>&1); then
        network_notice "$network_title" "${network_result:-Request accepted. Check STATUS for the current state.}"
    else
        network_notice "$network_title failed" "$network_result"
    fi
}
network_busy() {
    command -v notify-send >/dev/null 2>&1 || return 0
    notify-send -a "$1" -t 3000 "$1" 'Working…' >/dev/null 2>&1 || :
}
