# Packages, dependency policy and maintenance

The executable manifests are `packages.txt` (desktop/development roots),
`packages.local` (21 ordered native variants), and `packages.allowed` (reviewed
names, origins, version constraints and roles). The installer resolves the actual
FreeBSD quarterly dependency graph and checks every archive before installation.
These rules are implemented; a complete native build/install has not run on the
laptop. A cached catalog or an older OpenBSD audit is not that result.

## Scope of the GNU exceptions

Stock FreeBSD base stays intact. Git is explicitly retained as `git-lite`; its
name describes the reduced FreeBSD package, not the removal of Git. GPL licensing
does not by itself make a project GNU. The exact added GNU exceptions are:

| Role | Package and reviewed version | Reason |
| --- | --- | --- |
| Runtime | gettext-runtime 1.0_1 | Translation ABI used by required packaged clients/libraries; removing it requires rebuilding their consumers |
| Runtime | libiconv 1.18_1 | Required encoding ABI in the native packaged desktop closure; base iconv is not a drop-in package ABI replacement |
| Runtime | gmp 6.3.0 | Packaged ShellCheck/Haskell runtime dependency; LLVM does not replace the Haskell integer runtime |
| Runtime | libgcrypt 1.12.4; libgpg-error 1.61 | libsecret encrypted credential backend required by KiCad/wxWidgets; disabling encryption is not a replacement |
| Build | gmake 4.4.1 | Required upstream build recipes in the native ports dependency chain |
| Build | gettext-tools 1.0; libtextstyle 1.0; libunistring 1.4.2 | Required translation/build-tool chain; these do not authorize unrelated GNU runtime libraries |
| Build | gperf 3.3 | Zephyr kernel-object table generation |

These are exact policy entries, not wildcard GNU approval. Build-only means the
purpose of the exception, not automatic deletion after a build: tools remain
available for subsequent reviewed rebuilds. Upstream source archives also contain
GNU-generated configure/libtool scripts. This checkout does not claim that those
build scripts are GNU-free. No Bash/GCC/GnuPG toolchain is added by default.

## Native variants

`ports.lock` pins the FreeBSD ports archive to commit
`92ed857ab5f20e13114a4c01193751e7f0866a36`, with SHA256 verification. The variants
are Python 3.12, CMake, libxml2, libxslt, libpsl, curl, CUPS, Imath, FFmpeg,
wlroots 0.20, Hunspell, fcitx5, PipeWire, PyQt6, Python ECDSA, ngspice shared
library, wxGTK, OpenCASCADE, Poppler, Poppler GLib and KiCad.
`system/ports.conf` and `src/ports/` are the reviewed options/patches: libedit in
place of Readline where supported, ICU/OpenSSL where appropriate, reduced Qt
bindings and disabled optional GNU-heavy or X11 features. ECDSA uses its native
Python implementation without optional GMPY/GMPY2. The [KiCad workflow](EDA.md)
omits optional wxPython/WebKit, Draw/VTK/Qt examples and PDF-signature engines.
The ngspice shared build uses the release configure script, with no Readline or
X11 frontend. Its old-release download path is corrected without changing the
pinned checksum. Poppler uses its supplied generated lookup tables, avoiding
GNU sed regeneration. OpenCASCADE packages the files its selected CMake modules
actually install; the normal stage/QA and dependency gates still apply.

Builds run as the desktop user, using the pinned ports framework, native Clang,
ordinary-user staging and `check-plist`. Dependency lists pass through the same
root package gate. A recipe hash covers the manifests/options/patches and is
attached to each local archive. Local variants are locked after installation;
a normal update cannot silently replace them with stock binaries. Rebuild through
the PORTS menu, or rerun the installer after a reviewed recipe change.

The initial manual Git install can bring stock variants and automatic GNU
libraries. Bootstrap conversion accepts only an unlocked stock package with the
exact expected name, origin and version, or a previously accepted project receipt.
Cleanup removes only explicit unwanted GNU entries that are automatic, unlocked,
non-vital, have no reverse dependencies and provide no required local-library ABI.
Manual packages and still-needed libraries are preserved and reported for review.
There is no blanket autoremove or forced cascading deletion.

## Transaction and update behavior

`scripts/packages.sh` uses the signed FreeBSD 15 amd64 quarterly repository,
checks each package identity/ABI/dependency edge and rejects unknown origins,
missing receipts or unreviewed GNU versions. It copies the checked archives into
a private locally signed transaction repository, previews the operation, then
installs with `--no-remove`. It records the exact graph and archive hashes under
`/var/db/nostromo/packages/`. Existing system repository files are preserved.

The menu's **UPDATE** refreshes the catalogue, audits the installed application
set and its dependencies, then uses `pkg upgrade` against that private repository.
`pkg install` remains the command for adding selected packages. Updates preserve
the automatic/manual package flags and the existing build-tool protection list.
They do not turn every optional application into a required desktop component.

Native staged programs are checked with `ldd`; their required shared libraries
become a root-owned ABI-retention list. Required desktop roots, local variants,
reviewed build tools and their dependency closure are protected from removal.
The removal check also rejects pkg itself, base packages, locked/vital entries,
packages with consumers and providers of libraries used by locally built programs.
This check matters because native `pkg delete` can expand its deletion list to
include consumers. The menu never requests forced, recursive or orphan removal.
Updates stop when a reviewed version/ABI no longer fits; they do not relax policy
to make the update succeed. Review new versions and rebuild affected consumers.

SOFTWARE (`Super+F5`, or `software` in oksh) provides search, install, details,
update, **remove**, reviewed ports, base patches and firmware. Unknown catalog
entries are visible as unreviewed but cannot be installed until their full graph
is reviewed. PORTS rebuilds the selected maintained variant; it does not execute
arbitrary Makefiles as root. Privileged actions use base **mdo**.

## Does an update need to run twice?

Usually, **no**. `pkg update` refreshes repository metadata; it does not upgrade
installed software. `pkg upgrade` performs that upgrade. They are different
operations, rather than two passes of the same update.

The reviewed pkg **2.8.4** source handles its own upgrade first when necessary,
then restarts the original command with the newly installed binary. The wrapper
keeps the private signed repository available throughout that restart. Afterward,
it checks dependency health without installing repairs, checks installed package
identities and reports versions still behind the audited repository. It also
verifies that existing automatic flags were preserved. A lock, failed script or
interrupted transaction stops completion; the wrapper does not hide it by blindly
retrying. Read the output and receipt before rerunning the menu action.

`pkg check -B` is a compatibility no-op in that pkg version, so it has been
removed. `pkg check -d -n -a` performs the dependency check without fetching or
installing a repair outside the audited transaction.

Repeated `freebsd-update install` steps belong to the **base release-upgrade**
procedure: install the new kernel, reboot, install userland and, for a major
upgrade, rebuild/reinstall third-party packages before removing old libraries.
Follow the Handbook for that procedure. The software menu applies ordinary base
patches; it does not start a release upgrade or reboot the laptop.

## Base and firmware maintenance

Traditional distribution sets use `freebsd-update fetch` followed by
`freebsd-update install`. The maintenance helper detects pkgbase and uses its
separate signed base repository instead; it never mixes methods or converts the
base silently. Firmware detection uses base `fwget -nq`, then the package gate.
No automatic reboot or major release upgrade is performed.

Sources: [FreeBSD packages and ports](https://docs.freebsd.org/en/books/handbook/ports/),
[base updates](https://docs.freebsd.org/en/books/handbook/cutting-edge/),
[pkg upgrade](https://github.com/freebsd/pkg/blob/2.8.4/docs/pkg-upgrade.8),
[pkg self-restart](https://github.com/freebsd/pkg/blob/2.8.4/src/main.c),
[dependency checks](https://github.com/freebsd/pkg/blob/2.8.4/src/check.c),
[pkg delete](https://github.com/freebsd/pkg/blob/2.8.4/docs/pkg-delete.8), and
[pkg query fields](https://github.com/freebsd/pkg/blob/2.8.4/docs/pkg-query.8).
