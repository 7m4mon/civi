# Physical Ethernet DHCP follow-up — 2026-11-10–11

This extends the earlier [isolated network-stack tests](DHCP_2026-11-08.md)
to the real Pi eth0. It is not a complete LXI/RFC acceptance verdict.

## Configuration and containment

- Pi 4, NetworkManager 1.52.1; original wired address 192.168.73.2/24.
- Windows PC wired address 192.168.73.1/24, interface index 4; direct cable.
- Pi WLAN 192.168.4.54 remained the pinned-key SSH and HTTPS management path.
- The opt-in `tools/windows_dhcp_lab.py` fixture allocates only 192.168.73.3
  to the explicitly configured Pi MAC, accepting only its packets received on
  the chosen interface. Actual MAC addresses and raw captures stay in ignored
  private tmp artifacts and are not reproduced here.
- Windows replies explicitly select both source IP and outgoing interface using
  [Winsock IN_PKTINFO](https://learn.microsoft.com/en-us/windows/win32/api/ws2ipdef/ns-ws2ipdef-in_pktinfo).
  Missing interface metadata is an error, not permission to respond on any NIC.
  Unit tests reject requests from other NICs/MACs, relays, foreign servers and
  malformed messages; a real loopback test checks ancillary-data send/receive.
- No Windows IP, forwarding, ICS or firewall settings were modified. A single
  probe while Pi retained its fixed IP confirmed the existing bidirectional path;
  no new firewall rule or additional Pi was required.
- Each actual IPv4 change used the running CIVI helper's automatic-mode trial
  with a 180-second NetworkManager checkpoint. Trials were never confirmed or
  saved; each was rolled back to the original fixed profile. PTT OFF was checked
  before starting. No radio settings or transmission were part of this test.

The fixture is deliberately not a general DHCP server. It has no address pool,
relay, routing or DNS service and is not used by normal CIVI startup. It returns
only the controlled options needed for these trials. Initial delivery uses the
broadcast fallback described in [RFC 2131 section 4.1](https://www.rfc-editor.org/rfc/rfc2131.html#section-4.1);
renewal responses to an existing ciaddr are unicast. Default leases are 120 seconds
(T1=60/T2=105); an explicit 60-second fixture lease (T1=30/T2=52) leaves more time
to observe reacquisition within the bounded checkpoint. Client timing constants
and gateway settings are not shortened.

## Initial observations and correction

The first physical run acquired the DHCP address, gateway and DNS. A natural
renewal changed gateway from 192.168.73.1 to 192.168.73.254 and DNS from
192.168.73.53 to 192.168.73.54 without reactivation. Server records included an
ACK to a renewing request with ciaddr=192.168.73.3. Rollback restored the original
fixed profile and LAN Normal.

When the server became silent, the 120-second lease expired: the DHCP address,
gateway and DNS disappeared and AutoIP became active. However CIVI incorrectly
reported LAN Normal. Its monitor read the saved static profile while the
unconfirmed device-only trial was actually running DHCP.

The correction adds a read-only `NetworkManager.applied_ipv4()` query and makes
PiLanReader use those effective settings. NetworkManager explicitly distinguishes
saved profiles from the device's
[GetAppliedConnection settings](https://networkmanager.dev/docs/api/latest/gdbus-org.freedesktop.NetworkManager.Device.html).
This also distinguishes rollback to static mode from continued use of AutoIP after
lease loss. Failed effective-setting reads produce Unknown, with no silent fallback
to a potentially misleading saved profile. The privileged helper's authorization
and mutation operations are unchanged. Only CIVI needed restarting; helper and
panel continued running.

The corrected 120-second repeat retained the DHCP-loss Fault during AutoIP. Its
30-second reacquisition observation window ended before a new lease arrived. A
60-second lease with a longer observation window exposed the fixture problem:
NetworkManager sent a DISCOVER from 0.0.0.0 retaining its previous ciaddr, and the
fixture wrongly rejected it. The fixture now accepts the configured client's old
ciaddr and uses broadcast for pre-address reacquisition. Foreign addresses, NICs
and MACs are still rejected. Three recorded requests replayed successfully, and
the final 60-second repeat completed. These earlier timeouts are not counted as
successful recovery or established client defects; full RFC client validation
remains outside this run.

## Evidence and limits

Initial and corrected intermediate artifacts remain under local ignored
tmp/physical-dhcp-20261110/attempt1 and attempt2. Pi DHCP-only PCAP/JSONL captures
are under tmp/physical-dhcp-20261110, tmp/physical-dhcp-20261110-repeat and the
final tmp/physical-dhcp-20261110-short. Private trial tokens, MACs and credentials
are not part of this public report.

Final run completed on 2026-11-11 (Australia/Sydney). Earlier runs are retained
separately rather than overwritten.
This run does not establish DHCP acquisition at boot, cable reconnection or LCI;
physical duplicate-IP cases; full RFC3927 behavior; all DHCP options; external
DNS resolution/routing; or persistence of a confirmed DHCP mode across reboot.
LAN state comes from the live HTTPS API with the attached panel connected. A new
human visual confirmation of the panel during this DHCP fault is not claimed.

## Manual fixture usage

Run this only on an isolated direct-cable test segment. Supply a JSON config with
interface_index, server_ip, client_ip and client_mac (optionally lease_seconds of
60 or 120), and a separate state JSON with enabled, gateway, dns and hostname.
Use the actual adapter index and your test device MAC; do not use real customer
addresses/MACs in public examples or commit private captures.

```powershell
python tools/windows_dhcp_lab.py --config tmp/dhcp-config.json --state tmp/dhcp-state.json --output tmp/dhcp-run --check
python tools/windows_dhcp_lab.py --config tmp/dhcp-config.json --state tmp/dhcp-state.json --output tmp/dhcp-run --seconds 600
```

`--check` verifies the selected route, local address and exclusive UDP67 bind
without sending. Runtime is bounded to at most 1800 seconds; Ctrl+C stops the
server. An invalid control file stops response processing. Fixture shutdown does
not reconfigure the client: use a separate NetworkManager checkpoint and finally
rollback when conducting IPv4 trials. The ordinary Web form uses a shorter
90-second trial; do not assume that covers a 120-second expiry test.


## Completed results

| Check | Observation |
|---|---|
| Real eth0 DHCP acquisition | 192.168.73.3/24 acquired; LAN Normal |
| Requested options | Physical requests included subnet mask/router/DNS options 1/3/6 |
| Natural renewal | Renewal ACK 60.01 seconds after the first ACK; new gateway .254 and DNS .54 applied without reactivation |
| Lease expiry | Server silent; leased address, gateway and DNS removed; AutoIP active |
| Fault retention | Corrected live LAN state remained Fault while using AutoIP after lease loss |
| New lease | Server resumed; DHCP address reacquired and live LAN state returned to Normal without client reactivation |
| Missing gateway/DNS | DHCP acquired with those options omitted; LAN Normal, per-interface gateway/DNS empty |
| Server-supplied hostname | ACK included other-dhcp-name; system hostname remained civi |
| Restoration | Every trial rolled back to 192.168.73.2/24; original profile UUID/settings matched |

The final expiry/recovery and missing-option run reported success. The failure-state
samples showed the local panel connected and acknowledged, but that acknowledgement
is not a new human visual check of the panel's Fault banner. The final raw captures
are under tmp/physical-dhcp-20261111-final on Pi; Windows retains copies of all four
capture sets plus server logs, observations and hashes under its ignored
tmp/physical-dhcp-20261110 directory. The third intermediate run is attempt3.

Windows regression: **580 passed, 1 Linux-only skip**, 39.01 seconds. Pi related
regression: **68 passed, 1 Windows-only skip**, 0.90 seconds. The Windows-specific
skip is the real Winsock loopback integration, which passed on Windows. The new
applied-setting reader/indicator tests cover DHCP loss, held Fault, a new lease,
static rollback and unreadable/malformed runtime settings.

Cleanup confirmed saved CIVI config, Web credentials and network settings hashes
unchanged. The helper and panel were retained; only CIVI was restarted for its
monitor fix. Windows stayed at wired 192.168.73.1 and WLAN 192.168.4.93. The test
server was stopped and exclusive UDP67 bind was available again. No Windows
firewall rule was added. A proposed WLAN negative probe could not bind its client
UDP68 socket, so physical no-response on WLAN is **not** claimed; other-NIC rejection
is covered by the fixture tests and explicit packet metadata.

Final radio readback was 927000 Hz, AM, PTT OFF, SCPI error queue empty. No frequency
or mode setting command or transmit-start command was sent by this experiment.
This record does not attribute manual tuning or other external radio changes.
