# Native WireGuard client

`nostromo-vpn` and the VPN menu use FreeBSD's `wg(4)`. The source recipe builds
only `wg` with base Clang and libnv. It does not install wg-quick or Bash.
There is no alternative mesh client or server/router provisioning here.

Before using UP, create `/usr/local/etc/nostromo/wireguard` as root, mode 0700.
Put the real native `wg setconf` file in `wg0.conf`, mode 0600, owned by root.
It contains `[Interface]` with the actual `PrivateKey`, then real `[Peer]`
sections with `PublicKey`, `AllowedIPs`, and the actual `Endpoint` where needed.
Generate the private key locally with `wg genkey`; keep it out of the checkout,
terminal logs and process arguments. No working keys/endpoints are bundled.

Beside it, create `wg0.network`, also root-owned mode 0600. Its typed rows are:

```text
# Replace these documentation addresses with your real tunnel allocation.
address inet 192.0.2.2/32
route inet 192.0.2.1/32
```

`inet6` rows accept actual IPv6 CIDRs. AllowedIPs selects which peer may carry
traffic; the network file separately installs explicit kernel routes. The helper
rejects default routes and shell hooks, preserves DNS and existing routes, and
rolls back a failed setup. It refuses to destroy an interface it did not create.
This is the requested remote-access client path; a full-tunnel/default-route
policy needs a separate reviewed endpoint/DNS/route design.

Set a different `WG_INTERFACE` in `~/.config/nostromo/services.local` if needed.
The default is `wg0`. The fuzzel panel's TUNNEL action lists only numeric `wgN`
profiles with matching regular root-owned mode-0600 `.conf` and `.network` files.
Selecting a tunnel saves its name under `~/.local/state/nostromo/wireguard-interface`
so the bar and CLI track the same selection; remove that file to return to the
configured default. UP/DOWN/STATUS return to the panel and show failures explicitly. The root installer leaves auto-start disabled until real
keys and addressing exist. After testing, enable the provided native rc service:

```sh
su -
sysrc nostromo_wireguard_interfaces=wg0
sysrc nostromo_wireguard_enable=YES
exit
```

The bar reads the public interface state: OFF, DOWN or UP. It never prompts for
authentication and does not claim a current handshake. The panel's changes and
detailed STATUS use base su/PAM in a foot prompt. Generate real traffic, inspect `nostromo-vpn status`,
then test SSH to your own configured alias. Peer public keys/transfer counters
are shown; private/pre-shared keys are never printed by the status path.

Sources: [wg(4)](https://man.freebsd.org/cgi/man.cgi?query=wg&sektion=4&manpath=FreeBSD+15.1-RELEASE),
[wg tools](https://git.zx2c4.com/wireguard-tools/tree/src/man/wg.8).
