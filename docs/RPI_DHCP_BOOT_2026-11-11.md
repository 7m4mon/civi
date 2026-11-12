# DHCP persistence / boot / LAN RESET — 2026-11-11

This is a continuation of the [physical eth0 DHCP tests](RPI_DHCP_ETHERNET_2026-11-10.md).
It does not declare LXI conformity. Tests in progress are not recorded as passes.

## Preparation

Pi 4 is managed over WLAN 192.168.4.54. The original wired profile is static
192.168.73.2/24. Its UUID/settings and CIVI configuration/authentication hashes
were recorded before changes. Private copies of config, saved Web authentication,
network settings and existing LAN-recovery files are retained on the Pi in
tmp/dhcp-boot-backup-20261111-063756 (directory mode 700, files 600). No plaintext
passwords or real MACs are included in this document.

Windows uses wired 192.168.73.1, interface index 4. The same opt-in, single-client,
explicit-NIC DHCP fixture serves 192.168.73.3 with a 120-second lease. No gateway
or DNS options are supplied on the direct cable, preserving the WLAN's normal
management/internet route. No PC network/firewall changes or automatic CIVI startup
were introduced. The test server has a 30-minute maximum runtime per launch.

The helper/CIVI/panel were initially stopped; the user started all three. PTT OFF
was read before IPv4 changes. A 180-second checkpoint protected the DHCP trial.
Certificate-verified HTTPS identification succeeded on 192.168.73.3 before the
helper confirmed and saved automatic mode. Readback showed saved ipv4.method=auto,
no manual address and no pending checkpoint. CIVI config, saved Web authentication
and saved discovery settings hashes remained unchanged. This confirms the save
operation; restart persistence was verified in the separate boot check below.

## Current test status

| Case | Status |
|---|---|
| DHCP acquired and confirmed/saved | Passed, including HTTPS through the new wired address |
| DHCP acquisition after Pi reboot | Passed: boot ID changed, saved auto mode and 192.168.73.3/24, fresh post-boot ACKs, HTTPS and LAN Normal |
| LAN RESET while already on DHCP | Completed; recovery/discovery reload and DHCP renewal confirmed; fresh acquisition not inferred |
| LAN RESET from the original static profile | Passed: new initial DHCP ACK, 192.168.73.3/24, saved auto mode, live reset/recovery reload, LAN Normal |
| Final restoration of original static profile | Passed: 192.168.73.2/24; original saved profile matched; HTTPS and LAN Normal |

LAN RESET must be performed at the Pi's attached console. It changes the Web
password to the per-device recovery default displayed there. That expected
authentication change will be recorded separately from the earlier unchanged-hash
check; it is not silently undone. The user should keep the displayed recovery
password. DHCP mode was intentional during the reboot test; final saved mode is static.

Private Windows artifacts are below tmp/dhcp-boot-20261111. The old boot ID,
prechange snapshot and successful save record allow the next connection to be
distinguished from an application-only restart.

## Confirmed reboot observation

The user rebooted the entire Pi and manually started CIVI/helper/panel. The new
boot ID differed from the prechange ID. Saved automatic mode remained active,
and the Windows fixture recorded two DHCP ACKs after this boot. Wired HTTPS
reported LAN Normal, Identify OFF, and the local panel connected/acknowledged.
This confirms an OS reboot, rather than only a CIVI process restart. The subsequent
local LAN RESET cases are recorded below.

## Local RESET prerequisite

The first local LAN RESET attempt reported helper unavailable. Inspection found
all three application components stopped on the same verified Pi boot. DHCP
mode and the acquired address remained active; the reset failed at its initial
helper status request, before any initialization or password change. The user was
asked to relaunch CIVI, retain the helper terminal, and use a separate new terminal
for lan-reset.sh. This prerequisite failure is not recorded as a RESET pass.

## RESET test interpretation and message improvement

The successful first RESET was performed while DHCP was already active. The
helper reapplication preserves an existing valid lease when settings already
match; the live reset revision and recovery/discovery reload were confirmed, as
were subsequent renewal ACKs. The first verifier incorrectly demanded a new
initial ACK for that idempotent case. That expectation was not used to classify
a device failure. The original static profile was then restored and matched
exactly, and a second local RESET was requested to verify new acquisition from
static mode explicitly.

The user also requested clearer errors. The CLI now reports that it cannot
connect to the CIVI LAN helper and that LAN RESET has not started. It explains
that no LAN/password changes were made, how to launch CIVI, and that the helper
terminal must remain open while RESET runs in a separate terminal. A transport
failure during initialize has a different message: completion is unverified and
wired settings may already have changed. Genuine helper operation errors are not
mislabelled as missing-helper errors. No reset/authentication policy changed.

Four new regression cases cover that distinction. Windows full suite: 584 passed,
one Linux-only skip (40.50 seconds). Pi related suite: 24 passed (2.58 seconds).
The CLI/client update was deployed with backups, requiring no app/helper restart.

## Final static-to-RESET result and cleanup

The user kept helper running and executed LAN RESET from a separate attached
console terminal after the original static profile had been restored. The reset
revision changed, live recovery/discovery reload acknowledged that revision with
no error, and Windows recorded one new initial/reacquisition DHCP ACK since the
static baseline. Saved mode was auto and wired IPv4 was 192.168.73.3/24. Wired
HTTPS reported LAN Normal, Identify OFF and a connected/acknowledged panel.

The original static configuration was then applied, verified through wired HTTPS
and confirmed. The saved profile matched the original UUID/settings and address
192.168.73.2/24. LAN returned to Normal. The PC test server was stopped and its
UDP67 port was verified free. CIVI/helper/panel remain running; no automatic
startup, firewall policy or WLAN profile changes were introduced. No transmit
start or frequency/mode-setting command was sent; PTT OFF was checked before
network changes.

Finally, the recovery password was used **inside the Pi only** to authenticate a
certificate-verified local HTTPS GET of the protected wired-settings endpoint.
It returned 200 with the restored static settings. Neither password nor Basic
header was returned to the agent, printed or added to these test artifacts.
CIVI config.toml remained unchanged. Authentication is intentionally the LAN RESET
recovery default now; the earlier operator password was not silently restored.
The user should sign in as admin with the password last displayed by LAN RESET.

This closes the scoped saved-DHCP/reboot and static-to-LAN-RESET DHCP acquisition
checks. It is not a complete DHCP/RFC or LXI verdict. Physical link reconnection,
remaining duplicate-IP/option cases and final product/registration decisions
remain tracked in the requirement inventory.
