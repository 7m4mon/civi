# Physical unplugged boot and wired recovery — 2026-11-08

## Result

Passed with the Pi's existing **static IPv4** configuration. The user unplugged the physical wired cable, rebooted the Pi and manually launched the helper, CIVI and panel from the desktop icon. WLAN at `192.168.4.54` remained the management path. No automatic startup was enabled.

| Stage | Evidence |
|---|---|
| Boot without wired cable | User reported LAN Fault on the attached panel; kernel carrier was 0 and no active wired IPv4 was present |
| Saved settings | Helper selected the original saved recovery UUID, with inactive profile `netplan-eth0`, manual `192.168.73.2/24`, no gateway/DNS, profile autoconnect=yes and device autoconnect=yes |
| Application availability | Helper and CIVI ready; panel process running; HTTPS `/lan-status` returned Fault with `LAN cable disconnected / no carrier`, with display connected/acknowledged |
| Duplicate-IP guard | Running without fault/error while unplugged and after reconnection |
| Reconnect physical cable | User reinserted the cable; original profile activated with carrier=true and `192.168.73.2/24`, without reapplying settings or restarting processes |
| Display/status recovery | `/lan-status` returned Normal, no faults, panel connected/acknowledged |
| External wired HTTPS | Windows explicitly bound its client to `192.168.73.1` and connected to Pi `192.168.73.2:443`; `/lxi` and `/lan-status` returned HTTP/1.1 200 with certificate trust and `civi.local` name validation enabled |
| External wired SCPI | Same Windows wired source read `CIVI Project,CIVI/IC-7300,CIVI-0001,0.1.0`, frequency 774000 Hz, mode AM and `0,"No error"` |

Before and after insertion, the wired profile values were the same. The Pi hostname remained `civi`. The physical cable operations and reboot were performed by the user; CIVI observations and external protocol checks were read-only. No radio setting, transmission, LAN RESET, IP configuration change or password change was performed.

The external client report is retained locally under ignored `tmp/unplugged-boot-wired-20261108.json`. The check used the IP for the actual wired connection and `civi.local` as the TLS server name, because the existing certificate covers that name rather than the numeric wired IP.

## Scope

This verifies an actual Pi reboot and cable reinsertion for the saved static profile, including selection of the inactive recovery target and manual startup with no carrier. It supplements the [desktop startup verification](RPI_DESKTOP.md) and the earlier [unplugged LAN RESET test](RPI_DISCONNECTED_RESET.md).

It does **not** verify the separate combination of performing LAN RESET, then rebooting unplugged in DHCP/AutoIP mode. Collision-derived mDNS names across a physical Pi reboot, DHCP server/lease boot combinations, static gateway/DNS reboot retention, Ethernet autonegotiation/Auto-MDIX and all LXI conditions remain separate. Existing automated test results are unchanged (**271 passed, 1 skipped**); no product code changed for this physical acceptance test. LXI conformance is not claimed.

The later [full LAN RESET boot test](RPI_LCI_BOOT_2026-11-08.md) completed the physical unplugged boot/reconnection combination with DHCP unavailable and AutoIP used, including recovery authentication. That later result does not extend this static-profile run to all DHCP/boot cases.
