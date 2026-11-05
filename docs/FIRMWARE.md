# ThinkPad T14 Gen 2 Intel firmware profile

Updated **2026-11-04**. Manual BIOS choices for the FreeBSD 15.1 Wayland daily driver. The goal is available CPU
capacity under load, responsive graphics, working peripherals and low idle cost.
These are recommendations based on the supplied BIOS inventory, not settings
applied remotely or measured gains. The installer does not write firmware.
Every adjustable item in the supplied Config and Security inventory is covered
below. Main's identification fields are read-only; keep their existing values.
Optional Startup entries are listed separately because that menu was not supplied.

## Recorded baseline

| Field | Reported on 2026-10-27 |
| --- | --- |
| Model | ThinkPad T14 Gen 2 Intel, type/model 20W1S4F61C |
| Processor | Core i5-1135G7; BIOS lists 2.400 GHz |
| BIOS | N34ET71W (1.71), dated 2026-05-09 |
| Embedded controller | N34HT46W (1.46) |
| Management Engine firmware | 15.0.55.2751 |
| Installed memory | **16384 MB reported by BIOS** |
| Storage | Previously reported 2 TB WD BLACK SN850X NVMe |
| Boot / sleep | Secure Boot Off; Linux S3 |

Graphics confirmed separately on 2026-11-04: **Intel Iris Xe integrated GPU**.

The owner subsequently confirmed **16 GiB RAM and eight logical CPUs** using
native FreeBSD sysctl. This supersedes the earlier 24 GB description. Resource
limits still use `sysctl hw.physmem` dynamically. Do not infer the soldered/module
split from this total. Lenovo lists both
8 GB and 16 GB soldered variants, each with one SO-DIMM slot. Resolve the
discrepancy before sizing hibernation swap or planning a memory upgrade.
[Lenovo model specifications](https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_T14_Gen_2_Intel/ThinkPad_T14_Gen_2_Intel_Spec.pdf).

Unit/board serials, UUID, MAC address and Windows licensing identifiers are not
needed for these settings and are omitted. The firmware versions above are the
owner's observations; this document does not claim they are Lenovo's latest.

## CPU, power and display

| BIOS option | Current | Recommended | Purpose / tradeoff |
| --- | --- | --- | --- |
| Intel Hyper-Threading | On | **Keep On** | Expose the sibling threads; verify all eight logical CPUs are available in FreeBSD. |
| Intel SpeedStep | On | **Keep On** | Retain dynamic frequency control. |
| CPU Power Management | On | **Keep On** | Retain idle power saving. |
| Thermal scheme for AC | Maximize Performance | **Keep** | Favor sustained throughput and cooling. |
| Thermal scheme for Battery | Maximize Performance | **Balanced for battery use** | The latest request adds battery efficiency; Maximize Performance remains the explicit throughput-first alternative on battery. |
| Energy Efficient Turbo | On | **Keep On initially; compare Off on AC** | Preserve the new battery-efficiency baseline; retain Off only if repeated builds show a worthwhile gain. |
| Cool & Quiet on Lap | Off | **Keep Off on a ventilated desk** | Keep the selected performance profile; use the cooler setting when working on a lap. |
| Sleep State | Linux S3 | **Keep Linux S3** | Expose S3 sleep. This is a firmware label, not a Linux installation. |
| Power On with AC Attach | Off | **Keep Off** | Avoid an unintended boot/resume when connecting power. |
| Wake Up on Alarm | Disabled | **Keep Disabled** | No scheduled wake is required. |
| Disable Built-in Battery | Not invoked | **Leave alone** | Service action, not a performance setting. |
| Boot Display Device | ThinkPad LCD | **Keep** | Keep recovery visible on the laptop; runtime layouts use DISPLAYS. |
| Total Graphics Memory | 256 MB | **Keep 256 MB initially** | No demonstrated FreeBSD benefit from increasing it; test 512 MB only for a reproducible graphics problem. |
| Boot Time Extension | Disabled | **Keep Disabled** | Add delay only if an external boot display needs it. |

Lenovo documents the thermal profiles and idle clock control in its
[ThinkPad power reference](https://docs.lenovocdrt.com/ref/bios/settings/thinkpad/power/).
Its general Intel [Energy Efficient Turbo definition](https://docs.lenovocdrt.com/ref/bios/settings/thinkstation/cpusetup/#energy-efficient-turbo)
describes an efficiency/performance preference. Applying that definition to the
option visible on this T14 is a tuning inference: **Off is only an experiment, not a measured win**
and does not remove thermal or electrical limits. Revert to On if sustained
throughput declines or extra heat buys no useful improvement.
The graphics allocation and boot-display controls are described in Lenovo's
[display reference](https://docs.lenovocdrt.com/ref/bios/settings/thinkpad/display/).

## Network, USB and keyboard

These changes primarily affect firmware boot, standby power or ergonomics.
They are not claims of faster C/Rust builds or a smaller FreeBSD kernel.

| BIOS option | Current | Recommended | Purpose / tradeoff |
| --- | --- | --- | --- |
| Wake On LAN | AC Only | **Disabled** | No remote-wake requirement for this daily driver; retain AC Only if later needed. |
| Wake On LAN from Dock | On | **Off** | Same remote-wake choice for the dock. |
| UEFI IPv4 Network Stack | On | **Off** | Local USB/NVMe installation does not need firmware network boot. |
| UEFI IPv6 Network Stack | On | **Off** | Same; this does not disable FreeBSD IPv6. |
| UEFI Network Boot Priority | IPv4 First | **Leave** | Inactive while the firmware network stacks are off. |
| UEFI PXE TFTP Window Size | 4 | **Leave 4** | Only relevant to PXE transfers. |
| Lenovo Cloud Services / UEFI Wi-Fi Network Boot | Unavailable | **Leave unavailable** | Not needed for this install. |
| Wireless Auto Disconnection | Off | **Keep Off** | Let FreeBSD manage connectivity when Ethernet is attached. |
| MAC Address Pass Through | Disabled | **Keep Disabled** | No dock MAC-identity requirement. |
| Always On USB | On | **Off** | Stop peripheral charging in low-power states; re-enable if that feature is wanted. |
| Charge in Battery Mode | Off | **Keep Off** | Avoid using the laptop battery as an off-state charger. |
| TrackPoint / Trackpad | On / On | **Keep both On** | Preserve local input and recovery. |
| Fn and Ctrl Key swap | Off | **Keep Off** | Preserve the current physical layout. |
| Fn Sticky Key | Off | **Keep Off** | Keep ordinary modifier behavior. |
| F1–F12 as Primary Function | Off | **On** | Direct function keys for editor/debugger use; Fn accesses the media functions. |
| Keyboard Layout | English (United States) | **Keep** | Matches base installation and the Wayland compositor bindings. |
| Password Beep / Keyboard Beep | Off / On | **Off / Off** | Quiet keyboard use; no performance claim. |
| Setup UI | Graphical | **Keep Graphical** | Simple Text is an equally valid preference; neither changes desktop resource use. |

Definitions: Lenovo [network](https://docs.lenovocdrt.com/ref/bios/settings/thinkpad/network/),
[USB](https://docs.lenovocdrt.com/ref/bios/settings/thinkpad/usb/) and
[keyboard](https://docs.lenovocdrt.com/ref/bios/settings/thinkpad/keyboardmouse/) references.
Keep the separate Ethernet LAN, Wireless LAN and USB Port switches **On**.
Disabling a UEFI network stack affects preboot networking, not those devices.

## Devices, security and service actions

| BIOS option | Current | Recommended | Reason |
| --- | --- | --- | --- |
| Ethernet LAN / Wireless LAN / USB Port / Memory Card Slot | On | **Keep On** | Preserve normal networking, installation media and peripherals. |
| Integrated Camera / Audio / Microphone | On | **Keep On** | Keep hardware available; the OS and selected applications control access; verify the microphone mute path. |
| Wireless WAN | On | **Off for the present Wi-Fi/Ethernet setup** | Re-enable if a supported cellular modem/SIM is needed. |
| Bluetooth | On | **On** | Latest request restores Bluetooth; detect its FreeBSD driver, firmware and device profiles. |
| Fingerprint Reader | On | **Keep On for identification** | BIOS settings do not establish native driver or login support. |
| Fingerprint Predesktop Authentication | On | **Off for password-based FreeBSD setup** | Do not introduce a second, unconfigured preboot authentication path. |
| Fingerprint Security Mode / Single-touch authentication | Normal / On | **Leave while predesktop authentication is off** | No enrollment changes; do not invoke Reset Fingerprint Data. |
| Thunderbolt 4 device / PCIe Tunneling | On / On | **Keep for required dock/peripheral testing** | Disabling tunneling can remove PCIe devices behind a dock. |
| Intel Virtualization Technology | Off | **Keep for the initial no-VM baseline** | Not needed for this workload; switching it off is not a demonstrated speedup. |
| VT-d / Kernel DMA Protection | Off / Off | **Keep the recorded baseline for initial compatibility testing** | Do not claim this is a performance optimization or that DMA protection is active. Test protection separately with the actual dock. |
| Enhanced Windows Biometric Security / Device Guard | Off / Off | **Keep Off** | Windows-specific facilities are outside this installation. |
| Execution Prevention | On | **Keep On** | Retain memory protection; no measured reason to remove it. |
| Security Chip Type | TPM 2.0 | **Keep TPM 2.0** | Retain the installed chip type. |
| Security Chip / SMBIOS Reporting / Physical Presence for Clear | On / On / On | **Keep all On** | Do not clear the chip as a tuning step. |
| Secure Boot | Off | **Keep Off for this initial FreeBSD install** | Preserve the current boot arrangement; do not reset, clear or replace its keys. |
| Flash BIOS Updating by End-Users | On | **Keep for firmware maintenance** | Use the official package for this exact model. |
| Secure RollBack Prevention | On | **Keep On** | No performance benefit from permitting firmware downgrades. |
| Windows UEFI Firmware Update | Off | **Keep Off** | Not the update route for this FreeBSD machine. |
| Bottom Cover / Internal Storage Tamper Detection | Off / Off | **Leave during setup** | Administrative protection choice, not runtime tuning. |
| ThinkShield secure wipe in App Menu | On | **Off** | Hide an unused destructive service action; never invoke a wipe for optimization. |

Lenovo's [Thunderbolt reference](https://docs.lenovocdrt.com/ref/bios/settings/thinkpad/thunderbolttm4/)
explains the tunneling dependency. Its [virtualization reference](https://docs.lenovocdrt.com/ref/bios/settings/thinkpad/virtualization/)
states that enabling Kernel DMA Protection also enables VT-x and VT-d. Keeping
them off for the recorded baseline is **not** a claim that they hurt performance.
An enabled firmware checkbox alone does not certify FreeBSD DMA isolation.
See [hardware acceptance](HARDWARE.md) for the dock and fingerprint tests.

Leave the supplied password policy unchanged while establishing this baseline:
Supervisor, System Management, Power-On and NVMe1 passwords remain unset;
their access-control switches remain Off; Block SID Authentication stays On;
Lock UEFI BIOS Settings stays Off; Password at Unattended Boot and Password
Count Exceeded Error stay On; Password at Restart and Boot Device List stay Off;
minimum-length enforcement and Strong Password remain disabled. These choices
are **not a hardening recommendation** or a performance improvement. A firmware
password/recovery policy is a separate owner decision; do not create passwords,
reset fingerprint data, clear the TPM, erase storage or clear boot keys here.
Once installation and recovery work, a Supervisor Password together with Lock
UEFI BIOS Settings can protect changes to the firmware. Keep its recovery record
outside the laptop. That is separate from the OS login and disk encryption;
the BIOS lock does not take effect without a Supervisor Password.
[Lenovo password controls](https://docs.lenovocdrt.com/ref/bios/settings/thinkpad/password/).

## Remaining password, key and service options

These rows complete the supplied inventory. Leave them as recorded for the
initial comparison; they are not recommendations to weaken a personal firmware
password policy and provide no desktop performance gain.

| BIOS option | Recorded / initial choice |
| --- | --- |
| Supervisor Password | Disabled / unset |
| System Management Password | Disabled / unset |
| System Management Password Control | Off |
| Power-On Password Control | Off |
| Storage Password Control | Off |
| BIOS Setup Configurations access control | Off |
| Power-On Password | Disabled / unset |
| NVMe1 Password | Disabled / unset |
| Block SID Authentication | On |
| Lock UEFI BIOS Settings | Off |
| Password at Unattended Boot | On |
| Password at Restart | Off |
| Password at Boot Device List | Off |
| Password Count Exceeded Error | On |
| Set Minimum Length | Disabled |
| Set Strong Password | Off |
| Secure Boot Mode | User Mode; leave unchanged |
| Secure Boot Key State | Customized; leave unchanged |
| Reset to Setup Mode / Restore Factory Keys / Clear All Secure Boot Keys | Do not invoke |
| Key Management | Leave existing keys alone |
| Reset Fingerprint Data | Do not invoke |
| Clear Security Chip | Do not invoke |
| Disable Built-in Battery | Do not invoke except during physical servicing |
| ThinkShield secure wipe | Never invoke as a tuning operation |

## Boot and clock

Use UEFI boot for the FreeBSD installer and installed system. Use the F12 device
menu for the installer USB, then put the installed FreeBSD/NVMe boot entry first.
Do not load factory defaults, delete boot entries or clear keys to apply this
profile. Save the selected changes with the firmware's Save and Exit action.

The Startup menu was not included in the hardware inventory. These are conditional
choices for controls that actually appear, using Lenovo's
[Startup definitions](https://docs.lenovocdrt.com/ref/bios/settings/thinkpad/startup/):

| Option, if present | Initial choice |
| --- | --- |
| UEFI/Legacy Boot | UEFI Only |
| CSM | Disabled |
| Boot Mode (Quick / Diagnostics) | Quick; Diagnostics for troubleshooting |
| Option key Display | On |
| Boot device List F12 Option | On |
| Boot Order Lock | Off while installing or updating the boot entry |
| Network Boot | Leave; unused with remote wake and firmware network stacks disabled |

Boot Mode's Quick/Diagnostics choice is distinct from UEFI versus legacy boot.
Do not search for a hidden or modified BIOS to expose an absent option.

For this FreeBSD-only installation, set the hardware clock to the current UTC
date/time and choose Asia/Kuala_Lumpur as the OS timezone. UTC is eight hours
behind Malaysia, including the date change around midnight. If the installer
asks whether the hardware clock uses UTC, answer to match what is actually set.
FreeBSD's [tzsetup(8)](https://man.freebsd.org/cgi/man.cgi?query=tzsetup&sektion=8&manpath=FreeBSD+15.1-RELEASE)
documents the distinction between the hardware clock and local timezone.

## Apply and compare manually

1. Keep a local record of the current values before changing BIOS options.
2. Keep UEFI boot, Secure Boot Off for this initial install, Linux S3, SpeedStep,
   CPU power management and Hyper-Threading. The firmware's Linux S3 label does
   not install Linux; test S3 on FreeBSD after graphics and locking work.
3. Use Maximize Performance on AC and Balanced on battery for the new combined
   performance/battery goal. Keep Energy Efficient Turbo On at first. Its Off
   comparison is optional and should change no other variable in the test.
4. Disable unnecessary firmware PXE stacks, remote wake, standby USB charging,
   and WWAN as listed. Ethernet, Wi-Fi, Bluetooth and USB remain enabled.
5. Leave the Intel framebuffer reservation at 256 MB initially. GPU acceleration
   depends on the correct DRM driver/firmware, not simply reserving more RAM.
6. After FreeBSD installation, check the detected CPU, memory and HWP driver:

```sh
sysctl hw.model hw.physmem hw.ncpu
sysctl dev.cpufreq.0.freq_driver
sysctl -a | grep '^dev.hwpstate_intel\.[0-9][0-9]*\.epp:'
```

An absent HWP sysctl is a diagnostic result, not a reason to paste another OS's
CPU settings. See [PERFORMANCE.md](PERFORMANCE.md) for the native profiles and
[HARDWARE.md](HARDWARE.md) for actual GPU, dock, audio and suspend acceptance.
The old OpenBSD apmd/hw.perfpolicy/hw.blockcpu choices do not apply to this OS.

Compare three identical builds on AC with the same job count and starting
thermal state. Record elapsed time, temperature and energy use. Keep the faster
stable configuration, not merely the one showing the highest idle frequency.
On battery use the same brightness, network state and workload when comparing
Wayland/CRT settings. No tuning value here is a measured result for this laptop.
