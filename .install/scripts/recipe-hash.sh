#!/bin/sh
set -eu
# .install in a checkout, or the installed policy that copies its layout.
base=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
# File paths do not enter the digest, so a checkout can live in any user's home.
{
    cat "$base/ports.lock" "$base/packages.local" "$base/ports/ports.conf" "$base/scripts/ports-variants.sh" "$base/scripts/fetch-source.sh"
    awk -F '|' '$1=="ports" {print}' "$base/sources.lock"
    cat "$base"/ports/*.patch
} | sha256 -q
