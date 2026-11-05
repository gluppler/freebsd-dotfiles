#!/bin/sh
# Sourced inside the system file transaction; compose with the current ruleset.
# shellcheck disable=SC2154
sf_safe /etc/devfs.rules
if [ -f /etc/devfs.rules ]; then devfs_original=/etc/devfs.rules; else devfs_original=/dev/null; fi
cat /etc/defaults/devfs.rules "$devfs_original" >"$work/devfs-all"
awk '
    /^\[[a-zA-Z0-9_]+[[:space:]]*=[[:space:]]*[0-9]+\][[:space:]]*$/ {
        row=$0;gsub(/[\[\][:space:]]/,"",row);split(row,p,"=");print p[1],p[2]
    }
' "$work/devfs-all" >"$work/devfs-ids"
active=$(sysrc -n devfs_system_ruleset 2>/dev/null || :)
if [ "$active" = nostromo ]; then
    parent=$(awk '/^# BEGIN NOSTROMO DEVICES$/{inside=1;next}
        /^# END NOSTROMO DEVICES$/{inside=0} inside && $1=="add" && $2=="include" {print $3}' "$devfs_original")
    number=$(awk '$1=="nostromo"{print $2;n++}END{exit n!=1}' "$work/devfs-ids")
else
    if grep -Eq '^nostromo ' "$work/devfs-ids"; then
        echo 'An unmanaged nostromo devfs ruleset already exists.' >&2
        exit 1
    fi
    parent=
    if [ -n "$active" ]; then
        case $active in *[!0-9]*) parent=$(awk -v name="$active" '$1==name {print $2;n++}END{exit n!=1}' "$work/devfs-ids") ;;
        *) parent=$active ;; esac
    fi
    number=1000
    while awk -v id="$number" '$2==id{found=1}END{exit !found}' "$work/devfs-ids"; do number=$((number + 1)); done
fi
case $parent:$number in *[!0-9:]*) exit 1 ;; esac
[ "$number" -lt 65536 ] && [ "$parent" != "$number" ] || exit 1
{
    printf '[nostromo=%s]\n' "$number"
    [ -z "$parent" ] || printf 'add include %s\n' "$parent"
    cat <<'EOF'
add path 'dri/*' group video mode 0660
add path 'backlight/*' group video mode 0660
add path 'cuaU*' group dialer mode 0660
add path 'cuau*' group dialer mode 0660
add path 'acpi' group nostromo_power mode 0664
EOF
} >"$work/devfs-block"
awk -v name=DEVICES -v replacement="$work/devfs-block" -f "$repo/scripts/merge-block.awk" "$devfs_original" >"$work/devfs-candidate"
pw groupshow dialer >/dev/null
if ! id -Gn "$account" | tr ' ' '\n' | grep -Fxq dialer; then
    printf 'dialer %s\n' "$account" >>"$work/groups"
    pw groupmod dialer -m "$account"
fi
sf_put "$work/devfs-candidate" /etc/devfs.rules 644
sysrc -f "$work/rc.conf" devfs_system_ruleset=nostromo
