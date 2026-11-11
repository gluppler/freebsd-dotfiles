# Offline documentation

Press **Super+D**, choose **DOCS** in the launcher, or press **Space od** in vis. Manuals and example
templates open in a separate foot window, so the editor remains usable. Inside
abduco/dvtm, **Ctrl+B d** creates a documentation pane instead. Use **Ctrl+B h/j/k/l**
to move between the editor and the reference.

The terminal reader preserves code indentation and uses bold/underline for
headings, with the existing monochrome theme and Azeret Mono font. Use **j/k** to
scroll, **/** to search, **n/N** for matches, arrow keys for long lines and **q** to
close. The helper displays examples; it never executes them. HTML opens in a new
qutebrowser window and PDF documents open in zathura, each in its own window.
Every reference below is a local file; reading one downloads nothing.

## Installed references

| Subject | Local reference | Menu entry or command |
| --- | --- | --- |
| C and FreeBSD APIs | Base section 2/3 manuals | `nostromo-docs c malloc` |
| C and C++ language/library | Full cppreference HTML archive, including syntax and examples | **C LANGUAGE**, **C++ LANGUAGE** |
| C standard | ISO/IEC 9899:2024 (C23) working draft N3220, PDF | **C STANDARD** |
| POSIX | POSIX.1-2024 (The Open Group Base Specifications Issue 8), HTML | **POSIX** |
| C++ library | stdman, with declarations and examples | `nostromo-docs cpp std::vector` |
| C++ standard and practice | C++23 working draft N4950 (PDF) and the C++ Core Guidelines | **C++ STANDARD**, **C++ GUIDELINES** |
| Rust | Compiler/Cargo man pages, Book, Reference, standard library, Rust by Example and embedded book | **RUST BOOK**, `nostromo-docs rust std` |
| Go packages | Installed toolchain's `go doc` and example test sources | `nostromo-docs go fmt.Printf`, `nostromo-docs go-examples fmt` |
| Go language | Specification, memory model, assembler guide and GODEBUG history from the toolchain | **GO LANGUAGE** |
| Go command | Every `go help` command and topic, such as modules and build constraints | **GO COMMAND**, `nostromo-docs go-help modules` |
| Go by Example | 85 annotated programs with their recorded output, in reading order | **GO BY EXAMPLE** |
| Python | Installed Python 3.12 text and HTML manuals | `nostromo-docs python pathlib` |
| Python language/C API | Tutorial, Reference, C API, extending, HOWTOs, usage, FAQ and release notes | **PYTHON BOOK** |
| Lua | Lua 5.4 reference manual, the language of the vis configuration | **LUA MANUAL** |
| Shell and everyday tools | sh, oksh, make, Git, OpenSSH, PF, wg and desktop manuals | **SHELL AND TOOLS**, `nostromo-docs man sh` |
| CMake | cmake, ctest, cpack and the language, commands, variables, properties, modules, generator expressions, presets, toolchains and policy manuals | **CMAKE**, `nostromo-docs man cmake-buildsystem` |
| LLVM/assembly | LLVM assembler manual and local architecture examples | `nostromo-docs llvm`, `nostromo-docs examples assembly` |
| Arm ABI | AAPCS32, AAPCS64 and the System V ABI for AArch64, 2026Q3 | **ARM ABI** |
| Style | Google style guides for C++, Python, shell, Go, Rust and other languages, and its documentation guide | **STYLE GUIDES** |
| Systems | See [the systems library](#systems-library) | **SYSTEMS LIBRARY** |
| Electronics and robotics | See [the electronics guide](#electronics-guide): drawn, animated circuits with their laws and equations, from schematic symbols to PCBs and badges, and a formula sheet | **ELECTRONICS GUIDE**, `nostromo-docs electronics` |
| Circuits | MIT 6.002 lecture notes, Lessons in Electric Circuits and the Logisim guide | **CIRCUITS LIBRARY** |
| Robotics and control | Feedback Systems, robotic manipulation, autonomous robots and planning algorithms | **ROBOTICS LIBRARY** |
| PCBs and badges | A PCB design tutorial, the Tildagon badge documentation and two Hackaday badge schematics | **PCB AND BADGES** |
| Operations and networking | Selected chapters of The Book of Secret Knowledge | **SECRET KNOWLEDGE** |
| FreeBSD | Installed English Handbook and other books/articles | **FREEBSD HANDBOOK** |
| vis hooks and embedded work | Shipped examples, project guides and initialized Zephyr sources | `nostromo-docs examples vis`, `nostromo-docs examples zephyr` |
| Your own manuals | PDFs saved in `~/.local/share/nostromo/manuals` | **SAVED MANUALS** |

The example picker also covers C, C++, Rust, Go, Python and shell scripts. The
assembly examples cover x86-64, Thumb, AArch64 and MIPS32, with commands to inspect
instruction encodings. They are small starting points, not substitutes for the
exact CPU's ISA manual or the board's datasheet. Save those as PDFs in
`~/.local/share/nostromo/manuals`; **SAVED MANUALS** then lists them by file name.

**RUST BOOK** lists the books actually installed for the selected compiler:
Book, Reference, Rust by Example, embedded book, std/core/alloc, Cargo, rustc,
rustdoc, Clippy, Nomicon, edition/style guides and unstable features when bundled.
**PROJECT GUIDES** opens every installed guide of these dotfiles, from keyboard and
installation to browser, input methods, security, performance, firmware and boot,
with the same Markdown reader.

Language books, POSIX and the Handbook open **local HTML in a new qutebrowser window**, where
code blocks, links and the supplied search interface retain their layout. Rust's
reference follows the selected compiler's sysroot. The Python text reader opens
the installed manual directly; it does not import the named module. Go queries
set `GOTOOLCHAIN=local`, `GOPROXY=off` and `GOSUMDB=off` to prevent downloads.
The Markdown reader shows the text of embedded HTML and Jekyll tags, and image
descriptions in brackets, instead of the raw markup; code is shown as written.
MkDocs notes appear as quoted notes and content tabs as titled sections, not as code.

## Systems library

**SYSTEMS LIBRARY** offers each book, then its chapters by title, in the order of
the book's own table of contents:

- The System Design Primer and its worked interview solutions
- Awesome Scalability, a reading list of scalability, availability and stability patterns
- HTTP/2 explained and HTTP/3 explained, on the protocols and QUIC
- What happens when you type a URL and press Enter
- Let's Build a Simple Database, a SQLite clone in C, chapter by chapter
- Kubernetes the Hard Way
- The Art of Command Line and the pure sh bible

**SECRET KNOWLEDGE** holds six chapters selected from
[The Book of Secret Knowledge](https://github.com/trimstray/the-book-of-secret-knowledge): command-line and network
tools, systems, services and containers, manuals and tutorials, reading lists,
shell one-liners, and shell tricks and functions. They are committed with the
book's MIT license, so they need no download.

## Electronics guide

**ELECTRONICS GUIDE** offers the chapters of a local illustrated guide by title
and opens each in a qutebrowser window:

- Schematic symbols in both drawing styles, what each part does and its equation
- DC circuits: Ohm's and Kirchhoff's laws, dividers, Thévenin and Norton,
  superposition and node analysis
- Capacitors, inductors and AC: charging, phasors, impedance, filters, Bode plots
  and resonance
- Diodes and transistors, op-amps and comparators, and digital logic
- Signals, sampling and control: PWM, spectra, aliasing, smoothing, poles and a PID loop
- Robotics mathematics: rotations and transforms, arm kinematics, differential
  drive and odometry, motors and encoders, sensor fusion, the Kalman filter and A*
- Microcontroller hardware: pins, debouncing, level shifting, UART, I2C and SPI,
  regulators, battery life, decoupling and sensors
- PCB design: the design steps, stack-ups, track widths, return paths, decoupling,
  controlled impedance, footprints, fabrication files and bring-up
- Badges and projects: board art, SAO add-ons, Tildagon hexpansions, charlieplexing,
  addressable LEDs, key matrices, touch pads, lithium charging and project ideas
- A formula sheet of every named equation, each linked to where it is explained

The figures are drawn by the guide's own code: plots are computed from the
values shown, moving dots show conventional current, faster where more current
flows, and animated figures step through each case in turn. **Pause motion** at
the top of each page freezes the figures where they are, and a reduced-motion
preference keeps them on their first frame. Equations are MathML set in Noto Sans
Math. The pages run no scripts and load nothing from the network. The guide is
committed in `docs/electronics/`, so it needs no download; `.install/electronics/build.py`
regenerates it and `build.py --check` confirms that it matches its source.

The library holds the books the guide summarizes. **CIRCUITS LIBRARY** has the
25 lecture notes of MIT 6.002 Circuits and Electronics (Spring 2007), the six
volumes of Lessons in Electric Circuits and the Logisim 2.7.1 guide: tutorial,
user's guide and component reference. Logisim itself is not installed: it is a
Java Swing program, which needs X11, and this desktop runs Wayland only.
**ROBOTICS LIBRARY** has Feedback Systems (Åström and Murray), A Mathematical
Introduction to Robotic Manipulation (Murray, Li and Sastry), Introduction to
Autonomous Robots (Correll and others) and Planning Algorithms (LaValle).
**PCB AND BADGES** has David L. Jones' PCB Design Tutorial; the EMF Camp 2024
Tildagon badge documentation on hexpansion add-on boards, the hardware and
programming reference, assembly, repair and use, and writing apps, with examples;
the schematic of Hackaday's 2025 Communicator badge; and the board layers of its
2023 Vectorscope badge. PCB design itself runs on a separate server, so no PCB
design program is installed here.

Books still in print, such as The Art of Electronics, are not downloaded. Save a
copy you own as a PDF in `~/.local/share/nostromo/manuals` and **SAVED MANUALS**
lists it.

## Installation and updates

The installer adds five documentation-only packages: `stdman`, `python-doc-text`,
`python-doc-html`, `en-freebsd-doc` and `cmake-man`. The checked quarterly archives
have no package dependencies and occupy about **192 MiB** unpacked in total. Rust,
Go, Lua and LLVM documentation come with the already selected toolchains and
editor. This adds no background documentation service.

The installer also downloads a SHA256-pinned full cppreference HTML archive.
Its latest published offline snapshot found during review on **2026-11-05** is
**2025-02-09**, from the maintained fork linked by cppreference itself. It includes
the complete archived C/C++ reference tree and rendered examples. The separately
packaged stdman quick lookup remains the older **2024.07.05** snapshot.

Development-tool setup then installs the library from the `doc-*` records of
`.install/sources.lock`: 58 documents and archives, about **187 MiB** to download and
**217 MiB** unpacked in `~/.local/share/nostromo/library`. Each is checked against
its SHA256 and archives are confined to their own top directory. Where a record
names one directory of a larger archive, such as the guide inside Logisim's jar,
only that directory is extracted. A tree that
contains a special file, or a link leading outside itself, is refused. Only the
checked documents are kept: no archive, including cppreference's, stays on the
laptop. A rerun downloads only what changed. A document that no longer matches its
pin is downloaded again, an item whose pin changes is replaced, and an item no
longer pinned is removed.

Choose **REFERENCE VERSIONS** or run `nostromo-docs versions` to see the installed
toolchain/manual versions, the pinned standards and the checksum of each library
archive. Rust and Go references follow their selected toolchain; the Python books
follow the pinned Python 3.12 package line (currently 3.12.15). The C and C++
standards are the public working drafts that match C23 and C++23 apart from
editorial changes. These are version-matched references, not a
promise to cover every future language feature, compiler extension, external
library or vendor ISA. This setup does not label a dated snapshot as a live, fully
current website.

Locally built desktop programs now install their manuals under
`~/.local/share/man`. The profile adds this directory to `MANPATH` and preserves
FreeBSD's default paths. Base C/system-call manuals must be present too; do not
omit them during a minimal or pkgbase installation.
The staged `vis.1.gz` link points to FreeBSD's packaged `vise` manual, matching
the editor wrapper's command name.

Before setup enables graphical login, `nostromo-docs --check` verifies essential
manuals, the CMake manuals, Rust books, Python references, the Lua manual, the Go
documents and command help, the Handbook, examples, every library document, every
Go by Example program, the Secret Knowledge chapters, the electronics guide and a
local Go query.
An absent document fails that stage. `man nostromo-docs` explains the command.

Use the software menu to update documentation packages with the reviewed package
set. A new cppreference archive requires updating its URL/hash in `.install/sources.lock`,
the dated install directory and snapshot label, then rerunning development-tool
setup and relinking. To change a library document, update its `doc-*` record in
`.install/sources.lock`; to add one, add a record and its line in the reader's catalogue.
Existing embedded Rust toolchains created before this change can add their
matching documentation while online:

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

## Licenses

The library is downloaded from its publishers, never committed, and keeps their
terms: the POSIX HTML is The Open Group's download for personal use and the C++
Core Guidelines allow personal or internal business use. The C and C++ drafts are
the committees' public documents. The Arm ABI documents are CC BY-SA 4.0 with a
patent grant. Go by Example and the Google style guides are CC BY 3.0; the System
Design Primer and the HTTP/2 and HTTP/3 books are CC BY 4.0; The Art of Command
Line is CC BY-SA 4.0; What happens when is CC0; Awesome Scalability, the database
tutorial and the pure sh bible are MIT. Kubernetes the Hard Way ships an Apache 2.0
license file while its copyright notice puts the content under CC BY-NC-SA 4.0.
The MIT 6.002 notes are CC BY-NC-SA 4.0; Lessons in Electric Circuits and the
Tildagon documentation are CC BY 4.0; the Logisim guide is GPL version 2 or later;
Introduction to Autonomous Robots is CC BY-NC-ND 4.0. Feedback Systems and
A Mathematical Introduction to Robotic Manipulation are for personal use only,
Planning Algorithms is its author's free download, and the PCB Design Tutorial is
free for educational and personal use. The Communicator and Vectorscope badge
repositories are MIT. The exact sources and checksums are in `.install/sources.lock`.

Sources: [FreeBSD package documentation](https://docs.freebsd.org/en/books/handbook/ports/),
[cppreference offline archives](https://en.cppreference.com/Cppreference:Archives),
[stdman](https://github.com/jeaye/stdman),
[Rust components](https://rust-lang.github.io/rustup/concepts/components.html),
[Go documentation command](https://go.dev/doc/cmd),
[Go toolchain selection](https://go.dev/doc/toolchain),
[Python offline formats](https://docs.python.org/3.12/download.html),
[WG14 documents](https://www.open-std.org/jtc1/sc22/wg14/www/docs/),
[WG21 papers](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/),
[POSIX.1-2024](https://pubs.opengroup.org/onlinepubs/9799919799/),
[Arm ABI releases](https://github.com/ARM-software/abi-aa/releases),
[MIT 6.002 lecture notes](https://ocw.mit.edu/courses/6-002-circuits-and-electronics-spring-2007/pages/lecture-notes/),
[Lessons in Electric Circuits](https://www.ibiblio.org/kuphaldt/electricCircuits/),
[Logisim](https://cburch.com/logisim/index.html) and the
[Tildagon documentation](https://github.com/emfcamp/badge-2024-documentation).
