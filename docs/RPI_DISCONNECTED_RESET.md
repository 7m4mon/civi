# LAN RESET with no active wired connection

The Pi helper can read the intended saved profile and perform local LAN RESET even when the Ethernet cable is unplugged. It does not guess from profile names or pick an arbitrary inactive connection.

## Establish the recovery target

Start the updated helper once while the intended wired profile is active:

```bash
cd ~/civi-rpi-lxi
sudo python3 -m civi.pi.broker --owner nom --interface eth0
```

It validates the active profile, logs its UUID and saves a root-owned `/var/lib/civi/lan-eth0.json` (mode 600). Later starts reuse this UUID, including when disconnected. The target survives helper/Pi restarts independently of CIVI's user-owned settings. An active profile different from the saved UUID is an error, not permission to change a different network.

For first setup when already disconnected, explicitly select the known wired profile UUID:

```bash
sudo python3 -m civi.pi.broker --owner nom --interface eth0 --profile-uuid YOUR_WIRED_PROFILE_UUID
```

Only an Ethernet profile is accepted. Interface-name or MAC bindings to a different device are rejected. A deliberately unbound Ethernet profile is accepted only through the remembered or explicitly selected UUID. Profile selection cannot be changed through the Web/helper protocol. To intentionally switch profiles, stop the helper and start it with the new explicit UUID when that profile is active or the device is disconnected.

## Local reset

From the Pi's attached desktop terminal, as the normal user:

```bash
cd ~/civi-rpi-lxi
bash lan-reset.sh
```

Confirm **LAN RESET**. The existing password/reset behavior applies. With no active wired connection, the helper persists DHCP + AutoIP fallback, clears static IPv4/gateway/DNS settings, enables profile and device autoconnect, and enables Ping and Avahi. It verifies the saved values before reporting completion. The display explicitly says to reconnect the cable and that no IP address is ready yet.

No temporary device reapply/checkpoint or Web confirmation is needed for this local reset of an inactive profile. When the link is absent, it does not wait for a nonexistent IP or activate another connection. Reconnecting permits NetworkManager to activate the selected profile automatically. If carrier is already present but the selected profile is inactive, the helper requests asynchronous activation of that UUID on the selected interface. Saved configuration completion is distinct from address readiness.

Failure attempts to restore the old saved IPv4/profile-autoconnect fields, device autoconnect, Ping and mDNS. A failed restoration is reported explicitly for local inspection. WLAN, hostnames, radio settings and unrelated profiles are not changed. The ordinary active-profile path retains its existing checkpoint-based behavior.

`Read wired LAN` also works against the saved target when disconnected. Temporary Web apply still requires an active connection; the local reset is the offline recovery mechanism. The user must keep the attached display/keyboard and manually started helper available for the defined appliance configuration.

## Verification

Tests cover target persistence and interface isolation, wrong active UUID, wrong NIC/MAC/type, blank bindings with explicit selection, offline save without activation/checkpoints, carrier-present asynchronous activation, rejecting temporary Web changes while inactive and restoration after a failure. Full suite at this stage: 253 passed, one skipped.

Physical test on 2026-11-07: used the Pi's actual wired profile and WLAN SSH path. Saved the original profile/Ping/mDNS state, provisioned the root-owned target, and asked the user to unplug the cable. With carrier absent and no active connection, the updated privileged transaction code saved and verified DHCP+AutoIP and autoconnect without a checkpoint or IP readiness claim. The user reconnected the cable; without any connection-up command from the test, NetworkManager acquired `169.254.108.9/16`. The test then restored the exact original saved profile, device autoconnect, Ping and mDNS, activated the original configuration, and verified `192.168.73.2/24` was back. WLAN and production credentials were retained. A root-only profile backup is in the ignored Pi `tmp/offline-reset-before.json`.

This tests the real network-reset backend, with the root-owned target on disk. It deliberately did not invoke the full `lan-reset.sh` credential-reset flow or restart the user's running helper/application. The existing local CLI confirmation/password workflow is covered by its previous tests. The updated helper must be manually restarted to use this behavior in the normal UI/CLI. A Pi reboot while unplugged and a profile-deleted or different-device recovery scenario were not exercised; missing/mismatched targets fail explicitly.

Subsequent verification: the [full local LAN RESET and physical unplugged reboot test](RPI_LCI_BOOT_2026-11-08.md) on 2026-11-08 includes credential reset/startup, persisted DHCP/AutoIP settings, AutoIP acquisition after cable reinsertion and verified restoration of the original fixed IP. DHCP-server-present boot cases remain separate.
