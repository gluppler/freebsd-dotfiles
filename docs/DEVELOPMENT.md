# Development and terminal workspace

The implemented stack is **vis + abduco/dvtm + actual oksh**. Native language tools,
editor plugins and the embedded workflow are provisioned by the root installer
as the ordinary user. Neovim/LazyVim/Mason, tmux/TPM, Zsh and Bash remain superseded;
the requested useful editing/session workflows are retained without claiming the
same plugin APIs. FreeBSD interactive execution still needs native acceptance.

## Editor

The original 2D orb gently floats beside the plain dashboard menu. It adapts to
the actual pane size; opening a file bypasses it. Four cached pages keep the
animation from accumulating text edits or undo history. Its clock stops when
the dashboard is not the active clean Normal-mode view, and static/off effects
disable movement. Small panes keep the menu without an animation process.
The configuration includes project/recent/open-file pickers, working-file
bookmarks, saved filename/cursor sessions, lazygit, nnn, fuzzy completion and LSP
navigation, hover, rename, symbols and diagnostics. Plugins are pinned vis-lspc
and dkjson; language tool startup does not fetch arbitrary plugins.

Build/test/lint tasks save modified files first and stop if saving fails. The
configuration supports format, selected/repeated tests and an LLDB entry point.
Ctrl+S saves with terminal flow-control restoration. Space mp renders the **unsaved**
Markdown buffer through Lowdown inside vis; PDF reading uses Zathura/MuPDF.
[KEYBINDINGS](KEYBINDINGS.md) lists the actual mappings and [DOCUMENTS](DOCUMENTS.md)
explains the preview workflow.

FreeBSD's `editors/vis` installs `vise`; the installed `vis` wrapper intentionally
launches `/usr/local/bin/vise`. Native WL_COPY integration uses Wayland clipboard
commands. `nostromo-dev health` reports the real tool paths, not assumed Linux
locations. Project configuration and dependency locks remain user-controlled.

| Workload | Installed native workflow |
| --- | --- |
| C/C++ | Base clang/clang++, LLVM 21 clangd/format/tidy and LLDB, CMake/Ninja/BSD make; compilation database per project |
| Rust | Packaged rustc/Cargo, rustfmt/Clippy and rust-analyzer for native code; project-scoped embedded toolchain below |
| Go | Go 1.26/gofmt, modules/build/test, gopls; no assumed Linux Delve binary |
| Python | Packaged Python 3.12, uv, Ruff, pylsp/Jedi and pinned Ruff plugin; project `.venv`, no downloaded Linux interpreter |
| POSIX shell | sh, interactive oksh, ShellCheck/shfmt and efm-langserver; Bash source support does not install Bash |
| Assembly | LLVM MC/objdump and asm-lsp with per-project triples for ARM/Thumb/AArch64, x86 and MIPS; ABI/endian/sysroot/linker settings remain target-specific |
| Documents | Lowdown live Markdown preview and native GTK Wayland Zathura/MuPDF |

`nostromo-tool` resolves installed LLVM executables and the `go`/`gofmt` wrappers
handle FreeBSD's versioned Go executable names. Native desktop CC/CXX are not replaced
by a cross compiler in the login environment. The configured editor uses these
same dispatch helpers for build, formatting and LSP processes.

## Offline references

**DOCS** in the desktop menu or **Space od** in vis opens installed manuals,
language references and Markdown example templates alongside the editor.
**Ctrl+B d** opens the reference picker in a dvtm pane. C/C++ manuals, Rust books
and API docs, Go documentation/example sources, Python library manuals, LLVM and
shell tools, the FreeBSD Handbook and project examples are available locally.
Code blocks retain their indentation and terminal styling. See
[OFFLINE-DOCS](OFFLINE-DOCS.md) for topics, commands and the installation check.

## Terminal and multiplexer

Patched foot provides Azeret Mono, 90% default-background opacity, explicit
5%-step opacity keys/reset, scrollback/search, clipboard/URL actions and a literal
visible-line picker. Text, selections and dividers stay opaque. vis/dvtm use
terminal-default backgrounds so they inherit the same transparency.

`work /path/to/project` starts or attaches a named abduco session. New sessions
use a 65% editor master and a right shell/Git stack, Ctrl+B controls, connected
dividers and copy mode. The selected pane's directory is obtained using FreeBSD
libprocstat. Both shell and dvtm emit OSC 7 and an encoded `NOSTROMO_CWD:file://`
display title. The compositor bounds/validates that title and draws the white
right rail from home at the top to the current project below; it never executes titles or treats them as trusted
filesystem instructions. Remote terminfo, Unicode width, resize and clipboard
behavior remain native tests.

Abduco preserves detached processes until shutdown, not across reboot. Dvtm uses
tags/tiling rather than tmux's independent split tree. oksh supplies its own
history/completion, zoxide, fuzzy file/directory helpers and aliases; it does not
imitate Zsh widgets it cannot implement. Noninteractive startup stays quiet.

## Embedded C/C++ and Rust

[EMBEDDED](EMBEDDED.md) is the complete terminal workflow: pinned Zephyr 4.5.0/west,
uv-managed native Python, LLVM/LLD/compiler-rt profiles, board enumeration,
menuconfig, build, flash context, OpenOCD/ST-Link/DFU, serial and remote LLDB.
It separately covers project-scoped Rust 1.98.1 no_std targets and Zephyr's
optional Rust module. No VS Code, Linux SDK, container or VM is used.

Architecture, word-size and ARM float-ABI guards reject incompatible runtime
profiles. Each runtime must contain archive members and link an actual bare-metal
ELF before it is published. The ARM host link check passed; no board was flashed.
The family matrix explicitly distinguishes STM32, NXP, ESP32 RISC-V vs Xtensa,
RP2040/RP2350 and full-size Raspberry Pis. FreeBSD is not an upstream supported
Zephyr getting-started host, and no generic LLVM installation establishes all-board
support. Hardware acceptance records build, flash, debug and peripheral results
for each exact board/probe separately.
