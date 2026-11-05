#!/bin/sh
# Resolve, fetch, audit, then install only from a private signed local repository.
set -eu
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin
LC_ALL=C
export PATH LC_ALL
umask 077
[ "$(uname -s)" = FreeBSD ] && [ "$(uname -m)" = amd64 ] && [ "$(id -u)" = 0 ] || exit 1
policy=/usr/local/share/nostromo/policy
action=${1:-}
[ "$#" -gt 0 ] || exit 2
shift
build=0
case ${1:-} in --build)
    build=1
    shift
    ;;
esac
validate() { case $1 in '' | [!A-Za-z0-9]* | *[!A-Za-z0-9_+.-]*)
    echo 'Invalid package name.' >&2
    exit 2
    ;;
esac }
case $action in
install | preview)
    [ "$#" -gt 0 ] || exit 2
    for name; do validate "$name"; done
    ;;
update) [ "$#" = 0 ] || exit 2 ;;
finish-bootstrap) [ "$#" = 0 ] || exit 2 ;;
catalog) [ "$#" = 0 ] || exit 2 ;;
details)
    [ "$#" = 1 ] || exit 2
    validate "$1"
    ;;
remove | remove-check)
    [ "$#" = 1 ] || exit 2
    validate "$1"
    ;;
reinstall)
    [ "$#" = 1 ] || exit 2
    validate "$1"
    ;;
import)
    [ "$#" = 2 ] || exit 2
    validate "$1"
    ;;
*)
    echo 'Usage: packages.sh install|preview [--build] names... | update | remove[-check] name | import name archive | finish-bootstrap' >&2
    exit 2
    ;;
esac
store=/var/db/nostromo/packages
for dir in /var/db/nostromo "$store" "$store/local"; do
    [ ! -L "$dir" ] || exit 1
    mkdir -p "$dir"
    [ "$(stat -f '%u %Lp' "$dir")" = '0 700' ] || {
        echo "Unsafe package state directory: $dir" >&2
        exit 1
    }
done
lock=/var/run/nostromo-packages.lock
mkdir "$lock" || {
    echo 'A package operation is already running.' >&2
    exit 1
}
temp=
relock=
finish() {
    result=$?
    trap - 0
    [ -z "$relock" ] || pkgtool lock -y "$relock" || :
    [ -z "$temp" ] || rm -rf "$temp"
    rmdir "$lock"
    exit "$result"
}
trap finish 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
temp=$(mktemp -d /var/tmp/nostromo-packages.XXXXXXXX)
mkdir "$temp/remote" "$temp/db" "$temp/repo" "$temp/local"
# Ignore injected pkg configuration/environment; preserve all system repo files.
pkgtool() { env -i PATH="$PATH" HOME=/root LC_ALL=C /usr/local/sbin/pkg -C /dev/null "$@"; }
remote() { pkgtool -R "$temp/remote" -o "PKG_DBDIR=$temp/db" "$@"; }
localpkg() { pkgtool -R "$temp/local" "$@"; }
upstream_for() {
    case $1 in
    *-kmod | *-kmod-*) printf 'NostromoKmods\n' ;;
    *) printf 'NostromoUpstream\n' ;;
    esac
}
recipe=$(cat "$policy/recipe.sha256")
case $recipe in '' | *[!0-9a-f]*) exit 1 ;; esac
[ "${#recipe}" = 64 ] || exit 1
known_recipe() {
    [ -n "$1" ] && { [ "$1" = "$recipe" ] ||
        { [ -f "$policy/accepted-recipes" ] && grep -Fxq -e "$1" "$policy/accepted-recipes"; }; }
}
identity() {
    pkgtool query -F "$1" 'P|%n|%v|%o|%q|%#d'
    pkgtool query -F "$1" 'D|%n|%dn|%dv|%do' >"$temp/dependencies"
    # pkg prints D|owner||| for an empty list when %n is in the format.
    # Keep partial records: the audit must still reject missing or malformed edges.
    awk -F '|' '!(NF==5 && $1=="D" && $3=="" && $4=="" && $5=="")' "$temp/dependencies"
    pkgtool query -F "$1" 'A|%n|%At|%Av' >"$temp/annotations"
    awk -F '|' '$3=="nostromo_recipe"' "$temp/annotations"
}
if [ "$action" = finish-bootstrap ]; then
    # Stock Git's initial curl chain can leave automatic GNU dependencies after
    # our variants replace it. Remove only unneeded, unlocked, non-vital entries
    # from this explicit list. Never run blanket autoremove or delete user roots.
    changed=yes
    while [ "$changed" = yes ]; do
        changed=no
        pkgtool query -a '%n|%a|%#r|%k|%V|%o' >"$temp/bootstrap-installed"
        awk -F '|' 'NR==FNR {if($0!~/^#/)allowed[$1]=1;next}
            $6 !~ /^base\// && !($1 in allowed) &&
            $1 ~ /^(bash|readline|gdbm|gcc[0-9]*|binutils|gnutls|nettle|mpfr|mpc|libidn2?|libltdl|libgcrypt|libgpg-error|m4|autoconf|automake|texinfo)$/ {print}
        ' "$policy/packages.allowed" "$temp/bootstrap-installed" >"$temp/bootstrap-gnu"
        while IFS='|' read -r name automatic reverse locked vital _origin; do
            [ "$automatic:$reverse:$locked:$vital" = '1:0:0:0' ] || continue
            # Preserve requirements of previously installed user-built clients.
            if [ -s "$policy/local-libraries" ]; then
                pkgtool query '%b' "$name" >"$temp/provides"
                if grep -Fxq -f "$policy/local-libraries" "$temp/provides"; then continue; fi
            fi
            pkgtool delete -n "$name"
            pkgtool delete -y "$name"
            changed=yes
        done <"$temp/bootstrap-gnu"
    done
    [ ! -s "$temp/bootstrap-gnu" ] || {
        echo 'Retained GNU packages still need review (name|automatic|consumers|locked|vital|origin):' >&2
        cat "$temp/bootstrap-gnu" >&2
        exit 1
    }
    exit
fi
if [ "$action" = import ]; then
    [ -f "$2" ] && [ ! -L "$2" ] || exit 1
    # Copy before inspection so the user cannot alter an archive between check/use.
    cp "$2" "$temp/import.pkg"
    wanted=$(awk -F '|' -v name="$1" '$1==name {print $1 "|" $3 "|" $2;n++} END{exit n!=1}' "$policy/packages.local")
    [ "$(pkgtool query -F "$temp/import.pkg" '%n|%v|%o')" = "$wanted" ] || exit 1
    [ "$(pkgtool query -F "$temp/import.pkg" '%At|%Av' | awk -F '|' '$1=="nostromo_recipe" {print $2}')" = "$recipe" ] || exit 1
    # Dependency/ABI/signature checks still precede installation in the next stage.
    mv "$temp/import.pkg" "$store/local/$1.pkg"
    exit
fi
if [ "$action" = remove ] || [ "$action" = remove-check ]; then
    pkgtool query -a 'P|%n|%o|%k|%V|%#r' >"$temp/installed"
    pkgtool query -a 'D|%n|%dn' >"$temp/dependencies"
    awk -F '|' '!(NF==3 && $1=="D" && $3=="")' "$temp/dependencies" >>"$temp/installed"
    {
        awk '!/^#/ && NF {print $1}' "$policy/packages.txt"
        awk -F '|' '!/^#/ && NF {print $1}' "$policy/packages.local"
        [ ! -f "$store/protected-build" ] || cat "$store/protected-build"
    } >"$temp/protected"
    awk -F '|' -v wanted="$1" '
        NR==FNR {protected[$1]=1;next}
        $1=="P" && $2==wanted {
            found++
            unsafe=($2=="pkg" || $3~/^base\// || $4!="0" || $5!="0" || $6!="0")
        }
        $1=="D" {edges[$2 SUBSEP $3]=1}
        END {
            if(found!=1 || unsafe){print "Cannot remove a missing, locked, vital, base or required package: " wanted > "/dev/stderr";exit 1}
            do {changed=0;for(e in edges){split(e,p,SUBSEP);if(protected[p[1]]&&!protected[p[2]]){protected[p[2]]=1;changed=1}}} while(changed)
            if(protected[wanted]){print "Required by the configured desktop/build stack: " wanted > "/dev/stderr";exit 1}
        }' "$temp/protected" "$temp/installed"
    if [ -s "$policy/local-libraries" ]; then
        pkgtool query '%b' "$1" >"$temp/provides"
        if grep -Fxq -f "$policy/local-libraries" "$temp/provides"; then
            echo 'A locally built program still needs this package library.' >&2
            exit 1
        fi
    fi
    # Reject consumers above: pkg delete can otherwise add them to its work list.
    if [ "$action" = remove-check ]; then pkgtool delete -n "$1"; else pkgtool delete "$1"; fi
    exit
fi
if [ "$action" = update ]; then
    [ ! -f "$store/protected-build" ] || build=1
    pkgtool query -a '%n|%o' >"$temp/update-installed"
    # pkgbase has its own repository/update path, outside the application gate.
    awk -F '|' '$2 !~ /^base\// {print $1}' "$temp/update-installed" >"$temp/request"
    [ -s "$temp/request" ] || {
        echo 'No installed packages.'
        exit
    }
else printf '%s\n' "$@" >"$temp/request"; fi
cat >"$temp/remote/upstream.conf" <<'EOF'
NostromoUpstream: {
    url: "pkg+https://pkg.FreeBSD.org/FreeBSD:15:amd64/quarterly",
    mirror_type: "srv", signature_type: "fingerprints",
    fingerprints: "/usr/share/keys/pkg", enabled: yes
}
NostromoKmods: {
    url: "pkg+https://pkg.FreeBSD.org/FreeBSD:15:amd64/kmods_quarterly_${VERSION_MINOR}",
    mirror_type: "srv", signature_type: "fingerprints",
    fingerprints: "/usr/share/keys/pkg", enabled: yes
}
EOF
remote update -f
if [ "$action" = catalog ]; then
    remote rquery -U -r NostromoUpstream -a '%n|%v|%c' >"$temp/catalog"
    remote rquery -U -r NostromoKmods -a '%n|%v|%c' >"$temp/kmods-catalog"
    awk -F '|' 'NR==FNR {if($0!~/^#/) approved[$1]=$4;next}
        $1 ~ /-kmod($|-)/ && FILENAME!=ARGV[3] {next}
        $1 !~ /-kmod($|-)/ && FILENAME!=ARGV[2] {next}
        {print $1 "\t" $2 "\t" ($1 in approved ? approved[$1] : "unreviewed") "\t" $3}' \
        "$policy/packages.allowed" "$temp/catalog" "$temp/kmods-catalog" | tr -d '\000-\010\013-\037\177'
    exit
fi
if [ "$action" = details ]; then
    upstream=$(upstream_for "$1")
    remote rquery -U -r "$upstream" '%n-%v\n%o\n%w\n%e' "$1"
    remote rquery -U -r "$upstream" 'dependency: %dn-%dv' "$1"
    exit
fi
cp "$temp/request" "$temp/queue"
: >"$temp/seen"
index=1
while name=$(sed -n "${index}p" "$temp/queue") && [ -n "$name" ]; do
    index=$((index + 1))
    validate "$name"
    if grep -Fxq -e "$name" "$temp/seen"; then continue; fi
    printf '%s\n' "$name" >>"$temp/seen"
    approved=$(awk -F '|' -v name="$name" '$1==name {print;n++} END{exit n!=1}' "$policy/packages.allowed") || {
        echo "Unreviewed package: $name. No packages installed." >&2
        exit 1
    }
    kind=${approved##*|}
    archive=$temp/repo/$name.pkg
    if [ "$kind" = local ]; then
        [ -f "$store/local/$name.pkg" ] && [ ! -L "$store/local/$name.pkg" ] || {
            echo "Build the required local variant first: $name" >&2
            exit 1
        }
        cp "$store/local/$name.pkg" "$archive"
    else
        [ "$kind" != gnu-build ] || [ "$build" = 1 ] || {
            echo "Build-only dependency requires a reviewed build transaction: $name" >&2
            exit 1
        }
        upstream=$(upstream_for "$name")
        remote rquery -U -r "$upstream" 'P|%n|%v|%o|%q|0' "$name" >"$temp/candidate"
        # Check origin/version/ABI before any download; full dependency graph below.
        awk -v build="$build" -f "$policy/scripts/package-policy.awk" "$policy/packages.allowed" "$temp/candidate"
        version=$(awk -F '|' '{print $3}' "$temp/candidate")
        remote fetch -U -r "$upstream" -y -o "$temp/fetch" "$name-$version"
        # Fetch output paths are not an API: inspect the exact identity of regular archives.
        find "$temp/fetch" -type f -name '*.pkg' >"$temp/archives"
        found=0
        while IFS= read -r file; do
            if [ "$(pkgtool query -F "$file" '%n|%v')" = "$name|$version" ]; then
                cp "$file" "$archive"
                found=$((found + 1))
            fi
        done <"$temp/archives"
        [ "$found" = 1 ] || {
            echo 'Missing or ambiguous fetched package identity.' >&2
            exit 1
        }
    fi
    pkgtool query -F "$archive" '%dn' >>"$temp/queue"
done
: >"$temp/records"
for file in "$temp/repo"/*.pkg; do identity "$file" >>"$temp/records"; done
awk -v build="$build" -v recipe="$recipe" -f "$policy/scripts/package-policy.awk" \
    "$policy/packages.allowed" "$temp/records"
# Protect shared-library requirements of our unregistered user-built binaries.
if [ -s "$policy/local-libraries" ]; then
    pkgtool query -a 'I|%n|%b' >"$temp/libraries"
    for file in "$temp/repo"/*.pkg; do pkgtool query -F "$file" 'C|%n|%b' >>"$temp/libraries"; done
    awk -F '|' '
        NR==FNR {wanted[$1]=1;next}
        $1=="P" {replaced[$2]=1;next}
        $1=="I" || $1=="C" {entries[$1 SUBSEP $2 SUBSEP $3]=1}
        END {
            for(e in entries){split(e,p,SUBSEP);if(p[1]=="C"||!replaced[p[2]])provided[p[3]]=1}
            for(n in wanted)if(!provided[n]){print "Rebuild local programs before removing library ABI: " n > "/dev/stderr";bad=1}
            exit bad
        }' "$policy/local-libraries" "$temp/records" "$temp/libraries"
fi
# Record exact archive hashes and the checked graph for recovery/auditing.
receipt=$store/transaction-$(date +%Y%m%d-%H%M%S)-$$
mkdir "$receipt"
cp "$temp/records" "$receipt/packages"
pkgtool query -a '%n|%v|%o|%q|%a' >"$receipt/before"
sha256 "$temp/repo"/*.pkg >"$receipt/sha256"
if [ ! -e "$store/signing.pem" ]; then
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out "$store/signing.pem"
fi
[ ! -L "$store/signing.pem" ] && [ "$(stat -f '%u %Lp' "$store/signing.pem")" = '0 600' ] || exit 1
openssl pkey -in "$store/signing.pem" -pubout -out "$temp/public.pem"
pkgtool repo "$temp/repo" "rsa:$store/signing.pem"
cat >"$temp/local/local.conf" <<EOF
NostromoTransaction: {
    url: "file://$temp/repo", signature_type: "pubkey",
    pubkey: "$temp/public.pem", enabled: yes
}
EOF
localpkg update -f
set --
while IFS= read -r name; do
    validate "$name"
    set -- "$@" "$name"
done <"$temp/request"
if [ "$action" = reinstall ]; then
    awk -F '|' -v name="$1" '$1==name {found=1} END{exit !found}' "$policy/packages.local"
    if pkgtool info -e "$1"; then
        # Replace a matching unlocked stock bootstrap package, or our own receipt.
        installed_recipe=$(pkgtool query '%At|%Av' "$1" | awk -F '|' '$1=="nostromo_recipe" {print $2}')
        if known_recipe "$installed_recipe"; then
            relock=$1
            pkgtool unlock -y "$1"
        else
            [ -z "$installed_recipe" ] && [ "$(pkgtool query '%k' "$1")" = 0 ] || exit 1
            expected=$(awk -F '|' -v name="$1" '$1==name {print $1 "|" $2 "|" $3}' "$policy/packages.local")
            [ "$(pkgtool query '%n|%o|%v' "$1")" = "$expected" ] || {
                echo 'Review the existing variant/version before replacing it.' >&2
                exit 1
            }
        fi
    fi
    localpkg install -U -f -n --no-remove -r NostromoTransaction "$@"
    localpkg install -U -f -y --no-remove -r NostromoTransaction "$@"
elif [ "$action" = update ]; then
    localpkg upgrade -U -n --no-remove -r NostromoTransaction "$@"
    localpkg upgrade -U -y --no-remove -r NostromoTransaction "$@"
else
    localpkg install -U -n --no-remove -r NostromoTransaction "$@"
    [ "$action" != preview ] || exit
    # --no-remove makes conflicting replacements a stop, not an implicit uninstall.
    localpkg install -U -y --no-remove -r NostromoTransaction "$@"
fi
localpkg check -d -n -a
pkgtool query -a '%n|%v|%o|%q|%a' >"$receipt/after"
awk -F '|' '
    NR==FNR {if($1=="P"){origin[$2]=$4;abi[$2]=$5};next}
    {installed[$1]=1;if($1 in origin && ($3!=origin[$1] || $4!=abi[$1]))bad=1}
    END {for(n in origin)if(!installed[n]){print "Missing transaction package: " n > "/dev/stderr";bad=1};exit bad}
' "$temp/records" "$receipt/after"
if [ "$action" = update ]; then
    # pkg re-executes after a self-upgrade. Check the result instead of retrying blindly.
    localpkg version -U -R -r NostromoTransaction -l '<' >"$receipt/pending"
    if [ -s "$receipt/pending" ]; then
        cat "$receipt/pending" >&2
        echo 'Updates remain pending. Review locks and the transaction output before retrying.' >&2
        exit 1
    fi
    awk -F '|' 'NR==FNR {automatic[$1]=$5;next}
        $1 in automatic && $5!=automatic[$1] {print "Automatic flag changed: " $1 > "/dev/stderr";bad=1}
        END {exit bad}' "$receipt/before" "$receipt/after"
fi
if [ "$build" = 1 ] && [ "$action" != update ]; then
    {
        [ ! -f "$store/protected-build" ] || cat "$store/protected-build"
        cat "$temp/request"
    } |
        sort -u >"$temp/protected-build"
    mv "$temp/protected-build" "$store/protected-build"
fi
while IFS='|' read -r name _origin _version; do
    case $name in '' | '#'*) continue ;; esac
    if pkgtool info -e "$name"; then
        installed_recipe=$(pkgtool query '%At|%Av' "$name" | awk -F '|' '$1=="nostromo_recipe" {print $2}')
        # Later variants may still be stock during the ordered bootstrap. The
        # final runtime transaction requires every installed variant's receipt.
        if [ "$build" = 1 ] && [ -z "$installed_recipe" ] && ! grep -Fxq -e "$name" "$temp/request"; then continue; fi
        # Sequential rebuilds retain the last reviewed recipe for unaffected ports.
        # A requested variant must have the new receipt before its transaction passes.
        expected_recipe=$recipe
        if ! grep -Fxq -e "$name" "$temp/request" && known_recipe "$installed_recipe"; then
            expected_recipe=$installed_recipe
        fi
        [ "$installed_recipe" = "$expected_recipe" ] || {
            echo "Installed $name does not have the current recipe receipt; rebuild it through install.sh." >&2
            exit 1
        }
        pkgtool lock -y "$name"
    fi
done <"$policy/packages.local"
printf 'Audited package transaction completed. Receipt: %s\n' "$receipt"
