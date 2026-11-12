# AutoIP TCP and reply routing — 2026-11-08

## Physical result

Passed with the PC **retaining static IPv4 `192.168.73.1`**, talking over the direct wired link to Pi **AutoIP `169.254.108.9`**. WLAN management stayed available throughout. After testing, the original Pi static profile `192.168.73.2/24`, autoconnect/Ethernet settings and WLAN UUID/IPv4 were restored and verified.

| Check | Result |
|---|---|
| Pi AutoIP reply route | `ip route get 192.168.73.1 from 169.254.108.9` selected `eth0`, table 31927, with no router next hop |
| Normal management route | `192.168.4.93` continued through `wlan0`, source `192.168.4.54` |
| Actual AutoIP HTTPS | PC wired source `192.168.73.1` reached AutoIP port 443; `/lxi` and `/lan-status` returned 200 with certificate trust and `civi.local` name validation |
| Actual AutoIP SCPI | Identity IC-7300, frequency 774000 Hz, mode AM, S-meter raw 74, `0,"No error"` |
| Windows test route | One active-store `169.254.108.9/32` on-link route was added on wired interface 4 with administrator consent, then deleted by the test's `finally` block; absence was independently checked |
| Restore | Fixed-IP HTTPS/SCPI worked before confirmation; saved profile/IP/autoconnect/Ethernet/WLAN matched the baseline after confirmation |
| Pi route cleanup | No priority-11927 rule or table-31927 route remained after AutoIP disappeared; the monitor was still healthy with an empty source list |

The PC's wired address, other link-local routes and default routes were not modified. No radio setting/transmit operation, password reset or autostart change was performed. The Web recovery password from the earlier LAN RESET remains authoritative.

## Two routing issues distinguished

The PC had its existing `169.254/16` route on another adapter, not on the selected wired NIC. Initial ordinary/per-socket-interface TCP attempts timed out, and a short header capture on the Pi saw no matching TCP traffic. Those physical timeouts alone therefore were not attributed solely to the Pi.

Independently, the Pi's route lookup for a reply **sourced from AutoIP** selected the WLAN gateway for the routable wired peer. AutoIP assignment and mDNS discovery by themselves did not establish correct TCP reply routing. In an isolated namespace test, a real routable-address peer and a separate simulated management default route reproduced failed TCP, then succeeded with the source-routing fix.

[RFC 3927 section 2.6.2](https://www.rfc-editor.org/rfc/rfc3927#section-2.6.2) requires packets using a link-local source to reach their destination directly on the chosen link rather than through a router. The helper now maintains an on-link route table for **exact currently assigned AutoIP source addresses on its selected wired NIC**. It does not add a broad source rule for every interface's `169.254/16` traffic or replace the normal default route.

## Implementation and operation

`civi/pi/linklocal.py` runs with the manually started privileged LAN helper. It uses priority **11927** and table **31927**, reserved for this deployment's single selected wired interface. For each current AutoIP address it adds an exact `/32` source rule and a direct on-link default in that separate table. Routable-source management traffic keeps its ordinary routes.

The monitor updates as addresses change, removes its owned rules/routes after AutoIP disappears or during normal helper shutdown, and keeps a root-private ownership journal under `/run/civi-lan`. A lock prevents two monitors using the same journal. Unowned rules, incompatible routes or conflicting ownership are rejected. Do not assign this priority/table to another routing policy.

Routing health is included in the existing helper `conflict_status` response. A stopped, stale or failed routing monitor is surfaced through the existing guard error path, preventing a healthy LAN from being displayed as Normal. The user restarted the helper to load the update during this test; no CIVI/radio settings restart was needed. Future use requires keeping the updated manual helper running.

Ownership/lifecycle behavior was tested in isolated namespaces, including recovery after an abruptly killed routing process, preservation of an unrelated default route, and cleanup after switching back to static IPv4. On the real Pi, source policy was confirmed active in AutoIP and absent after restoration.

## Reproduce and evidence

Run the isolated TCP acceptance manually as root; it moves no production interface:

```bash
cd ~/civi-rpi-lxi
sudo python3 tools/pi_autoip_tcp_check.py
```

Successful isolated artifacts: `/home/nom/civi-rpi-lxi/tmp/autoip-tcp-lab-20261108-182144-0a5753`. The shared fixture verified that the production network baseline was unchanged by that isolated test.

Physical baseline/restoration/cleanup reports are in ignored Pi `tmp/autoip-tcp-before-20261108.json`, `autoip-tcp-restored-20261108.json` and `autoip-tcp-cleanup.json`. The Windows one-shot client and report are local ignored `tmp/autoip_windows_test.py`, `autoip-windows-admin-result.json` and `autoip-tcp-restored-wired.json`. The client added only the selected Pi host route in ActiveStore, used normal sockets, and removed the route before exit. No Windows execution policy or persistent addressing was changed.

Automated Windows regression: **275 passed, 1 skipped**. Tests cover exact-source add/remove, refusal to mutate unowned rules and propagation of routing failure to helper health. The skip remains the Linux-only Unix-socket integration, not a pass.

## Limits

This confirms actual AutoIP TCP interoperability with a routable-address peer and the scoped reply-routing/lifecycle cases above. It is not complete RFC 3927 or LXI conformance: all multiple-AutoIP-interface combinations, packet forwarding/ARP requirements, existing TCP connections across address replacement, new-policy physical Pi reboot and every failure mode remain separate. Abrupt whole-process termination can leave owned entries until recovery/reboot; the private journal permits a restarted helper to recognize them, and that recovery was tested in isolation. Cleanup does not erase unrelated policies.

See the [preceding full LAN RESET/AutoIP boot test](RPI_LCI_BOOT_2026-11-08.md) and [maintained LXI matrix](LXI.md).
