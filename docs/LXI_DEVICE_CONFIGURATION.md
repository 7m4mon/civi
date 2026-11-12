# CIVI Pi device configuration and operating boundary

This fixes the intended configuration for the LXI 1.6.2 review. It is not a
declaration of conformance, certification, or a trademark license.

## Device boundary

- Raspberry Pi 4 Model B Rev 1.4, onboard bcmgenet/BCM54213PE Ethernet, unmodified
  RJ45 connection; eth0 is the single interface in the intended LXI declaration.
- The attached front display and local keyboard/mouse or equivalent local input
  are supplied/retained parts of the device. LAN RESET must remain accessible
  locally without working Ethernet, WLAN, DNS, Web authentication or another PC.
- Displayed POWER ON, LAN Normal/Fault and Identify are part of the local panel.
  A running integrated display is the chosen front-panel power indication;
  connector link/activity LEDs do not substitute for the LAN status display.
  The user visually accepted the green POWER ON label and LAN state on the attached display on 2026-11-11.
- Desktop CIVI launches gateway, privileged helper and local panel manually.
  Keep all three running and the panel visible while operating the configuration
  as an LXI candidate. No automatic startup is introduced. A bare Pi/software
  installation without the local display/input is outside this device definition.
- IC-7300 is attached through stable-path USB CI-V; transmission stays disabled
  by default. WLAN is a separate management path, not a declared LXI interface.

Read-only inventory on 2026-11-11: Debian GNU/Linux 13 (trixie), release 13.7,
kernel 6.18.50+rpt-rpi-v8, NetworkManager 1.52.1, Python 3.13.5. This is the
tested deployment, not a claim covering arbitrary Windows/Linux images.
The official [Pi 4 hardware description](https://magazine.raspberrypi.com/articles/raspberry-pi-4-in-detail)
identifies the onboard Ethernet PHY; runtime inventory is recorded separately.

## Network and name policy

Automatic mode means DHCP with dynamically allocated link-local fallback; manual
mode uses saved IPv4 settings. NetworkManager owns address allocation, lease
renewal and initial conflict detection. The CIVI helper adds live conflict
monitoring and on-link reply routing for current AutoIP sources.

CIVI does not implement RFC2136 Dynamic DNS Update or expose a Dynamic DNS
enable/disable control. The mDNS switch controls Avahi/mDNS/DNS-SD only. Existing
NetworkManager DHCP hostname behavior and server-side DNS registration are not
advertised as a CIVI-controlled DDNS service. Consequently the conditional
DDNS-disable-default rule is not an applicable missing feature. DHCP-provided
hostnames do not replace the user/default mDNS hostname.

No LXI Extended Functions are declared: IPv6, LXI Security, full LXI API,
HiSLIP/VXI-11, synchronization, events and triggers are outside the declaration.
The identification GET subset referenced by the Device rules remains applicable;
HTTPS/password support does not claim the complete LXI Security extension.

## Readiness and HTTP meaning

The controlled LXI candidate is the gateway. Its own complete identification is
available with HTTP 200 while the radio is off, disconnected or recovering.
Radio state is reported separately. A known but unavailable child radio returns
503; an unidentified child returns 404. Gateway shutdown returns 503. This is a
synchronous GET implementation and does not use 202/PendingDetails.

## Hardware evidence boundary

1000 Mbps full duplex was previously verified. On 2026-11-11, temporary negotiated
100 Mbps full and half duplex each passed wired SCPI *IDN? and certificate-verified
HTTPS /lxi. The saved auto-negotiation profile was reactivated, and a subsequent
read confirmed 1000 Mbps full, auto-negotiation on, and 192.168.73.2/24. No saved
link setting, Windows interface setting or radio setting was changed.

An immediate post-reactivation check ran before link negotiation completed; the
subsequent read verified recovery. This is not a failed 100 Mbps functional test.
10 Mbps hardware modes are reported by ethtool but have not been functionally
accepted. Auto-MDIX remains Unknown in runtime output; no unverified PHY feature
or connector label is invented. The capability decision below records the
product-information basis and resolves the conditional label requirement for
the unmodified onboard Pi 4 configuration.

## Auto-MDIX evidence clarification

Device 7.4 recommends Auto-MDIX; 7.5 requires a physical label only when it is not supported. For the unmodified Pi Ethernet hardware, board/PHY capability documentation can establish applicability. No new CIVI implementation or independent all-cable-combinations test is prescribed by these clauses. The ethtool value Unknown is not evidence of missing hardware support. Remaining capability provenance is documentation review, not a newly required software feature or cable test.

## Auto-MDIX applicability decision

For the unmodified onboard Pi 4 Ethernet/BCM54213PE configuration, use the [BCM54213PE product information](https://www.mouser.com/pdfDocs/BroadcomBCM54213PERGMIIGigabitEthernetTransceiver.pdf), which specifies detection/correction of MDI crossover pair swaps, as the capability basis for Auto-MDIX. Device 7.5 applies only to hardware without Auto-MDIX; its special physical label is therefore not required for this configuration. Runtime ethtool Unknown remains an unreported status, not contrary capability evidence. This is a documentation-based capability decision, not a claim of new physical cable testing. Re-evaluate if a different NIC/PHY or modified board is used.
