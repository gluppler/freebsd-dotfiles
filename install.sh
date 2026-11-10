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
    printf 'Usage: %s [--preview|--check|--apply|--wifi] [account]\n' "$0"
    echo 'Check and apply need the desktop account; none is built in.'
    exit 0
    ;;
--apply | --check | --wifi)
    mode=${1#--}
    shift
    ;;
--preview | --dry-run) shift ;; esac
[ "$#" -le 1 ] || {
    echo "Usage: $0 [--preview|--check|--apply|--wifi] [account]" >&2
    exit 2
}
account=${1:-}
case $mode:$account in check: | apply:)
    echo "Name the desktop account: $0 --$mode account" >&2
    exit 2
    ;;
esac
# Spelled out: in en_US.UTF-8, sh ranges follow collation and a-z matches A and é.
case $account in root | [!_abcdefghijklmnopqrstuvwxyz]* | *[!_abcdefghijklmnopqrstuvwxyz0123456789-]*)
    echo 'Use an ordinary local account name.' >&2
    exit 2
    ;;
esac
if [ "$mode" = preview ]; then
    who=${account:-the desktop account}
    cat <<EOF
FreeBSD 15.1-RELEASE amd64 / Wayland setup for $who:
  1. Check release, running kernel, account, permanent checkout and source files.
     Remove what earlier runs left: stale locks, workspaces, logs and backups.
     Offer console Wi-Fi setup with a hidden password prompt before downloads.
     Offer a clean install: remove every earlier package (stock Git too), the
     package state and build output, then build and install everything again.
  2. Bootstrap signed pkg; publish the reviewed package policy and preserve its prior version.
  3. Build the pinned native library variants as $who; audit every dependency before installation.
  4. Install the reviewed desktop/development roots and detected Intel firmware.
  5. Build patched Wayland clients, editor plugins and native language tools as $who.
  6. Check every staged binary/configuration, then transactionally install user links.
  7. Back up and merge the listed system settings; configure mdo and the native login session.
  8. Verify the final configuration before enabling SDDM at boot. Keep console login/recovery.
  9. Check the installed system again, remove every backup, then ask before rebooting into the desktop.
No partitioning, OS installation or server provisioning.
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
    scripts/development-tools.sh scripts/build-desktop.sh scripts/link-home.sh scripts/clean-build.sh \
    scripts/checkout-modes.sh; do
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
as_user '{ [ "$(id -u)" = "$NOSTROMO_UID" ] && [ -w "$HOME" ] && [ -w "$NOSTROMO_REPO" ]; } || {
        echo "The desktop account must be able to write its home and the checkout." >&2; exit 1; }
    foreign=$(find . ! -user "$USER")
    [ -z "$foreign" ] || {
        printf "%s\n" "$foreign" | head -n 20 >&2
        echo "The checkout must belong to the desktop account. Check the ownership of the paths above before installing." >&2; exit 1; }'
# Check lists what apply removes: group/world write that tools left in the checkout.
as_user "sh scripts/checkout-modes.sh --$mode"
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
boot=$(sysctl -n kern.boottime | sed -n 's/^{ sec = \([0-9][0-9]*\),.*/\1/p')
# Boot cleanup keeps directories in /var/run, and SIGKILL or power loss skips the
# exit trap. A lock from an earlier boot is stale unless its recorded owner runs.
stale_lock() {
    [ -d "$1" ] && [ ! -L "$1" ] && [ -n "$boot" ] || return 1
    birth=$(stat -f %B "$1") && [ "$birth" -lt "$boot" ] || return 1
    owner=$(cat "$1/pid" 2>/dev/null) || return 0
    case $owner in '' | *[!0-9]*) return 0 ;; esac
    ! kill -0 "$owner" 2>/dev/null
}
if ! mkdir "$lock" 2>/dev/null; then
    if ! { stale_lock "$lock" && rm -f "$lock/pid" && rmdir "$lock" && mkdir "$lock"; }; then
        printf 'Another install holds %s. If none is running, reboot or remove that directory.\n' "$lock" >&2
        exit 1
    fi
    echo 'Removed the lock of an install interrupted before the last boot.'
fi
printf '%s\n' "$$" >"$lock/pid"
log=
policy=
stage=preflight
prune_logs() {
    # The lock is held, so every other run has ended, including one that power
    # loss left without a result. Keep only this run's logs. A run's backups
    # serve its own rollback, so they go with its logs.
    for previous in /var/log/nostromo/install-????????; do
        [ -d "$previous" ] && [ ! -L "$previous" ] && [ "$previous" != "$log" ] || continue
        case ${previous##*/install-} in *[!A-Za-z0-9]*) continue ;; esac
        if [ "$(stat -f '%u %Lp' "$previous")" != '0 700' ] ||
            [ ! -f "$previous/release-before" ] || [ ! -f "$previous/account-before" ]; then
            printf 'Retained unrecognized or unsafe log directory: %s\n' "$previous"
        else
            rm -rf "$previous" || return 1
            printf 'Removed old install log: %s\n' "$previous"
        fi
    done
}
sweep() {
    # Under the lock, another run's workspace was left by SIGKILL or power loss.
    for stale in /usr/local/share/nostromo/.policy.???????? /var/tmp/nostromo-system.????????; do
        [ -d "$stale" ] && [ ! -L "$stale" ] && [ "$(stat -f %u "$stale")" = 0 ] || continue
        rm -rf "$stale" || return 1
        printf 'Removed stale workspace: %s\n' "$stale"
    done
    for stale in /var/run/nostromo-*.lock; do
        [ "$stale" != "$lock" ] || continue
        stale_lock "$stale" || continue
        rm -rf "$stale" || return 1
        printf 'Removed a lock left by an earlier boot: %s\n' "$stale"
    done
    # Earlier installers kept replaced policies and recovery archives. Wi-Fi setup
    # backups serve only its own rollback; skip them while a setup holds its lock.
    for previous in /usr/local/share/nostromo/policy.previous.* /var/log/nostromo/recovery \
        /var/backups/nostromo/wifi-*; do
        [ -d "$previous" ] && [ ! -L "$previous" ] && [ "$(stat -f %u "$previous")" = 0 ] || continue
        case $previous in */wifi-*) [ ! -d /var/run/nostromo-wifi-setup.lock ] || continue ;; esac
        rm -rf "$previous" || return 1
        printf 'Removed an old backup: %s\n' "$previous"
    done
    rmdir /var/backups/nostromo 2>/dev/null || :
    # After the final check, this run's rollback copies have no further use.
    if [ "${1:-}" = final ]; then
        for previous in "$log/system-backup" "$log/policy-backup"; do
            [ -e "$previous" ] || [ -L "$previous" ] || continue
            rm -rf "$previous" || return 1
            printf 'Removed a backup: %s\n' "$previous"
        done
    fi
    prune_logs || return 1
    as_user 'sh scripts/clean-build.sh' || return 1
    # Tools in this run's stages may have left group/world write again.
    [ "${1:-}" != final ] || as_user 'sh scripts/checkout-modes.sh --apply'
}
# Like the package helper, ignore injected pkg configuration and environment.
pkgtool() { env -i PATH="$PATH" HOME=/root LC_ALL=C /usr/local/sbin/pkg -C /dev/null "$@"; }
clean_packages() {
    # Keep pkg, base (its origin has no category), vital packages and the firmware
    # fwget detects, since Wi-Fi may need it before its own stage, with everything
    # they depend on.
    /usr/sbin/fwget -nq >"$log/clean-firmware" || return 1
    pkgtool query -a '%n|%o|%k|%V' >"$log/clean-installed" || return 1
    pkgtool query -a '%n|%dn' >"$log/clean-dependencies" || return 1
    awk -F '|' 'FILENAME==ARGV[1] {kept[$1]=1; next}
        FILENAME==ARGV[2] {row[++n]=$0; name[n]=$1
            if ($1=="pkg" || $1 ~ /^FreeBSD-/ || $2 !~ /\// || $4!=0) kept[$1]=1
            next}
        {from[++m]=$1; to[m]=$2}
        END {
            do {changed=0
                for (i=1; i<=m; i++) if ((from[i] in kept) && !(to[i] in kept)) {kept[to[i]]=1; changed=1}
            } while (changed)
            for (i=1; i<=n; i++) if (!(name[i] in kept)) print row[i]
        }' "$log/clean-firmware" "$log/clean-installed" "$log/clean-dependencies" >"$log/clean-packages" || return 1
    # Without its shell, an account could not log in again if a later stage stops.
    pw usershow -a -7 >"$log/clean-accounts" || return 1
    reset=
    while IFS=: read -r user _ _ _ _ _ shell; do
        [ -e "$shell" ] || continue
        origin=$(pkgtool which -qo "$shell") || continue
        awk -F '|' -v origin="$origin" '$2==origin {found=1} END {exit !found}' "$log/clean-packages" || continue
        if [ "$user" != "$account" ]; then
            printf 'Give %s a base login shell first; %s goes with its package.\n' "$user" "$shell" >&2
            return 1
        fi
        reset=yes
    done <"$log/clean-accounts"
    if [ -n "$reset" ]; then
        pw usermod "$account" -s /bin/sh || return 1
        printf 'The login shell of %s is /bin/sh until the login-shell stage.\n' "$account"
    fi
    set --
    while IFS='|' read -r name _origin locked _vital; do
        [ "$locked" = 0 ] || pkgtool unlock -y "$name" || return 1
        set -- "$@" "$name"
    done <"$log/clean-packages"
    [ "$#" = 0 ] || pkgtool delete -y "$@" || return 1
    pkgtool clean -a -y
}
clean_install() {
    # Start every stage from scratch: earlier packages, the package helper's state
    # and the checkout's build output. Merged system settings stay; the
    # configuration stage merges them again.
    [ ! -d /var/run/nostromo-packages.lock ] || {
        echo 'A package operation holds /var/run/nostromo-packages.lock; let it finish first.' >&2
        return 1
    }
    if [ -x /usr/local/sbin/pkg ]; then clean_packages || return 1; fi
    for state in /var/db/nostromo/packages /usr/local/share/nostromo/policy; do
        [ -e "$state" ] || [ -L "$state" ] || continue
        rm -rf "$state" || return 1
        printf 'Removed installer state: %s\n' "$state"
    done
    # Staged ports can leave read-only directories; chmod -R follows no symlinks.
    as_user 'if [ -e .build ] || [ -L .build ]; then chmod -R u+w .build; rm -rf .build
        echo "Removed the build output: $NOSTROMO_REPO/.build"; fi'
}
final_check() {
    as_user 'sh scripts/verify-stage.sh --installed' || return 1
    [ "$(pw usershow "$account" -7 | cut -d: -f7)" = /usr/local/bin/oksh ] || {
        echo 'The login shell is not oksh.' >&2
        return 1
    }
    [ "$(sysrc -n sddm_enable)" = YES ] || {
        echo 'SDDM is not enabled at boot.' >&2
        return 1
    }
    recipe=$(cat /usr/local/share/nostromo/policy/recipe.sha256) || return 1
    while IFS='|' read -r name _origin version; do
        case $name in '' | '#'*) continue ;; esac
        [ "$(pkg query '%v|%k' "$name")" = "$version|1" ] &&
            [ "$(pkg query '%At|%Av' "$name" | awk -F '|' '$1=="nostromo_recipe" {print $2}')" = "$recipe" ] || {
            printf 'The %s variant is not installed, locked and built from the current recipe.\n' "$name" >&2
            return 1
        }
    done <"$repo/packages.local"
    printf 'Final checks passed for %s.\n' "$account"
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
    rm -f "$lock/pid"
    rmdir "$lock"
    if [ "$result" = 0 ] && [ "$stage" = reboot ]; then
        # The log and lock are final. Like the Wi-Fi offer, this reads the console.
        { printf 'Reboot into the new desktop now? [Y/n] ' >/dev/tty; } 2>/dev/null &&
            IFS= read -r answer </dev/tty || answer=n
        case $answer in
        '' | y | Y | yes | YES) shutdown -r now || echo 'Reboot when ready; keep console recovery available.' >&2 ;;
        *) echo 'Reboot when ready; keep console recovery available.' ;;
        esac
    fi
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
run cleanup sweep
# Prompts bypass tee/logging; the password is read only from the console.
stage=wifi-setup
sh "$repo/scripts/setup-wifi.sh" --offer
stage=clean-offer
{ printf '%s\n%s\n%s' 'A clean install removes every package except pkg, base and detected firmware,' \
    'then the package state and build output; this run builds everything again.' \
    'Start with a clean install? [y/N] ' >/dev/tty; } 2>/dev/null &&
    IFS= read -r answer </dev/tty || answer=n
case $answer in y | Y | yes | YES) run clean-install clean_install ;; esac
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
    # A clean install removed Git as well. Restore it once its reviewed curl is
    # installed, so that a stopped run can still pull fixes.
    if [ "$component" = curl ] && ! pkg info -e git-lite && ! pkg info -e git; then
        run git-lite "$packages" install git-lite
    fi
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
run staged-validation as_user 'sh scripts/verify-stage.sh'
run user-files as_user 'sh scripts/link-home.sh --apply'
run system-configuration sh "$repo/scripts/configure-system.sh" "$account" "$log"
run login-shell pw usermod "$account" -s /usr/local/bin/oksh
# Activation is the last change; the current console/desktop keeps running until reboot.
run enable-login sysrc sddm_enable=YES
run final-check final_check
run final-cleanup sweep final
printf 'Setup completed for %s. Logs: %s\n' "$account" "$log"
# The exit handler offers the reboot after recording the result and releasing the lock.
stage=reboot
