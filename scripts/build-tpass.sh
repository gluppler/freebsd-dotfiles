#!/bin/sh
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
export CC=/usr/bin/clang CXX=/usr/bin/clang++
export CARGO_HOME="$repo/.build/cargo" CARGO_TARGET_DIR="$repo/.build/tpass-target"
memory=$(sysctl -n hw.physmem)
jobs=$((memory / 2147483648))
[ "$jobs" -ge 1 ] || jobs=1
cpus=$(sysctl -n hw.ncpu)
[ "$jobs" -le "$cpus" ] || jobs=$cpus
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/tpass.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/scripts/fetch-source.sh" tpass "$work/src"
sh "$repo/scripts/stage-licenses.sh" tpass "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p1 <"$repo/src/tpass/freebsd.patch"
cp "$repo/src/tpass/clip.rs" src/tpass/util/clip.rs
cargo build --locked --release --jobs "$jobs" --bin tpass --bin tcli --bin tclig
# No agent, secret store or key enrollment is started by installation.
for binary in tpass tcli tclig; do
    install -m 755 "$CARGO_TARGET_DIR/release/$binary" "$repo/.build/prefix/bin/$binary"
    "$repo/.build/prefix/bin/$binary" --version
done
