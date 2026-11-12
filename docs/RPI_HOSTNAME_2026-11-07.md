# Pi hostname save verification

Verified on the existing Pi 4 / Debian 13.7 / NetworkManager 1.52.1 development installation on 2026-11-07.

- Read the starting static, running and `/etc/hostname` values: `civi`.
- Checked that the running LAN helper had no pending IPv4 transaction.
- Used the new hostname backend to save `civi-hostname-test`.
- Read back the saved hostname through NetworkManager, `/etc/hostname`, and the running kernel hostname; all matched.
- Verified that the wired connection UUID, saved IPv4 profile and active IPv4 address were unchanged.
- Restored `civi` in a finally block and verified the same three hostname values and wired settings again. Final wired address: `192.168.73.2/24`.

The existing manually started CIVI application and LAN helper were left running. This test invoked the new backend in a separate privileged process after checking the existing helper's pending state. It did not exercise the running helper's new operation, because that process still needs a manual restart to load the update.

Automated verification: 192 pytest tests passed on Windows, including valid/invalid hostname handling, pending IPv4 refusal, failed-save restoration, explicit recovery failures, Web authentication/CSRF/transmission guards and re-advertising a changed mDNS SRV target. JavaScript syntax validation passed. No radio transmission or automatic startup was used.

## Follow-up with the running application

The user saved `civi2` through the Web page and supplied the success screen. After manually rebooting the Pi, the user checked `hostname` and `/etc/hostname`; both returned `civi2`.

After the application was manually started again, the Windows client received all three queried service types (`_lxi._tcp`, `_scpi-raw._tcp`, `_https._tcp`) with SRV target `civi2.local.` and addresses `192.168.73.2` and `192.168.4.54`. Ports were 8443 for LXI/HTTPS and 5025 for raw SCPI. LXI/SCPI TXT records identified CIVI/IC-7300.

Windows system name resolution returned the Pi's addresses. A first SCPI attempt was refused; a subsequent check succeeded through both numerical addresses and `civi2.local`, returning `CIVI Project,CIVI/IC-7300,CIVI-0001,0.1.0` with LF termination. HTTPS TCP port 8443 was reachable through all three names/addresses. This port check does not validate the TLS certificate for the renamed host. Hostname collision handling and full LXI discovery conformance remain unverified.

The hostname operation uses NetworkManager's persistent system hostname API: [nmcli general hostname](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nmcli.html). The change is saved immediately and is not covered by the IPv4 checkpoint deadline. Hostname collision resolution, DHCP/DNS server updates and TLS certificate regeneration are outside this change.
