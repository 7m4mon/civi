# LAN RESET from the attached Pi console

This is a development implementation of the local LAN Configuration Initialize (LCI) mechanism. It does not establish LXI conformance. It is available on the Raspberry Pi/Linux target, using its permanently attached keyboard and display. No GPIO button, service installation or automatic startup is added.

## Run

Start the updated LAN helper once in its own terminal:

```bash
cd ~/civi-rpi-lxi
sudo python3 -m civi.pi.broker --owner nom
```

CIVI can stay running. In another terminal on the **Pi's attached keyboard/display**, run as the normal CIVI user:

```bash
cd ~/civi-rpi-lxi
bash lan-reset.sh
```

Read the displayed scope and enter `LAN RESET` to execute. Any other answer cancels before mutation. SSH and redirected input are refused by the command. There is no Web/SCPI reset endpoint. The helper's Unix socket is accessible only to the designated local user.

The implementation requires NetworkManager >= 1.52, the manually running helper and a writable CIVI configuration directory. The updated helper records the intended wired recovery UUID in a root-owned file and can initialize that profile while the cable is disconnected. Start it once with the intended profile active, or provision it explicitly with `--profile-uuid`. Unknown or mismatched targets are rejected. See [disconnected reset setup and physical verification](RPI_DISCONNECTED_RESET.md). Bind CIVI to `0.0.0.0` so its listeners remain available after an address change.

## Reset scope

| Setting | Result |
|---|---|
| Selected wired IPv4 profile | DHCP with AutoIP fallback; remove manual address, gateway and DNS; accept DHCP DNS and default gateway |
| IPv4 Ping replies | Set Linux `icmp_echo_ignore_all` to 0 immediately and persist it in `/etc/sysctl.d/90-civi-lan.conf` |
| CIVI mDNS/DNS-SD | Enable and save discovery; a running updated CIVI reloads it within its normal monitoring cycle |
| CIVI Web password | Reset to the device's recovery default; username remains `admin` |
| Hostname and service description | Retain the user's configured values, including `civi2` |
| WLAN | Retain profiles and Wi-Fi credentials; the Ping sysctl is OS-wide |
| Radio | No radio control command is issued by LAN RESET |

The operation first restores a pending IPv4 trial. It then applies and saves automatic IPv4 settings, checks the saved fields, and enables Ping. NetworkManager checkpoints protect errors during the wired change. A successful local reset is persistent and does **not** require reconnection confirmation; it does not revert after 90 seconds. The resulting wired IP is shown. The previous fixed address, such as `192.168.73.2`, normally stops working. With no DHCP server, use the displayed 169.254 address and a compatible controller address, or use the retained WLAN management path.

Automatic mode explicitly uses an infinite DHCP transaction timeout (`2147483647`) while link-local fallback remains available. On this Pi, the default finite DHCP timeout otherwise caused activation failure and repeated reconnects despite an assigned AutoIP address. NetworkManager may display “connecting” while DHCP is pending; this does not by itself mean that the AutoIP address is unreachable. Static mode restores the default DHCP timeout value. The optional 30-second DHCP-timeout recommendation is not claimed by this implementation.

The Ping setting does not remove firewall rules. Auto-negotiation (an additional recommendation), full DHCP/DDNS behavior, reset while the cable is disconnected, and every LCI/LXI test condition remain outside the verified scope. User-configured hostnames/services are retained; collision-derived name persistence is not implemented yet.

## Web recovery credentials

On the first LAN RESET, a strong random recovery default is generated for this installation and stored in `.civi-lci-default.json` with mode 600. Subsequent resets reuse this default. It is displayed only in the local command's output. Do not post the password or commit these files.

The reset saves `.civi-lci.json` (credential plus revision) and enables discovery in `.civi-network.json`. A running updated CIVI reloads the credential and discovery settings and acknowledges completion in `.civi-lci-applied.json`. If CIVI is stopped, the values are loaded on its next manual launch. Startup states that local recovery credentials override the password environment variable; `start.sh` does not ask for an environment password in that state. Existing clients must authenticate again using the recovery password.

A missing runtime acknowledgement is reported explicitly, as is a failed live discovery update. The command does not report an unverified live change as successful. A local `.civi-lci-backup.json` records the prior wired snapshot and discovery settings for diagnosis; it is not an automatic full-system restore facility.

### Change the Web password after recovery

Open `/network#web-password`, enter the current recovery password and a new password twice, then click **Change password**. Passwords must contain 12–256 characters and no control characters. The new password takes effect immediately; other pages/clients must authenticate with it. CIVI and the LAN helper do not need restarting for this operation.

The new password is saved as a salted PBKDF2-SHA256 hash in `.civi-web-auth.json` (mode 600 on Linux). It overrides the startup environment password and the current LAN RESET password. LAN RESET creates a new reset revision, invalidating the custom credential and restoring the per-device recovery default. A later Web change is retained through restarts, including after a prior LAN RESET.

To intentionally return to environment-based authentication, stop CIVI, back up and remove `.civi-lci.json` and `.civi-web-auth.json` if present, then manually start CIVI with the desired password environment variable. Keep `.civi-lci-default.json` for future resets. This is local administration; do not expose credential files through a Web server.

## Standards mapping

Reference: [LXI Device Specification 1.6.2](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf), sections 2.4.5 (local mechanism and protection), 8.13 (reset state), 8.13.1 (auto-negotiation recommendation), 10.5.1 (discovery enable), and 10.7.1 (last user-configured hostname/service name). The attached-console design and confirmation prompt implement the local UI/protection approach; complete physical appliance and protocol compliance remain unverified.

## Helper connection errors (2026-11-11)

LAN RESET now states when it cannot connect to the CIVI LAN helper, before changes. Open the CIVI desktop shortcut, enter the Linux/sudo password if requested, keep the helper terminal open and run lan-reset.sh in a separate new terminal. Losing contact during initialization instead warns that completion is unverified and wired settings may already have changed. See [the boot/reset follow-up](RPI_DHCP_BOOT_2026-11-11.md).
