# Wired mDNS reprobe after reconnection — 2026-11-11

This follows [physical name collision and reboot retention](RPI_NAME_COLLISION_2026-11-11.md).
It verifies a physical eth0 disconnect/reconnect with the same saved static IPv4
address and no competing name owner. It is not complete RFC6762/6763 or LXI validation.

## Method

- Pi eth0 192.168.73.2/24, Windows wired peer 192.168.73.1.
- WLAN remained available for management. CIVI/helper/panel stayed manually running.
- The user unplugged the Pi Ethernet cable, observed LAN FAULT, and reconnected it.
- A bounded private AF_PACKET capture on eth0 selected only IPv4 UDP5353 traffic.
  No host, IP, firewall, authentication or automatic-start settings were modified.
- The first run verified address restoration, Avahi rejoining, fresh service
  discovery, HTTPS and SCPI. Its 15-minute capture expired before reconnection,
  so it is not evidence of reprobe packets. A second complete physical cycle was
  captured with a longer bounded timeout and stopped immediately after collection.

## Observed result

The complete capture contained 141 mDNS packets and recorded carrier up/down/up.
Relative times below start at the capture monitor's first observation of link up;
the monitor polls at about 250 ms, so these are observations, not performance limits.

| IPv4 mDNS observation from Pi | Seconds after observed link up |
|---|---|
| civi.local. ANY probe, with proposed records in the authority section | 0.371, 0.621, 0.872 |
| First hostname/address announcement | 1.072 |
| All four CIVI service names probed, with authority records | 5.246, 5.497, 5.748 |
| First advertisements for all four CIVI services | 5.949 |

The advertisements targeted civi.local. at 192.168.73.2. HTTP, LXI and HTTPS
advertised port 443; raw SCPI advertised port 5025. Fresh Windows DNS-SD queries
resolved all four services after reconnection. Certificate-verified HTTPS /network
and a read-only TCP *IDN? also succeeded. HTTPS connected to the Pi numeric address
while checking the certificate against its covered civi.local name.

Configuration, saved network preferences, authentication/recovery state, acquired
names, OS hostname and Avahi configuration hashes were unchanged. The active and
saved wired address remained 192.168.73.2/24. CIVI/helper/panel were still running.
No transmit or radio-setting commands were sent. No product code change was needed.
The capture process exited normally; it is not part of CIVI startup.

Private captures remain under tmp/mdns-reconnect-20261111 on Windows and the
corresponding private tmp directories on Pi. MAC-derived workstation/IPv6 records
are omitted from this public report.
