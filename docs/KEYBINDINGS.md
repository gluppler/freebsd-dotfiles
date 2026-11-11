# Keyboard reference

Everything in the desktop can be done from the keyboard. These bindings are
configured in the migrated sources and helpers; native keyboard/layout, client
behavior and hardware acceptance remain laptop tests.

Super is the Windows key. The desktop keys follow one pattern:

- **Super** with a key opens something or moves focus.
- Add **Shift** to act on the focused window, or for the key's alternative
  (Super+P projects, Super+Shift+P passwords).
- Add **Ctrl** for system panels and for resizing.
- **Super+Alt** drives the pointer.
- **Super+X** lists every action: type part of its name, then Enter.
  **Super+/** opens this reference.

Inside foot, Ctrl+Shift belongs to the terminal and Alt to the shell. dvtm uses
Ctrl+B, released before the next key. vis keeps its normal modal editing keys.

## Common tasks

| Task | Keys |
| --- | --- |
| Update the system | Super+Ctrl+Shift+U updates packages. Super+Ctrl+U opens SOFTWARE for base patches, firmware, install, remove and ports |
| Take a screenshot | Print or Super+S: a region. Shift+Print or Super+Shift+S: the focused window. Ctrl+Print or Super+Ctrl+S: the whole screen. Each is saved in `~/Pictures/Screenshots` and copied to the clipboard |
| Copy terminal text | Ctrl+Shift+Space opens the scrollback in vis: `v` selects, `y` copies. Also Ctrl+Shift+F search selection, Ctrl+Shift+L for a line, Ctrl+Shift+Y for a URL |
| Copy an image | Screenshots are copied as they are taken; `y` in the image viewer copies the image shown |
| Copy text from a PDF | `y` in zathura copies the current page's text |
| Copy in the editor or browser | `Space y` on a vis selection; in qutebrowser `v`, then `v` to mark, `y` to copy |
| Paste | Ctrl+Shift+V or Alt+V in foot; `Space p` in vis; Super+Ctrl+C moves text between the clipboard and the primary selection |
| Volume and microphone | Super+F1 / F2 / F3 mute / down / up, Super+F4 microphone. Fn with the same keys, or Super+scroll, also work. Super+Ctrl+A chooses the output and recording source |
| Brightness | Super+F5 / F6, or Fn+F5 / F6 |
| Wi-Fi, VPN, Bluetooth | Super+Ctrl+W, Super+Ctrl+V, Super+Ctrl+B |
| Displays | Super+Ctrl+D or Super+F7; Super+Ctrl+Shift+D sets the lid policy for docking |
| Lock, suspend, log out, power | Super+Escape, Super+Shift+Escape, Super+Shift+Q, Super+Ctrl+P |
| Notifications | Super+N dismisses, Super+Shift+N dismisses all, Super+O opens actions and links, Super+Ctrl+N recalls, Super+Ctrl+Shift+N pauses |
| Input language | Super+Ctrl+Space next, Super+Ctrl+Shift+Space choose |
| Passwords | Super+Shift+P copies a password; the clipboard clears after 45 seconds |
| USB drives | Super+Ctrl+M |
| Documentation | Super+D |

## Desktop

| Applications | Action |
| --- | --- |
| Super+Enter | Terminal (foot) |
| Super+Space | Search apps, actions, file names and file contents |
| Super+X | Menu of every action |
| Super+E / V | Files (nnn) / editor (vis) |
| Super+P / Shift+P | Project workspace / password picker |
| Super+G | lazygit |
| Super+R | SSH to the configured server |
| Super+B / Shift+D | qutebrowser / the configured Discord web UI in qutebrowser |
| Super+D | Offline documentation |
| Super+' | Scratch terminal |
| Super+/ or Super+? | This reference |

| Windows | Action |
| --- | --- |
| Super+J / K | Focus the next / previous window |
| Super+H / L | Shrink / grow the master area |
| Super+Shift+H/J/K/L | Move the window. A floating one moves 32 px; a tiled one goes into the master area (H), down or up the stack (J/K) or out of the master area (L) |
| Super+Ctrl+H/J/K/L | Resize. A floating window becomes narrower / taller / shorter / wider; for a tiled one H/L move the master border |
| Super+Shift+Enter | Swap with the master window |
| Super+I / Shift+I | More / fewer master windows |
| Super+Q | Close the window |
| Super+F | Fullscreen |
| Super+Shift+Space | Float or tile the window |
| Super+T / M / Shift+F | Tile / monocle / floating layout; floating is the default |
| Super+Shift+B | Show or hide the bar |
| Super+minus / equals / Shift+equals | Smaller / larger / default gaps |

| Tags and monitors | Action |
| --- | --- |
| Super+1…9 | View a tag |
| Super+Shift+1…9 | Move the window to a tag |
| Super+Ctrl+1…9 / Ctrl+Shift+1…9 | Show or hide a tag in the view / toggle the window on a tag |
| Super+[ / ] | Previous / next tag |
| Super+Shift+[ / ] | Take the window to the previous / next tag |
| Super+Tab | The previous view |
| Super+0 / Shift+0 | View all tags / show the window on every tag |
| Super+comma / period | Focus the left / right monitor; add Shift to move the window |
| Ctrl+Alt+F1…F12 | Switch to a text console |

| System panels | Action |
| --- | --- |
| Super+Ctrl+W | Wi-Fi |
| Super+Ctrl+V | WireGuard VPN |
| Super+Ctrl+B | Bluetooth |
| Super+Ctrl+A | Audio: levels, output device and recording source |
| Super+Ctrl+D / Shift+D | Display layout / docked or portable lid policy |
| Super+Ctrl+P / Shift+P | Power menu / power profile |
| Super+Ctrl+U / Shift+U | Software / update packages now |
| Super+Ctrl+M | Mount, unmount and USB probe access |
| Super+Ctrl+I | System information |
| Super+Ctrl+C | Clipboard: selection ↔ clipboard, clear |
| Super+Ctrl+Space / Shift+Space | Next input language / language chooser |

| Session, notifications and screenshots | Action |
| --- | --- |
| Super+Escape / Shift+Escape | Lock / lock and suspend |
| Super+Shift+Q | Log out, after a confirmation |
| Super+Shift+C | CRT effect on or off |
| Super+N / Shift+N | Dismiss the newest / every notification |
| Super+O | Actions and links of the shown notifications |
| Super+Ctrl+N / Ctrl+Shift+N | Recall a notification / pause notifications |
| Print / Shift+Print / Ctrl+Print | Screenshot of a region / the focused window / the screen |
| Super+S / Shift+S / Ctrl+S | The same three, without the Print key |

| Laptop keys | Action |
| --- | --- |
| Super+F1 / F2 / F3 | Mute / volume down / volume up |
| Super+F4 | Microphone mute |
| Super+F5 / F6 | Brightness down / up |
| Super+F7 | Display layout |
| Fn+F1…F6 | The same actions through the media keys |

The firmware profile makes F1–F12 ordinary function keys, so the icons on F1–F7
are reached with Fn or with Super. The Super chords also work where FreeBSD does
not report a ThinkPad hotkey as a key press.

| Keyboard pointer | Action |
| --- | --- |
| Super+Alt+H/J/K/L | Move the pointer; add Shift for fine movement |
| Super+Alt+Enter / Backspace | Left / right click |
| Super+Alt+comma / period | Scroll up / down |

Each mouse action has a key: Super+drag moves (Super+Shift+H/J/K/L), Super+right-drag
resizes (Super+Ctrl+H/J/K/L), Super+middle-click floats (Super+Shift+Space),
Super+scroll changes the volume (Super+F2/F3) and clicking a bar field opens the
same panel as its key. Notification clicks dismiss (Super+N), open actions
(Super+O) and dismiss all (Super+Shift+N).

There is no client-preserving compositor restart key: ending a Wayland
compositor disconnects its clients. Save work and log out/in when replacing it.

The launcher accepts a query, then offers combined results. An empty query lists
apps/actions; Escape cancels. **SOFTWARE** opens the keyboard package/update/ports
menu in foot; `software` runs it from oksh. System changes authenticate through
base su/PAM, then use mdo and the shared GNU dependency gate. Search roots,
controls and limits are in [PACKAGES.md](PACKAGES.md).

DISPLAYS also exposes detected resolutions/refresh rates, rotation and primary
output. CLAMSHELL selects DOCKED or PORTABLE lid behavior for this boot; enable
an external monitor first. CRT STATIC retains CRT shading/transparency while
removing the continuous sweep. See [HARDWARE.md](HARDWARE.md) and
[PERFORMANCE.md](PERFORMANCE.md).

**VPN** shows native WireGuard status/up/down in the fuzzel panel; the oksh alias
`vpn` runs the same helper. Configure real peer details first using
[WIREGUARD.md](WIREGUARD.md); an interface being UP is not proof of peer
reachability.

The native lock keeps a bouncing logo, masked Password input and animated outer
brackets; type the password, then Enter. Suspend waits for compositor lock
acknowledgement; native PAM, hotplug and resume still need the laptop acceptance
pass.

## Menus and panels

Every picker uses the same fuzzel panel as the launcher. Type to filter; Enter
selects; Up/Down, Ctrl+P/N or Alt+K/J move; Esc or Ctrl+G cancels. Wi-Fi supports
scan, hidden and saved profiles; VPN includes tunnel selection; Bluetooth includes
controller selection and supported classic-device operations. Secrets are masked
separately. Terminal menus such as SOFTWARE, PROJECTS and PASSWORDS use fzf with
the same keys.

## Terminal (foot)

| Key | Action |
| --- | --- |
| Ctrl+Shift+C / V | Copy / paste; Alt+C / V also work |
| Shift+Insert | Paste the primary selection |
| Ctrl+Shift+Space | Copy mode: the scrollback in vis. `v` selects, `y` or Enter copies, `q` cancels |
| Ctrl+Shift+F | Search the scrollback; the match is selected (Ctrl+Shift+R also works) |
| Ctrl+Shift+L | Pick a visible line and copy it literally |
| Ctrl+Shift+O / Y | Open / copy a URL through hint labels |
| Ctrl+Shift+J/K / D/U | Scroll a line / half a page down or up |
| Shift+PageUp / PageDown | Scroll a page |
| Shift+Home / End | Top / bottom of the scrollback |
| Ctrl+Shift+N | New terminal in the same directory |
| Ctrl+= / Ctrl+- / Ctrl+0 | Font larger / smaller / default |
| Alt+A / S / Shift+A | Lower / raise background opacity in 5% steps / reset to 90% |
| Ctrl+Shift+I | Type a Unicode code point in hex, then Enter |
| Shift+mouse selection | Select locally when an application captures the mouse |

To copy part of a line, press Ctrl+Shift+F and type the start of the text. Ctrl+R
and Ctrl+S find the previous / next match. Shift+arrows, Ctrl+W (next word
boundary) and Ctrl+Shift+W (next whitespace) extend the selection. Enter keeps it
as the primary selection; Ctrl+Shift+C then copies it to the clipboard. Escape
cancels.

Copy mode is the same vis copy editor as Ctrl+B [ in dvtm, opened in a new
window. The scrollback is only displayed there; nothing in it runs.

Foot's opacity actions come from our pinned patch; its line picker and copy mode
use the configured `pipe-visible` and `pipe-scrollback` bindings. See
[the actual config](../foot/foot.ini).

## Project workspace (abduco and dvtm)

`work /path/to/project` or Super+P starts or attaches one abduco session for that
physical project path. The Super+P picker lists projects with a running session
first: with one session running, Super+P then Enter reattaches it after a detach.
New sessions open vis in the left 65%, with an oksh shell
and Git stacked on the right. Quitting lazygit leaves an oksh shell. The bottom
bar shows tags, layout, project directory and time. Connected
horizontal/vertical dividers separate panes. Their backgrounds inherit foot
transparency, including vis; text and selected-row highlights remain opaque. The
right window rail follows the focused pane directory.

| dvtm / abduco | Action |
| --- | --- |
| Ctrl+B, c / \| / - | New terminal inheriting the selected pane's directory |
| Ctrl+B, C | New terminal in the session's original project directory |
| Ctrl+B, h/j/k/l | Directional focus |
| Ctrl+B, N/P | Next/previous non-minimized pane |
| Ctrl+B, H/L | Shrink/grow master width |
| Ctrl+B, i / I | More / fewer master panes |
| Ctrl+B, Enter | Promote the focused terminal to master |
| Ctrl+B, z / Space | Fullscreen layout / cycle layouts |
| Ctrl+B, f / G / b | Master-and-stack / grid / bottom-stack layout |
| Ctrl+B, 1…9 / Tab | Focus terminal / last terminal |
| Ctrl+B, [ | Scroll/copy with vis; `v` selects, `y` or Enter copies and exits, `q` cancels |
| Ctrl+B, ] / p | Paste dvtm's internal copy register |
| Ctrl+B, PageUp / PageDown | Scroll the pane's history |
| Ctrl+B, / or E | Search or read the pane's history in less |
| Ctrl+Shift+V or Alt+V | Paste the Wayland clipboard through foot |
| Ctrl+B, g / e | lazygit / vis in the selected pane's directory |
| Ctrl+B, d | Offline documentation picker in a new pane |
| Ctrl+B, v, 1…5 / t, 1…5 | View a tag / move a pane to a tag |
| Ctrl+B, V, 1…5 / T, 1…5 | Show or hide a tag in the view / toggle the pane on a tag |
| Ctrl+B, 0 | View every tag |
| Ctrl+B, . | Minimize/restore focused terminal |
| Ctrl+B, s | Show or hide the dvtm bar |
| Ctrl+B, a | Type into every visible pane at once; press again to stop |
| Ctrl+B, r | Redraw the screen |
| Ctrl+B, x, x | Close terminal (two deliberate keypresses) |
| Ctrl+B, q, q | Quit dvtm, closing every pane |
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

## Editor (vis)

Opening **vis with no file** displays the current monochrome orb dashboard.
Its keys are shown beside the logo: find/new/recent/working files, search,
restore, Git, key reference and quit. It adapts to the actual pane dimensions;
very small panes retain the menu. File arguments bypass the dashboard.
The original 2D orb has a gentle idle float while the dashboard is active;
static/off mode keeps it still and editing stops the clock.

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
| Space bb / tt | Build / test project |
| Space tf | Test the current Python file or Go package |
| Space tr | Choose a test discovered by Cargo, Go, pytest or CTest |
| Space tl | Repeat the last project task, including its selected test |
| Space db / ch | Native LLDB / developer-tool health report |
| Space y (on a selection) | Copy the selection to the Wayland clipboard |
| Space p / P | Paste the clipboard after / before the cursor |
| Space wv / ws / wd / ww | Vertical split / horizontal split / close / save |
| Space sk / ? | This reference |
| Ctrl+H/J/K/L / Ctrl+S | Editor split navigation / save |
| Space mp | Toggle live Markdown preview from the unsaved buffer |
| Space od | Offline manuals and formatted example templates in a separate window |

Build/test/lint first save all modified open files and stop if any save fails.
Editor sessions refuse unsaved files; they store plain filenames/positions and
reuse already-open files, not executable scripts or unsaved contents. Native vis
motions, text objects, selections, registers, macros and undo remain available;
the `+` register is the Wayland clipboard. The upstream client supplies LSP
features, not Neovim's plugin API. See [DEVELOPMENT.md](DEVELOPMENT.md) for
dependencies and exact remaining differences. The rendered Markdown split and
existing PDF workflow are described in [DOCUMENTS.md](DOCUMENTS.md).

## Shell (oksh)

Oksh uses Emacs-style prompt editing as the previous Zsh configuration did:
Ctrl+R history, Tab completion, Ctrl+A/E line boundaries, Ctrl+W previous word,
Alt+B/F word movement, Alt+D word deletion and Alt+U/L word case. `z`/`zi` use zoxide when its
POSIX initialization is supported. `f` selects a file, `c` selects a directory,
`mkcd` creates/enters one, `work` opens a project session, `lg` starts lazygit,
`fetch` runs fastfetch with the compact orb and detected
OS/CPU/RAM/root-disk/shell/uptime fields. Zsh-specific autosuggestion and
syntax-highlighting widgets are not supplied by oksh.

**SYSTEM INFO** (Super+Ctrl+I) or `fetch` opens the complete Fastfetch report
with the same 2D idle logo. Use `j/k` (or Ctrl+N/P), Space/`b`, `g/G` and `h/l`
to navigate; `q`, Esc or Enter closes it. `nostromo-fetch --plain` prints
ordinary output, and `nostromo-fetch --format json` emits the detected fields as
JSON.

`server` and Super+R open the locally configured SSH alias. Set the Discord UI
URL in the local browser settings described in [BROWSER](BROWSER.md); no service
is provisioned on another machine. A missing setting is reported as a
notification. `pass` and Super+Shift+P use the implemented OpenPGP-compatible
tpass workflow and expiring Wayland clipboard; see [PASSWORDS](PASSWORDS.md).

## Viewers and browser

The image viewer is swayimg, the PDF reader remains Zathura/MuPDF, and mpv keeps
the existing keyboard controls. Their Wayland paths are acceptance work.

| Viewer | Keys |
| --- | --- |
| swayimg | `h/j/k/l` pan the image or move through gallery thumbnails; `n/p` next/previous image; `y` copies the image; Enter switches viewer/gallery; `f` fullscreen; `+/-` zoom; Backspace resets; `q` exits |
| zathura | `J/K` next/previous page; `h/j/k/l` scroll; `/`, `n`, `N` search; `f` follows a link through hints; Tab shows the index; `y` copies the page's text; Ctrl+N shows the status bar; `q` quits |
| mpv | `h/l` seek 5 s; `j/k` volume; `J/K` next/previous file; Space pauses; `f` fullscreen; `m` mute; `q` quits |
| qutebrowser | `yy` / `yt` copy the URL / title; `;y` copies a link through hints; `v` starts keyboard selection, `v` again marks it and `y` copies it. [BROWSER.md](BROWSER.md) lists the rest |

Swayimg uses Michroma and the dedicated bottom bar. The image's own colours are
preserved; only the surrounding interface is monochrome. Its `y` copies the file
with its own image type. Zathura's `y` replaces its full-page scroll to the right
(`l` still scrolls right); a page without a text layer, such as a scan, has
nothing to copy.

PDF/image filenames appear in the bottom extended bar. In Zathura, Ctrl+N toggles
the optional statusbar (hidden initially to avoid a second filename). Image
selection, next/previous and slideshow changes update the bottom title.

WALLPAPER applies the default orb, or another set added to `wallpapers/`,
to connected outputs. DEVICES provides explicit USB mount/unmount and
debug-probe grants; no automount daemon or hibernation action is added.

## Every menu action

Super+X opens this menu and Super+Space includes it in search results. The keys
reach each action directly. Settings changed once in a while have no chord of
their own: press Super+X and type the first letters of their name.

| Action | Keys |
| --- | --- |
| PROJECTS | Super+P |
| EDITOR | Super+V |
| DOCS | Super+D |
| GIT | Super+G |
| FILES | Super+E |
| DEVICES | Super+Ctrl+M |
| BROWSER | Super+B |
| DISCORD | Super+Shift+D |
| SERVER | Super+R |
| PASSWORDS | Super+Shift+P |
| EMBEDDED | Super+X; the guide is also under Super+D, PROJECT GUIDES |
| WIFI | Super+Ctrl+W |
| VPN | Super+Ctrl+V |
| BLUETOOTH | Super+Ctrl+B |
| LANGUAGE | Super+Ctrl+Shift+Space |
| DISPLAYS | Super+Ctrl+D or Super+F7 |
| AUDIO | Super+Ctrl+A |
| BRIGHTNESS | Super+F5 / F6 |
| CLAMSHELL | Super+Ctrl+Shift+D |
| CLIPBOARD | Super+Ctrl+C |
| SOFTWARE | Super+Ctrl+U |
| INSTALL PACKAGES | Super+Ctrl+U, then INSTALL |
| UPDATE PACKAGES | Super+Ctrl+Shift+U |
| REMOVE PACKAGES | Super+Ctrl+U, then REMOVE |
| PORTS | Super+Ctrl+U, then PORTS |
| BASE PATCHES | Super+Ctrl+U, then BASE PATCHES |
| FIRMWARE | Super+Ctrl+U, then FIRMWARE |
| SYSTEM INFO | Super+Ctrl+I |
| AUTHENTICATION | Super+X |
| POWER PROFILE | Super+Ctrl+Shift+P |
| WALLPAPER | Super+X |
| CRT TOGGLE | Super+Shift+C |
| CRT STATIC | Super+X |
| NOTIFICATION HISTORY | Super+Ctrl+N |
| NOTIFICATION ACTION | Super+O |
| NOTIFICATION QUIET | Super+Ctrl+Shift+N |
| SCREENSHOT WINDOW | Super+Shift+S or Shift+Print |
| SCREENSHOT FULL | Super+Ctrl+S or Ctrl+Print |
| LOCK | Super+Escape |
| POWER | Super+Ctrl+P |
| KEYBINDINGS | Super+/ |
