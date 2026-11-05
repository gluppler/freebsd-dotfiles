#!/bin/sh
# One root entry point. Sources/plugins/builds run as the selected ordinary user.
# Values in as_user's single-quoted commands expand only after switching accounts.
# shellcheck disable=SC2016
set -eu
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
export PATH
repo=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
mode=preview
case ${1:-} in --help | -h)
    printf 'Usage: %s [--preview|--check|--apply|--wifi] [gluppler]\n' "$0"
    exit 0
    ;;
--apply | --check | --wifi)
    mode=${1#--}
    shift
    ;;
--preview | --dry-run) shift ;; esac
[ "$#" -le 1 ] || {
    echo "Usage: $0 [--preview|--check|--apply|--wifi] [gluppler]" >&2
    exit 2
}
account=${1:-gluppler}
case $account in '' | root | [!a-z_]* | *[!a-z0-9_-]*)
    echo 'Use an ordinary local account name.' >&2
    exit 2
    ;;
esac
if [ "$mode" = preview ]; then
    cat <<EOF
FreeBSD 15.1-RELEASE amd64 / Wayland setup for $account:
  1. Check release, running kernel, account, permanent checkout and source files.
     Offer console Wi-Fi setup with a hidden password prompt before downloads.
  2. Bootstrap signed pkg; publish the reviewed package policy and preserve its prior version.
  3. Build the pinned native library variants as $account; audit every dependency before installation.
  4. Install the reviewed desktop/development roots and detected Intel firmware.
  5. Build patched Wayland clients, editor plugins and native language tools as $account.
  6. Check every staged binary/configuration, then transactionally install user links.
  7. Back up and merge the listed system settings; configure mdo and the native login session.
  8. Verify the final configuration before enabling SDDM at boot. Keep console login/recovery.
No partitioning, OS installation, server provisioning or automatic reboot.
See docs/BASE-SETUP.md for the separate manual installation and docs/VALIDATION.md for readiness.
Preview only. On the laptop, run --check first, then --apply from its root console.
EOF
    exit
fi
[ "$(uname -s)" = FreeBSD ] && [ "$(uname -m)" = amd64 ] && [ "$(id -u)" = 0 ] || {
    echo 'Run --check or --apply from a root console on the FreeBSD amd64 laptop.' >&2
    exit 1
}
case $(freebsd-version -u) in 15.1-RELEASE*) ;; *)
    echo 'Review this release before installing.' >&2
    exit 1
    ;;
esac
# Root cannot write through a read-only mount, including single-user boot defaults.
for path in /etc /var /usr; do
    [ -w "$path" ] || {
        echo "Read-only/unwritable $path. Finish multi-user boot; see docs/BASE-SETUP.md." >&2
        exit 1
    }
done
service devd onestatus >/dev/null 2>&1 || {
    echo 'devd is not running. Finish multi-user boot before configuring hardware or installing the desktop.' >&2
    exit 1
}
[ -z "${SSH_CONNECTION:-}${SSH_CLIENT:-}${SSH_TTY:-}" ] || {
    echo 'Run setup at the laptop console so network changes cannot disconnect this install.' >&2
    exit 1
}
if [ "$mode" = wifi ]; then
    exec sh "$repo/scripts/setup-wifi.sh"
fi
[ "$(freebsd-version -k)" = "$(freebsd-version -r)" ] || {
    echo 'Reboot into the installed kernel first.' >&2
    exit 1
}
[ -x /usr/bin/mdo ] || {
    echo 'FreeBSD base mdo is missing.' >&2
    exit 1
}
uid=$(id -u "$account")
[ "$uid" -ge 1000 ] || {
    echo 'The desktop account must have UID >= 1000.' >&2
    exit 1
}
account_home=$(pw usershow "$account" -7 | cut -d: -f6)
case $account_home in /*) ;; *) exit 1 ;; esac
account_home=$(CDPATH='' cd -- "$account_home" && pwd -P)
[ "$account_home" != / ] || exit 1
case $repo in "$account_home"/*) ;; *)
    echo 'Keep this permanent checkout inside the desktop account home.' >&2
    exit 1
    ;;
esac
# The ports framework does not support whitespace in PORTSDIR/WRKDIRPREFIX.
case $repo in *[[:space:]]* | *'|'*)
    echo 'Use a checkout path without whitespace or a vertical bar for native ports builds.' >&2
    exit 1
    ;;
esac
for script in scripts/configure-system.sh scripts/verify-stage.sh scripts/editor-plugins.sh \
    scripts/development-tools.sh scripts/build-desktop.sh scripts/link-home.sh; do
    [ -f "$repo/$script" ] || {
        echo "Incomplete checkout: $script. No system changes made." >&2
        exit 1
    }
done
sh "$repo/scripts/verify-stage.sh" --sources
as_user() {
    env -i HOME="$account_home" USER="$account" LOGNAME="$account" SHELL=/bin/sh \
        PATH="$account_home/.local/bin:$PATH" LANG=en_US.UTF-8 TERM="${TERM:-vt100}" \
        NOSTROMO_REPO="$repo" NOSTROMO_UID="$uid" NOSTROMO_COMPONENT="${component:-}" \
        NOSTROMO_COMMAND='set -eu; umask 022; cd "$NOSTROMO_REPO"; '"$1" \
        /usr/bin/su -f "$account" -c 'exec /bin/sh -c "$NOSTROMO_COMMAND"'
}
as_user '[ "$(id -u)" = "$NOSTROMO_UID" ] && [ -w "$HOME" ] && [ -w "$NOSTROMO_REPO" ];
    [ -z "$(find "$NOSTROMO_REPO" ! -user "$USER" -print -quit)" ] || {
        echo "The checkout must belong to the desktop account. Check its ownership before installing." >&2; exit 1; }
    [ -z "$(find "$NOSTROMO_REPO" \( -perm -0020 -o -perm -0002 \) -print -quit)" ] || {
        echo "The checkout has group/world-writable files. Review their permissions before installing." >&2; exit 1; }'
umask 077
for path in /var/log/nostromo /usr/local/share/nostromo; do
    parent=$path
    while [ "$parent" != / ]; do
        [ ! -L "$parent" ] || exit 1
        if [ -e "$parent" ]; then
            [ -d "$parent" ] && [ "$(stat -f '%u' "$parent")" = 0 ] || exit 1
            path_mode=$(stat -f '%Lp' "$parent")
            [ "$((0$path_mode & 0022))" = 0 ] || exit 1
        fi
        parent=${parent%/*}
        [ -n "$parent" ] || parent=/
    done
done
if [ "$mode" = check ]; then
    printf 'Preflight passed for %s on FreeBSD 15.1 amd64. No installation performed.\n' "$account"
    exit
fi
mkdir -p /var/log/nostromo
lock=/var/run/nostromo-install.lock
mkdir "$lock" || {
    echo 'Another install or an interrupted install lock exists.' >&2
    exit 1
}
log=
policy=
stage=preflight
prune_logs() {
    # Retain this run and two older diagnostic-only runs. Recovery data stays.
    for previous in /var/log/nostromo/install-????????; do
        [ -d "$previous" ] && [ ! -L "$previous" ] && [ "$previous" != "$log" ] || continue
        case ${previous##*/install-} in *[!A-Za-z0-9]*) continue ;; esac
        [ "$(stat -f '%u %Lp' "$previous")" = '0 700' ] || continue
        [ ! -e "$previous/system-backup" ] && [ ! -L "$previous/system-backup" ] || continue
        [ ! -e "$previous/policy-backup" ] && [ ! -L "$previous/policy-backup" ] || continue
        [ -f "$previous/release-before" ] && [ -f "$previous/account-before" ] || continue
        ended=no
        if [ -f "$previous/result" ] && [ ! -L "$previous/result" ]; then
            case $(cat "$previous/result") in completed | failed) ended=yes ;; esac
        else
            # Older installers have no result marker, but record stage failures.
            for status in "$previous"/*.status; do
                [ -f "$status" ] && [ ! -L "$status" ] || continue
                case $(cat "$status") in '' | *[!0-9]* | 0) ;; *) ended=yes ;; esac
            done
        fi
        [ "$ended" = yes ] || continue
        modified=$(stat -f '%m' "$previous") || return 1
        printf '%s %s\n' "$modified" "$previous" || return 1
    done >"$log/retention" || return 1
    sort -rn "$log/retention" >"$log/retention.sorted" || return 1
    kept=0
    while read -r _modified previous; do
        kept=$((kept + 1))
        [ "$kept" -le 2 ] || rm -rf "$previous" || return 1
    done <"$log/retention.sorted"
    rm -f "$log/retention" "$log/retention.sorted"
}
finish() {
    result=$?
    trap - 0
    set +e
    if [ -n "$log" ] && [ -d "$log/policy-backup" ] &&
        [ ! -e /usr/local/share/nostromo/policy ] && [ ! -L /usr/local/share/nostromo/policy ]; then
        mv "$log/policy-backup" /usr/local/share/nostromo/policy ||
            echo "Restore the package policy from $log/policy-backup before retrying." >&2
    fi
    [ -z "$policy" ] || rm -rf "$policy"
    if [ -n "$log" ]; then
        printf '%s\n' "$stage" >"$log/last-stage"
        printf '%s\n' "$result" >"$log/exit-status"
        if [ "$result" = 0 ]; then outcome=completed; else outcome=failed; fi
        printf '%s\n' "$outcome" >"$log/result"
        prune_logs || echo "Log cleanup was incomplete; review $log." >&2
    fi
    if [ "$result" != 0 ] && [ -n "$log" ]; then
        printf 'Setup stopped at %s (exit %s). Logs: %s\n' "$stage" "$result" "$log" >&2
        echo 'No reboot was requested. Resolve the reported stage and rerun the same command.' >&2
    fi
    rmdir "$lock"
    exit "$result"
}
trap finish 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
log=$(mktemp -d /var/log/nostromo/install-XXXXXXXX)
run() {
    stage=$1
    shift
    printf '%s — log: %s/%s.log\n' "$stage" "$log" "$stage"
    (
        set +e
        "$@"
        printf '%s\n' "$?" >"$log/$stage.status"
    ) 2>&1 | tee "$log/$stage.log"
    result=$(cat "$log/$stage.status")
    [ "$result" = 0 ] || exit "$result"
}
freebsd-version -kru >"$log/release-before"
id "$account" >"$log/account-before"
# Prompts bypass tee/logging; the password is read only from the console.
stage=wifi-setup
sh "$repo/scripts/setup-wifi.sh" --offer
# Base pkg bootstrap verifies FreeBSD's repository signature. No doas/sudo bootstrap.
run pkg-bootstrap env -i HOME=/root PATH="$PATH" /usr/sbin/pkg bootstrap -y
pkg -v >"$log/pkg-version"
stage=package-policy
install -d -m 755 /usr/local/share/nostromo /usr/local/libexec
policy=$(mktemp -d /usr/local/share/nostromo/.policy.XXXXXXXX)
mkdir "$policy/scripts" "$policy/system" "$policy/src" "$policy/src/ports"
for file in packages.allowed packages.local packages.txt ports.lock sources.lock; do install -m 644 "$repo/$file" "$policy/$file"; done
for file in package-policy.awk ports-variants.sh recipe-hash.sh fetch-source.sh; do install -m 644 "$repo/scripts/$file" "$policy/scripts/$file"; done
install -m 644 "$repo/system/ports.conf" "$policy/system/ports.conf"
for file in "$repo"/src/ports/*.patch; do install -m 644 "$file" "$policy/src/ports/"; done
sh "$repo/scripts/recipe-hash.sh" >"$policy/recipe.sha256"
printf 'Nostromo managed package policy\n' >"$policy/managed"
chmod 755 "$policy" "$policy/scripts" "$policy/system" "$policy/src" "$policy/src/ports"
chmod 644 "$policy/recipe.sha256" "$policy/managed"
if [ -e /usr/local/share/nostromo/policy ]; then
    [ ! -L /usr/local/share/nostromo/policy ] &&
        [ "$(cat /usr/local/share/nostromo/policy/managed)" = 'Nostromo managed package policy' ] || exit 1
    unsafe_policy=$(find /usr/local/share/nostromo/policy \( ! -user root -o -type l -o -perm -0020 -o -perm -0002 \) -print -quit)
    [ -z "$unsafe_policy" ] || {
        echo 'Unsafe installed package policy ownership, permissions or symlinks; review it before retrying.' >&2
        exit 1
    }
    if cmp -s "$policy/recipe.sha256" /usr/local/share/nostromo/policy/recipe.sha256; then
        for history in previous-recipe.sha256 accepted-recipes; do
            [ ! -f "/usr/local/share/nostromo/policy/$history" ] ||
                install -m 644 "/usr/local/share/nostromo/policy/$history" "$policy/$history"
        done
    else
        install -m 644 /usr/local/share/nostromo/policy/recipe.sha256 "$policy/previous-recipe.sha256"
        {
            for history in recipe.sha256 previous-recipe.sha256 accepted-recipes; do
                [ ! -f "/usr/local/share/nostromo/policy/$history" ] || cat "/usr/local/share/nostromo/policy/$history"
            done
        } | sort -u >"$policy/accepted-recipes"
        chmod 644 "$policy/accepted-recipes"
    fi
    if [ -f /usr/local/share/nostromo/policy/local-libraries ]; then
        install -m 644 /usr/local/share/nostromo/policy/local-libraries "$policy/local-libraries"
    fi
    comparison=0
    diff -r /usr/local/share/nostromo/policy "$policy" >/dev/null || comparison=$?
    case $comparison in
    0) rm -rf "$policy" ;;
    1) mv /usr/local/share/nostromo/policy "$log/policy-backup" ;;
    *) exit "$comparison" ;;
    esac
fi
if [ -d "$policy" ]; then
    mv "$policy" /usr/local/share/nostromo/policy || {
        [ ! -d "$log/policy-backup" ] || mv "$log/policy-backup" /usr/local/share/nostromo/policy
        exit 1
    }
fi
policy=
install -m 755 "$repo/scripts/packages.sh" /usr/local/libexec/nostromo-packages
packages=/usr/local/libexec/nostromo-packages
run prepare-ports as_user 'sh scripts/ports-variants.sh prepare'
while IFS='|' read -r component _origin version; do
    case $component in '' | '#'*) continue ;; esac
    run "$component-dependency-list" as_user 'sh scripts/ports-variants.sh deps "$NOSTROMO_COMPONENT" > .build/variant-deps'
    set --
    while IFS= read -r dependency; do
        case $dependency in '' | [!A-Za-z0-9]* | *[!A-Za-z0-9_+.-]*) exit 1 ;; esac
        set -- "$@" "$dependency"
    done <"$repo/.build/variant-deps"
    [ "$#" = 0 ] || run "$component-dependencies" "$packages" install --build "$@"
    run "$component-build" as_user 'sh scripts/ports-variants.sh build "$NOSTROMO_COMPONENT"'
    run "$component-import" "$packages" import "$component" "$repo/.build/ports-packages/All/$component-$version.pkg"
    if pkg info -e "$component"; then operation=reinstall; else operation=install; fi
    run "$component-install" "$packages" "$operation" --build "$component"
done <"$repo/packages.local"
set --
while IFS= read -r name; do
    case $name in '' | '#'*) continue ;; esac
    set -- "$@" "$name"
done <"$repo/packages.txt"
run desktop-packages "$packages" install "$@"
run embedded-build-tools "$packages" install --build gperf
run finish-bootstrap "$packages" finish-bootstrap
# fwget is detection only: its own pkg install would bypass the policy gate.
/usr/sbin/fwget -nq >"$log/firmware-request"
set -- drm-612-kmod
while IFS= read -r name; do
    case $name in '' | *[!A-Za-z0-9_+.-]*) exit 1 ;; esac
    set -- "$@" "$name"
done <"$log/firmware-request"
run firmware "$packages" install "$@"
run desktop-build as_user 'sh scripts/build-desktop.sh'
run editor-plugins as_user 'sh scripts/editor-plugins.sh'
run development-tools as_user 'sh scripts/development-tools.sh'
run pcb-workflow as_user 'sh scripts/setup-eda.sh'
run staged-validation as_user 'sh scripts/verify-stage.sh'
run user-files as_user 'sh scripts/link-home.sh --apply'
run system-configuration sh "$repo/scripts/configure-system.sh" "$account" "$log"
run login-shell pw usermod "$account" -s /usr/local/bin/oksh
# Activation is last; the current console/desktop stays running until user reboot.
run enable-login sysrc sddm_enable=YES
printf 'Setup completed for %s. Logs: %s\nReboot when ready; keep console recovery available.\n' "$account" "$log"
