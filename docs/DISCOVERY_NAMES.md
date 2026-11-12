# Discovery names and collision recovery

Names submitted through the Web/API are truncated at complete UTF-8 characters within the first 63 bytes, then saved and advertised consistently. Blank-name factory reset remains supported. Pi services are advertised only on the configured wired interface.

## Raspberry Pi

Pi discovery uses the existing Avahi daemon for both hostname/address records and a single group of CIVI service records. This avoids competing hostname publishers. Windows retains Python zeroconf; its service-name selection also persists, while the Pi hostname collision behavior described here depends on Avahi.

Install the Pi dependency in the project's environment:

```bash
.venv/bin/python -m pip install -e '.[pi]'
```

Avahi must already be running on the Pi. CIVI and the LAN helper remain manually started; no new service or automatic startup is installed.

## Desired and acquired names

The user-configured OS hostname remains the desired name; the service Description remains the desired service name. Collision resolution does not overwrite either setting.

- Avahi probes and chooses the acquired mDNS hostname, with a numeric suffix when necessary. CIVI follows the daemon's current claimed hostname rather than independently publishing address records.
- CIVI registers HTTP/LXI/SCPI/HTTPS services as one Avahi group. A collision retries the complete group under a common numbered name such as `My radio (2)` and then `My radio (3)`.
- Candidates are streamed without a fixed candidate limit, with bounded memory and a short wait between collisions. Shutdown cancellation frees the group/socket. A mock test covers 110 consecutive collisions followed by common-name `(111)` registration and persistence; it is not a 111-device physical test.
- The desired and acquired names are saved separately in `.civi-discovery.json` (ignored by Git). A subsequent application launch reuses the acquired names. If an acquired service name conflicts again, the desired name is retried before continuing with numbered candidates. A saved acquired hostname that conflicts is similarly followed by a desired-name retry.
- Restoring a saved mDNS hostname uses the helper's fixed `mdns_hostname` operation, which calls only Avahi `SetHostName`. It does not change the OS hostname or IP settings. The helper must be available when such restoration is needed.
- LAN RESET changes the reset generation so that the last user-configured names are tried again, rather than blindly reusing collision-derived names. They can acquire suffixes again if the network still has a conflict.

The Welcome/LAN page shows **System hostname** and **Advertised mDNS hostname** separately. The panel also shows the mDNS name. The Description information shows the actual common service instance; the editable Description field retains the user's desired value. Startup/runtime logs report the advertised hostname and service name.

The periodic discovery monitor checks Avahi group state and follows hostname changes. A change from the registered hostname rebuilds the complete service group, so SRV targets and Web metadata follow the same acquired name. Group collision or registration failure also triggers re-registration; failures and inability to save names are visible rather than reported as successful discovery. Host records and other applications' advertisements remain managed by Avahi.

## Scope and limitations

On Pi, the discovery switch uses the helper to stop Avahi hostname replies and all Avahi service advertisements and block socket/D-Bus reactivation. Disabled state persists through a root-owned flag; IP-based Web access can enable it again, and LAN RESET re-enables it. See [device mDNS switch and tested scope](RPI_MDNS.md). Windows still withdraws only CIVI services. The kernel/DHCP desired hostname and an acquired mDNS hostname can differ after a collision. Certificates are not regenerated for acquired names; use a covered IP/name or update the certificate.
