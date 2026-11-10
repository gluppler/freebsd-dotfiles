# Target controls for FreeBSD / Wayland

These bindings are configured in the migrated sources and helpers. Native
keyboard/layout, client behavior and hardware acceptance remain laptop tests.

Super is the Windows key. foot uses Alt for terminal actions. dvtm uses Ctrl+B,
released before the next key. vis retains its normal modal editing keys.

| Desktop | Action |
| --- | --- |
| Super+Enter / Space | foot / unified app, action, filename and content search |
| Super+Shift+Space | Desktop action menu, including DOCS, SOFTWARE and PORTS |
| Super+P | Project/session selector |
| Super+Shift+N / Shift+E | vis / nnn files |
| Super+B / Shift+D | qutebrowser / server-hosted Discord UI in qutebrowser |
| Super+J/K / H/L | Focus client / resize master area |
| Super+Shift+J/K | Move client in stack |
| Super+W/E/R | Tile / floating (default) / monocle |
| Super+Shift+F | Toggle fullscreen |
| Super+Ctrl+W | Wi-Fi scan/connect menu |
| Super+Ctrl+Space | Cycle US / Japanese / Korean input method |
| Super+Shift+R | Toggle floating for the focused window |
| Super+Ctrl+H/J/K/L | Move a floating window left/down/up/right |
| Super+Ctrl+Shift+H/J/K/L | Shrink width / grow height / shrink height / grow width |
| Super+1…9 / Shift+1…9 | View tag / move client to tag |
| Super+comma/period | Focus monitor; add Shift to move client |
| Super+apostrophe | Scratch terminal |
| Super+minus/equals | Adjust gaps; Shift+equals resets |
| Super+Q / Shift+Q | Close client / log out through the power helper |
| Super+G | Show/hide the bar |
| Super+Ctrl+B | Native Bluetooth menu |
| Super+Alt+H/J/K/L | Move the pointer; add Shift for fine movement |
| Super+Alt+Enter / Backspace | Left / right click |
| Super+Alt+comma/period | Scroll up / down |
| Super+Shift+L | Lock |
| Super+Shift+C | CRT toggle |
| Super+Shift+S / Ctrl+S | Focused-window screenshot / full screenshot |
| Super+Ctrl+D / Ctrl+P / Ctrl+C | Display layout / power / clipboard menu |
| Super+Ctrl+A | Native audio level, mute, input/device routing and recording controls |
| Super+N / Ctrl+N / Ctrl+Shift+N | Dismiss notification / recall history / quiet toggle |
| Brightness/audio/mic keys | FreeBSD backlight / audio controls |

Pointer keys run inside dwl. Floating-window movement/resizing leaves tiled and
fullscreen clients alone. There is no client-preserving compositor restart key:
ending a Wayland compositor disconnects its clients. Save work and log out/in
when replacing it. Ctrl+Alt+F1…F12 switches to a console.

The launcher accepts a query, then offers combined results. An empty query lists
apps/actions; Escape cancels. **SOFTWARE** opens the keyboard package/update/ports
menu in foot; `software` runs it from oksh. System changes authenticate through
base su/PAM, then use mdo and the shared
GNU dependency gate. Search roots, controls and limits are in
[PACKAGES.md](PACKAGES.md).

DISPLAYS also exposes detected resolutions/refresh rates, rotation and primary
output. CLAMSHELL selects DOCKED or PORTABLE lid behavior for this boot; enable
an external monitor first. CRT STATIC retains CRT shading/transparency while
removing the continuous sweep. See [HARDWARE.md](HARDWARE.md) and
[PERFORMANCE.md](PERFORMANCE.md).

The desktop action menu includes **VPN** for native WireGuard status/up/down in
the native fuzzel panel. The oksh alias `vpn` runs the same helper. Configure real peer details
first using [WIREGUARD.md](WIREGUARD.md); an interface being UP is not proof of
peer reachability.

The native lock keeps a bouncing logo, masked Password input and animated outer
brackets. Suspend waits for compositor lock acknowledgement; native PAM, hotplug
and resume still need the laptop acceptance pass.

| Patched foot | Action |
| --- | --- |
| Alt+C / V | Copy / paste |
| Alt+A / S / Shift+A | Lower / raise background opacity in 5% steps / reset to 90% |
| Alt+J/K / U/D | Scroll lines / half-pages in the current foot config |
| Ctrl+Shift+Up/Down | Font size |
| Alt+L / Y | Open URL / copy URL in the current foot config |
| Alt+O | Pick a visible line and copy it literally to the Wayland clipboard |
| Shift+mouse selection | Select locally when an application captures the mouse |

`work /path/to/project` starts or attaches one abduco session for that physical
project path. New sessions open vis in the left 65%, with an oksh shell and Git
stacked on the right. Quitting lazygit leaves an oksh shell. The bottom bar shows
tags, layout, project directory and time. Connected horizontal/vertical dividers
separate panes. Their backgrounds inherit foot transparency, including vis; text
and selected-row highlights remain opaque. The right window rail follows the
focused pane directory.

| dvtm / abduco | Action |
| --- | --- |
| Ctrl+B, c / \| / - | New terminal inheriting the selected pane's directory |
| Ctrl+B, C | New terminal in the session's original project directory |
| Ctrl+B, h/j/k/l | Directional focus |
| Ctrl+B, N/P | Next/previous non-minimized pane |
| Ctrl+B, H/L | Shrink/grow master width |
| Ctrl+B, Enter | Promote the focused terminal to master |
| Ctrl+B, z / Space | Fullscreen layout / cycle layouts |
| Ctrl+B, f / G / b | Master-and-stack / grid / bottom-stack layout |
| Ctrl+B, 1…9 / Tab | Focus terminal / last terminal |
| Ctrl+B, [ | Scroll/copy with vis; `v` selects, `y` or Enter copies and exits, `q` cancels |
| Ctrl+B, ] / p | Paste dvtm's internal copy register |
| Alt+V | Paste Wayland clipboard through foot |
| Ctrl+B, g / e | lazygit / vis in the selected pane's directory |
| Ctrl+B, d | Offline documentation picker in a new pane |
| Ctrl+B, v, 1…5 / t, 1…5 | View a tag / move a pane to a tag |
| Ctrl+B, . | Minimize/restore focused terminal |
| Ctrl+B, x, x | Close terminal (two deliberate keypresses) |
| Ctrl+B, ? | This key reference in a pane |
| Ctrl+B, Ctrl+B | Send Ctrl+B to the focused application/remote tmux |
| Ctrl+backslash | Detach abduco; programs keep running |
| `work` / `work --sessions` | Project picker / existing session picker, after detaching |

FreeBSD pane-directory inheritance and vis/dvtm Wayland clipboard integration
still require native verification. Preserve both clipboard and primary-selection
behavior, terminal-default backgrounds and copy-mode isolation from project plugins.

Abduco owns detach, so use its native Ctrl+backslash. Dvtm uses tags and tiling,
not tmux's independent pane split tree: `|` and `-` add a terminal to the active
layout. `z` selects fullscreen; Space cycles back. Detach preserves processes
until shutdown, not across reboot. There is no tmux/TPM runtime or plugin server.

Opening **vis with no file** displays the current monochrome orb dashboard.
Its keys are shown beside the logo: find/new/recent/working files, search,
restore, Git, key reference and quit. It adapts to the actual pane dimensions;
very small panes retain the menu. File arguments bypass the dashboard.
The original 2D orb has a gentle idle float while the dashboard is active;
static/off mode keeps it still and editing stops the clock.

**SYSTEM INFO** or `fetch` opens the complete Fastfetch report with the same
2D idle logo. Use `j/k` (or Ctrl+N/P), Space/`b`, `g/G` and `h/l` to navigate;
`q`, Esc or Enter closes it. `nostromo-fetch --plain` prints ordinary output,
and `nostromo-fetch --format json` emits the detected fields as JSON.

| vis (normal mode, except completion) | Action |
| --- | --- |
| Space Space / Space ff | Fuzzy project files |
| Space fr / fb | Recent files / open editor windows |
| Space / | Search project text and jump to a line |
| Space gg / e | lazygit / nnn |
| Space H / h / 1…9 | Remember working file and cursor / picker / direct working-file slot |
| Space qs / qr | Save / reopen project editor session files and cursor positions |
| Space bh | In-editor orb dashboard |
| gd / gD / gi / gr | Definition / declaration / implementation / references |
| K / Ctrl+] / Ctrl+T | Hover documentation / definition / LSP jump back |
| Ctrl+Space or Ctrl+X Ctrl+O | Request LSP completion, in Normal or Insert mode; fzf chooses the result |
| Space cr / cs | Enter a new symbol name / document symbol navigator |
| Space cd / [d / ]d | Line diagnostics / previous / next diagnostic |
| Space cf | Format buffer with its native formatter |
| Space cl / cL | Lint current file / project |
| Space bb / tt / tT | Build / test project / test project |
| Space tf | Test the current Python file or Go package |
| Space tr | Choose a test discovered by Cargo, Go, pytest or CTest |
| Space tl | Repeat the last project task, including its selected test |
| Space db / ch | Native LLDB / developer-tool health report |
| Space wv / ws / wd / ww | Vertical split / horizontal split / close / save |
| Space sk / ? | This reference |
| Ctrl+H/J/K/L / Ctrl+S | Editor split navigation / save |
| Space mp | Toggle live Markdown preview from the unsaved buffer |
| Space od | Offline manuals and formatted example templates in a separate window |

Build/test/lint first save all modified open files and stop if any save fails.
Editor sessions refuse unsaved files; they store plain filenames/positions and
reuse already-open files, not executable scripts or unsaved contents. Native vis
motions, text objects, selections, registers, macros and undo remain available.
The upstream client supplies LSP features, not Neovim's plugin API. See
[DEVELOPMENT.md](DEVELOPMENT.md) for dependencies and exact remaining differences.
The rendered Markdown split and existing PDF workflow are described in
[DOCUMENTS.md](DOCUMENTS.md).

Oksh uses Emacs-style prompt editing as the previous Zsh configuration did:
Ctrl+R history, Tab completion, Ctrl+A/E line boundaries, Ctrl+W previous word.
`z`/`zi` use zoxide when its POSIX initialization is supported. `f` selects a file,
`c` selects a directory, `mkcd` creates/enters one, `work` opens a project session,
`lg` starts lazygit, `fetch` runs fastfetch with the compact orb and detected
OS/CPU/RAM/root-disk/shell/uptime fields. Zsh-specific
autosuggestion and syntax-highlighting widgets are not supplied by oksh.

`server` opens the locally configured SSH alias. Set the Discord UI URL in the
local browser settings described in [BROWSER](BROWSER.md); no service is provisioned
on another machine. `pass` uses the implemented OpenPGP-compatible tpass workflow
and expiring Wayland clipboard; see [PASSWORDS](PASSWORDS.md).

For qutebrowser's controls see [BROWSER.md](BROWSER.md).
The image viewer becomes swayimg, the PDF reader remains Zathura/MuPDF, and
mpv keeps the existing keyboard controls. Their Wayland paths are acceptance work.

Swayimg uses Michroma and the dedicated bottom bar. `h/j/k/l` pans the image or
moves through gallery thumbnails; `n/p` changes images, `q` exits, Enter switches
viewer/gallery, `f` toggles fullscreen, `+/-` zooms and Backspace resets the view.
The image's own colours are preserved; only the surrounding interface is monochrome.

Foot's opacity actions come from our pinned patch; its line picker uses the
configured `pipe-visible` binding. See [the actual config](../home/.config/foot/foot.ini).
WALLPAPER applies the default orb, or another set added to `assets/wallpapers/`,
to connected outputs. DEVICES provides explicit USB mount/unmount and
debug-probe grants; no automount daemon or hibernation action is added.

Wi-Fi, VPN and Bluetooth use the same fuzzel panel as the launcher. Enter selects;
Up/Down, Ctrl+P/N or Alt+K/J navigate; Esc cancels. Wi-Fi supports scan, hidden and
saved profiles; VPN includes tunnel selection; Bluetooth includes controller
selection and supported classic-device operations. Secrets are masked separately.

PDF/image filenames appear in the bottom extended bar. In Zathura, Ctrl+N toggles
the optional statusbar (hidden initially to avoid a second filename). Image
selection, next/previous and slideshow changes update the bottom title.
