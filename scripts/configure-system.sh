#!/bin/sh
# Root-only file transaction. Package/user stages have already passed.
set -eu
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
export PATH
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" = 0 ] && [ "$#" = 2 ] || exit 1
account=$1 log=$2
case $account in '' | root | [!a-z_]* | *[!a-z0-9_-]*) exit 2 ;; esac
uid=$(id -u "$account")
[ "$uid" -ge 1000 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
# shellcheck source=scripts/system-files.sh
. "$repo/scripts/system-files.sh"
sf_safe "$log" && [ -d "$log" ] || exit 1
umask 077
sf_begin "$log/system-backup"
work=$(mktemp -d /var/tmp/nostromo-system.XXXXXXXX)
mdo_before='' mdo_enabled='' mdo_changed=no power_group_created=no power_gid=''
finish() {
    result=$?
    trap - 0
    if [ "$result" != 0 ]; then
        sf_rollback || echo "Review recovery journal: $sf_backup/journal" >&2
        if [ "$mdo_changed" = yes ]; then
            if [ "$(sysctl -n security.mac.do.rules)" = "$expected" ]; then
                sysctl "security.mac.do.rules=$mdo_before" >/dev/null || :
            fi
            if [ "$(sysctl -n security.mac.do.enabled)" = 1 ]; then
                sysctl "security.mac.do.enabled=$mdo_enabled" >/dev/null || :
            fi
        fi
        # Only remove memberships introduced by this transaction.
        if [ -f "$work/groups" ]; then
            while IFS=' ' read -r group member; do pw groupmod "$group" -d "$member" || :; done <"$work/groups"
        fi
        if [ "$power_group_created" = yes ] &&
            [ "$(pw groupshow nostromo_power | cut -d: -f3,4)" = "$power_gid:" ]; then
            pw groupdel nostromo_power || :
        fi
        if [ -f "$work/acpi-before" ]; then
            while IFS='=' read -r key value; do
                [ "$(sysctl -n "$key")" != NONE ] || sysctl "$key=$value" >/dev/null || :
            done <"$work/acpi-before"
        fi
    fi
    rm -rf "$work"
    exit "$result"
}
trap finish 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sf_directory 755 /usr/local/etc/nostromo
sf_directory 700 /usr/local/etc/nostromo/wireguard
sf_directory 755 /usr/local/libexec
for name in session sddm-session performance wifi wireguard bluetooth maintenance device suspend lock-session; do
    sf_put "$repo/system/nostromo-$name" "/usr/local/libexec/nostromo-$name" 755
done
sf_put "$repo/.build/prefix/bin/wg" /usr/local/libexec/nostromo-wg 755
for name in nostromo_mdo nostromo_performance nostromo_wireguard; do
    sf_put "$repo/system/rc.d/$name" "/usr/local/etc/rc.d/$name" 755
done
for helper in merge-mdo merge-block ssid-hex; do
    sf_put "$repo/scripts/$helper.awk" "/usr/local/share/nostromo/$helper.awk" 644
done
# This group grants only ACPI device access, never operator's disk access.
if ! pw groupshow nostromo_power >/dev/null 2>&1; then
    pw groupadd nostromo_power
    power_group_created=yes
else
    sf_safe /usr/local/etc/nostromo/power-group
    [ -f /usr/local/etc/nostromo/power-group ] &&
        [ "$(cat /usr/local/etc/nostromo/power-group)" = "$(pw groupshow nostromo_power | cut -d: -f3)" ] || {
        echo 'An unmanaged nostromo_power group exists; choose its policy explicitly before installing.' >&2
        exit 1
    }
fi
power_gid=$(pw groupshow nostromo_power | cut -d: -f3)
case $power_gid in '' | *[!0-9]*) exit 1 ;; esac
[ "$power_gid" -ge 1000 ] && [ -z "$(pw groupshow nostromo_power | cut -d: -f4)" ] || {
    echo 'nostromo_power must be a dedicated group with no permanent members.' >&2
    exit 1
}
printf '%s\n' "$power_gid" >"$work/power-group"
sf_put "$work/power-group" /usr/local/etc/nostromo/power-group 644
# ABI receipt is produced by the ordinary user's native ldd checks, then validated.
awk 'NF!=1 || $1 !~ /^lib[A-Za-z0-9_+.-]+\.so\.[0-9.]+$/ {bad=1} END{exit bad || NR==0}' "$repo/.build/local-libraries"
sf_put "$repo/.build/local-libraries" /usr/local/share/nostromo/policy/local-libraries 644
printf '%s %s\n' "$uid" "$account" >"$work/mdo-account"
sf_put "$work/mdo-account" /usr/local/etc/nostromo/mdo-account 600
sf_put "$repo/system/nostromo-ac.conf" /usr/local/etc/devd/nostromo-ac.conf 644
sf_put "$repo/system/nostromo-suspend.conf" /usr/local/etc/devd/nostromo-suspend.conf 644
sf_put "$repo/system/pam.d/gtklock" /usr/local/etc/pam.d/gtklock 644
for module in fido fingerprint; do
    sf_put "$repo/system/pam.d/optional/$module" "/usr/local/share/nostromo/pam-examples/$module" 644
done
# Fonts must be readable by the unprivileged SDDM greeter, outside the user's home.
for font in "$repo"/assets/fonts/*; do
    [ -f "$font" ] || continue
    sf_put "$font" "/usr/local/share/fonts/nostromo/${font##*/}" 644
done
sf_put "$repo/assets/nostromo-orb.png" /usr/local/share/nostromo/nostromo-orb.png 644
sf_put "$repo/assets/loader-orb.png" /boot/images/nostromo-orb.png 644
sf_put "$repo/system/loader/gfx-nostromo.lua" /boot/lua/gfx-nostromo.lua 644
for file in "$repo"/system/sddm/theme/*; do
    sf_put "$file" "/usr/local/share/sddm/themes/nostromo/${file##*/}" 644
done
sf_safe /usr/local/etc/sddm.conf
if [ -f /usr/local/etc/sddm.conf ]; then
    original=/usr/local/etc/sddm.conf
    mode=$(stat -f '%Lp' "$original")
else
    original=/dev/null
    mode=644
fi
# SDDM's final config overrides its drop-ins; merge only our explicit keys here.
awk -f "$repo/scripts/merge-ini.awk" "$repo/system/sddm/nostromo.conf" "$original" >"$work/sddm.conf"
sf_put "$work/sddm.conf" /usr/local/etc/sddm.conf "$mode"
sf_put "$repo/system/wayland-sessions/nostromo.desktop" /usr/local/share/nostromo/wayland-sessions/nostromo.desktop 644
sf_directory 755 /usr/local/share/nostromo/empty-sessions
# Keep the package's PAM login/greeter stacks. Require native runtime-dir support.
grep -Eq '^[[:space:]]*session[[:space:]].*pam_xdg\.so' /etc/pam.d/system || {
    echo 'Base PAM session lacks pam_xdg.so; review the local PAM policy before enabling Wayland.' >&2
    exit 1
}
grep -Eq '^[[:space:]]*session[[:space:]].*pam_xdg\.so' /usr/local/etc/pam.d/sddm-greeter || exit 1
grep -Eq '^[[:space:]]*auth[[:space:]]+include[[:space:]]+login' /usr/local/etc/pam.d/sddm || exit 1
for member in "$account" sddm; do
    pw usershow "$member" >/dev/null
    pw groupshow video >/dev/null
    if ! id -Gn "$member" | tr ' ' '\n' | grep -Fxq video; then
        printf 'video %s\n' "$member" >>"$work/groups"
        pw groupmod video -m "$member"
    fi
done
if ! id -Gn "$account" | tr ' ' '\n' | grep -Fxq wheel; then
    printf 'wheel %s\n' "$account" >>"$work/groups"
    pw groupmod wheel -m "$account"
fi
merge_settings() {
    destination=$1 replacements=$2 mode=$3
    sf_safe "$destination" || return 1
    if [ -f "$destination" ]; then
        original=$destination
        mode=$(stat -f '%Lp' "$destination")
    else original=/dev/null; fi
    awk -f "$repo/scripts/merge-settings.awk" "$replacements" "$original" >"$work/merged"
    sf_put "$work/merged" "$destination" "$mode"
}
cat >"$work/loader" <<'EOF'
mac_do_load="YES"
coretemp_load="YES"
acpi_video_load="YES"
loader_logo="nostromo"
loader_color="NO"
EOF
merge_settings /boot/loader.conf "$work/loader" 644
cat >"$work/sysctl" <<'EOF'
kern.evdev.rcpt_mask=12
EOF
# A tunable is persisted only if the running kernel implements it.
sysctl -n kern.evdev.rcpt_mask >/dev/null
merge_settings /etc/sysctl.conf "$work/sysctl" 644
sf_safe /etc/rc.conf
if [ -f /etc/rc.conf ]; then cp /etc/rc.conf "$work/rc.conf"; else : >"$work/rc.conf"; fi
sysrc -f "$work/rc.conf" hostname=nostromo dbus_enable=YES seatd_enable=YES devd_enable=YES \
    nostromo_mdo_enable=YES nostromo_performance_enable=YES kld_list+=i915kms
# shellcheck source=scripts/configure-devices.sh
. "$repo/scripts/configure-devices.sh"
# Hardware events must reach the session's lock handshake before requesting S3.
: >"$work/acpi"
for key in hw.acpi.lid_switch_state hw.acpi.sleep_button_state; do
    if before=$(sysctl -n "$key" 2>/dev/null); then
        printf '%s=%s\n' "$key" "$before" >>"$work/acpi-before"
        printf '%s=NONE\n' "$key" >>"$work/acpi"
        sysctl "$key=NONE" >/dev/null
    fi
done
merge_settings /etc/sysctl.conf "$work/acpi" 644
if sysctl -aN | grep -Eq '^dev\.hwpstate_intel\.[0-9]+\.epp$'; then
    sysrc -f "$work/rc.conf" powerd_enable=NO
elif sysctl -n dev.cpu.0.freq_levels >/dev/null 2>&1; then
    sysrc -f "$work/rc.conf" powerd_enable=YES 'powerd_flags=-a hiadaptive -b adaptive'
else
    echo 'No supported HWP/cpufreq driver found; keep the native CPU policy.' >&2
    sysrc -f "$work/rc.conf" nostromo_performance_enable=NO
fi
sh -n "$work/rc.conf"
# SSH/PF change only their listed settings/anchor and use native syntax checks.
# shellcheck source=scripts/configure-security.sh
. "$repo/scripts/configure-security.sh"
mode=644
[ ! -f /etc/rc.conf ] || mode=$(stat -f '%Lp' /etc/rc.conf)
sf_put "$work/rc.conf" /etc/rc.conf "$mode"
# Shared memory for clients uses anonymous descriptors; no global filesystem mount.
fc-cache -f /usr/local/share/fonts/nostromo
kldstat -q -m mac_do || kldload mac_do
mdo_before=$(sysctl -n security.mac.do.rules)
mdo_enabled=$(sysctl -n security.mac.do.enabled)
expected=$(printf '%s\n' "$mdo_before" | awk -v uid="$uid" -v gid="$power_gid" -f "$repo/scripts/merge-mdo.awk")
mdo_changed=yes
service nostromo_mdo onestart
[ "$(sysctl -n security.mac.do.rules)" = "$expected" ] || exit 1
# Validate as a fresh login account (including the newly added groups) while the
# root file transaction can still roll back. Single quotes defer expansion to su.
account_home=$(pw usershow "$account" -7 | cut -d: -f6)
# shellcheck disable=SC2016
env -i HOME="$account_home" USER="$account" LOGNAME="$account" PATH="$PATH" \
    LANG=en_US.UTF-8 NOSTROMO_REPO="$repo" /usr/bin/su -f "$account" \
    -c 'exec /bin/sh "$NOSTROMO_REPO/scripts/verify-stage.sh" --installed'
# Do not start/restart SDDM, networking, SSH or PF in this file transaction.
printf 'System files configured. Recovery journal: %s/journal\n' "$sf_backup"
