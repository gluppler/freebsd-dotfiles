# Performance, available resources and battery

The target is responsive interactive use, full useful CPU capacity for builds,
accelerated graphics and low idle activity. There are no measured FreeBSD results
from this laptop yet. Wayland, fewer daemons and a lean compositor do not by
themselves establish better battery life.

## CPU policy

The i5-1135G7 is a four-core/eight-thread Intel platform. Keep firmware SpeedStep,
CPU power management and Hyper-Threading enabled. Check:

```sh
sysctl hw.ncpu
sysctl dev.cpufreq.0.freq_driver
sysctl -a | grep '^dev.hwpstate_intel\.[0-9][0-9]*\.epp:'
```

If **hwpstate_intel** is attached, retain it. Its EPP scale is **0–100**: lower
values prefer performance, higher values efficiency. This is a hardware policy
hint, not a guaranteed clock/throughput setting or an allocation of CPU time.
Configured starting profiles, to measure rather than advertise as optimal:

| Profile | Detected HWP EPP nodes | Intended use |
| --- | --- | --- |
| AC performance | 0 | Available throughput on AC, with normal idle-state support |
| Battery balanced | 50 | Starting point for the new battery-efficiency priority |
| Battery saver | 80 | Explicit optional endurance comparison |

The root-owned `nostromo-performance` helper and devd hook apply only present
nodes on AC transitions and honor the saved manual override. They do not silently
force package-vs-core control or write unsupported sysctls. Query ACPI state
instead of assuming an AC event argument is trustworthy. Do not run powerd or
powerdxx alongside HWP as a second competing governor. If HWP is absent, inspect
the attached cpufreq driver and use FreeBSD powerd only through its documented
fallback path; do not disable HWP just to make a copied powerd recipe apply.
[FreeBSD power guide](https://docs.freebsd.org/en/books/handbook/config/#configtuning-power-management),
[hwpstate_intel(4)](https://man.freebsd.org/cgi/man.cgi?query=hwpstate_intel&sektion=4&manpath=FreeBSD+15.1-RELEASE).

Keep GENERIC/SMP, the release scheduler and thermal/fan safeguards. No manual fan
mode, fixed max frequency, forced PCIe ASPM state, custom scheduler or disabling
NX/ASLR/mitigations without a specific measured reason. The old OpenBSD apmd,
`hw.perfpolicy`, `hw.blockcpu` and login-class formulas are not FreeBSD tuning.

## Graphics and effects

Use a release-compatible Intel DRM driver/firmware and native Wayland clients.
Verify hardware rendering rather than accept llvmpipe/software rendering as a
successful performance configuration. Choose output modes/scales from actual
EDID/support; do not force 4K/8K simply because wallpaper exports exist.

Keep hardware cursor/direct scanout where compatible with the chosen effects.
A whole-output CRT pass can prevent direct scanout and increase redraw/power.
Measure the tradeoff. The space_dots reference has a nominal 96-sample bloom,
time-dependent full-screen effects and fixed dimensions; it cannot be dropped
unchanged into a battery-conscious dwl renderer. See [DESIGN.md](DESIGN.md).
Animated/static/off modes are implemented in `dwl/crt.h`. Animated mode
requests up to 12 effect refreshes/second; static/off disarm that timer. The short
map fade shares this timer and finishes when effects become static/off. Cap effect refresh independently from input/render latency
when that is possible without visual damage. The 90% panel opacity remains in
every mode. Foot, menus and notifications use background alpha; other application
contents are blended by dwl. This needs composition of the pixels underneath,
but adds no blur pass or separate timer. Measure its cost on the laptop.

## Memory and storage

Detect `hw.physmem` and the active login limits. The owner has confirmed 16 GiB
RAM and eight logical CPUs with native sysctl. Do not impose OpenBSD's old 8/12 GiB per-process limit formula on FreeBSD,
reserve all RAM for builds, or raise every kernel limit to an arbitrary maximum.
Increase a real limiting process/file limit only after reproducing that limit;
keep user overrides and record values before/after.

Default build parallelism should consider actual logical CPUs and memory per
compiler/linker job. Eight hardware threads do not imply eight simultaneous
memory-heavy QtWebEngine/LLVM links are safe. Never use the laptop to rebuild all
ports just to install a desktop.

Keep ZFS compression and reclaimable ARC behavior at supported defaults first,
dedup off, synchronous writes intact and usable free space. Review TRIM support
and schedule before enabling it; do not send arbitrary NVMe feature commands or
disable write barriers. With UFS, use the filesystem's own supported defaults.
Keep the requested 16 GiB swap partition as pressure protection; it is not a
FreeBSD hibernation guarantee. Read SSD health without writing controller settings.

## Measure idle and load

Record a five-minute settled idle with the same brightness, Wi-Fi, output count
and browser state, then the same repeated build/test workload. Compare effects
animated/static/off and AC/battery profiles separately. Capture process RSS,
CPU wake/redraw activity, temperatures, runtime and battery energy change.
Report kernel/wired memory, application RSS, GPU buffers and reclaimable cache
separately. One 32-bit 1080p frame is about 7.9 MiB, one 4K frame about 31.6 MiB,
before additional buffers. A complete GUI cannot be guaranteed to fit in a few
MiB; helper footprint and low idle work are practical optimization targets.

The splash/login/lock space_dots treatment updates at about 30 Hz while animated.
Native logo rendering reuses a 1 MiB cache; small repeated tiles supply grain and
scanlines. Static/off stop those animation clocks. The desktop GPU pass still
uses its separate 12 Hz idle timer; an animating client can request more frames.
Measure both client and compositor power on hardware, including mixed-DPI docks.
