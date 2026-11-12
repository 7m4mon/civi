# Discovery collision verification — 2026-11-07

This is the historical 2026-11-07 record. Hostname collision and daemon-restart acceptance was subsequently completed in [isolated Pi namespaces on 2026-11-08](MDNS_HOSTNAME_2026-11-08.md); physical-interface and actual Pi reboot checks remain.

## Implementation coverage

Unit tests cover desired/acquired name separation, UTF-8 suffix limits, reuse after restart, resetting the acquired-name generation after LCI, an Avahi group collision, its synchronous `CollisionError`, bounded helper hostname restoration and retrying the user's desired hostname when a saved acquired hostname conflicts again. Windows common functionality retains zeroconf.

## Real Pi / external PC test

Used the Pi's existing Avahi daemon and installed `dbus-next` 0.2.3 in the development virtual environment. No service or automatic startup was added.

Created only uniquely prefixed test service groups (`CIVI collision test …`), separate temporary state files and test ports. The test intentionally bypassed global hostname restoration, retaining the existing Avahi hostname and production configuration.

1. Registered a blocking group under the desired instance name.
2. Verified CIVI registered all four services under one common `… (2)` name.
3. Closed and recreated the CIVI discovery object, then verified it reused the persisted `… (2)` name.
4. Added a second blocker under that acquired instance and verified the next CIVI instance selected `… (3)` without compound suffixes.
5. Resolved the LXI service through Avahi and checked its actual host and port.
6. Queried `_lxi._tcp` from the separate Windows PC with Python zeroconf. Received the desired blocker, `(2)` blocker and CIVI `(3)` advertisements, their expected ports, shared claimed hostname and `CIVI/Mock` TXT identity.
7. Freed all temporary groups and disconnected their D-Bus clients.

The actual Avahi hostname at the time was `civi2-2.local.`; the test did not change it, the kernel hostname, IP settings, radio or production credentials. The example/test service names were withdrawn after the check. The README photo was replaced with the user's latest MAC-redacted file.

Physical two-host hostname collision injection, restoring an acquired hostname after a Pi reboot, daemon restart behavior and device-wide mDNS disabling remain unverified or incomplete. The hostname restoration paths were verified with mock D-Bus responses, not by renaming the production daemon during this test. See [scope and limitations](DISCOVERY_NAMES.md).
