# Boot loader, login and Wayland session

The configured path is **UEFI → FreeBSD Lua loader → kernel/services → SDDM
Wayland login → authenticated dwl session**. SDDM is enabled only after the root
installer's build/configuration gates pass. Installation does not reboot or start
the display manager over the current console. Automatic startup is not autologin.

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

`system/sddm/nostromo.conf` explicitly selects `DisplayServer=wayland`, cage,
Qt's Wayland backend, the Nostromo QML theme and the one managed Wayland session.
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
the authenticated session starts. Owned children are stopped on logout. Session
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

Console recovery is kept. From a root console, `sysrc sddm_enable=NO` prevents the
next graphical startup; inspect the session/install logs and restore only the
relevant backed-up files. See [INSTALL](INSTALL.md) for transaction boundaries.

Sources: [FreeBSD Wayland](https://docs.freebsd.org/en/books/handbook/wayland/),
[loader.conf](https://man.freebsd.org/cgi/man.cgi?query=loader.conf&sektion=5),
[SDDM](https://github.com/sddm/sddm), [gtklock](https://github.com/jovanlanik/gtklock).
