# Native Bluetooth controls

The bar's `ᛒ` field opens the styled fuzzel panel; Super+Ctrl+B does the same.
`HCI` means the USB Bluetooth driver is present; `--` means it was not detected.
This public reading does not claim a connected device or a working profile.
The panel's STATUS action shows actual HCI links after base su/PAM authentication
in a foot prompt. The bar never asks for a password or retains root privileges.
Discovery never assigns a
dummy MAC address, guesses a PIN or reports success for absent hardware.

If no HCI controller exists, the menu offers **INITIALIZE**. It checks attached
USB vendor/product IDs against the Intel IDs supported by the base firmware
attachment rule, installs `iwmbt-firmware` through the reviewed package gate when
needed, and invokes base `iwmbtfw`. It loads the USB Bluetooth driver and starts
the native per-device Bluetooth service only for controllers without an HCI node.
The operation fails if no controller appears; it never treats a package install
as proof that the hardware works. Base devd handles subsequent supported device
attachments. A working Internet connection is needed if firmware is absent.

`nostromo-bluetooth` exposes a persistent keyboard menu with controller selection,
inquiry, classic PIN pairing,
ACL connect/disconnect, classic HID descriptor setup and connection status.
The fixed root helper uses FreeBSD `hccontrol`, `hcsecd` and `bthidcontrol`.
Configuration changes replace only a marked block for the chosen address;
unmanaged device entries cause an explicit stop. Failed daemon/connection setup
restores the prior file. PIN input is masked in fuzzel, never cached or passed as a command argument,
and travels through stdin, with
root-only temporary files. hcsecd manages persisted link keys itself.

Identify the actual controller with `usbconfig list`. Intel controllers may
need `iwmbt-firmware` and the base `iwmbtfw` loader before an `ubtNhci` node is
available. Match the USB vendor/product ID and firmware revision rather than
assuming that the Wi-Fi model proves Bluetooth support. Review package/firmware
dependencies before installing. Leave the BIOS Bluetooth device enabled.

For a supported classic keyboard or mouse, pair using its documented PIN, then
choose CONFIGURE CLASSIC HID. FreeBSD's bthidd rc script detects evdev support
and loads uinput as needed; its `-u` path feeds native desktop input. Verify real
keystrokes/pointer events after reconnecting and after reboot. The helper enables
only hcsecd/bthidd when those selected workflows actually succeed.

**Bluetooth LE HID, LE Audio and arbitrary modern headphones are not certified
by this implementation.** The classic base stack is not Linux BlueZ. A successful
ACL request alone supplies neither an audio sink nor a working HID profile.
Devices that require an unsupported pairing/profile remain unsupported until
their actual native implementation is established. USB/wired audio continues
through the existing mixer menu; no fake Bluetooth-audio route is created.

Sources: [FreeBSD Bluetooth](https://docs.freebsd.org/en/books/handbook/advanced-networking/#network-bluetooth),
[hcsecd](https://man.freebsd.org/cgi/man.cgi?query=hcsecd&sektion=8&manpath=FreeBSD+15.1-RELEASE),
[bthidd rc integration](https://cgit.freebsd.org/src/tree/libexec/rc/rc.d/bthidd?h=releng/15.1).
