# LAN RESET verification — 2026-11-07

## Automated tests

201 pytest tests passed on Windows. New checks cover explicit cancellation without mutations, reuse of the per-device recovery default, refusal of remote CLI invocation, no HTTP reset endpoint, invalid credentials, restoration on Ping failure, resetting a pending IPv4 change, and live authentication reload rejecting the previous password. Existing Windows, SCPI, Web, CI-V and Pi tests remain passing.

## Pi network backend

Used the running Pi 4 through its WLAN management path, after checking that the existing LAN helper had no pending change. The test invoked the new backend directly in a dedicated privileged process; it did not stop the existing application or helper and did not access the radio.

1. Captured the wired profile/UUID, active IPv4, hostname, active network profile list, Ping runtime value and CIVI Ping persistence file.
2. Executed the local reset backend: saved IPv4 method `auto`, link-local mode `4` (fallback), active address `169.254.108.9/16`, hostname `civi2` retained.
3. Restored and confirmed the original static IPv4 settings in a finally block.
4. Read back the exact original profile, UUID, hostname and active IPv4 `192.168.73.2/24`.
5. Restored and checked the prior Ping runtime/file state and unchanged active profile list, including WLAN.

The test did not leave the Pi on automatic IPv4. It did not reset the production application's Web password or discovery configuration.

## Pi runtime reload with mock radio

Started a separate normal-user CIVI instance with mock radio and TX disabled, separate random TCP ports, separate credentials/configuration files and a unique test discovery instance. The fixture simulated the helper's verified reset result; the real network reset was tested separately above.

- Used verified TLS with a dedicated locally trusted test certificate, including hostname verification.
- Verified old authentication worked before resetting.
- Invoked the local reset orchestration with confirmation supplied by the test harness.
- Verified the running monitor acknowledged the reset.
- Verified the old password was rejected with 401 and the recovery password accepted with 200.
- Verified the Web network page reported discovery active after it had initially been disabled.
- Stopped the temporary mock instance and its advertisements. Its test credentials remain in ignored `tmp`, not in tracked files.

The attached-keyboard prompt itself, reset with a disconnected/disabled wired profile, DHCP-server lease behavior, firewall effects, reboot persistence of a completed LCI, and full LXI conformance remain unverified. No actual transmission, system reboot, automatic startup or production password reset was performed.

## Subsequent user operation and finite DHCP timeout defect

The user subsequently executed LAN RESET from the local console. The Windows client received the production advertisement with addresses `169.254.108.9` and `192.168.4.54`, and verified SCPI through WLAN and `civi2.local`. The former fixed address was no longer reachable. The recovery password authenticated successfully against the localhost LAN API.

Later, the user reported intermittent “Interface must have exactly one active NetworkManager profile” failures. The Pi journal showed that the connection failed with `ip-config-unavailable` after the default 45-second DHCP wait and was retried, despite a link-local address having appeared. The earlier immediate-address tests did not cover this sustained behavior and were insufficient to establish stable AutoIP operation.

Automatic-mode plans now explicitly keep the DHCP transaction running with `ipv4.dhcp-timeout=2147483647`; static-mode plans restore `0`. The setting was applied to the production wired profile without changing its AutoIP address, hostname, Web password or WLAN profile. Snapshot reads also consult the selected device's own connection UUID when the active-list query transiently omits it; no saved profile is guessed. Automated regression tests, including that transition case, passed: 202 tests total. See [NetworkManager's DHCP timeout definition](https://www.networkmanager.dev/docs/api/latest/settings-ipv4.html).

After the correction, seven reads spanning 60 seconds all returned `169.254.108.9/16`, crossing the previous 45-second timeout without losing the profile. NetworkManager remained in its DHCP “connecting” state while the link-local address stayed configured. Longer-duration operation and DHCP-server transitions remain to be tested.
