#!/bin/sh
# Build compiler-rt builtins for the selected embedded target.
set -eu
[ "$(uname -s)" = FreeBSD ] && [ "$(id -u)" != 0 ] && [ "$#" = 1 ] || exit 2
repo=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd -P)
record=$(awk -F '|' -v name="$1" '$1==name{print;n++}END{exit n!=1}' "$repo/embedded/runtimes.txt")
IFS='|' read -r profile triple flags <<EOF
$record
EOF
llvm=/usr/local/llvm21
for tool in clang clang++ llvm-ar llvm-ranlib llvm-nm; do [ -x "$llvm/bin/$tool" ] || exit 1; done
prefix=$repo/.build/embedded/$profile
[ ! -e "$prefix" ] && [ ! -L "$prefix" ] || {
    echo 'Runtime exists; preserve it before rebuilding.' >&2
    exit 1
}
mkdir -p "$repo/.build/work" "$repo/.build/embedded"
work=$(mktemp -d "$repo/.build/work/runtime.XXXXXXXX")
trap 'rm -rf "$work"' 0
trap 'exit 130' INT
trap 'exit 143' HUP TERM
sh "$repo/.install/scripts/fetch-source.sh" compiler-rt "$work/compiler-rt"
sh "$repo/.install/scripts/fetch-source.sh" llvm-cmake "$work/cmake"
# The runtime build mode avoids deprecated LLVM_CONFIG_PATH/source-tree guessing.
cmake -S "$work/compiler-rt/lib/builtins" -B "$work/build" -G Ninja \
    -DCMAKE_SYSTEM_NAME=Generic -DCMAKE_SYSTEM_PROCESSOR="${triple%%-*}" \
    -DCMAKE_C_COMPILER="$llvm/bin/clang" -DCMAKE_CXX_COMPILER="$llvm/bin/clang++" \
    -DCMAKE_ASM_COMPILER="$llvm/bin/clang" -DCMAKE_AR="$llvm/bin/llvm-ar" \
    -DCMAKE_RANLIB="$llvm/bin/llvm-ranlib" -DCMAKE_NM="$llvm/bin/llvm-nm" \
    -DCMAKE_C_COMPILER_TARGET="$triple" -DCMAKE_CXX_COMPILER_TARGET="$triple" \
    -DCMAKE_ASM_COMPILER_TARGET="$triple" -DCMAKE_C_FLAGS="$flags -ffreestanding" \
    -DCMAKE_CXX_FLAGS="$flags -ffreestanding" -DCMAKE_ASM_FLAGS="$flags" \
    -DCMAKE_BUILD_TYPE=Release -DCOMPILER_RT_DEFAULT_TARGET_ONLY=ON \
    -DCOMPILER_RT_BAREMETAL_BUILD=ON -DCOMPILER_RT_BUILTINS_ENABLE_PIC=OFF \
    -DCOMPILER_RT_OS_DIR=baremetal -DLLVM_RUNTIMES_BUILD=ON \
    -DCOMPILER_RT_INCLUDE_TESTS=OFF -DCMAKE_INSTALL_LIBDIR=lib \
    -DCMAKE_INSTALL_PREFIX="$work/stage/resource"
cmake --build "$work/build" --parallel 4
cmake --install "$work/build"
ln -s "$("$llvm/bin/clang" -print-resource-dir)/include" "$work/stage/resource/include"
printf '%s\n' "$record" >"$work/stage/profile"
sh "$repo/.install/scripts/stage-licenses.sh" compiler-rt "$work/compiler-rt" "$work/stage"
# Verify the driver resolves the actual archive for this exact ISA/ABI.
# shellcheck disable=SC2086
library=$("$llvm/bin/clang" --target="$triple" $flags -resource-dir="$work/stage/resource" --rtlib=compiler-rt --print-libgcc-file-name)
[ -s "$library" ] || {
    echo "Missing target runtime: $library" >&2
    exit 1
}
"$llvm/bin/llvm-ar" t "$library" >"$work/members"
[ -s "$work/members" ] || {
    echo 'Empty target runtime archive.' >&2
    exit 1
}
# Resolve an actual compiler builtin in a bare-metal ELF before publishing it.
# shellcheck disable=SC2086
"$llvm/bin/clang" --target="$triple" $flags -resource-dir="$work/stage/resource" \
    -ffreestanding -nostdlib -fuse-ld=lld -Wl,-e,_start -Wl,--gc-sections \
    "$repo/embedded/runtime-smoke.c" "$library" -o "$work/stage/runtime-smoke.elf"
"$llvm/bin/llvm-nm" --undefined-only "$work/stage/runtime-smoke.elf" >"$work/undefined"
[ ! -s "$work/undefined" ] || {
    cat "$work/undefined" >&2
    exit 1
}
mv "$work/stage" "$prefix"
printf 'Built %s in %s\n' "$profile" "$prefix"
