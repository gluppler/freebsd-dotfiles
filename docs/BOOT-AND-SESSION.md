# Boot loader, login and Wayland session

The configured path is **UEFI → FreeBSD Lua loader → kernel/services → SDDM
Wayland login → authenticated dwl session**. SDDM is enabled only after the root
installer's build/configuration gates pass. Installation does not start the
display manager over the current console; after its final check it asks before
rebooting. Automatic startup is not autologin.

## Loader

The installer adds the retained hybrid orb at `/boot/images/nostromo-orb.png`
and an isolated `/boot/lua/gfx-nostromo.lua` logo module. It manages only its
listed keys in `/boot/loader.conf`, including `loader_logo="nostromo"`, keeping
unrelated settings and a rollback copy. It never replaces `loader.lua`, the
whole loader configuration or EFI firmware. Stock boot-environment/kernel/recovery
menus remain available. To undo only the logo selection, use `loader_logo="orb"`
from a recovery console. Loader typography and effects are limited by the loader;
it does not run the GUI fonts or GLSL compositor shader.

[Daisy](https://jonathan-linux.itch.io/daisy) remains the user's historical logo
reference, not an installed dependency. The custom logo is implemented directly
through FreeBSD's loader extension mechanism.

## Login and session

`sddm/nostromo.conf` explicitly selects `DisplayServer=wayland`, the cage kiosk
`/usr/local/libexec/nostromo-cage`, Qt's Wayland backend, the Nostromo QML theme
and the one managed Wayland session. That cage 0.3.1 is built here against the
wlroots variant. The stock package was built with wlroots' X11 and XWayland
support, which the variant leaves out. It calls `wlr_xwayland_create` before it
creates its socket, so at the first boot on 2026-11-12 SDDM's VT 9 stayed a
blank console with a cursor. The build and staged validation now load every
symbol the kiosk and dwl use (`LD_BIND_NOW=1`), and the retired stock package
is removed.
No X11 session or automatic login is configured. The login shows the retained orb,
Michroma Login/Password fields, bottom-right cuts and animated outside brackets.
The space_dots-derived logo arrival, phosphor motion and grain also run here;
`Effects` in the root-owned theme.conf selects animated/static/off.
The QML theme has been rendered and exercised with a mock SDDM backend; actual
FreeBSD seat/PAM/login/logout still require the laptop.

The installer retains the package's native SDDM PAM stacks and verifies base
`pam_xdg.so` session integration. It appends the account and greeter to the needed
`video` group without replacing their existing groups. Seatd supplies DRM/input
access; no world-writable device policy is used.

`nostromo-sddm-session` accepts only the managed session command.
`nostromo-session` runs as the authenticated ordinary user, checks a private
UID-owned mode-0700 `XDG_RUNTIME_DIR`, loads the normal profile and starts one
D-Bus session. It clears X11/input-method overrides and selects native Wayland
backends. It neither runs startx nor starts the desktop from every SSH shell.

The dwl startup helper owns the bar, status producer, native Dunst, wallpaper,
PipeWire/WirePlumber, fcitx5, swayidle and hardware-event watcher. Local kanshi
profiles are optional. The native space_dots-style splash runs for about 2.4 seconds after
the authenticated session starts. If the wallpaper, the splash or the D-Bus
activation update fails, the session log names it and the bar and services keep
running. Owned children are stopped on logout. Session
logs rotate to `~/.local/state/nostromo/session.previous.log` at the next login;
the current log is `session.log`. There is no automatic compositor restart loop.

## Lock and sleep

The patched gtklock uses **ext-session-lock**, FreeBSD unix-selfauth/PAM and a
native Cairo presentation: orb, masked Password input, bottom-right field cut,
animated joined left/right focus brackets and a bouncing idle logo. It uses the
same space_dots-style motion as login/splash and reads the saved session CRT mode;
static/off stop the animation timer. Inputs remain stationary and responsive. Unlocking
requires successful authentication; a signal cannot bypass it. The GUI is not
setuid. Splash/idle artwork is not substituted for a compositor lock.

`nostromo-lock` waits for actual lock acknowledgement before using mdo's limited
ACPI group capability; the user remains non-root. Automatic ACPI lid/sleep-button
actions are disabled, and the session watcher handles these events after locking.
The system devd Suspend handler checks all existing Wayland sockets again before
native suspend hooks run. Failure or timeout cancels the kernel request. A short
resume debounce ignores the wake button's duplicate sleep event. With no verified
desktop session, suspension is refused. Test every output, hotplug, failed passwords, locker failure and resume
on the laptop before treating authentication/suspend as accepted.

## Console recovery and manual tests

Ctrl+Alt+F1 to F8 open the text consoles, each with a login prompt. They work
from a blank screen, from the login screen (the kiosk runs with cage's `-s`,
which allows the switch) and from the desktop. SDDM uses VT 9, so Ctrl+Alt+F9
returns to it. As root, `service sddm stop` ends the login screen, and
`sysrc sddm_enable=NO` keeps it off at the next boot; `sysrc sddm_enable=YES`
restores it. A completed install keeps no backup copies. See
[INSTALL](INSTALL.md) for transaction boundaries.

Console logins get their `XDG_RUNTIME_DIR` from the base `pam_xdg.so` session,
so each part can be started by hand from a console as the ordinary user:

- `/usr/local/libexec/nostromo-session` starts the whole desktop, as SDDM does.
  Its log is `~/.local/state/nostromo/session.log`. Super+Shift+Q, then LOGOUT,
  ends it.
- Plain `dwl` starts the compositor alone: a black screen with a pointer and no
  bar, wallpaper or services. Super+Return opens foot there. It has no quit key;
  switch to another console and run `pkill -x dwl`.
- `/usr/local/libexec/nostromo-cage -s -- foot` tests the login kiosk with a
  terminal; exiting foot ends it.
- `QT_QPA_PLATFORM=wayland /usr/local/libexec/nostromo-cage -s -- sddm-greeter-qt6 --test-mode --theme /usr/local/share/sddm/themes/nostromo`
  shows the login screen without logging in. Leave it from another console with
  `pkill -x nostromo-cage`.

SDDM's own log is `/var/log/sddm.log`, readable by root. A login that returns
straight to the login screen leaves its messages from before dwl starts, such
as a missing program, in `~/.local/share/sddm/wayland-session.log`.

Sources: [FreeBSD Wayland](https://docs.freebsd.org/en/books/handbook/wayland/),
[loader.conf](https://man.freebsd.org/cgi/man.cgi?query=loader.conf&sektion=5),
[SDDM](https://github.com/sddm/sddm), [gtklock](https://github.com/jovanlanik/gtklock).
