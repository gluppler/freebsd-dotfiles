# Native LLVM tools with a separately built, target-specific compiler-rt.
set(TOOLCHAIN_VARIANT_COMPILER llvm CACHE STRING "Native LLVM")
set(TOOLCHAIN_KCONFIG_DIR ${ZEPHYR_BASE}/cmake/toolchain/host/llvm)
include(${ZEPHYR_BASE}/cmake/toolchain/host/llvm/generic.cmake)
set(TOOLCHAIN_HAS_NEWLIB OFF CACHE BOOL "No implicit newlib" FORCE)
set(TOOLCHAIN_HAS_PICOLIBC OFF CACHE BOOL "No implicit picolibc" FORCE)
set(TOOLCHAIN_HAS_LIBCXX OFF CACHE BOOL "No target C++ library supplied" FORCE)
