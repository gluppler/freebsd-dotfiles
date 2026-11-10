# Input 1: name|origin|version-or-*|stock/gnu/gnu-build/local. Then pkg-query records:
# P|name|version|origin|ABI|dependency-count, D|owner|name|version|origin,
# A|owner|annotation-key|value. Unknowns, missing edges and stock variants fail.
BEGIN { FS="|" }
NR==FNR {
    if ($0 ~ /^#/ || !NF) next
    if (NF!=4 || $1 in origin || $4 !~ /^(stock|gnu|gnu-build|local)$/ ||
        ($4!="stock" && $3=="*")) {bad=1; next}
    origin[$1]=$2; version[$1]=$3; kind[$1]=$4
    if ($1 ~ /^(bash|readline|gdbm|gcc[0-9]*|binutils|gnutls|nettle|gmp|mpfr|mpc|libiconv|libidn2?|libunistring|libltdl|libgcrypt|libgpg-error|gettext-runtime|gettext-tools|libtextstyle|gmake|gperf|m4|autoconf|automake|texinfo)$/ && $4 !~ /^gnu/)
        {print "GNU provenance mislabeled: " $1 > "/dev/stderr";bad=1}
    next
}
function fail(message) {print message > "/dev/stderr"; bad=1}
function identity(name, ver, src) {
    if (name !~ /^[A-Za-z0-9_+.-]+$/ || !(name in origin) || src!=origin[name] ||
        (version[name]!="*" && ver!=version[name]))
        fail("Unreviewed package: " name " " ver " (" src ")")
}
$1=="P" {
    # Architecture-independent packages carry pkg's FreeBSD:15:* ABI.
    if (NF!=6 || $6 !~ /^[0-9]+$/ || $2 in present ||
        ($5!="FreeBSD:15:amd64" && $5!="freebsd:15:x86:64" &&
         $5!="FreeBSD:15:*" && $5!="freebsd:15:*")) {
        fail("Invalid/duplicate package identity: " $0); next
    }
    identity($2,$3,$4); present[$2]=$3; expected[$2]=$6; count++
    if (kind[$2]=="gnu-build" && !build) fail("Build-only exception in runtime request: " $2)
    next
}
$1=="D" {
    if (NF!=5 || ($2 SUBSEP $3) in edges) {fail("Invalid dependency: " $0);next}
    identity($3,$4,$5); edges[$2 SUBSEP $3]=$4; actual[$2]++
    next
}
$1=="A" {
    if (NF!=4 || $3!="nostromo_recipe" || $2 in local_build) {
        fail("Invalid local build receipt: " $0); next
    }
    local_build[$2]=$4
    next
}
{fail("Unknown package record: " $0)}
END {
    if (!count) fail("Empty package audit")
    for (name in present) {
        if (actual[name]+0 != expected[name]+0) fail("Incomplete dependency list: " name)
        if (kind[name]=="local" && (recipe=="" || local_build[name]!=recipe))
            fail("Required local variant/recipe is missing: " name)
    }
    for (edge in edges) {
        split(edge,p,SUBSEP)
        if (!(p[1] in present) || !(p[2] in present) || present[p[2]]!=edges[edge])
            fail("Unresolved dependency: " p[1] " -> " p[2] " " edges[edge])
    }
    exit bad
}
