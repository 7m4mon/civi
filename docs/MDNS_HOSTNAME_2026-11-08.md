# Real Avahi hostname collision and restart acceptance — 2026-11-08

## Result

Passed on Raspberry Pi 4, Avahi 0.8, NetworkManager 1.52.1 and Python 3.13.5. Two real Avahi daemons communicate across isolated virtual Ethernet namespaces.

| Check | Observation |
|---|---|
| Desired hostname already occupied | Client acquired `civi-mdns-lab-2.local.` |
| Fresh CIVI discovery process | Reused the saved `-2` acquired hostname |
| Conflict while running | A conflicting mDNS A announcement caused Avahi to acquire `-3`; CIVI rebuilt all four services and saved the new name |
| Avahi daemon restart, same CIVI process | With the desired name now free, restarted Avahi initially used it; CIVI restored saved `-3` through the actual bounded helper operation |
| Fresh CIVI process after daemon restart | Reused `-3` |
| Saved acquired name now occupied | Attempted saved `-3`, then retried the desired name and acquired `civi-mdns-lab.local.` |
| Peer service resolution | HTTP/LXI/raw SCPI/HTTPS SRV targets matched each acquired hostname, with client address `192.0.2.77` and the expected advertised ports |
| Web information | Actual `/lxi` and `/network` responses showed the acquired mDNS name while the desired OS hostname remained unchanged |

The successful artifacts are `/home/nom/civi-rpi-lxi/tmp/mdns-lab-20261108-100810-3d3ae0`. Both cleanup checks passed: production hostname/Avahi PID/name were unchanged, and production wired profile/IPv4, NetworkManager PID, resolver file and Netplan YAML hashes matched the baseline. Created namespaces and processes were removed.

Automated Windows regression: **266 passed, 1 skipped**. The skip remains the Linux-only Unix-socket integration. A regression test verifies that a live hostname change rebuilds service registration before exposing the new metadata.

## Bug fixed

The first live-conflict test exposed a stale service target: CIVI's Web metadata followed the new Avahi hostname, but the existing dynamic EntryGroup SRV records still pointed at the old hostname. The independent peer continued resolving the old target after a bounded 15-second convergence wait. This was not treated as a successful advertisement update.

`AvahiDiscovery.inspect()` now treats a change from the registered hostname as a reason to rebuild the entire service group through `Discovery.refresh()`. The replacement group uses Avahi's newly acquired hostname. Saving and publishing the updated metadata follow successful registration. Desired user settings are not overwritten by collision-derived names.

The fix is in the Pi checkout. Manually restart CIVI to load it. The running production process was not restarted during acceptance; no new service or automatic startup was installed.

## Reproduce and scope

```bash
cd ~/civi-rpi-lxi
sudo python3 tools/pi_mdns_check.py
```

The script reuses the [isolated network fixture](DHCP_2026-11-08.md), including private NetworkManager/D-Bus/Netplan runtime state. Each Avahi has a private runtime and configuration; no production `SetHostName` call is made. Test files, per-phase JSON/logs, generated Web HTML, Ethernet PCAP and cleanup records stay under ignored root-only `tmp/mdns-lab-*`.

The desired-name startup collision uses a real peer Avahi. The live-conflict case injects a conflicting DNS A announcement only onto the virtual link. Service resolution runs through the independent peer daemon. The local helper fixture uses the real `BrokerClient` request path, broker dispatch, hostname validation and `Transactions.mdns_hostname()`/Avahi `SetHostName`. Its `mdns, enabled=true` check is a fixture-only read response; global mDNS enable/disable behavior is covered separately by [the device switch tests](RPI_MDNS.md).

Web checks use actual CIVI routes over HTTP on private loopback port 18843, with a mock identity. They verify rendered names, not TLS or radio control. Refresh polling is accelerated for the test, so these timings are not production recovery-time guarantees. Avahi's configuration and behavior are based on its [upstream configuration documentation](https://github.com/avahi/avahi/blob/master/man/avahi-daemon.conf.5.xml.in).

Physical eth0/two-host collision tests, an actual Pi reboot with acquired names saved, and all link-disconnection/boot combinations remain. Certificates are not regenerated for acquired names. See [name handling](DISCOVERY_NAMES.md) and [the maintained LXI matrix](LXI.md).
