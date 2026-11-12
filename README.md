# CIVI

**English** | [日本語](README.ja.md) · Author: **7M4MON**

CIVI turns an **Icom IC-7300 into a LAN-controlled instrument**: connect the radio by USB to Windows or a Raspberry Pi 4, then control it from SCPI/VISA, a local English web interface, a typed Python driver, or LabVIEW.

The gateway shares one serialized CI-V control service across TCP and HTTPS. The Raspberry Pi edition adds persistent wired LAN configuration, discovery, local recovery, LAN status and Identify on the attached display.

## Implemented capabilities

| Area | Delivered implementation |
|---|---|
| SCPI / VISA | TCP 5025, LF termination, abbreviations, units, compound commands, error queue, completion and receive-profile reset |
| Radio control | VFO/frequency/mode, gains, filters, meters, memory, band stacks, keyer storage, scans, scope, menus and permission-gated operations |
| Python instrument driver | **All 339 extended CIVI command definitions mapped to dedicated typed APIs**, plus base commands; 43 public/returned types and 352 indexed constructors/members/fields |
| Web | HTTPS, authenticated operation/settings, command explorer, 475-point scope, connection recovery and persistent password management |
| Pi LAN | DHCP/AutoIP/static IPv4, hostname and DNS settings, save/confirm/rollback, duplicate-address protection, mDNS/DNS-SD and Ping controls |
| Local operation | POWER ON, LAN NORMAL/FAULT, flashing Identify, LAN RESET, password recovery and a manual desktop launcher |
| LabVIEW | VISA session API and examples for reads, frequency/mode changes, and frequency sweeps with CSV export |

**Implementation and completed-test evidence are ready for registration review.** IVI registration and formal LXI/IVI conformance are not claimed. The feature totals describe CIVI's documented command catalog, not every possible radio function.

## Completed tests and results

| Test campaign | Recorded result |
|---|---|
| Publication regression | **619 passed, one Linux-only skip**; driver strict typing and six documentation consistency checks passed |
| Typed driver core and receiver, MAIN 1.41 | 40 core/receive checks, 65 receiver-setting checks and **all 216 menu reads** passed |
| VFO API, MAIN 1.42 | 57 checks passed: both views, frequency bounds, eight modes, DATA/filter settings, swap and restoration |
| Memory record write/read/clear, MAIN 1.42 | 24 checks passed using empty memory 99; original empty state restored |
| Selected-memory operations and VFO copy, MAIN 1.42 | 29 selected-memory checks and 23 copy checks passed; original states restored |
| Band-stack and keyer writes, MAIN 1.42 | 33 band-stack slots and eight keyer texts written/read/restored; 89 checks passed |
| Scope API, MAIN 1.42 | 72 checks passed; complete **475-point sweep**, 52 fixed-edge reads and 14 controls restored |
| Scan operations/settings, MAIN 1.42 | All seven start enums exercised in eight runs; all seven ΔF widths and ALL/★1/★2/★3 selection exercised |
| TX Inhibit, MAIN 1.42 | True/False readback and invalid-type checks passed; original setting restored |
| Pi wired LAN | DHCP acquisition/renewal/expiry/reacquisition, static save/reboot, AutoIP access, LAN RESET and cable recovery verified |
| Discovery and local panel | Physical name collisions, reboot name retention, reconnection probes/advertisements, LAN Fault and Identify verified |
| Web / identification | XML/schema, authentication boundaries, stale-value removal and confirmation expiry checks passed; Windows and phone Chrome displays confirmed |

[**Requirements → implementation → test procedure → result and evidence**](docs/IMPLEMENTATION_AND_TEST_RESULTS.md) provides the review table and dated records. Counts belong to individual campaigns and are not added into a unique-test total. Physical setting tests use read/change/readback/restore where applicable; automated tests use simulated radios and fake serial ports.

## Drivers and review material

- [Python driver installation and examples](drivers/civi-ic7300/README.md) · [public API reference](drivers/civi-ic7300/src/civi_ic7300/REFERENCE.md)
- [Complete 339-command typed API mapping](docs/PYTHON_DRIVER_COVERAGE.md) · [base commands and unified inventory](docs/PYTHON_SCPI_AUDIT.md)
- [LabVIEW project, VISA settings and examples](labview/CIVI/README.md)
- [Completed implementation/test results](docs/IMPLEMENTATION_AND_TEST_RESULTS.md) · [full clause-by-clause LXI audit](docs/LXI_REQUIREMENTS_2026-11-10.md)

![CIVI Identify on the Raspberry Pi display with an IC-7300](civi-identify.jpg)

## Run on Windows

Install Python 3.11 or later, then run these commands in PowerShell from this repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
Copy-Item config.example.toml config.toml
.\.venv\Scripts\python.exe -m civi --make-cert certs --host 192.168.1.20
.\start.cmd
```

Replace `192.168.1.20` with the LAN IP address or DNS name clients will use. `localhost` is included automatically. This generates a self-signed certificate without overwriting an existing certificate. Verify and trust the certificate on each client, or configure a trusted CA certificate and key in `config.toml`. Keep the private key private.

- Web: `https://localhost:8443`
- SCPI: `localhost:5025`
- Web username: `admin`
- Web password: saved Web credentials, or the environment variable specified by `password_env` on first use; at least 12 characters

For subsequent launches, run `.\start.cmd` from PowerShell or `start.cmd` from Command Prompt. On first use, it prompts for the web password without displaying it and saves a Windows DPAPI-encrypted credential in `.civi-password.xml` (ignored by Git). Only the same Windows account on the same computer can decrypt it. Later launches reuse it and supply the configured password environment variable to CIVI. The `-ResetPassword` launcher option replaces that DPAPI credential; a password subsequently saved through the Web takes precedence over the environment value. The launcher runs in the foreground; Ctrl+C stops it. No automatic startup is configured. Direct `python -m civi` launches use saved Web credentials when available, otherwise the password environment variable is required.

The example configuration uses a **simulated radio**, so no hardware is needed to try CIVI. Passwords are not stored in the source or configuration file.

`bind = "0.0.0.0"` accepts connections from localhost and the LAN. Allow TCP 5025/8443 from the required clients in Windows Firewall, and UDP 5353 for discovery. Use `127.0.0.1` for localhost-only access. SCPI uses plaintext TCP without authentication; the web password does not protect the SCPI port. Restrict SCPI access to the intended LAN clients.

## Raspberry Pi desktop launcher

Run `bash desktop.sh --install` from the Pi checkout as the normal desktop user to create a **CIVI** desktop icon. Double-click it to start the LAN helper, CIVI and panel in order; existing components are reused. Enter the Linux/sudo password in the helper terminal if asked. No automatic startup is configured. See [desktop launch and shutdown](docs/RPI_DESKTOP.md).

## Raspberry Pi Web passwords and recovery

The examples below assume this branch is checked out at `~/civi-rpi-lxi`; adjust the directory for your installation.

### First start and normal password changes

```bash
cd ~/civi-rpi-lxi
bash start.sh
```

On first start, when no saved Web credential or password environment variable exists, enter a Web password at the hidden prompt. The username is **admin**. Environment-based passwords must be supplied again on later starts unless retained in the launching shell.

To save a password, open **LAN information / discovery settings → Change Web password** (`/network#web-password`). Enter the current password and the new password twice (12–256 characters). The change takes effect immediately and is saved as a salted hash in `.civi-web-auth.json`. Subsequent Pi launches reuse it without asking for another password. Re-enter the new password on other open Web pages. See [Web password management](docs/WEB_PASSWORD.md).

### Forgotten password: retain the LAN settings

Use the Pi's **attached keyboard/display terminal**, as the normal CIVI user:

```bash
cd ~/civi-rpi-lxi
bash password-reset.sh
```

Type **PASSWORD RESET**, then enter a new password twice. Input is hidden; the old password is not required. This command needs neither sudo nor the LAN helper. It changes only Web authentication, retaining IP, hostname, discovery and the device recovery default.

Updated running CIVI reloads the password within about five seconds. If CIVI is stopped, start it with `bash start.sh`; the saved password is used without a second prompt. When installing the code update that adds this feature, restart CIVI once to enable live reload. The helper and Pi do not need restarting for a password-only reset.

### LAN RESET: recover network access as well

For network recovery, use `bash lan-reset.sh` from the attached console with the [LAN helper](docs/RPI_LAN_SETTINGS.md) running, then type **LAN RESET**. This switches wired IPv4 to DHCP with AutoIP fallback, enables Ping/discovery, and restores the device's recovery Web password displayed locally. **The previous fixed IP stops working; a successful local reset has no 90-second automatic reversion.** WLAN profiles and the user-configured hostname/service name are retained.

After LAN RESET, authenticate with the displayed recovery password, then use **Change Web password** to choose and save your own again. See [LAN RESET scope and limitations](docs/RPI_LAN_RESET.md).

## Pi LAN status and Identify

Pi discovery uses Avahi to handle hostname/service collisions and saves acquired names for later launches. Install the Pi dependency with `.venv/bin/python -m pip install -e '.[pi]'`; keep Avahi running and restart the updated LAN helper and CIVI. The required Python dependency has been installed on the development Pi. See [collision handling and remaining limitations](docs/DISCOVERY_NAMES.md).

<img src="civi-identify.jpg" alt="CIVI Identify running on the attached Raspberry Pi display above an IC-7300" width="560">

The attached display and Identify operation were confirmed by the user on 2026-11-07. The photo shows hostname `civi2`, wired IPv4 `192.168.73.2`, and the connected IC-7300. See the [verification record](docs/RPI_PANEL_2026-11-07.md).

After starting the updated CIVI, open another terminal on the Pi desktop:

```bash
cd ~/civi-rpi-lxi
bash panel.sh
```

Keep this window visible on the attached monitor. It shows wired LAN status and addresses; the LAN connector LEDs keep their normal hardware function. Open `/lxi` or `/network`, enter the current Web password under **LAN status / Identify**, and use **Start Identify** / **Stop Identify**. Identify flashes continuously until stopped. Starting without a visible local panel is rejected. The panel and CIVI are started manually; no service or GPIO setup is added. See [display behavior and verification limits](docs/RPI_PANEL.md).

## Connect an IC-7300

1. Install Icom's USB driver and find the COM port in Device Manager.
2. Put the radio in VFO mode. Match the CI-V address and USB baud rate in `config.toml`. The example uses **94h (decimal 148)** and **115200 baud**. For scope data, set the radio's **CI-V USB Port** to **Unlink from [REMOTE]** and **CI-V USB Baud Rate** to **115200**. Close other CAT applications using the port.
3. Check the USB SEND and USB keying settings, and set **USB SEND to OFF**. CIVI opens the serial port with DTR/RTS deasserted, but electrical transitions during driver changes have not been verified.
4. Set `backend = "civ"` and the actual serial port, such as `port = "COM25"` under `[serial]`, then start CIVI. Background polling updates the connection status and radio readings.
5. Start with frequency/mode queries, the S-meter, and receive frequency changes. Transmit control is disabled by default.

CIVI uses direct CI-V; it does not use Hamlib as its control backend. Model profiles define commands, modes, frequency ranges, and features. The IC-7300 profile conservatively allows 30 kHz–60 MHz reception; region-specific 70 MHz extensions are not enabled. CI-V 03/05 access the displayed frequency.

The extended catalog includes VFO selection, DATA/filter control, gains and meters, RIT/XIT, memories, CW/voice-memory playback, power, menus, and scope controls. **USB audio streaming over the network is not implemented.**

## Identification and connection status

`*IDN?` returns the gateway identity together with the identified radio model, for example:

```text
CIVI Project,CIVI/IC-7300,CIVI-0001,0.1.0
```

The model component is `Unknown` when the radio is disconnected or its model ID is unrecognized. The final field is the **CIVI software version**. Radio firmware is shown separately as **Radio firmware** in the web interface and through `RAD:FIRM?`. Firmware is not read automatically: it remains `Unknown` unless manually supplied as the top-level `radio_firmware` value in `config.toml`.

The web interface remains available when the radio is not connected and shows **Waiting for radio** before login. CIVI retries an unavailable serial port approximately every two seconds.

If the port opens but a CI-V response times out, CIVI quarantines the connection to prevent a delayed reply from being mistaken for a later response. The web interface shows **Radio not ready — recovery required**. Check power, USB, and CI-V settings, reset the radio and USB link, then sign in and use **CI-V connection settings → confirmation checkbox → Recover connection**. Connection settings and the SCPI console remain accessible while the radio is unavailable.

`ERR_CONNECTION_REFUSED` means the browser cannot reach the web server. CIVI cannot serve a waiting page after its own process exits. Keep the launching PowerShell window open and check for **Web is ready** or startup errors. Restart CIVI and reload the browser after updating the code.

## Extended commands

In addition to the basic commands, CIVI provides **339 extended command definitions**, including **216 menu items**. The web **Radio command explorer** shows examples for every definition and runs them through the same queue as SCPI clients. See the [command inventory](docs/COMMANDS.md) for CI-V mappings, arguments, and write permissions.

```text
RAD:AFGAIN 128;AFGAIN?
READ:SWR?
RAD:VFO:FREQ OTHER,14.074MHz;FREQ? OTHER
RAD:RIT:FREQ -1200;FREQ?
RAD:MENU:0094?
```

Persistent menu changes, memory writes/erasure, power, communication settings, and calibration writes require the corresponding permission under `[permissions]` in `config.toml`. Existing configurations are not automatically granted those permissions. Queries remain available.

CW output, voice-memory playback, VOX, break-in, and tuner operations that can cause transmission also use the transmit-enable gate, client ownership, and maximum transmit duration. Software cannot guarantee TX stop after a USB or power loss. See the [architecture and transmit-control documentation](docs/ARCHITECTURE.md).

The web S-meter shows an approximate S reading alongside the original raw value, such as **≈ S7 (raw 96)**. It uses an IC-7300 approximation table, does not compensate for preamp/attenuator settings, and does not convert to dBm. `READ:SMET?` continues to return the uncalibrated raw integer.

### Spectrum scope

Scope data requires the IC-7300 USB CI-V connection at **115200 baud**, with the USB port **unlinked from [REMOTE]**. In the web interface, use **Start scope** to enable both waveform transfer and scope operation. **Stop scope** disables transfer. **Refresh scope** only displays received data; it does not start transfer.

For SCPI operation, enable both settings:

```text
RAD:SCOPE:STREAM 0,ON
RAD:SCOPE:ENABLE 0,ON
RAD:SCOPE:WAVE?
```

Allow a complete sweep to arrive before querying it. The web interface displays a spectrum and waterfall history. Scope packets are separated from ordinary command replies; incomplete sweeps and data older than five seconds are not returned as current readings. Scope levels are uncalibrated raw values.

### CI-V communication logs

The direct CI-V backend logs TX frames and complete received RX frames in hexadecimal to stdout and the authenticated web communication log. Echoes, ACK/NAK responses, unsolicited notifications, and frames addressed to other devices are included. TX is logged after a successful serial write; the radio response determines whether the command succeeded. This is a frame log, not a capture of every fragmented or noise byte. The simulated backend does not generate physical serial frames.

```text
INFO civi.wire: CI-V TX: FE FE 94 E0 27 11 01 FD
INFO civi.wire: CI-V RX: FE FE E0 94 FB FD
```

Under `[serial]`, `trace_frames = true` enables logging by default. Continuous scope frames (27 00) are sampled once every two seconds with a packet count; reception and plotting still process the full data stream. Set `trace_scope_frames = true` to log every scope frame, or `trace_frames = false` to disable frame logging. Restart CIVI to apply these settings. The web log retains the latest 200 entries; CIVI does not automatically save it to a file.

## Validation and documentation

[Completed test results](docs/IMPLEMENTATION_AND_TEST_RESULTS.md) links each implementation area to its procedure and dated evidence. Firmware, hardware and simulation contexts are retained in the underlying reports.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Automated tests use simulated backends and fake serial ports. Physical acceptance tools are separate and require an explicitly prepared instrument.

- [SCPI commands and VISA examples](docs/SCPI.md)
- [Full command inventory and argument examples](docs/COMMANDS.md)
- [Architecture, communication failures and transmit control](docs/ARCHITECTURE.md)
- [Pi HTTPS 443 setup](docs/RPI_HTTPS.md) · [wired LAN helper](docs/RPI_LAN_SETTINGS.md)
- [Validation history](docs/VALIDATION.md) · [device configuration](docs/LXI_DEVICE_CONFIGURATION.md)

For manual experiments on Raspberry Pi, after preparing `.venv`, `config.toml`, and TLS certificates, run:

```bash
bash ~/civi/start.sh
```

The script uses the existing configuration and saved Web credentials when available. It prompts only when neither saved credentials nor the password environment variable is available. Keep the terminal open and press Ctrl+C to stop. It does not install a service or enable automatic startup. See [Web passwords and recovery](#raspberry-pi-web-passwords-and-recovery) for password changes and [porting work](docs/PORTING.md) for installation and remaining validation.

## References

- [Official IC-7300 CI-V supplement](https://www.icom.co.jp/support/manual/2557/): implementation reference, December 2023 edition, printed pages 2–15.
- [Icom America IC-7300 manuals and USB SEND guidance](https://icomamericasupport.zendesk.com/hc/en-us/articles/35050809291668-IC7300-Instruction-Manuals-and-FAQs).

The vendor reference PDF is not redistributed with CIVI.
