#!/bin/sh
# Console bootstrap uses the same connection helper as the desktop menu.
set -eu
set +x
umask 077
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
LC_ALL=C
export PATH LC_ALL
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" = 0 ] || exit 1
[ "$#" = 0 ] || { [ "$#" = 1 ] && [ "$1" = --offer ]; } || exit 2
# The first file pkg reads from its repository. fetch resolves names over UDP as pkg
# does; getent hosts cannot stand in, because sethostent(1) sends its queries over
# TCP, which many home routers refuse.
reachable() { fetch -q -T 15 -o /dev/null https://pkg.FreeBSD.org/FreeBSD:15:amd64/quarterly/meta.conf 2>/dev/null; }
exec 3<>/dev/tty
if [ "${1:-}" = --offer ]; then
    echo 'Checking the connection to pkg.FreeBSD.org...'
    offline=no
    if reachable; then
        via=$(route -n get default 2>/dev/null | awk '$1=="interface:" {print $2}')
        echo "pkg.FreeBSD.org is reachable${via:+ through $via}."
    else
        echo 'pkg.FreeBSD.org is not reachable.'
        offline=yes
    fi
    printf 'Configure a Wi-Fi connection now? [y/N] ' >&3
    IFS= read -r answer <&3 || exit 1
    case $answer in y | Y | yes | YES) ;; *)
        # Without the package server, a clean install would remove packages it cannot reinstall.
        [ "$offline" = no ] || {
            echo 'Connect a cable or set up Wi-Fi, then rerun.' >&2
            exit 1
        }
        exit 0
        ;;
    esac
fi
[ -w /etc ] && [ -w /var/run ] || {
    echo 'Finish booting into multi-user mode with writable filesystems first. See BASE-SETUP.md.' >&2
    exit 1
}
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
# shellcheck source=.install/scripts/system-files.sh
. "$repo/.install/scripts/system-files.sh"
work=/var/run/nostromo-wifi-setup.lock
sf_safe "$work"
mkdir "$work" || {
    echo 'Console Wi-Fi setup is already running.' >&2
    exit 1
}
terminal='' backup='' interface='' previous_country='' previous_domain=''
committed=no created=no regulatory_changed=no supplicant_changed=no was_up=no was_running=no live_changed=no
finish() {
    result=$?
    trap - 0
    [ -z "$terminal" ] || stty "$terminal" <&3
    unset secret
    if [ "$result" != 0 ] && [ "$committed" = no ]; then
        [ -z "$backup" ] || sf_rollback || :
        if [ "$created" = yes ]; then
            service wpa_supplicant onestop "$interface" >/dev/null 2>&1 || :
            ifconfig "$interface" destroy || :
        elif [ "$live_changed" = yes ]; then
            if [ "$regulatory_changed" = yes ]; then
                ifconfig "$interface" down || :
                ifconfig "$interface" regdomain "$previous_domain" country "$previous_country" || :
            fi
            # A connection this run never touched keeps running undisturbed.
            if [ "$supplicant_changed" = yes ] || [ "$regulatory_changed" = yes ]; then
                if [ "$was_running" = yes ]; then
                    service wpa_supplicant onerestart "$interface" || :
                else service wpa_supplicant onestop "$interface" >/dev/null 2>&1 || :; fi
            fi
            if [ "$was_up" = yes ]; then ifconfig "$interface" up || :; else ifconfig "$interface" down || :; fi
        fi
        [ -z "$backup" ] || printf 'Wi-Fi setup stopped. Configuration backups: %s\n' "$backup" >&2
    fi
    rm -f "$work/rc.conf" "$work/wpa.conf" "$work/wpa.conf.new"
    rmdir "$work"
    exit "$result"
}
trap finish 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
radios=$(sysctl -n net.wlan.devices)
[ -n "$radios" ] || {
    echo 'No wireless radio detected. Check if_iwlwifi and firmware; use wired bootstrap if necessary.' >&2
    exit 1
}
printf 'Detected radios: %s\nRadio to configure: ' "$radios" >&3
IFS= read -r radio <&3 || exit 1
case $radio in '' | *[!a-zA-Z0-9]*) exit 2 ;; esac
printf '%s\n' "$radios" | tr ' ' '\n' | grep -Fxq -e "$radio" || exit 2
interface=
for candidate in $(ifconfig -g wlan); do
    parent=$(ifconfig "$candidate" | awk '$1=="parent" && $2=="interface:" {print $3}')
    [ "$parent" != "$radio" ] || {
        interface=$candidate
        break
    }
done
if [ -z "$interface" ]; then
    number=0
    while ifconfig "wlan$number" >/dev/null 2>&1; do number=$((number + 1)); done
    interface=wlan$number
fi
sf_safe /etc/rc.conf
file=$(sysrc -n wpa_supplicant_conf_file)
case $file in /etc/*) ;; *)
    echo 'Review the custom WPA path outside /etc first.' >&2
    exit 1
    ;;
esac
sf_safe "$file"
if [ -e "$file" ]; then
    [ -f "$file" ] && [ "$(stat -f '%u %Lp' "$file")" = '0 600' ] || {
        echo 'Existing WPA configuration must be root-owned with mode 600.' >&2
        exit 1
    }
fi
sf_directory 700 /var/backups/nostromo
sf_begin "/var/backups/nostromo/wifi-$(date +%Y%m%d-%H%M%S)-$$"
backup=$sf_backup
if ! ifconfig "$interface" >/dev/null 2>&1; then
    ifconfig "$interface" create wlandev "$radio"
    created=yes
fi
state=$(ifconfig "$interface")
printf '%s\n' "$state" | grep -Eq '^[^:]+: flags=.*[<,]UP[,>]' && was_up=yes
service wpa_supplicant onestatus "$interface" >/dev/null 2>&1 && was_running=yes
previous_country=$(printf '%s\n' "$state" | awk '{for(i=1;i<NF;i++) if($i=="country") print $(i+1)}')
previous_domain=$(printf '%s\n' "$state" | awk '{for(i=1;i<NF;i++) if($i=="regdomain") print $(i+1)}')
printf 'Using %s. Current regulatory settings:\n' "$interface" >&3
ifconfig "$interface" list regdomain >&3
printf 'Country code (for example MY; Enter keeps current): ' >&3
IFS= read -r country <&3 || exit 1
case $country in '') ;; [A-Z][A-Z])
    args=$(sysrc -n "create_args_$interface" 2>/dev/null || :)
    case " $args " in *' country '* | *' regdomain '*)
        echo 'Persistent regulatory settings already exist; rerun and keep them, or review them manually.' >&2
        exit 1
        ;;
    esac
    case $previous_country:$previous_domain in *[!A-Za-z0-9_:.-]* | :* | *:)
        echo 'Cannot save current regulatory settings; keep the current country for now.' >&2
        exit 1
        ;;
    esac
    live_changed=yes regulatory_changed=yes
    ifconfig "$interface" down
    ifconfig "$interface" country "$country"
    ;;
*) exit 2 ;;
esac
live_changed=yes
ifconfig "$interface" up
ifconfig "$interface" list scan >&3 || :
helper=$repo/system/nostromo-wifi
offered='wpa2 wpa3 open owe'
if [ "$was_running" = yes ]; then
    # A running supplicant shows the current network and what it can use, before any secret.
    sh "$helper" status "$interface" 2>/dev/null | awk -F= '
        $1 == "ssid" {name = substr($0, 6)} $1 == "key_mgmt" {security = $2} $1 == "wpa_state" {state = $2}
        END {if (state == "COMPLETED") printf "Connected to %s with %s.\n", name, security}' >&3
    available=$(sh "$helper" modes "$interface" 2>/dev/null | paste -sd ' ' -)
    [ -z "$available" ] || offered=$available
fi
printf 'Network name (SSID): ' >&3
IFS= read -r name <&3 || exit 1
[ -n "$name" ] && [ "${#name}" -le 32 ] || exit 2
case $name in *[[:cntrl:]]*) exit 2 ;; esac
ssid=$(printf '%s' "$name" | od -An -v -tx1 | tr -d ' \n')
if [ -f "$file" ] && awk -v ssid="$ssid" -v mode=find -f "$repo/.install/scripts/forget-network.awk" "$file"; then
    echo 'This network has a saved profile; the new settings replace it once they connect.' >&3
fi
missing=
for option in wpa2 wpa3 open owe; do
    case " $offered " in *" $option "*) ;; *) missing="$missing $option" ;; esac
done
[ -z "$missing" ] || printf 'Not available with this Wi-Fi driver and supplicant:%s.\n' "$missing" >&3
printf 'Security [%s; default wpa2]: ' "$(printf '%s' "$offered" | tr ' ' /)" >&3
IFS= read -r security <&3 || exit 1
security=${security:-wpa2}
case $security in wpa2 | wpa3 | open | owe) ;; *) exit 2 ;; esac
case " $offered " in *" $security "*) ;; *)
    echo "$security is not available with this Wi-Fi driver and supplicant." >&2
    exit 1
    ;;
esac
secret=
if [ "$security" = wpa2 ] || [ "$security" = wpa3 ]; then
    terminal=$(stty -g <&3)
    stty -echo <&3
    printf 'Wi-Fi password (hidden): ' >&3
    IFS= read -r secret <&3 || exit 1
    stty "$terminal" <&3
    terminal=
    printf '\n' >&3
fi
[ ! -f /etc/rc.conf ] || cp /etc/rc.conf "$work/rc.conf"
[ -f "$work/rc.conf" ] || : >"$work/rc.conf"
# sysrc edits only these keys; other interface/address settings remain intact.
sysrc -f "$work/rc.conf" "wlans_$radio+=$interface" >/dev/null
address=$(sysrc -n "ifconfig_$interface" 2>/dev/null || :)
if [ -z "$address" ]; then address='WPA DHCP'; fi
case " $address " in *' WPA '*) ;; *) address="WPA $address" ;; esac
sysrc -f "$work/rc.conf" "ifconfig_$interface=$address" >/dev/null
if [ -n "$country" ]; then
    sysrc -f "$work/rc.conf" "create_args_$interface=$args country $country" >/dev/null
fi
case $radio in iwlwifi[0-9]*) sysrc -f "$work/rc.conf" 'kld_list+=if_iwlwifi' >/dev/null ;; esac
if [ -f "$file" ]; then cp "$file" "$work/wpa.conf"; else : >"$work/wpa.conf"; fi
if ! grep -Eq '^[[:space:]]*ctrl_interface=' "$work/wpa.conf"; then
    {
        printf 'ctrl_interface=/var/run/wpa_supplicant\n'
        cat "$work/wpa.conf"
    } >"$work/wpa.conf.new"
    mv "$work/wpa.conf.new" "$work/wpa.conf"
fi
mode=644
[ ! -f /etc/rc.conf ] || mode=$(stat -f '%Lp' /etc/rc.conf)
sf_put "$work/rc.conf" /etc/rc.conf "$mode"
sf_put "$work/wpa.conf" "$file" 600
# A later rc.conf.local assignment must not silently defeat persistence.
effective=$(sysrc -n "wlans_$radio")
if ! printf '%s\n' "$effective" | tr ' \t' '\n' | grep -Fxq -e "$interface" ||
    [ "$(sysrc -n "ifconfig_$interface")" != "$address" ]; then
    echo 'Another rc configuration overrides this interface. Review it before retrying.' >&2
    exit 1
fi
if [ -n "$country" ] && [ "$(sysrc -n "create_args_$interface")" != "$args country $country" ]; then
    echo 'Another rc configuration overrides the country setting. Review it before retrying.' >&2
    exit 1
fi
# A supplicant usually already serves the interface, and rc.subr refuses to start a
# second one; restarting also loads the control socket setting added above.
supplicant_changed=yes
if service wpa_supplicant onestatus "$interface" >/dev/null 2>&1; then
    service wpa_supplicant onerestart "$interface"
else
    service wpa_supplicant onestart "$interface"
fi
# The root-only helper accepts the checkout's awk programs before anything is installed.
printf '%s\n%s\n%s\n' "$ssid" "$security" "$secret" |
    NOSTROMO_WIFI_SHARE="$repo/.install/scripts" sh "$helper" connect "$interface"
unset secret
committed=yes
printf 'Wi-Fi profile saved. Checking pkg.FreeBSD.org before installing packages.\n'
netstat -rn
reachable || {
    echo 'The Wi-Fi profile is saved, but pkg.FreeBSD.org is not reachable. Check DHCP/DNS before continuing.' >&2
    exit 1
}
