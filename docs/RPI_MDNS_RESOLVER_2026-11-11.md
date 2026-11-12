# Pi outward mDNS resolution — 2026-11-11

This checks Pi as a resolver, separately from Windows discovering CIVI.
It follows [wired reprobe and advertising verification](RPI_MDNS_RECONNECT_2026-11-11.md).

## Setup

- Pi eth0 192.168.73.2/24, Windows direct-cable peer 192.168.73.1.
- Pi used its existing `hosts: files mdns4_minimal [NOTFOUND=return] dns`
  NSS configuration. No resolver package, NSS setting or IP setting was changed.
- A private Windows fixture shared UDP5353 on the selected wired interface only,
  filtered received packet metadata to that interface and Pi source, and replied
  through the same NIC with source 192.168.73.1 and multicast TTL255.
- Only the two fresh test names below were answered. The fixture ran with a
  five-minute limit and was stopped normally immediately after verification.
  Response DNS TTL was 30 seconds; there was no persistent service registration.

## Results

| Pi standard lookup | Result | Elapsed |
|---|---|---|
| `getent ahostsv4 civi-peer-20261111a.local` | 192.168.73.1 | 0.126 s |
| `getent hosts 169.254.73.1` | civi-autoip-fixture-20261111a.local | 0.106 s |

Both commands exited successfully without stderr. Python's standard
`socket.getaddrinfo(..., AF_INET)` and `socket.gethostbyaddr(...)` subsequently
returned the same forward/reverse results; these later calls may reuse cache.

The Windows fixture received the fresh A question for the forward name and the
PTR question for `1.73.254.169.in-addr.arpa.` from 192.168.73.2 on the selected
wired NIC. Thus the initial successful lookups were backed by actual outgoing
Pi mDNS queries and peer responses, rather than only a local hosts entry or a
Windows-to-Pi lookup.

The forward A record used the peer's actual assigned address. **169.254.73.1 was
synthetic DNS test data, not an assigned or reachable AutoIP peer address.**
The reverse result demonstrates the installed resolver's handling of that
link-local PTR name. It does not demonstrate AutoIP allocation, reachability,
reverse-record publication by an actual AutoIP device, or all RFC edge cases.
Those scopes remain separate from this resolver check.

Configuration, saved network preferences, authentication/recovery state, acquired
names, OS hostname and Avahi configuration hashes matched the preceding baseline.
No radio-setting or transmit commands were issued. No product change was required.
CIVI/helper/panel remain manually started. Private fixture output and lookup
results are retained under `tmp/mdns-resolver-20261111` on Windows.

The [requirements table](LXI_REQUIREMENTS_2026-11-10.md) records these limited
positive results without treating the full referenced RFC requirements as passed.

A [follow-up with a NetworkManager-allocated AutoIP peer](RPI_MDNS_AUTOIP_2026-11-11.md) verified real address publication, standard NSS lookups and TCP in isolated namespaces. The physical AutoIP-pair distinction remains.
