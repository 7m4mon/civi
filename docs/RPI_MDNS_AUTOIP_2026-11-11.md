# Allocated AutoIP peer: NSS and TCP — 2026-11-11

## Scope

The [preceding wired resolver test](RPI_MDNS_RESOLVER_2026-11-11.md) used synthetic
link-local PTR data. This follow-up used an address actually allocated by
NetworkManager, a real Avahi responder and real TCP sockets in isolated Pi Linux
network namespaces. It is a virtual Ethernet test, not a second physical device
or a physical eth0 AutoIP-pair test.

The existing private NetworkManager/Avahi laboratory isolates network, mount,
UTS and D-Bus state. No physical interface is moved or reconfigured. The normal
CIVI/helper/panel stay running; authentication and radio settings are untouched.
The Windows network-management query was unavailable, so no Windows adapter or
route setting was changed.

## Reproduction

Run manually on the Pi checkout with the existing laboratory dependencies:

```sh
sudo .venv/bin/python tools/pi_mdns_autoip_check.py
```

The opt-in tool is never launched by CIVI or pytest. It uses the existing
`tools/pi_dhcp_check.py` private NetworkManager harness and
`tools/pi_mdns_check.py` private Avahi wrappers. The network namespaces and child
processes are removed in the harness's cleanup path.

## Observed result

No DHCP server was started. CIVI's automatic-mode apply/confirm ran inside the
private NetworkManager instance; its saved IPv4 method was `auto` with no static
address configured. NetworkManager assigned **169.254.127.84** to the peer.
The separate requester had a distinct static link-local source, 169.254.220.1.

| Check from requester | Result |
|---|---|
| Standard NSS `getent ahostsv4 civi-autoip-peer.local` | 169.254.127.84 |
| Standard NSS `getent hosts 169.254.127.84` | civi-autoip-peer.local |
| TCP connection to allocated address, port 18881 | Request/reply payload matched |
| Private saved address mode | Automatic, no static address |
| Cleanup | Both test namespaces removed; host network matched baseline |

The TCP listener is a one-connection test server and has no radio backend.
No radio commands were sent. Production configuration, saved network preferences,
authentication/recovery state, acquired names, OS hostname and Avahi configuration
hashes matched the preceding baseline. Production eth0 remained 192.168.73.2/24;
CIVI/helper/panel remained running. No product code change was required.

Private Pi artifacts are in
`tmp/mdns-autoip-lab-20261111-193651-8c29c6`, with a verified result copy under
Windows `tmp/mdns-autoip-20261111`. Only the opt-in test tool and this report are
published; MAC-derived identifiers and authentication data are omitted.

## Remaining limits

This closes the synthetic-address limitation for the isolated AutoIP resolver/TCP
case. A pair of physical AutoIP endpoints, interface-speed combinations and all
referenced RFC boundary cases remain unverified. Combined with the preceding
physical wired Pi standard-resolver check, it provides separate evidence for the
production resolver path and real allocated-address behavior, without treating
the two runs as a single physical AutoIP-pair test or claiming LXI conformance.
