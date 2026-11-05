# Native embedded development

The laptop uses native FreeBSD programs: LLVM 21, CMake/Ninja, dtc, OpenOCD,
ST-Link tools, dfu-util, Python/uv, west and Rust. It installs no Linux SDK,
container, virtual machine or VS Code extension. Board firmware and host support
are separate: Zephyr's official getting-started hosts do not include FreeBSD.
This workflow is configured for native testing, not a claim that every vendor's
board, USB driver or binary-only tool works here.

## Zephyr, C and C++

The pinned baseline is Zephyr **4.5.0**, commit
`41d10b59730406bbab4ca9f1fbbe9e96aafb4966`, and west **1.5.0**. The installer
creates a uv environment around the packaged native Python 3.12. Core
devicetree, ELF, YAML, JSON-schema and serial dependencies are reviewed packages;
west is a hash-pinned Python wheel. No Python interpreter is downloaded.

```sh
nostromo-zephyr init ~/Projects/zephyr
cd ~/Projects/zephyr
nostromo-zephyr boards
nostromo-zephyr profiles
nostromo-zephyr runtime cortex-m4-hard
# Substitute the exact board qualifier and a matching CPU/FPU runtime profile:
nostromo-zephyr build cortex-m4-hard YOUR_BOARD zephyr/samples/hello_world
```

Use the board catalog for its exact `board/soc/core` spelling. The helper does not
guess a board from a manufacturer name. `boards` lists the checked-out release;
`west boards --help` describes its filters/formats. The build directory is
`build/BOARD-WITH-SLASHES-REPLACED-PROFILE`. CMake generates a compilation database
for clangd. Set a project's `.clangd` `CompileFlags.CompilationDatabase` to that
directory when it is outside the application tree. `nostromo-zephyr menuconfig
BUILD-DIRECTORY` opens terminal Kconfig; no GUI configurator is required.

The native toolchain reuses Zephyr's own LLVM compiler and LLVM binary-tool
definitions, explicitly selects **LLD + compiler-rt**, and defaults to Zephyr's
in-tree minimal libc. Each `runtime PROFILE` builds the matching compiler-rt
builtins from pinned LLVM sources in the checkout's user-owned `.build/embedded`.
Profiles distinguish architecture, CPU and float ABI. Choose the actual ISA/FPU;
matching manufacturer names are not sufficient. The build refuses architecture, word-size
and ARM float-ABI mismatches. A runtime is published only after its archive has
members and a bare-metal ELF smoke program links without unresolved symbols. It does not turn a host FreeBSD libc or libc++ into
an embedded runtime. Applications needing full libc, C++ standard-library support
or vendor-specific libraries must supply suitable target libraries and settings.

```sh
nostromo-zephyr flash BUILD-DIRECTORY --context
# Review runner/probe/board before the command that writes hardware:
nostromo-zephyr flash BUILD-DIRECTORY --runner openocd
nostromo-zephyr debugserver BUILD-DIRECTORY --runner openocd
nostromo-tool lldb path/to/zephyr.elf
# At the LLDB prompt, for a local OpenOCD GDB-protocol server:
# gdb-remote localhost:3333
nostromo-embedded serial
```

`debugserver` starts the runner's server; it does not install GNU GDB. LLDB's
remote target support varies by architecture/probe. For a runner other than
OpenOCD, inspect `west flash --context` and that runner's native host requirements.
The installer never flashes a board, erases a chip, imports a key, or updates a
vendor firmware image. Serial access uses base `cu` and the `dialer` group;
leave cu with a new line followed by `~.`. USB debug probes may need an explicit
device access grant; see [HARDWARE.md](HARDWARE.md).

Zephyr's gperf generator is an explicit GNU **build-only** exception: userspace
kernel-object tables require its output. LLVM does not replace this generator.
The dependency gate pins it to the reviewed version. Optional Zephyr tools
(CANopen, vendor runners, license reports, signing or test infrastructure) may
require additional packages; they are not silently fetched by opening the editor.
`west packages pip` can report upstream requirements, but do not bypass the
package/dependency review with an unrestricted installation of that entire list.

## Rust and no_std

Native packaged Rust remains the default. Embedded projects opt in to a private
upstream **1.98.1 FreeBSD host toolchain**, managed by a pinned, natively compiled
rustup with Rustls transport and self-update disabled. The wrapper activates it
only below a project containing the generated `.nostromo-rust` marker. It does
not change the login PATH, system compiler, global Cargo target or other projects.

```sh
nostromo-rust targets
nostromo-rust init thumbv7em-none-eabihf ~/Projects/my-mcu
cd ~/Projects/my-mcu
cargo check
cargo build --release
cargo clippy
vis src/lib.rs
```

The generated project is a compiling `no_std` **library**, deliberately without
invented flash/RAM addresses, GPIOs or vector tables. Add the exact chip's PAC/HAL
and startup crate, its verified `memory.x`/linker script and runner when making a
firmware application. `rust-analyzer`, Cargo, rustfmt and Clippy use the same
project toolchain through the installed wrappers. Test pure logic separately on
the host (`cargo test --target x86_64-unknown-freebsd`); a bare-metal executable
cannot run as a laptop process.

For Rust **inside Zephyr**, run `nostromo-zephyr rust` in the workspace. This
adds the pinned manifest's optional `zephyr-lang-rust` module while preserving
other project filters. Use its `samples`, `etc/platforms.txt`, Cargo manifest and
`rust_cargo_application()` CMake integration, with `CONFIG_RUST=y`. That module's
target support is narrower than Zephyr's C board catalog. Follow the checked-out
module's toolchain requirements; do not assume the no_std example automatically
configures every Zephyr Rust target.

## Family boundaries

| Family | Native path | What still depends on the exact board |
| --- | --- | --- |
| STM32 Cortex-M | LLVM/Zephyr; Rust Thumb target + STM32 HAL; OpenOCD/ST-Link/DFU | CPU/FPU ABI, memory layout, probe and supported SoC |
| NXP Cortex-M (LPC/Kinetis/i.MX RT etc.) | LLVM/Zephyr; Rust PAC/HAL where available; OpenOCD/CMSIS-DAP where supported | Boot mode, SDK/HAL license, probe; MCU-Link/J-Link/LinkServer tools are not assumed FreeBSD-compatible |
| ESP32 C2/C3/C6/H2 and other RISC-V ESP parts | LLVM/RISC-V where Zephyr's board supports it; Rust RISC-V + esp-hal; native esptool | Exact ISA, flash layout, radio blobs and vendor component support |
| Original ESP32, S2, S3 (Xtensa) | Edit sources and use native serial/esptool | The supplied LLVM/Rust toolchains have no supported Xtensa path here. Espressif toolchain host support must be established before claiming native builds |
| Raspberry Pi Pico/RP2040 | Thumbv6m; Zephyr/Rust RP2040 HAL; CMSIS-DAP/OpenOCD/UF2 | Bootloader, UF2 destination and exact memory map |
| RP2350/Pico 2 | Cortex-M33 or supported RISC-V target | Select the intended core/ISA; firmware built for one core is not interchangeable |
| Full-size Raspberry Pi | AArch64 targets where Zephyr lists the board; bare-metal Rust | Pi generation, boot firmware and limited peripheral support; not a general Pi operating-system workflow |
| ARM, x86 and MIPS assembly | LLVM MC/objdump + asm-lsp, per-project target settings | LLVM backends are not complete board runtimes. MIPS is not presented as a Zephyr 4.5 board architecture or a prebuilt Rust tier-2 bare-metal target |

Sources: [Zephyr CLI setup](https://docs.zephyrproject.org/latest/develop/getting_started/index.html),
[custom toolchains](https://docs.zephyrproject.org/latest/develop/toolchains/custom_cmake.html),
[Zephyr Rust](https://docs.zephyrproject.org/latest/develop/languages/rust/index.html),
[Rust FreeBSD hosts](https://doc.rust-lang.org/rustc/platform-support/freebsd.html),
[rustup installation](https://rust-lang.github.io/rustup/installation/other.html),
[LLVM builtins](https://llvm.org/docs/HowToCrossCompileBuiltinsOnArm.html).
