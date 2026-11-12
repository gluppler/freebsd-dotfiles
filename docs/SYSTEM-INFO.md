# Laptop information

Run `fetch`, `nostromo-fetch`, **SYSTEM INFO** in the launcher, or press Super+Ctrl+I. Fastfetch uses
a detailed profile with the original monochrome 2D orb and Azeret Mono font.
In an interactive terminal, the report opens beside the gently floating orb.
Narrow windows put the orb above the information; very small windows prioritize
the report. Resize freely. Use `j/k` or Ctrl+N/P to scroll, Space/`b` for pages,
`g/G` for the start/end, `h/l` for long columns, and `q`, Esc or Enter to close.

The report is captured once per invocation. Only the logo animates; sensors are
not repeatedly polled. Closing the view stops its process and restores the
terminal. Static/off effects keep a still orb without a periodic redraw.
Use `nostromo-fetch --plain` for ordinary scrollback output. Redirected output
and explicit Fastfetch options bypass the interactive view.

The profile includes OS/kernel/boot and firmware details; CPU physical cores,
logical threads, temperature and load; memory/swap; GPU/graphics APIs; physical
storage, filesystems and ZFS; battery/power; displays/brightness; compositor,
login manager, themes/fonts, terminal/editor; network interfaces, DNS, Wi-Fi,
WireGuard, Bluetooth, audio and input devices. Values are detected at runtime.
There are no copied RAM sizes, CPU counts, firmware versions, addresses or
hardware identifiers in the configuration.

Some FreeBSD drivers do not expose every sensor or hardware field. Fastfetch
skips unavailable modules by default; `nostromo-fetch --show-errors` explains
missing detections. A missing temperature is not reported as zero. TPM presence
does not establish enrollment, and an HCI controller is not proof of a working
Bluetooth audio profile. WireGuard's brief status reports the interface state,
not peer reachability; use the VPN manager for handshake details.

The profile makes no weather/public-IP request and starts no monitoring daemon.
It runs as the ordinary user and does not prompt for root. Local IP/MAC and Wi-Fi
details can appear in the report, so review an output before sharing it publicly.
For raw fields supplied by each module, use `nostromo-fetch --format json`.

The same report works on the text console. Its key symbols (`◆ ↑ › ■ ≡ ▬`) and
the orb's block characters exist in FreeBSD 15.1's built-in console font and in
the loader's 16x32 Terminus that the T14's panel selects. The earlier `◈ ▣ ▤ ▰`
are in neither and showed as broken glyphs there. Fastfetch aligns values with a
cursor-column escape (`ESC[18G`) even in pipe mode; the interactive view now
turns it into padding. It printed `[18G` on every line before.

Configuration: `fastfetch/config.jsonc`, checked against fastfetch
2.69.0's schema and parser. The wrapper accepts normal fastfetch overrides.
See the [upstream configuration reference](https://github.com/fastfetch-cli/fastfetch/wiki/Configuration).
