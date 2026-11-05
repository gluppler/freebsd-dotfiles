#!/bin/sh
set -eu
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
# File paths do not enter the digest, so a checkout can live in any user's home.
{
    cat "$repo/ports.lock" "$repo/packages.local" "$repo/system/ports.conf" "$repo/scripts/ports-variants.sh" "$repo/scripts/fetch-source.sh"
    awk -F '|' '$1=="ports" {print}' "$repo/sources.lock"
    cat "$repo"/src/ports/*.patch
} | sha256 -q
