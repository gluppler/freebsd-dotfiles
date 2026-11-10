# Packages, dependency policy and maintenance

The executable manifests are `packages.txt` (desktop/development roots),
`packages.local` (15 ordered native variants), and `packages.allowed` (reviewed
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
wlroots 0.20, Hunspell, fcitx5, PipeWire, PyQt6 and Python ECDSA.
`system/ports.conf` and `src/ports/` are the reviewed options/patches: libedit in
place of Readline where supported, ICU/OpenSSL where appropriate, reduced Qt
bindings and disabled optional GNU-heavy or X11 features. ECDSA uses its native
Python implementation without optional GMPY/GMPY2. Readline's ports module also
adds the `/usr/local` include and library search paths. Python's patch keeps them
for its system libmpdec and expat; Hunspell links nothing from there, and PipeWire
gets them from `USES=localbase`.

Builds run as the desktop user, using the pinned ports framework, native Clang,
ordinary-user staging and `check-plist`. Dependency lists pass through the same
root package gate. When pkg's advisory file (`/var/db/pkg/vuln.xml`, fetched by
the nightly security run) lists a variant, its build prints pkg's report and
continues. The ports framework would otherwise refuse every later build of that
variant, even a finished one, until a pinned tree carries a fix; stock packages
are built without that check. The nightly report still lists vulnerable installed
packages. A recipe hash covers the manifests/options/patches and is
attached to each local archive. When the hash changes, preparation replaces an
unedited generated ports tree and its build work; an edited tree stops for review.
Local variants are locked after installation; a normal update cannot silently
replace them with stock binaries. Rebuild through the PORTS menu, or rerun the
installer after a reviewed recipe change.

The initial manual Git install can bring stock variants and automatic GNU
libraries. Bootstrap conversion accepts only an unlocked stock package with the
exact expected name, origin and version, or a previously accepted project receipt.
Cleanup removes only explicit unwanted GNU entries that are automatic, unlocked,
non-vital, have no reverse dependencies and provide no required local-library ABI.
Manual packages and still-needed libraries are preserved and reported for review.
There is no blanket autoremove or forced cascading deletion.

## Transaction and update behavior

`scripts/packages.sh` uses the signed FreeBSD 15 amd64 quarterly repository,
with kernel-module packages selected from `kmods_quarterly_${VERSION_MINOR}`
(`kmods_quarterly_1` on FreeBSD 15.1),
checks each package identity/ABI/dependency edge and rejects unknown origins,
missing receipts or unreviewed GNU versions. It copies the checked archives into
a private locally signed transaction repository and records pkg's dry-run plan.
A plan that removes any package, or that the helper does not recognize, stops
the transaction. pkg 2.8.4 has no option that forbids removal, so the reviewed
command receives exactly one approval: a conflict that makes pkg propose a second
solution reads end-of-input and stops instead of being approved again. It records
the exact graph, plans and archive hashes under `/var/db/nostromo/packages/`.
Existing system repository files are preserved.
The private upstream names do not depend on the system repositories being named
`FreeBSD`, `FreeBSD-ports` or `FreeBSD-ports-kmods`. Disabled pkgbase repositories
are not enabled by an application transaction. The kmods URL follows the
[release repository configuration](https://github.com/freebsd/freebsd-src/blob/releng/15.1/usr.sbin/pkg/FreeBSD.conf.quarterly-release).

The archive reader accounts for pkg's empty-list output: a mixed query containing
`%n` and dependency fields can produce `D|owner|||` for a leaf package. Only a
fully empty dependency placeholder is removed. Declared dependency counts,
nonempty identities, origins, ABI, versions and local-build receipts still have
to pass the unchanged audit. Query failures stop the transaction before package
installation. See [pkg's query implementation](https://github.com/freebsd/pkg/blob/2.8.4/src/query.c).

Architecture-independent packages, such as fonts, headers and Python modules,
carry pkg's `FreeBSD:15:*` ABI; 128 of the 507 reviewed repository packages do in
the cached 2026Q4 catalogue. The audit accepts that exact FreeBSD 15 wildcard, as
pkg does, and still rejects any other release, architecture or broader pattern.
After installation, every audited package must be present with its reviewed
origin and ABI. That check does not
require the transaction's version: pkg leaves an older installed dependency in
place when a new package does not need it replaced. UPDATE reports any version
still behind the audited repository.

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
then restarts the original command with the newly installed binary, which solves
the remaining plan again. Because each plan receives one approval, the wrapper
upgrades pkg as its own reviewed transaction whenever the transaction repository
contains pkg. The restarted command then has nothing left to approve, and the
remaining plan is reviewed and approved separately. The wrapper keeps the private
signed repository available throughout. Afterward,
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
