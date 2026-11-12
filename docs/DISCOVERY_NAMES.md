# Discovery names and collision recovery

2026-11-10 correction: names submitted through the Web/API are truncated at complete UTF-8 characters within the first 63 bytes, then saved and advertised consistently. Blank-name factory reset remains supported. Pi services are now advertised only on the configured wired interface.

## Raspberry Pi

Pi discovery uses the existing Avahi daemon for both hostname/address records and a single group of CIVI service records. This avoids competing hostname publishers. Windows retains Python zeroconf; its service-name selection now also persists, while the Pi hostname collision behavior described here depends on Avahi.

Install the Pi dependency in the project's environment:

```bash
.venv/bin/python -m pip install -e '.[pi]'
```

Avahi must already be running on the Pi. CIVI and the LAN helper remain manually started; no new service or automatic startup is installed. Restart the updated helper and CIVI after installing this change. This installation's Python dependency was installed during development.

## Desired and acquired names

The user-configured OS hostname remains the desired name; the service Description remains the desired service name. Collision resolution does not overwrite either setting.

- Avahi probes and chooses the acquired mDNS hostname, with a numeric suffix when necessary. CIVI follows the daemon's current claimed hostname rather than independently publishing address records.
- CIVI registers HTTP/LXI/SCPI/HTTPS services as one Avahi group. A collision retries the complete group under a common numbered name such as `My radio (2)` and then `My radio (3)`.
- Candidates are streamed beyond the former `(101)` limit, with bounded memory and a short wait between collisions. Shutdown cancellation frees the group/socket. A mock test covers 110 consecutive collisions followed by common-name `(111)` registration and persistence; it is not a 111-device physical test.
- The desired and acquired names are saved separately in `.civi-discovery.json` (ignored by Git). A subsequent application launch reuses the acquired names. If an acquired service name conflicts again, the desired name is retried before continuing with numbered candidates. A saved acquired hostname that conflicts is similarly followed by a desired-name retry.
- Restoring a saved mDNS hostname uses the helper's fixed `mdns_hostname` operation, which calls only Avahi `SetHostName`. It does not change the OS hostname or IP settings. The helper must be available when such restoration is needed.
- LAN RESET changes the reset generation so that the last user-configured names are tried again, rather than blindly reusing collision-derived names. They can acquire suffixes again if the network still has a conflict.

The Welcome/LAN page shows **System hostname** and **Advertised mDNS hostname** separately. The panel also shows the mDNS name. The Description information shows the actual common service instance; the editable Description field retains the user's desired value. Startup/runtime logs report the advertised hostname and service name.

The periodic discovery monitor checks Avahi group state and follows hostname changes. A change from the registered hostname rebuilds the complete service group, so SRV targets and Web metadata follow the same acquired name. Group collision or registration failure also triggers re-registration; failures and inability to save names are visible rather than reported as successful discovery. Host records and other applications' advertisements remain managed by Avahi.

## Scope and limitations

On Pi, the discovery switch now uses the helper to stop Avahi hostname replies and all Avahi service advertisements and block socket/D-Bus reactivation. Disabled state persists through a root-owned flag; IP-based Web access can enable it again, and LAN RESET re-enables it. See [device mDNS switch and tested scope](RPI_MDNS.md). Windows still withdraws only CIVI services. The kernel/DHCP desired hostname and an acquired mDNS hostname can differ after a collision. Certificates are not regenerated for acquired names; use a covered IP/name or update the certificate.

Real Pi tests covered conflicting service groups, restart reuse, another collision of the saved instance, and reception from the Windows PC. The [2026-11-08 hostname acceptance](MDNS_HOSTNAME_2026-11-08.md) additionally used two real Avahi daemons in isolated namespaces to verify startup collision, live renaming with updated service targets/Web metadata, acquired-name reuse, same-process recovery after an Avahi restart and retrying the desired name when the saved name conflicts. The [2026-11-11 physical wired test](RPI_NAME_COLLISION_2026-11-11.md) verified hostname/service collisions, saved-name reuse after a full Pi reboot with the peer removed, and restoration of original names/settings. A [physical same-static-IP reconnection](RPI_MDNS_RECONNECT_2026-11-11.md) also verified fresh hostname/service probes and advertisements. Reconnection with a competing owner, repeated collisions beyond the candidate limit and other link/boot combinations remain unverified. This is not a claim of LXI conformance.
