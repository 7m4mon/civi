# Web failure / reconfiguration states — 2026-11-10

G08 follow-up to [the Web/API review](WEB_API_REVIEW_2026-11-10.md).
No LXI conformity or certification is claimed. This work uses mock radio and LAN
responses; production wired addressing, authentication and radio settings are not
changed, and no transmission is started.

## Fixes

- A status read that reports a disconnected, connecting or quarantined radio no
  longer repaints old cached frequency/mode/PTT/S-meter values after clearing them.
  The display keeps those readings unknown until a connected status is available.
- Scope plots/waterfall history are cleared when the radio becomes unavailable.
  Radio-specific explorer and scope actions are disabled as well as frequency,
  mode and TX start. The SCPI console, serial settings, connection recovery and
  stop-TX action remain available. Connected status restores controls subject to
  their original permissions; disabled transmit configuration stays disabled.
- An authenticated polling failure distinguishes a reachable gateway with
  unavailable radio status from a network-unreachable gateway. Unknown readings
  are hidden instead of retaining the preceding successful display.
- A failed LAN-status poll no longer leaves the previous panel/Identify
  acknowledgement visible. The lamp and panel/Identify status become unknown
  until a successful poll restores current information.
- The LAN trial countdown disables confirmation/rollback buttons on expiry.
  Failed helper status reads also disable them until a successful status read.
  Existing backend token, deadline and changed-address checks remain authoritative.
- Restoration is described as verified only when the helper reports that result.
  An unverified restoration explicitly asks the user to inspect the Pi locally.
  Connection loss while applying retains the new-address link and time-limit
  guidance; it does not fabricate a token or claim confirmation.

## Automated transition checks

`tests/test_web_state_transitions.py` executes the shipped app.js, indicator.js
and network.js in Node's VM with a small DOM/network/timer fixture. These are
actual script execution checks, not screenshots or full browser-engine tests.

| Scenario | Expected result |
|---|---|
| Connected → disconnected/connecting/quarantined → connected | Old readings disappear, radio actions disable, fresh readings/control permissions return |
| Gateway health fetch fails | Gateway unavailable message; unknown readings |
| Health succeeds, authenticated status returns 503 | Radio status unavailable message; unknown readings |
| Identify acknowledged → LAN poll fails → normal poll succeeds | Unknown panel status during failure; current normal/Identify-off state on recovery |
| LAN trial pending → deadline passes | New-address guidance retained; expired confirmation disabled |
| Pending trial → helper unavailable → readable again | Confirmation disabled while status is unavailable; helper result shown on recovery |
| Restoration unverified / verified rollback / confirmed save | Distinct messages; no unverified success claim |
| Apply request loses its connection | Reconnection guidance remains; no automatic confirmation request |
| LAN fault/no IPv4 with pending trial or stopped helper | Welcome/LAN and gateway identification remain available; authenticated helper failure is JSON 409, parent identity is schema-valid XML 200 |

Windows full suite: **542 passed, 1 Linux-only skip**, 39.81 seconds. All seven
new JavaScript cases ran successfully. The eighth new case exercised the HTTP
server with a fake helper, a fault-state indicator and an unaddressed eth0.

Pi isolated-copy related suite: **42 passed, 8 Node-only skips**, 35.01 seconds,
under tmp/web-states-20261110-231624. Node is absent on this Pi; the eight skipped
cases are the seven new script cases plus the preceding subnet-display case.
They passed on Windows. Existing test dependencies were reused outside the Pi
runtime environment. No physical LAN failure was induced by these tests.

## Deployment and limits

Only static Web scripts require deployment for these behavior changes. Reloading
the browser loads them through the existing no-store responses; gateway, helper
and panel do not require a restart. The deployment checks below distinguish live
asset delivery from the mock transition checks.

Windows and smartphone Chrome normal display checks reported earlier remain
recorded in the preceding review. Actual browser display/interaction of these
failure paths is not inferred from that normal-state report. Physical DHCP,
duplicate-IP, boot and name-resolution cases stay in G05/G06. Device-wide
normal-operation interpretation in the final product configuration remains open.

Production Pi follow-up: the three scripts were deployed with backups under
tmp/deploy-web-states-20261110-121841. Certificate-verified HTTPS GETs from Windows
returned each script byte-for-byte identical to the updated local source, with
no-store headers. Gateway health reported online/radio connected; identification
returned 200; LAN was Normal, Identify OFF, and the attached panel acknowledged.
Configuration, saved Web credentials and saved network settings were unchanged.
No application restart or additional physical fault test was performed.

## User follow-up: reconnect session

The user reported that reconnection shows “Your session expired. Sign in again.”
This is accepted as the recovery flow: an expired Web operation session requires
a new sign-in rather than automatic reuse. This report does not by itself verify
successful sign-in afterward or every failure/reconfiguration scenario above.

## User-confirmed failure displays

The user explicitly confirmed both of the following on the deployed application:

- Old received values disappear after disconnection.
- LAN confirmation is disabled on expiry or when status cannot be obtained.

The reconnection session-expiry prompt is accepted as documented above. Browser/OS
versions and subsequent sign-in success were not specified. These confirmations
cover these two behaviors; other physical network lifecycle cases remain open.
