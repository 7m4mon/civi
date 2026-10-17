# CIVI

**English** | [日本語](README.ja.md)

Author: **7M4MON**

CIVI is a Python SCPI-to-Icom CI-V network gateway. It connects an Icom radio to VISA clients and an English web interface through a shared control service and a single serialized USB connection.

The initial radio is the **IC-7300**. Development currently targets **Windows**, with **Raspberry Pi OS 64-bit** planned as the deployment platform. The current version is **0.1.0**. CIVI is **not LXI certified**.

## Run on Windows

Install Python 3.11 or later, then run these commands in PowerShell from this repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
Copy-Item config.example.toml config.toml
$env:CIVI_PASSWORD = 'replace-with-your-own-long-password'
.\.venv\Scripts\python.exe -m civi --make-cert certs --host 192.168.1.20
.\.venv\Scripts\python.exe -m civi --config config.toml
```

Replace `192.168.1.20` with the LAN IP address or DNS name clients will use. `localhost` is included automatically. This generates a self-signed certificate without overwriting an existing certificate. Verify and trust the certificate on each client, or configure a trusted CA certificate and key in `config.toml`. Keep the private key private.

- Web: `https://localhost:8443`
- SCPI: `localhost:5025`
- Web username: `admin`
- Web password: the environment variable specified by `password_env`; at least 12 characters

The example configuration uses a **simulated radio**, so no hardware is needed to try CIVI. Passwords are not stored in the source or configuration file.

`bind = "0.0.0.0"` accepts connections from localhost and the LAN. Allow TCP 5025/8443 from the required clients in Windows Firewall, and UDP 5353 for discovery. Use `127.0.0.1` for localhost-only access. SCPI uses plaintext TCP without authentication; the web password does not protect the SCPI port. Restrict SCPI access to the intended LAN clients.

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

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Automated tests use the simulated backend and fake serial ports only. They do not operate or transmit through a physical radio.

Physical IC-7300 checks on **2026-10-17** covered five basic and 303 extended queries: **307 succeeded**, while `RAD:TXINHIBIT?` returned a NAK. Additional change/readback/restore checks covered 233 setting targets, including 189 ordinary menu items. A complete 475-point scope sweep and VFO copy/swap operations were also verified. These results do not establish support for every value, mode, channel, or write operation.

Actual transmission, calibration changes, end-to-end TCP/HTTPS operation with the physical radio, Linux operation, and LXI certification remain unverified. See the [hardware validation report](docs/HARDWARE_2026-10-17.md) for tested directions, parameters, limitations, and excluded operations. Some supporting documents are currently in Japanese.

- [SCPI commands and VISA examples](docs/SCPI.md)
- [Full command inventory and argument examples](docs/COMMANDS.md)
- [Architecture, communication failures, and transmit control](docs/ARCHITECTURE.md)
- [LXI requirements matrix](docs/LXI.md)
- [Validation history and acceptance procedure](docs/VALIDATION.md)
- [IC-7300 hardware validation and untested operations](docs/HARDWARE_2026-10-17.md)
- [Raspberry Pi porting plan](docs/PORTING.md)

Raspberry Pi installation instructions and systemd service configuration are deferred to the porting phase.

## References

- [Official IC-7300 CI-V supplement](https://www.icom.co.jp/support/manual/2557/): implementation reference, December 2023 edition, printed pages 2–15.
- [Icom America IC-7300 manuals and USB SEND guidance](https://icomamericasupport.zendesk.com/hc/en-us/articles/35050809291668-IC7300-Instruction-Manuals-and-FAQs).

The vendor reference PDF is not redistributed with CIVI.
