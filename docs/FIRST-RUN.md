# First-run requirements

The installer configures the desktop after a normal **multi-user boot**. Root
does not make a read-only filesystem writable. Check [BASE-SETUP](BASE-SETUP.md)
if you selected single-user mode; finish booting before running the installer.
Preflight checks writable `/etc`, `/var` and `/usr`, and that `devd` is running.

| Area | What is configured | What still comes from you or the hardware |
| --- | --- | --- |
| Base installation | Native release/kernel checks, account/home discovery, protected checkout validation | Install FreeBSD, create the account/root password and put the owned checkout in its permanent location |
| Downloads | Signed package transactions and checksum-pinned sources | Working DNS, correct clock, internet access and enough storage for builds/libraries |
| Wi-Fi | Console bootstrap before pkg; detected radio/WLAN, protected profile setup; desktop hotspot/open/OWE connections and PORTAL browser action | Actual country, SSID and password where required; supported authentication/band; venue web sign-in or provider EAP settings; working internet for initial downloads |
| Bluetooth | INITIALIZE in the manager loads supported Intel USB firmware and native HCI service when missing; pairing/HID files are created when needed | Supported USB controller and actual device PIN/profile; not every BLE/audio device is supported |
| Graphics/displays | Detected Intel DRM/firmware, Wayland session, output/layout menu | Native graphics, monitor and suspend acceptance; optional preferred dock arrangement |
| Audio/microphone | Native sound and routing helpers | Choose the attached input/output; verify microphone level and hardware mute |
| WireGuard | Native tools, profile permissions, manager and status | Your keys, peer endpoint, routes and DNS policy; no credentials are generated for an unknown peer |
| SSH | Client setup and selective sshd/PF hardening | Trusted host keys and authorized login keys; passwords are not replaced with invented keys |
| Password store | pass-compatible tpass workflow | Initialize/import your own OpenPGP key and password store |
| Fingerprint/FIDO | Optional discovery/enrollment helpers and documented PAM path | Supported device, explicit enrollment and a successful password-fallback test |
| Printers/scanners/camera | Device discovery, permissions and native service helpers | Actual device/backend/queue choices and a hardware test |
| Embedded work | LLVM/Rust/Go/Python tools, west and probe utilities | Board/target selection, vendor SDK/model licenses, pin map, linker memory map and probe connection |
| KiCad | Suite, libraries, missing global library tables, assembly plugin, exports and offline manuals | Project circuit, footprints, SPICE models and fabrication constraints |
| Fonts/reference books | Bundled fonts and explicit staged documentation checks | Optional project/CPU/vendor documentation not supplied by a language toolchain |

The setup does not assume credentials, a printer model, a board memory map or a
working biometric sensor. Those steps remain explicit. Native acceptance is
listed in [VALIDATION](VALIDATION.md); a host test cannot replace it.
