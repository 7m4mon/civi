# IPv4 Ping responder control

The Pi `/network` page now provides **IPv4 Ping responder**, with **Read Ping setting**, **Enable IPv4 Ping replies** and **Save Ping setting**. Enter the current CIVI Web password in the Pi LAN section, read the actual state, then change/save it. Restart the updated helper and CIVI and reload the Web page after installing this change. No Pi reboot is needed to apply a setting.

This controls IPv4 echo replies on **all Pi interfaces**, including WLAN. It does not disable HTTPS, SSH or SCPI, change IP addresses, or alter IPv6 Ping. An IPv6 reply from `ping civi.local` is therefore not evidence that IPv4 disabling failed; use `ping -4` with a numeric address when testing.

The fixed helper operations are `ping_status` (no arguments) and `ping` with a Boolean `enabled`. No caller-selected sysctl key or file path is accepted. Web requests retain current authentication, same-origin and CSRF checks. The operation is independent of wired connection/profile availability.

The helper saves the desired value in `/etc/sysctl.d/90-civi-lan.conf`, applies `/proc/sys/net/ipv4/icmp_echo_ignore_all` and reads back runtime and saved state. `enabled` reports actual runtime state; `saved_enabled` reports the CIVI-owned saved value or null if none exists. Saving verifies both. A failure attempts to restore the exact previous file/runtime value; unverified restoration is an explicit error. A later administrator sysctl override can supersede the saved value, so the UI distinguishes observed from saved settings.

The saved file is applied by normal OS sysctl processing at boot, without needing CIVI to run. LAN RESET enables and saves replies again, via the same verified setter. CIVI and its helper remain manually started. This addresses core rules 8.2–8.4; exposing the control on the Web follows recommendation 9.5.3. It is not a full LXI conformance claim.

## Verification — 2026-11-07

- Full suite: **257 passed, one skipped**. Tests cover runtime/saved status, default recovery enable, reload from saved settings, invalid types/fields, authentication/CSRF, helper errors, and exact restoration after a failed runtime write. Existing LCI transaction tests also passed.
- A separate real root helper used `/run/civi-ping-test/control.sock`; a mock-backend HTTPS fixture on 18446 ran as ordinary user `nom`. The production application/helper were left running.
- From the Windows PC, authenticated HTTPS POST disabled IPv4 Ping; authenticated GET confirmed runtime and saved values were false. Fresh IPv4 echo probes to both `192.168.73.2` and `192.168.4.54` received no replies.
- During the disabled interval, production HTTPS on 443 through both addresses and TCP SCPI on 5025 remained available. `*IDN?` succeeded. No radio setting or transmit command was issued.
- Authenticated HTTPS POST re-enabled replies; both interfaces answered fresh probes again. TLS certificate/hostname verification stayed enabled, using the certificate-covered `civi.local` server name while connecting by numerical IP.
- The test supervisor stopped its fixture/helper and restored the exact original runtime setting and saved sysctl file. Production IPs, names, credentials and radio settings were unchanged.

The user subsequently confirmed production-page operation with actual Ping probes, then disabled both Ping and mDNS and rebooted the Pi. The user observed no Ping replies after reboot. Read-only inspection of that boot confirmed `icmp_echo_ignore_all=1`, so disabled runtime state survived restart. The user then re-enabled both controls; fresh IPv4 Ping replies from both wired and WLAN addresses were independently confirmed. Final state is enabled. The wire test deliberately avoided a full LAN RESET, which would also reset the Web password and wired IP configuration.
