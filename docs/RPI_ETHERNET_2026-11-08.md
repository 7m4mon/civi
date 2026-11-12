# Wired Ethernet auto-negotiation — 2026-11-08

## Finding and change

The Pi's saved NetworkManager profile reported `802-3-ethernet.auto-negotiate=no`, `speed=0` and an unset duplex. This combination means NetworkManager leaves link configuration alone; it does **not** establish that the NIC's auto-negotiation is disabled. This behavior is documented in the [NetworkManager wired settings](https://www.networkmanager.dev/docs/api/latest/settings-802-3-ethernet.html). The observed runtime setting was already on.

The existing wired profile was explicitly provisioned as:

```text
802-3-ethernet.auto-negotiate = yes
802-3-ethernet.speed = 0
802-3-ethernet.duplex = (unset)
```

This requests unrestricted auto-negotiation rather than a forced 1000 Mb/s mode. The runtime advertised modes included all reported supported 10/100/1000 modes. Both endpoints advertised auto-negotiation, and the resulting link was **1000 Mb/s, full duplex**. The earlier 100 Mb/s observation remains historical evidence of that earlier connection, not the current speed.

Only the selected wired profile UUID was modified and reactivated. Its static `192.168.73.2/24`, IPv4 settings and autoconnect settings were retained. The management route to the Windows WLAN address remained via `wlan0`, source `192.168.4.54`; its active UUID and IPv4 were unchanged. CIVI, the helper and panel remained running.

## Verification

- Runtime: `ethtool eth0` showed auto-negotiation on, advertised auto-negotiation Yes, 1000 Mb/s, Full, link detected yes.
- Persistence: the saved Netplan YAML contained `ethernet.auto-negotiate: "true"`. After `nmcli connection reload`, the profile still read yes / 0 / unset.
- Reactivation: the selected wired profile was activated a second time, then the same runtime link settings were confirmed.
- Gateway: the duplicate-IP guard remained running without fault/error. LAN status returned Normal with the local display connected/acknowledged.
- External wired client: Windows explicitly used source `192.168.73.1` to Pi `192.168.73.2`. HTTPS 443 passed certificate trust and `civi.local` name validation. SCPI returned IC-7300 identity, 774000 Hz, AM and `0,"No error"`. No radio setting/transmit command was sent.

The provisioning baseline and result are under ignored root-only `/home/nom/civi-rpi-lxi/tmp/ethernet-20261108-173229-625780`. The external protocol check is under local ignored `tmp/ethernet-wired-20261108.json`. No application code changed, so the existing automated result remains **271 passed, 1 skipped**; it is not presented as a new automated Ethernet test run.

## Reproduce on another Pi deployment

Read-only audit, as root for complete ethtool output:

```bash
cd ~/civi-rpi-lxi
sudo python3 tools/pi_ethernet_check.py
```

To explicitly provision the selected active wired profile with a separate active management NIC:

```bash
sudo python3 tools/pi_ethernet_check.py --interface eth0 --management-interface wlan0 --apply-auto
```

This manual step stores a baseline, creates a NetworkManager checkpoint, changes only the three wired link settings above, reactivates that profile and verifies runtime/save/IP/management state before confirming. Errors trigger checkpoint rollback plus explicit restoration of the original wired link settings. Do not change network settings concurrently or run this provisioning tool in parallel. Its failure recovery uses the existing checkpoint implementation; an additional forced-failure injection test of this new wrapper was not performed.

The script is not run automatically by CIVI, the helper, an installer or a service. It is a deployment configuration step; ordinary Web IPv4 changes retain these link settings. A deliberate OS-level override remains possible with nmcli, as described by NetworkManager. LAN RESET currently retains these link settings rather than forcing auto-negotiation back on after an external override.

## Remaining hardware/LXI scope

[LXI Device Specification 1.6.2](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf) section 7.6 covers default auto-negotiation; 7.6.1 recommends an override and 8.13.1 recommends restoring auto-negotiation through LCI. This configuration check is not a declaration of full LXI conformity.

The Pi reported driver `bcmgenet` and PHY driver `Broadcom BCM54213PE`, PHY ID `0x600d84a2`. `ethtool` reported **MDI-X: Unknown**, so this run does not establish Auto-MDIX support or non-support. Auto-MDIX/physical-label requirements in sections 7.4/7.5 remain separate. The initial provisioning run did not include a reboot; the physical reboot follow-up below completes that check. Every slower-link mode and all cable combinations remain separate. The [previous unplugged boot test](RPI_UNPLUGGED_BOOT_2026-11-08.md) preceded this explicit profile change.

## Follow-up: physical Pi reboot

The user rebooted the Pi with the wired cable connected and radio powered on, then manually started the desktop launcher. Read-only checks confirmed the saved profile still contained auto-negotiate=yes, speed=0 and duplex unset. Runtime auto-negotiation remained on, all supported modes were advertised, and ethtool plus kernel sysfs confirmed 1000 Mb/s and full duplex.

The static address remained `192.168.73.2/24`; the WLAN management route still used `wlan0`/`192.168.4.54`. Helper, CIVI and panel were running, the duplicate-IP guard had no fault/error, and the panel was connected/acknowledged with LAN Normal. From Windows source `192.168.73.1`, trusted/name-verified HTTPS `/lxi` and `/lan-status` returned 200, and SCPI read IC-7300 identity, 774000 Hz, AM and no error. The external report is in local ignored `tmp/ethernet-reboot-20261108.json`. No settings were changed during this follow-up, and no automatic startup was configured.
