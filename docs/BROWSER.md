# Qutebrowser and the retained start page

The user approved **qutebrowser as the sole browser**, replacing surf and tabbed
together. No Firefox, LibreWolf or Chromium application is added as a fallback.
QtWebEngine is qutebrowser's rendering dependency, not a separately installed
Chromium browser. Its package/library closure passes through the FreeBSD transaction gate; native browser acceptance remains pending.

The initial [configuration](../qutebrowser/config.py) sets native
Wayland, Michroma GUI/web defaults, Azeret Mono fixed-width text, monochrome
chrome, tab focus inversion and the local Nostromo start page. The
[launcher](../bin/nostromo-browser) sets Qt's Wayland backend, quotes
arguments, rejects option-looking input and opens the encoded local file URL
when no URL is provided. There is no XCB fallback or browser sandbox-disable flag.
Qutebrowser requires Python for its own config; this is application configuration,
not a non-POSIX installation script.

`config.load_autoconfig()` preserves native saved site permissions; project
appearance/backend settings follow it. No unverified Chromium feature flags,
`--no-sandbox`, globally ignored TLS errors or spoofed user agent are added.
GPU rendering, video, microphone, downloads and screen sharing still require
native Qt/portal/media tests.

## Start page

The existing local HTML/CSS/JavaScript design is retained under
`qutebrowser/start/`, with the same orb, typography, monochrome
CRT treatment and six placeholder tiles. `links.js` remains user-editable data
for Containers, Pods, Files, AI, Discord and Services. No service connection or
health result is fabricated, and no server-side setup is included.

Qutebrowser's normal-mode bindings intercept j/k and numbers before a page sees
them. Use **f** for link hints, Tab/Enter for focus, or **i** to send the start
page its existing j/k, / and 1–6 keys; Escape returns to browser normal mode.
Do not globally rebind j/k to start-page JavaScript and break normal web navigation.

## Initial controls

| Key | Action |
| --- | --- |
| o / O | Open URL/search here / new tab |
| f / F | Follow a link here / new tab |
| j/k, h/l | Page navigation using native Vim-style defaults |
| H / L | Back / forward |
| /, n / N | Search, next / previous match |
| J / K | Tab next / previous through qutebrowser defaults |
| Ctrl+G | Open URL command line |
| Ctrl+Shift+H / L | Explicit previous / next tab |
| Ctrl+Shift+Enter | New tab/start page |
| yy / yt | Copy the page URL / title |
| ;y | Copy a link address through hints |
| v, v, y | Caret mode: mark text with the keyboard, then copy it |
| i / Escape | Pass input to page / return to normal mode |
| Ctrl+E in insert mode | External editor; configured as foot + vis |
| :help / :version | Native help / backend and version diagnostics |

The browser tab row is separate from the compositor's blank white top strip.
That strip/outline is a dwl implementation item, not a Qt color setting.
Static configuration checks do not prove an actual Wayland browser launch.
Sources: [qutebrowser configuration](https://qutebrowser.org/doc/help/configuring.html),
[settings](https://qutebrowser.org/doc/help/settings.html),
[FreeBSD port](https://cgit.freebsd.org/ports/tree/www/qutebrowser).
