#!/bin/sh
# Ordinary-user builds of the few ports whose stock options conflict with policy.
set -eu
PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin:/usr/local/sbin
export PATH CC=/usr/bin/clang CXX=/usr/bin/clang++
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
revision=$(awk '!/^#/ && NF {print}' "$repo/ports.lock")
case $revision in *[!0-9a-f]* | '') exit 1 ;; esac
[ "${#revision}" = 40 ] || exit 1
ports=$repo/.build/ports
receipt=$repo/.build/ports.mtree
recipe_file=$repo/.build/ports.recipe
work=$repo/.build/ports-work
action=${1:-prepare}
case $action in prepare) [ "$#" = 1 ] || exit 2 ;; deps | build) [ "$#" = 2 ] || exit 2 ;; *) exit 2 ;; esac
recipe=$(sh "$repo/scripts/recipe-hash.sh")
# Native mtree exits 0 for missing and extra files, so any report is an edit.
unedited() {
    report=$(mtree -f "$receipt" -p "$ports") && [ -z "$report" ] && return
    [ -z "$report" ] || printf '%s\n' "$report"
    return 1
}
if [ "$action" = prepare ]; then
    mkdir -p "$repo/.build"
    pending=$(mktemp -d "$repo/.build/ports.XXXXXXXX")
    trap 'rm -rf "$pending"' 0
    trap 'exit 130' INT
    trap 'exit 143' HUP TERM
    if [ -d "$ports" ] && [ ! -L "$ports" ] && [ -f "$recipe_file" ] && [ -f "$receipt" ] &&
        [ "$(cat "$recipe_file")" != "$recipe" ]; then
        # A tree that matches its receipt holds only generated files.
        unedited || {
            echo 'Recipe changed and .build/ports has the edits listed above: preserve them, then prepare again.' >&2
            exit 1
        }
        echo 'Recipe changed: replacing the unedited generated ports tree.'
        mv "$ports" "$pending/previous"
    fi
    if [ ! -e "$ports" ]; then
        # Port cookies would reuse objects built from an earlier tree's patches and options.
        if [ -e "$work" ] || [ -L "$work" ]; then
            echo 'Discarding build work from the previous ports tree.'
            mv "$work" "$pending/previous-work"
        fi
        # Staged ports can leave read-only directories; chmod -R follows no symlinks.
        chmod -R u+w "$pending"
        rm -rf "$pending/previous" "$pending/previous-work"
        sh "$repo/scripts/fetch-source.sh" ports "$pending/tree"
        for patchfile in "$repo"/src/ports/*.patch; do
            (cd "$pending/tree" && patch -s -F 0 -p1 <"$patchfile")
        done
        mtree -c -k type,link,sha256digest -p "$pending/tree" >"$pending/ports.mtree"
        printf '%s\n' "$recipe" >"$pending/ports.recipe"
        mv "$pending/ports.mtree" "$receipt"
        mv "$pending/ports.recipe" "$recipe_file"
        # The tree moves last: an interrupted run leaves no tree, which prepare regenerates.
        mv "$pending/tree" "$ports"
    fi
fi
[ -d "$ports" ] && [ ! -L "$ports" ] && [ -f "$recipe_file" ] && [ -f "$receipt" ] || {
    echo 'Incomplete generated ports tree: preserve it before preparing a fresh tree.' >&2
    exit 1
}
[ "$(cat "$recipe_file")" = "$recipe" ] || {
    echo 'Recipe changed: prepare the ports tree again.' >&2
    exit 1
}
if [ "$action" = prepare ]; then
    unedited || {
        echo 'Generated .build/ports has the edits listed above: preserve them, then prepare again.' >&2
        exit 1
    }
    exit
fi
record=$(awk -F '|' -v name="$2" '$1==name {print;n++} END{exit n!=1}' "$repo/packages.local")
IFS='|' read -r name origin version <<EOF
$record
EOF
case $origin in *[!a-zA-Z0-9_./-]* | */../* | ../* | /*) exit 1 ;; esac
dist=$repo/.build/ports-distfiles
packages=$repo/.build/ports-packages
mkdir -p "$work" "$dist" "$packages"
cpus=$(sysctl -n hw.ncpu)
memory=$(sysctl -n hw.physmem)
jobs=$((memory / 2147483648))
[ "$jobs" -ge 1 ] || jobs=1
[ "$jobs" -le "$cpus" ] || jobs=$cpus
[ "$jobs" -le 8 ] || jobs=8
# No ports target may install its own missing dependencies or escalate privileges.
portmake() {
    make -C "$ports/$origin" __MAKE_CONF="$repo/system/ports.conf" \
        PORTSDIR="$ports" WRKDIRPREFIX="$work" DISTDIR="$dist" PACKAGES="$packages" \
        BATCH=yes STRICT_DEPENDS=yes INSTALL_AS_USER=yes NO_CHOWN=yes \
        MAKE_JOBS_NUMBER="$jobs" \
        "PKG_NOTE_nostromo_recipe=$(cat "$recipe_file")" "$@"
}
[ "$(portmake -V PKGNAME)" = "$name-$version" ] || {
    echo "Unexpected port version: $name" >&2
    exit 1
}
if [ "$action" = deps ]; then
    # Report direct build/run/library dependency names; root resolves their closure.
    portmake -V BUILD_DEPENDS -V LIB_DEPENDS -V RUN_DEPENDS -V FETCH_DEPENDS -V EXTRACT_DEPENDS -V PATCH_DEPENDS |
        tr ' \t' '\n' | awk -F: 'NF>=2 {print $2}' | sort -u >"$work/$name.origins"
    while IFS= read -r dependency; do
        case $dependency in '' | *[!a-zA-Z0-9_./@+-]* | */../* | ../* | /*) exit 1 ;; esac
        dep_origin=${dependency%@*}
        if [ "$dep_origin" = "$dependency" ]; then set --; else set -- "FLAVOR=${dependency##*@}"; fi
        make -C "$ports/$dep_origin" __MAKE_CONF="$repo/system/ports.conf" \
            BATCH=yes NO_DEPENDS=yes "$@" -V PKGBASE
    done <"$work/$name.origins"
else
    # Ports refuse a port listed in pkg's advisory file, even one already built;
    # stock packages are built without that check. Report advisories, then build.
    advisories=$(portmake -V AUDITFILE)
    if [ -f "$advisories" ] && ! report=$(pkg audit -f "$advisories" "$name-$version" 2>&1); then
        printf '%s\nBuilding %s despite the audit report above.\n' "$report" "$name" >&2
    fi
    portmake DISABLE_VULNERABILITIES=yes checksum stage stage-qa check-plist package
    file=$packages/All/$name-$version.pkg
    [ -f "$file" ] && [ ! -L "$file" ] || exit 1
    [ "$(pkg query -F "$file" '%At|%Av' | awk -F '|' '$1=="nostromo_recipe" {print $2}')" = "$(cat "$recipe_file")" ] || exit 1
    printf '%s\n' "$file"
fi
