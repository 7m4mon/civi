# Pi device-wide mDNS / DNS-SD switch

2026-11-10 scope correction: CIVI LXI services are advertised only on the configured wired NIC. Avahi hostname support and its device-wide enable/disable still operate globally. WLAN management access is retained, and it is not declared as an LXI interface in identification XML. Restart CIVI after deploying this change.

The `/network` **Enable mDNS / DNS-SD** switch now controls the Pi's Avahi hostname replies as well as CIVI's service advertisements. On the supported Pi configuration Avahi is the sole mDNS provider; systemd-resolved was inactive and no other UDP 5353 listener was found. Windows continues to withdraw only CIVI's own zeroconf services.

## Use

Restart the updated LAN helper and CIVI manually, then reload `/network`. Use the numeric IP address (for example `https://192.168.73.2/network`) before disabling discovery. Enter the current Web password, clear the checkbox and select **Save and apply**.

The Pi page shows **Device mDNS: Disabled (Avahi stopped; activation blocked)** only after the helper verifies the operation. Existing DNS caches may still resolve `.local` temporarily; cached resolution does not prove the device is answering fresh queries. Disabling also stops other applications' Avahi advertisements and Avahi-based outgoing `.local` resolution. IP-based HTTPS and SCPI remain available. A certificate that lacks the IP address can still cause a browser warning.

To restore discovery, open the page through its numeric IP, check the box and save. Description and the desired/acquired names are retained. CIVI re-registers its services; a name conflict can still acquire a suffix. A normal application shutdown does not automatically change the user's discovery setting.

The desired setting remains in `.civi-network.json`. A root-owned flag at `/var/lib/civi/mdns.disabled` also preserves the OS-level disabled state while CIVI is stopped and across boot. Updating source files alone does not restart already-running processes.

## Bounded helper operation

Only the fixed local helper operation `mdns` with a Boolean `enabled` is accepted; callers cannot choose a service, command or filesystem path. It uses the existing privileged Unix socket, not a new TCP service. Web access still requires authentication and CSRF protection.

For each of `avahi-daemon.service` and `avahi-daemon.socket`, the helper installs a dedicated `50-civi-mdns.conf` drop-in containing:

```ini
[Unit]
# CIVI device-wide mDNS switch
ConditionPathExists=!/var/lib/civi/mdns.disabled
```

When disabling, it creates the private flag, stops both units and verifies inactive/failed states plus absence of IPv4/IPv6 UDP 5353 listeners. The conditions prevent socket and D-Bus activation from starting Avahi again. A concurrently requested activation can cancel a stop job; the helper stops both paths and checks actual final state instead of treating that job's exit status alone as success or failure.

When enabling, it removes only its own flag, starts the existing Avahi units and verifies they are active. It does not unmask units, overwrite a foreign drop-in, change service enablement, install a CIVI service or grant permanent sudo access. If enabling fails after removal, it restores the disabled flag and stops Avahi again. Command failures or another UDP 5353 publisher are reported as errors, not a verified disable. The Web distinguishes the saved desired setting from an application failure, and the background monitor retries.

This controls the tested Avahi-based Pi configuration. Installing a different mDNS stack or publishing from another program requires another validation; this is not a general firewall that blocks arbitrary future software. Do not claim full LXI conformance from this change alone.

## LAN RESET and local recovery

The updated helper's LAN RESET initialization enables Avahi even if CIVI is not running. The local reset also saves discovery enabled for the next application launch. Initialization failure attempts to restore previous network/Ping/mDNS state. The [disconnected reset update](RPI_DISCONNECTED_RESET.md) removes the active-profile requirement when a validated recovery UUID has been provisioned.

If Web recovery is unavailable, from the Pi's attached terminal as an administrator:

```bash
sudo rm -f /var/lib/civi/mdns.disabled
sudo systemctl start avahi-daemon.socket avahi-daemon.service
```

This restores the OS service only. If the saved CIVI discovery setting is still false, a running updated CIVI will disable it again; use numeric-IP Web access to save Enabled, or use the documented local LAN RESET. Do not delete credentials merely to restore discovery.

## Verification — 2026-11-07

- Unit tests cover stop/start, durable flags across controller recreation, both unit conditions, failed enable restoration, another UDP publisher, failed/cancelled stop jobs, rejecting foreign configuration and invalid helper fields, and retry after helper failure.
- LCI transaction tests cover enabling mDNS and restoring the previous disabled state on failure without retaining an unconfirmed network change.
- On the actual Pi, disabled the provider with the new controller, recreated the controller to check the flag, and attempted socket and D-Bus-alias activation. Both units stayed stopped and UDP 5353 was absent.
- From Windows on the direct wired LAN, fresh DNS queries received hostname and LXI PTR replies before disabling, no replies while disabled, and replies after re-enabling. This used fresh UDP requests, not cached OS hostname lookup.
- The production HTTPS page stayed accessible by numeric IP during the disabled interval. The test client connected by IP and verified the existing certificate using the covered `civi.local` TLS server name. This does not mean the certificate covers numeric-IP URLs in browsers.
- Restored Avahi enabled, confirmed production 443/5025 listeners and hostname `civi`. No production password, IP, Description or desired discovery setting was changed. The new persistent drop-ins remain, with the disabled flag absent.

References: [systemd activation conditions](https://www.freedesktop.org/software/systemd/man/latest/systemd.unit.html), [Avahi configuration](https://github.com/avahi/avahi/blob/master/man/avahi-daemon.conf.5.xml.in), and [LXI requirements matrix](LXI.md).

Final same-day state: the user re-enabled mDNS and Ping after the reboot check. Fresh hostname and LXI service replies returned; Ping replied through both wired and WLAN addresses. The device was left enabled. See the [complete daily record](PROGRESS_2026-11-07.md).
