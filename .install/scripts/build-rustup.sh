#!/bin/sh
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] || exit 1
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
export CC=/usr/bin/clang CXX=/usr/bin/clang++
export CARGO_HOME="$repo/.build/cargo" CARGO_TARGET_DIR="$repo/.build/rustup-target"
# aws-lc-sys 0.28 ships no FreeBSD bindings: its build generates them with
# libclang, from the reviewed LLVM, and then builds with CMake.
export LIBCLANG_PATH=/usr/local/llvm21/lib
mkdir -p "$repo/.build/work" "$repo/.build/prefix/bin"
work=$(mktemp -d "$repo/.build/work/rustup.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" rustup "$work/src"
sh "$repo/.install/scripts/stage-licenses.sh" rustup "$work/src" "$repo/.build/prefix"
cd "$work/src"
patch -s -F 0 -p1 <"$repo/rustup/rustup.patch"
# Native source build, Rustls transport, no bundled curl/GNU TLS or self-update.
cargo build --locked --release --jobs 2 --bin rustup-init --no-default-features \
    --features reqwest-rustls-tls,no-self-update
install -m 755 "$CARGO_TARGET_DIR/release/rustup-init" "$repo/.build/prefix/bin/rustup"
# Any rustup command creates its settings file; keep this check's out of ~/.rustup.
RUSTUP_HOME="$work/rustup" "$repo/.build/prefix/bin/rustup" --version
