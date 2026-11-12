# Wi-Fi menu and recovery

`install.sh --clean` and `--upgrade` report whether `pkg.FreeBSD.org` is
reachable, then offer this console setup with `Configure a Wi-Fi connection now?
[y/N]` before downloading packages. Enter keeps the current connection; without a
reachable package server, declining stops the run. The check fetches the
repository's `meta.conf` as pkg does. `getent hosts` would not do: it sends DNS
queries over TCP, which many home routers refuse.
It discovers the radio and an existing matching wlan interface, creates one if
needed, asks for the SSID/security/password, and configures the native rc services.
The password is hidden and the prompt bypasses installer logs. When a supplicant
already serves the interface, the setup first shows the current network and its
security, for example `Connected to Home with WPA2-PSK.`, and offers only the
security modes that supplicant can use. To change a saved network, such as its
security or password, enter its name again: the setup says it has a saved
profile, and the new settings replace it once they connect. Failed
authentication restores the previous persistent configuration from a backup
under `/var/backups/nostromo`; the installer's cleanup removes these backups. A
running supplicant is restarted with the merged profile; a setup that stops
before that step leaves it running undisturbed. If `pkg.FreeBSD.org` is still
unreachable after association, the saved network stays and the run stops for
diagnosis. See [Base-Setup](BASE-SETUP.md) for read-only filesystems and
single-user recovery.

Super+Ctrl+W and the Wi-Fi status action open the same native fuzzel panel. It uses the launcher's content-sized shape,
left divot rail, Michroma font and bottom-right body cut. Enter selects,
Up/Down or Ctrl+P/N navigate, and Esc cancels. Operations return to the menu;
ADAPTER switches radios. Privileged operations open a foot prompt for the root
password through base su/PAM, then return to this panel. Cancelling changes nothing.
It discovers wlan interfaces, requests scans, selects saved networks and accepts
hidden SSIDs. Scan SSIDs are decoded from wpa_cli's byte escapes into configuration
hex; they are never shell commands. Passwords use masked, uncached input without diagnostic logging. They are sent
on stdin and stored
only in root-owned mode-0600 configuration/temporary files.

The root helper uses the existing FreeBSD `wpa_supplicant_conf_file` from sysrc.
That file must be regular, root-owned and mode 0600, with a working
`ctrl_interface=/var/run/wpa_supplicant` (or an explicitly configured safe directory
beneath `/var/run`). Console Wi-Fi setup configures this control socket without giving the
ordinary account direct supplicant configuration access. No already-working
network or unrelated directive is erased.

CONNECT writes the chosen network as a `NOSTROMO WIFI <SSID hex>` block and
removes every other saved profile with that name, including one that bsdinstall
or an editor wrote, so an old profile cannot win after a restart. Other networks
and comments stay byte for byte. Names are read as wpa_supplicant reads them,
as `"text"`, `P"escaped"` or hex; a name it would reject stops the change.
CONNECT then restarts the native per-interface supplicant, checks with it that no
other profile names the network, selects the new profile and waits up to 30
seconds for authentication. A failure restores the previous file and selected
network. To change a saved network's security or password from the desktop,
choose it again through **SCAN** or **HIDDEN**.
DHCP is restarted only when the interface's existing rc configuration uses it;
static addressing is retained. Association success is separate from DHCP, DNS
and Internet reachability. Verify those after changing networks.

## Phone hotspots and public networks

Phone hotspots use the same **SCAN** or **HIDDEN** flow as a home access point.
Choose `wpa2` for a password-protected WPA2 hotspot or `wpa3` for SAE. Select
`open` for a network without wireless encryption, or `owe` for Enhanced Open.
Open/OWE connections do not request a Wi-Fi password. A name hidden by the phone
can be entered with HIDDEN. The helper checks the running supplicant's advertised
key-management capabilities before changing a profile; the driver must also
support the selected band and mode. A mode the supplicant lacks stops with
`… is not available with this Wi-Fi driver and supplicant` and the modes it offers,
before anything changes. FreeBSD 15.1's base wpa_supplicant is built without SAE
and OWE (`usr.sbin/wpa/Makefile.inc`), and its FreeBSD driver interface offers
only WPA/WPA2 key management (`driver_bsd.c`), so on 15.1 the base supplicant
cannot use `wpa3` or `owe` with any adapter. A router in WPA2/WPA3 mixed mode
still accepts `wpa2`. For a phone that offers a compatibility setting, WPA2 and
2.4 GHz are useful alternatives when its newer mode is unsupported. No automatic
security downgrade is made.

For a hotel, café, airport or other public network:

1. Connect to its advertised network, then use **STATUS** to check association.
2. Choose **PORTAL**. It opens `http://neverssl.com/` in an ordinary qutebrowser
   window so the access point can redirect to its sign-in/terms page. Complete
   that page in the browser. A portal can also exist on a password-protected network.
3. Once signed in, check normal browsing and bring up WireGuard if wanted.
   If an existing full-tunnel VPN interferes with sign-in, disconnect it explicitly
   through the VPN manager first. The Wi-Fi manager does not disable PF or a VPN.

PORTAL runs only when selected: there is no background connectivity probe or
stored portal password. Association does not prove that a portal has granted
Internet access. If the venue provides a specific sign-in URL, open that URL
instead. During the initial console installation, use a network with working
Internet access; the browser is not installed yet and a captive portal can
prevent package downloads even after DHCP/DNS succeed.

Enterprise/eduroam and Passpoint provisioning need the provider's EAP method,
identity, certificates and server-verification settings. They are not equivalent
to a web portal or a personal-network password. Add the provider's verified
profile to the native WPA configuration; **SAVED** can select it without replacing
it. This menu does not claim automatic enrollment for every public Wi-Fi service.
Open networks remain unencrypted; OWE encrypts the wireless link without
authenticating the access-point operator.

Use `service wpa_supplicant status wlanN`, `wpa_cli -i wlanN status`,
`ifconfig wlanN`, DHCP logs and the native handbook for recovery. Share redacted
status only; never paste the WPA configuration or passwords into issue reports.
[FreeBSD wireless networking](https://docs.freebsd.org/en/books/handbook/network/#network-wireless).
[Enterprise authentication](https://docs.freebsd.org/en/books/handbook/advanced-networking/#network-wireless-wpa-eap-tls)
describes provider-specific EAP setup.

Raw scan records are selected by index after display-only control-character
cleanup, preserving exact SSID bytes. SSIDs containing shell syntax are data.
The GUI keeps the session UTF-8 locale for Japanese/Korean network names.
