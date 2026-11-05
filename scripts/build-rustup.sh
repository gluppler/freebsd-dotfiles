#!/bin/sh
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
export CC=/usr/bin/clang CXX=/usr/bin/clang++
export CARGO_HOME="$repo/.build/cargo" CARGO_TARGET_DIR="$repo/.build/rustup-target"
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/rustup.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/scripts/fetch-source.sh" rustup "$work/src"
sh "$repo/scripts/stage-licenses.sh" rustup "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p1 <"$repo/src/embedded/rustup.patch"
# Native source build, Rustls transport, no bundled curl/GNU TLS or self-update.
cargo build --locked --release --jobs 2 --bin rustup-init --no-default-features \
    --features reqwest-rustls-tls,no-self-update
install -m 755 "$CARGO_TARGET_DIR/release/rustup-init" "$repo/.build/prefix/bin/rustup"
"$repo/.build/prefix/bin/rustup" --version
