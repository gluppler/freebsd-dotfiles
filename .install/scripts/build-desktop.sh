#!/bin/sh
# Build and stage the patched desktop as the ordinary account.
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
[ "$(uname -s)" = FreeBSD ] && [ "$(uname -m)" = amd64 ] || {
    echo 'Build the native desktop on FreeBSD amd64.' >&2
    exit 1
}
[ "$(id -u)" != 0 ] || {
    echo 'Build as the ordinary desktop account.' >&2
    exit 1
}
case $(freebsd-version -u) in 15.1-RELEASE*) ;; *)
    echo 'Review the pinned FreeBSD release before building.' >&2
    exit 1
    ;;
esac
for tool in cc pkg-config wayland-scanner meson ninja; do
    command -v "$tool" >/dev/null || {
        printf 'Missing build tool: %s\n' "$tool" >&2
        exit 1
    }
done
export CC=/usr/bin/clang CXX=/usr/bin/clang++
export PKG_CONFIG_PATH=/usr/local/libdata/pkgconfig:/usr/local/lib/pkgconfig:/usr/local/share/pkgconfig
log=$repo/.build/logs/$(date +%Y%m%d-%H%M%S)-$$
mkdir -p "$log"
for component in dwl dwlb foot dvtm gtklock fuzzel dunst nnn wireguard session tpass rustup; do
    printf 'Building %s; log: %s/%s.log\n' "$component" "$log" "$component"
    if sh "$repo/.install/scripts/build-$component.sh" >"$log/$component.log" 2>&1; then
        printf 'Built %s\n' "$component"
    else
        result=$?
        tail -n 40 "$log/$component.log" >&2
        printf 'Build stopped at %s. Existing user links and login service are unchanged.\n' "$component" >&2
        exit "$result"
    fi
done
printf 'Native desktop binaries staged in %s/.build/prefix; session provisioning remains a separate installer stage.\n' "$repo"
