# Local LAN status and Identify display

2026-11-10 correction: Fault/unknown status cancels Identify and takes priority on both local and Web indicators. Starting Identify requires normal LAN status; after recovery, start it explicitly again. Restart CIVI and panel to load this correction.

The Pi branch provides a manually opened graphical LAN status panel for the Pi's attached monitor. The RJ45 connector LEDs retain their hardware link/activity function; CIVI does not reconfigure them. No GPIO, service installation or automatic startup is added. The screen is the device's LAN/Identify indication for this development configuration, so keep the attached monitor powered and the panel visible.

For one desktop icon that starts the helper, CIVI and this panel together, see [the manual desktop launcher](RPI_DESKTOP.md).

## Start

Restart CIVI once after installing this update. The LAN helper can stay running. With `[pi_network] enabled = true`, CIVI monitors the configured wired interface (`interface = "eth0"` by default) and opens a user-private local panel socket.

In another terminal on the Pi desktop, as the normal CIVI user:

```bash
cd ~/civi-rpi-lxi
bash panel.sh
```

The panel needs Tk (`python3-tk`), which was already available on the tested Pi. It does not need sudo, the LAN helper or a Web password. F11 toggles fullscreen; Esc leaves fullscreen. Closing the window stops only the display.

Closing its launching terminal can also stop the panel. To keep it running after closing that terminal, launch it manually from the Pi desktop with `nohup bash panel.sh > /tmp/civi-panel.log 2>&1 < /dev/null &`. This does not enable automatic startup. Close the panel window to stop it.

After changing the hostname during an existing desktop session, Xauthority may still contain the old hostname. The panel reuses that session's existing cookie through a private temporary authority file when opening its display connection; it does not change the desktop's authentication file or disable access controls. If `couldn't connect to display` persists, run it as the desktop user from the Pi's graphical terminal (without sudo). Logging out of the Pi desktop and logging back in also recreates the graphical session; a full Pi reboot is generally unnecessary.

## Display and Web controls

- Normal: steady green LAN banner, wired IP, hostname, MAC and radio connection shown separately.
- Fault: red LAN banner with the observed reason, such as cable/no-carrier, no usable IPv4, a reported duplicate address, or loss of a previously observed DHCP address.
- Unknown/stale observations: amber indication. A stopped/unreachable CIVI is displayed as CIVI OFFLINE rather than a healthy instrument.
- Identify: green flashing banner until **Stop Identify** is requested. Existing fault text remains visible during Identify.

Open `/lxi` or `/network` and use **LAN status / Identify**. Enter the current CIVI Web password and select **Start Identify** or **Stop Identify**. Starting is rejected if no visible local panel has recently reported in. A later panel acknowledgement is displayed separately. The panel's own **Stop Identify** button also stops the indication. The Identify request remains active if the browser disconnects; closing/hiding the panel is reported as unavailable rather than as a successful visible indication.

The Web page polls the public read-only `/lan-status` resource. Changes use authenticated, same-origin protected `POST /api/identify`. The local display uses `.civi-panel.sock` (mode 600, owned by the CIVI user), not a LAN connection, so cable/address changes do not disconnect its transport. None of these operations issue CI-V commands or change LAN settings.

## Display-state interpretation

Monitoring targets the selected wired NIC. A working WLAN management path does not hide an Ethernet fault. Initial DHCP absence with a usable AutoIP address is normal. Loss of a DHCP address observed while CIVI is running is latched as a fault even if AutoIP subsequently becomes available; a new observed lease, link reinitialization, profile/method change, LAN RESET or CIVI restart clears the appropriate state.

Duplicate-address indication uses NetworkManager's reported reason 64 and the updated helper's [receive-only ARP guard](RPI_CONFLICT.md). The guard disconnects a conflicting active wired address and retains the fault; an unavailable/stale guard prevents a healthy LAN from being reported as Normal. Static/AutoIP conflict rejection, DHCP DECLINE and active static/AutoIP disconnection have been tested in isolated Pi namespaces. DHCP lease expiry/renewal is covered by the separate [DHCP test](DHCP_2026-11-08.md); LAN normal indicates link and usable local IPv4, not verified end-to-end reachability. The GUI can report whether its window is mapped, but cannot prove the physical monitor is powered, uncovered, or awake.

The graphical display approach is based on [LXI Device Specification 1.6.2](https://public.lxistandard.org/specifications/LXI_1.6_Specifications/LXI_Device_Specification_1.6.2_2026-04-02.pdf), sections 2.5.2, 8.10 and 9.3. NetworkManager reason values are documented in its [D-Bus types](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nm-dbus-types.html).
