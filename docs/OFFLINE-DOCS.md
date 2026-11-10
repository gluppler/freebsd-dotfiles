# Offline documentation

Choose **DOCS** in the launcher, or press **Space od** in vis. Manuals and example
templates open in a separate foot window, so the editor remains usable. Inside
abduco/dvtm, **Ctrl+B d** creates a documentation pane instead. Use **Ctrl+B h/j/k/l**
to move between the editor and the reference.

The terminal reader preserves code indentation and uses bold/underline for
headings, with the existing monochrome theme and Azeret Mono font. Use **j/k** to
scroll, **/** to search, **n/N** for matches, arrow keys for long lines and **q** to
close. The helper displays examples; it never executes them.

## Installed references

| Subject | Local reference | Example |
| --- | --- | --- |
| C and FreeBSD APIs | Base section 2/3 manuals | `nostromo-docs c malloc` |
| C and C++ language/library | Full cppreference HTML archive, including syntax and examples | `nostromo-docs language c`, `nostromo-docs language cpp` |
| C++ library | stdman, with declarations and examples | `nostromo-docs cpp std::vector` |
| Rust | Compiler/Cargo man pages, Book, Reference, standard library, Rust by Example and embedded book | `nostromo-docs rust std` |
| Go | Installed toolchain's `go doc` and example test sources | `nostromo-docs go fmt.Printf`, `nostromo-docs go-examples fmt` |
| Go language | Installed toolchain's complete language specification | `nostromo-docs go-language` |
| Python | Installed Python 3.12 text and HTML manuals | `nostromo-docs python pathlib` |
| Python language/C API | Tutorial, Reference, C API, extending, HOWTOs, usage and release notes | `nostromo-docs python-book reference` |
| Shell and everyday tools | sh, oksh, make, Git, OpenSSH, PF, wg and desktop manuals | `nostromo-docs man sh` |
| LLVM/assembly | LLVM assembler manual and local architecture examples | `nostromo-docs llvm`, `nostromo-docs examples assembly` |
| FreeBSD | Installed English Handbook and other books/articles | `nostromo-docs freebsd` |
| vis hooks and embedded work | Shipped examples, project guides and initialized Zephyr sources | `nostromo-docs examples vis`, `nostromo-docs examples zephyr` |

The example picker also covers C, C++, Rust, Go, Python and shell scripts. The
assembly examples cover x86-64, Thumb, AArch64 and MIPS32, with commands to inspect
instruction encodings. They are small starting points, not substitutes for the
exact CPU's ISA manual or the board's datasheet.

**RUST BOOK** lists the books actually installed for the selected compiler:
Book, Reference, Rust by Example, embedded book, std/core/alloc, Cargo, rustc,
rustdoc, Clippy, Nomicon, edition/style guides and unstable features when bundled.
**PROJECT GUIDES** opens the local keyboard, development, installation,
package and hardware guides with the same Markdown reader.

Language books and the Handbook open **local HTML in a new qutebrowser window**, where
code blocks, links and the supplied search interface retain their layout. Rust's
reference follows the selected compiler's sysroot. The Python text reader opens
the installed manual directly; it does not import the named module. Go queries
set `GOTOOLCHAIN=local`, `GOPROXY=off` and `GOSUMDB=off` to prevent downloads.

## Installation and updates

The installer adds four documentation-only packages: `stdman`, `python-doc-text`,
`python-doc-html` and `en-freebsd-doc`. The checked quarterly archives have no
package dependencies and occupy about **191 MiB** unpacked in total. Rust and
LLVM documentation come with the already selected toolchains. This adds no
background documentation service.

The installer also downloads a SHA256-pinned full cppreference HTML archive.
Its latest published offline snapshot found during review on **2026-11-05** is
**2025-02-09**, from the maintained fork linked by cppreference itself. It includes
the complete archived C/C++ reference tree and rendered examples. The separately
packaged stdman quick lookup remains the older **2024.07.05** snapshot.

Choose **REFERENCE VERSIONS** or run `nostromo-docs versions` to see the installed
toolchain/manual versions and snapshot date. Rust and Go references follow their
selected toolchain; the Python books follow the pinned Python 3.12 package line
(currently 3.12.15). These are version-matched references, not a promise to cover
every future language feature, compiler extension, external library or vendor ISA.
This setup does not label a dated snapshot as a live, fully current website.

Locally built desktop programs now install their manuals under
`~/.local/share/man`. The profile adds this directory to `MANPATH` and preserves
FreeBSD's default paths. Base C/system-call manuals must be present too; do not
omit them during a minimal or pkgbase installation.
The staged `vis.1.gz` link points to FreeBSD's packaged `vise` manual, matching
the editor wrapper's command name.

Before setup enables graphical login, `nostromo-docs --check` verifies essential
manuals, Rust books, Python references, the Handbook, examples and a local Go query.
An absent document fails that stage. `man nostromo-docs` explains the command.

Use the software menu to update documentation packages with the reviewed package
set. A new cppreference archive requires updating its URL/hash in `sources.lock`,
the dated install directory and snapshot label, then rerunning development-tool
setup and relinking. Existing embedded Rust toolchains created
before this change can add their matching documentation while online:

```sh
RUSTUP_HOME="$HOME/.local/share/nostromo/rustup" \
CARGO_HOME="$HOME/.local/share/nostromo/cargo" \
rustup component add --toolchain 1.98.1 rust-docs
```

The initialized Zephyr workspace retains its source documentation, headers and
sample applications. The dotfiles do not download every vendor's programming
manual. Save the chosen board/CPU/probe documents and fetch required west/Cargo/Go
dependencies while online. An offline reference library does not make uncached
build dependencies available.

Sources: [FreeBSD package documentation](https://docs.freebsd.org/en/books/handbook/ports/),
[cppreference offline archives](https://en.cppreference.com/Cppreference:Archives),
[stdman](https://github.com/jeaye/stdman),
[Rust components](https://rust-lang.github.io/rustup/concepts/components.html),
[Go documentation command](https://go.dev/doc/cmd),
[Go toolchain selection](https://go.dev/doc/toolchain), and
[Python offline formats](https://docs.python.org/3.12/download.html).
