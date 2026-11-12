# Full LAN RESET, unplugged Pi boot and AutoIP recovery — 2026-11-08

## Result

Passed the physical **AutoIP fallback** branch with no DHCP lease obtained on the direct wired segment. The user ran the full local `bash lan-reset.sh` workflow, kept the displayed recovery password privately, unplugged Ethernet, rebooted the whole Pi and manually started the desktop launcher. WLAN at `192.168.4.54` remained the management path. This includes the local credential reset/startup workflow, not only the network backend tested previously.

| Stage | Verified observation |
|---|---|
| Before reset | Saved original wired UUID/profile, `192.168.73.2/24`, autoconnect, explicit Ethernet auto-negotiation settings and WLAN UUID/IPv4 |
| Full local reset | User confirmed completion and recorded the password. NetworkManager showed method auto, no manual IPv4, link-local fallback=4, DHCP timeout=2147483647 and autoconnect=yes; AutoIP `169.254.108.9/16` was observed before shutdown |
| Unplugged physical reboot | Changed kernel boot ID confirmed a new Pi boot. The remembered wired UUID was selected with no active connection/carrier/address, retaining the saved DHCP/AutoIP settings |
| Display and helper | Attached panel connected/acknowledged with LAN Fault `LAN cable disconnected / no carrier`; helper and duplicate-IP guard running without fault/error |
| Credential persistence | A local authenticated HTTPS request using the saved per-device recovery credential returned 200 after reboot. The password remained on the Pi and was neither printed nor archived |
| Physical cable reinserted | Without an apply, connection-up or process-restart command, NetworkManager acquired `169.254.108.9/16`; LAN status returned Normal with no fault and the panel connected/acknowledged |
| Fresh external discovery | A new Windows zeroconf instance bound only to wired `192.168.73.1` received `_lxi._tcp` for `CIVI CIVI-0001`, target `civi.local.`, AutoIP `169.254.108.9`, port 443 and IC-7300 identity |
| Original fixed IP restored | Applied the original static address through the helper's checkpointed transaction, verified wired access, then confirmed. Saved IPv4/profile settings, autoconnect, Ethernet settings and WLAN UUID/IPv4 matched the baseline |
| Final wired access | Windows source `192.168.73.1` reached Pi `192.168.73.2` over trusted/name-verified HTTPS `/lxi` and `/lan-status`. SCPI returned IC-7300 identity, 774000 Hz, AM and `0,"No error"` |

Final state: static `192.168.73.2/24`, manual profile, LAN Normal, 1000 Mb/s full duplex, explicit unrestricted auto-negotiation retained, helper/guard/panel healthy, WLAN unchanged, no pending transaction. The Web recovery credential remains authoritative; the old authentication state was not restored. The user can choose a normal saved password through **Change Web password**.

No transmit or radio-setting operation was performed. No service, autostart, Windows IP change or Windows route change was introduced.

## Evidence and limits

Private non-credential reports on the Pi are in ignored `tmp/lci-boot-before-20261108.json`, `lci-boot-unplugged-20261108.json`, `lci-boot-reconnected-20261108.json` and `lci-boot-restored-20261108.json`. Windows reports are local ignored `tmp/lci-boot-mdns-20261108.json` and `lci-boot-restored-wired-20261108.json`. The temporary restore token was deleted after confirmation. Recovery-password files are excluded from the evidence archive.

The Web credential's acceptance after reboot was checked; this run did not separately test rejection of the previous password or live credential reload in an already running CIVI process. The full local reset had completed before the tested manual application start.

This run verifies physical boot/recovery with **DHCP unavailable and AutoIP used**. Boot with a real DHCP server, every lease/boot combination, collision-derived mDNS hostname restoration across a physical reboot and all LCI clauses remain separate. DHCP acquisition/renewal/expiry were previously tested in [isolated Pi namespaces](DHCP_2026-11-08.md).

AutoIP was verified by kernel/helper state, local HTTPS status and fresh discovery received over the physical Ethernet link. TCP/HTTPS/SCPI over the AutoIP itself from a routable-address peer was not tested; Windows' static wired interface had no link-local route, and its routes were left unchanged. External TCP checks above were made after restoring the fixed IP. RFC 3927 forwarding/routing behavior is not claimed complete from this test.

There were no product-code changes for this acceptance run. The existing automated result remains **271 passed, 1 skipped**, not a newly run suite. See the [earlier static-profile unplugged boot](RPI_UNPLUGGED_BOOT_2026-11-08.md), [desktop launcher](RPI_DESKTOP.md) and [LAN RESET scope](RPI_LAN_RESET.md). LXI conformance is not claimed.

Subsequently, [physical AutoIP TCP and reply routing](RPI_AUTOIP_TCP_2026-11-08.md) were verified and a source-routing fix was added. The limitations above describe this earlier boot-only run.
