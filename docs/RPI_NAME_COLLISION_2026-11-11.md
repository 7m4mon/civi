# Physical name collisions / restart retention — 2026-11-11

This follows [the isolated Avahi name tests](MDNS_HOSTNAME_2026-11-08.md).
It covers a direct-cable Windows/Pi test, not complete RFC6762/6763 or LXI
conformity. Unverified cases remain in [G06](LXI_REMAINING_2026-11-10.md).

## Setup and containment

- Windows wired interface 192.168.73.1 / index 4; Pi eth0 192.168.73.2.
- Pi WLAN 192.168.4.54 retained for pinned-key SSH management.
- Desired OS hostname civi; desired service Description CIVI CIVI-0001.
- The user started CIVI/helper/panel manually. A private Pi backup under
  tmp/name-collision-backup-20261111-071751 preserves the original acquired-name
  cache and configuration/authentication files, without exporting passwords.
- The opt-in tools/mdns_collision_peer.py fixture advertises four deliberately
  conflicting HTTP/LXI/SCPI/HTTPS service instances with test-only TXT identity
  and unused ports. It provides no HTTP or SCPI server and performs no radio I/O.
  Python zeroconf 0.151.5 binds advertising to the selected IPv4 interface.
- Its Windows hostname authority shares mDNS UDP5353 but filters incoming packet
  metadata by the selected interface, and explicitly selects source IP/NIC for
  replies. The UDP helper still uses exclusive bind by default for the separate
  DHCP fixture. No Windows IP, hostname, firewall or startup configuration changed.

The fixture uses the installed
[python-zeroconf API](https://python-zeroconf.readthedocs.io/en/latest/api.html)
and Windows packet metadata. It is a manual test tool and never runs with ordinary
CIVI startup. Stop with Ctrl+C, its output/stop file, or the bounded runtime.
Normal shutdown withdraws the registered records. Tests reject unassigned,
wildcard, public, loopback and link-local interface addresses and invalid names.

## Physical conflict observations

CIVI and Avahi advertisements were stopped temporarily, keeping helper/panel and
both IP management paths. The PC established the conflicting records first, then
Pi advertising and CIVI resumed. OS hostname and IP settings were not changed.

The first service-only fixture caused the common service name to become
CIVI CIVI-0001 (2). Its hostname advertisements did not establish the required
probe-response behavior, so that initial run is not counted as a host conflict
pass. Packet observation confirmed arrival of unique A answers on real eth0,
source 192.168.73.1, mDNS destination and TTL255. Avahi could return to probing
and reclaim the name if the fixture did not answer that probe.

The fixture was then given an explicit established-owner response to matching
IPv4 hostname/ANY questions, rather than relying on service announcements alone.
This matches the conflict/reprobe distinction in the
[Avahi server implementation](https://github.com/avahi/avahi/blob/master/avahi-core/server.c).
The corrected physical run produced:

| Item | Acquired value |
|---|---|
| mDNS hostname | civi-2.local. |
| Common service instance | CIVI CIVI-0001 (2) |
| Desired OS hostname | civi, unchanged |
| Desired editable Description | CIVI CIVI-0001, unchanged |
| Wired address | 192.168.73.2/24, unchanged |

The acquired hostname/service/reset generation were persisted together in
.civi-discovery.json. Original CIVI config, saved discovery preferences, saved
authentication/recovery, /etc/hostname and Avahi configuration hashes matched.

Fresh wired queries resolved all four Pi advertisements to civi-2.local. at
192.168.73.2, with HTTPS-related ports 443 and SCPI raw 5025. The LXI TXT identity
matched schema-valid identification XML and *IDN?. Web Hostname/Description showed
the acquired names, while System hostname/editable Description retained desired
values. IPv6/MAC-derived records and private captures are not reproduced here.

HTTPS checks connected to the numeric Pi address while validating the existing
certificate against its covered original civi.local name; HTTP Host was the numeric
address so generated identification URLs still referred to the Pi. No certificate
validation was disabled. This does not assert certificate coverage for civi-2.local;
collision names do not automatically regenerate the existing certificate.

## Reboot and cleanup status

The PC fixture was stopped and withdrew all four records. A new query no longer
found the original service instance. The Pi user was then asked to reboot the
whole Pi and manually start all three components, without LAN RESET or name edits.
The user completed that reboot and manual launch. A changed kernel boot ID
confirmed a full Pi reboot. Avahi initially acquired civi.local. while the peer
was absent; CIVI then restored the saved civi-2.local. and service instance
CIVI CIVI-0001 (2). Fresh wired queries, Web metadata and identification XML
matched those saved acquired names. This verifies retention independently of
another collision selecting the same suffix.

After the test, the original acquired-name cache was restored byte-for-byte and
CIVI was restarted manually. Avahi, Web and fresh queries for all four services
again reported civi.local. / CIVI CIVI-0001 at 192.168.73.2. Configuration,
authentication/recovery, OS hostname and Avahi configuration hashes matched the
baseline, and the saved IPv4 profile was unchanged. Both PC fixtures stopped
normally and withdrew their records. CIVI/helper/panel remain manually running.

Windows automatic tests: **599 passed, 1 Linux-only skip** (39.62 seconds).
Pi related tests: **49 passed, 1 Windows-only skip** (0.40 seconds).
The fixture tests cover validation, coherent service records and matching hostname
probe responses; they do not substitute for the physical observations above.

Private Windows artifacts are below tmp/name-collision-20261111. The initial
service-only observation and the corrected host-probe fixture are recorded
separately. A [same-static-IP physical reconnection follow-up](RPI_MDNS_RECONNECT_2026-11-11.md)
confirmed fresh hostname/service probes and advertisements. Normal browser display
after reboot, reconnection with a competing name owner, repeated
collisions beyond the current candidate limit, and complete RFC boundary behavior
are not inferred from this scoped run.
