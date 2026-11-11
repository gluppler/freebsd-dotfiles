# ThinkPad hardware and peripheral acceptance

The manual [firmware table](FIRMWARE.md) records every supplied BIOS choice.
Runtime tuning is in [PERFORMANCE](PERFORMANCE.md). Native sysctl confirms
16 GiB RAM and eight logical CPUs (four physical cores); scripts still detect
usable memory and device names at runtime. No serial/MAC/license identifiers are needed.
The GPU is **Intel Iris Xe integrated graphics**, confirmed on 2026-11-04.

## Native discovery before configuration

Use `freebsd-version -kru`, `pciconf -lv`, `usbconfig list`, `sysctl hw.physmem
hw.ncpu`, `ifconfig -a`, `sysctl net.wlan.devices`, `mixer -a`, `backlight`'s
installed manual and `sysctl -a` for actual ACPI/HWP/temperature nodes. Capture
only the relevant device/driver fields in shared logs; redact personal identifiers.
Keep driver firmware matched to the running kernel. Never assume the previous
OpenBSD device names or all sensors in an old ThinkPad manual exist on this model.

| Area | Required setup / native test |
| --- | --- |
| Intel Iris Xe graphics | Release-compatible DRM/i915 firmware, real hardware rendering, Wayland output mode and scaling; no software-rendering success claim |
| Wi-Fi | Discover parent device; cloned wlan interface and native WPA/DHCP; protected saved/hidden-network profiles, scan/connect/cancel, reconnect after resume |
| Ethernet/docks | Link/DHCP/route changes and USB/TB device identity; preserve normal networking without firmware PXE |
| Sound | Discover OSS mixer/output/input/record source, internal speakers, jack and USB devices; test mute/mic mute and browser/mpv routing |
| Camera/microphone | Identify actual UVC/audio devices; add webcamd/cuse or other services only when necessary and reviewed; verify permissions and browser capture separately |
| Backlight | Detect native backlight device; clamp to reported limits; verify keyboard controls and resume brightness |
| Thermal/battery | coretemp/ACPI readings where present, charging status and real capacity; show unavailable rather than invented temperatures |
| Keyboard/input | US base mapping, F-keys, external layouts, repeat, TrackPoint, touchpad and keyboard-only actions |
| Bluetooth | Latest request restores it; native ng_ubt/Intel firmware detection, bar icon, discovery/pair/connect/disconnect; distinguish classic HID/audio from BLE support |
| External display | Discover connectors/modes/EDID, test scale/rotation/position, preferred output, hotplug/unplug and per-output wallpaper |
| USB/serial/dev boards | Restrict devfs grants to actual device classes/account; safe serial permissions and mount/eject workflow; no chmod 666 of every device |
| Fingerprint/FIDO | Check actual USB IDs, libfprint/PAM availability and FIDO authenticators; configure supported paths after enrollment, retaining password/console recovery |
| Storage | Actual NVMe node/capacity, health, filesystem/encryption/swap and recovery path; no experimental controller feature writes |

## Intel Iris Xe setup

The installer selects the reviewed `drm-612-kmod` package for this FreeBSD 15.1
target, asks `fwget -nq` which firmware the detected hardware needs, and installs
that firmware through the package policy. Tiger Lake firmware is already allowed.
It merges `i915kms` into `kld_list` for boot, configures `video` access and uses
Mesa through native Wayland. `libva-intel-media-driver` is included for supported
video decoding. Existing module entries are preserved.

After reboot, check `kldstat`, `/dev/dri`, the relevant `dmesg` lines and the
dwl session log. Confirm hardware rendering, external displays and resume, then
test video decoding in mpv and qutebrowser separately. A loaded module alone does
not prove browser video acceleration. Keep the BIOS framebuffer reservation at
256 MB initially; it is not the integrated GPU's total available shared memory.
No GPU clocks, driver feature masks or software-renderer overrides are forced.

The Intel kernel-module guidance is in the
[FreeBSD graphics chapter](https://docs.freebsd.org/en/books/handbook/x11/#x-graphic-card-drivers).
The [Wayland chapter](https://docs.freebsd.org/en/books/handbook/wayland/) covers
the DRM, seatd and video-group requirements used here.

## Clamshell and suspend

PORTABLE means lock and suspend on lid closure only after the actual lock
protocol reports success. DOCKED requires a present, enabled external output and
usable external input; close the lid by disabling the internal panel while the
session continues on the external display. If that display disappears, restore
the internal output when usable and fall back to a locked safe state. Never
disable the last active output blindly or infer docking only from AC power.

FreeBSD devd/ACPI events drive this policy; kanshi handles detected display
profiles. A root devd action must not source arbitrary files from the user's home
or run unvalidated event strings. Coordinate the user session lock through a
defined trusted channel and require acknowledgement before `acpiconf -s 3`.
A failed lock must abort the sleep action. Test suspend/resume from the menu,
lid and idle path, including disconnecting the dock while asleep.

The firmware's Linux S3 setting is a useful baseline, not a guarantee of native
resume with this DRM/firmware combination. FreeBSD hibernation is not promised;
do not retain the OpenBSD hibernate menu item or assume swap sizing enables it.
Keep automatic thermal control and firmware protections while investigating
hardware issues.

## Fingerprint outcome must be explicit

Keep password login/lock working. Record device ID, candidate driver/library,
FreeBSD support and enrollment/test result before enabling biometric login.
No daemon, template or PAM change is justified by a firmware fingerprint toggle.
If the reader is unsupported, show that accurately and preserve password use;
do not install Linux drivers or fabricate an enrollment success.

## Configured peripheral controls

DISPLAYS queries the connected outputs/modes/scales. Temporary changes require
KEEP within the confirmation timeout; cancellation restores the previous layout.
The last enabled output cannot be disabled from this menu. `kanshi/config.local`
is the optional place for your actual monitor profiles, not guessed EDIDs.
CLAMSHELL (Super+Ctrl+Shift+D) offers the portable/docked policy after inspecting current outputs;
confirm that external keyboard input works before closing the lid.

AUDIO selects detected OSS output cards and available recording sources; hardware
keys control volume, mute and microphone mute. Super+F1–F6 do the same for audio
and brightness, in case FreeBSD does not report a ThinkPad hotkey as a key press. PipeWire/WirePlumber and the native
portals are configured for supported application routing/capture. A missing mixer
control is reported rather than mapped to an arbitrary device index. Brightness
and temperatures use detected FreeBSD interfaces. Native capture depends on the
specific camera/audio driver, not merely the presence of a bar icon.

DEVICES (Super+Ctrl+M) opens explicit mount/unmount and USB-probe actions in foot. The mount
list is limited to CAM USB mass-storage devices with recognised FAT or UFS
partitions. Choose read-only or read-write; mounts use `nosuid,noexec` under
`/media/nostromo-DEVICE`. FAT grants only the selected account; UFS preserves
filesystem ownership. Unmount before unplugging. Existing mounts and unexpected
mount-directory ownership are preserved. No formatting, blanket USB access,
automount daemon, NTFS/exFAT driver or encrypted-volume discovery is implied.

For an attached debugger, USB PROBE ACCESS displays the actual selected device
and requires typing GRANT. It grants only that device's current USB endpoints
to the account/dialer group; unplugging resets the grant. Serial adapters use the
managed dialer rules and `nostromo-embedded serial`. These are distinct from a
firmware flash operation, which always requires an explicit board/runner command.

## Optional camera, printing and scanning

Use `usbconfig list` and the native driver documentation to identify the camera.
If it requires webcamd/cuse, review that package's full dependency closure first,
then enable only the matching device/service and test browser capture. The
installer does not enable an unidentified camera daemon or claim UVC capture works
because the microphone does. Keep microphone/camera permissions explicit in
qutebrowser.

The maintained CUPS library variant is a dependency of the Qt desktop; it does
not start a print server or discover printers. For a supported network printer,
base FreeBSD `lpr`/LPD can be configured with its actual queue/filter; CUPS is an
optional explicit service when required. Scanner backends likewise depend on the
actual device and need their own reviewed package closure. No printer/scanner
has been identified, so no invented queue, driver or always-running discovery
service is installed. These are device-dependent acceptance items, not mandatory
background processes for an otherwise usable desktop.

Sources: [FreeBSD USB storage](https://docs.freebsd.org/en/books/handbook/disks/#usb-disks),
[multimedia and scanners](https://docs.freebsd.org/en/books/handbook/multimedia/),
[printing](https://docs.freebsd.org/en/books/handbook/printing/).
