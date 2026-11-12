# Duplicate IPv4 detection and wired disconnection

The Pi LAN helper now includes a receive-only ARP guard for its selected wired interface. It supplements NetworkManager's address checks before activation. No new service, automatic startup or radio operation is added.

## Behavior and recovery

- NetworkManager checks an address before assigning it. In the isolated Pi test, an occupied static address was rejected, occupied link-local candidates were skipped, and an occupied DHCP lease generated DHCP DECLINE.
- While the helper is running, a foreign Ethernet/ARP sender claiming an IPv4 address currently assigned to the selected interface triggers `nmcli device disconnect <interface>`. The helper verifies that the conflicting address disappears and logs the result. WLAN is not the target; disconnecting the wired NIC removes its other IPs too.
- Ordinary ARP probes (`sender IP = 0.0.0.0`), our own MAC, unrelated addresses and malformed frames do not trigger this guard. It does not send ARP packets or change saved IP settings.
- The conflict remains visible to CIVI's Web/local-panel status through a private helper request. The message distinguishes verified disconnection from an unverified attempt. An unavailable, stale or failed guard prevents a healthy LAN from being reported as Normal.
- Remove the conflicting peer/configuration first. Through WLAN, apply the intended wired configuration and **Confirm and save** from the wired address; successful confirmation clears the guard's fault. Local LAN RESET also clears it after successful initialization. A failed confirmation does not clear the fault. NetworkManager's device-disconnect operation prevents automatic reactivation until an explicit connection activation.

## Verification

Run manually as root on the Pi:

```bash
cd ~/civi-rpi-lxi
sudo python3 tools/pi_conflict_check.py
```

It uses the same isolated namespace/private NetworkManager fixture as the [DHCP test](DHCP_2026-11-08.md). Netplan inputs and generated runtime files are hidden inside the fixture, including Debian's Netplan integration in the keyfile plugin. Only synthetic peers and documentation addresses appear on this virtual Ethernet. Tests check actual kernel addresses, ARP/DHCP captures, the real `PiLanReader`/`LanIndicator` path and the guard's verified outcome. Artifacts are root-only under ignored `tmp/conflict-lab-*`.

Checks include static conflict rejection and recovery, conflict after static activation, occupied AutoIP candidates and recovery, DHCP DECLINE without using the address, and conflict after AutoIP activation. The cleanup compares the production wired profile/IP, NetworkManager PID, resolver file and Netplan YAML hashes with the baseline.

All of those checks passed on 2026-11-08 with Pi NetworkManager 1.52.1. The successful artifacts are `/home/nom/civi-rpi-lxi/tmp/conflict-lab-20261108-090615-8e1602`; cleanup reported `host_network_unchanged: true` at 09:06:47 Pi local time. Windows automated regression: **265 passed, 1 skipped** (the Linux-only Unix-socket test).

The first fixture attempt allowed Debian's Netplan generator to import host profiles; that attempt is not acceptance evidence. The fixture was corrected to isolate `/run` and Netplan inputs. A first DHCP peer sent periodic announcements that could miss the short DAD window; the final peer responds immediately to candidate probes. The unmodified runtime behavior retained a conflicting static address and reported Normal; this observation led to the guard implementation.

## Scope

This is partial verification against [LXI Device Specification 1.6.2](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf), sections 8.7 and 8.10. Physical eth0, power-on and all configuration paths still need appliance-level acceptance. NetworkManager's configurable initial DAD behavior is described in its [IPv4 settings](https://www.networkmanager.dev/docs/api/latest/settings-ipv4.html); an externally disabled DAD setting is not corrected by the runtime guard.

The guard requires the foreground privileged helper and handles ordinary untagged Ethernet ARP. VLAN/tunnel networks, IPv6 duplicate detection and malicious peers are outside this test. A silent peer that neither answers probes nor emits a conflicting claim cannot be established as a duplicate by this mechanism. The attached physical display was not used for this isolated test; Web status is also covered by automated tests. LXI conformance is not claimed.
