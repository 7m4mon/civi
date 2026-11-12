# CIVI IC-7300 Python driver

Version 0.13.1 · Author 7M4MON · Python 3.11+ · standard-library runtime.

Control the CIVI/IC-7300 gateway over TCP using dedicated typed APIs for all 339 extended command definitions and the base commands. Collections cover 101 memories, 33 band-stack slots, eight keyer texts and 216 menus.

- [API reference](src/civi_ic7300/REFERENCE.md) / [usage](src/civi_ic7300/API.md)
- [Completed results](src/civi_ic7300/EVIDENCE.md) / [command inventory](src/civi_ic7300/SCPI_COVERAGE.md)

Install from the repository root with Python 3.11 or newer:

```console
python -m pip install ./drivers/civi-ic7300
```

No VISA runtime or third-party Python runtime dependency is needed. The client
accepts VISA network resource names and connects using raw TCP; it does not implement
VXI-11, HiSLIP, logical names, IPv6 literals, GPIB or USB resources. Board/device fields do not change the raw TCP transport; explicit SOCKET ports are retained.

```python
from civi_ic7300 import CiviIc7300

with CiviIc7300("TCPIP::192.168.73.2::5025::SOCKET") as device:
    print(device.ivi_utility.instrument_model)
    print(device.radio.frequency_hz, device.radio.mode, device.radio.smeter_raw)
```

Construction checks `*IDN?` by default. Start CIVI and prepare/recover the radio
before connecting. `id_query=False` skips identity verification, but hardware
queries can still fail if the radio is unavailable. The initial timeout is five
seconds. A transport timeout/disconnection closes the session; explicitly open
a new instance after fixing the connection. This prevents reusing a timed-out
session with a late reply. Radio recovery remains CIVI's existing explicit
procedure, not a side effect of constructing this client.

For offline operation, simulation opens no sockets:

```python
with CiviIc7300("TCPIP::unused::5025::SOCKET",
                options={"simulate": True}) as device:
    device.radio.frequency_hz = 14000000
    device.radio.mode = "USB"
    print(device.radio.frequency_hz)
```

Hardware setting example (changes the selected VFO):

```python
with CiviIc7300("TCPIP::192.168.73.2::5025::SOCKET",
                options={"query_instrument_status": True}) as device:
    old_frequency = device.radio.frequency_hz
    try:
        device.radio.frequency_hz = 14000000
        assert device.radio.frequency_hz == 14000000
    finally:
        device.radio.frequency_hz = old_frequency
```

Automatic status checking defaults to false, as specified by IVI Core. Enable
it to raise gateway errors after ordinary typed scalar operations.
All typed APIs follow the option; use checked() for an explicit checked block.
See [the STATUS guide](src/civi_ic7300/STATUS.md) for OFF behavior and migration. Explicit `error_query()` /
`raise_on_device_error()` work regardless of the setting. Raw I/O never adds
status queries because doing so would consume user-managed responses.

The PTT property remains read-only; operations.start_transmit()/stop_transmit()
provide explicit guarded actions ([guide](src/civi_ic7300/BASIC.md)). Direct I/O can send any SCPI command supported
by CIVI; CIVI's transmit authorization and timeout rules still apply. Automated
driver tests never transmit. S-meter values are raw 0–255, not dBm.

API, installation/build instructions, limitations and source information are in
the packaged [introduction](src/civi_ic7300/Introduction.md),
[API help](src/civi_ic7300/API.md), and
[compliance report](src/civi_ic7300/COMPLIANCE.md).
Support/source: [7m4mon/civi](https://github.com/7m4mon/civi).

For a complete offline controls example, see the API help. The current catalog
mapping is 339 of 339 extended definitions in all catalog directions, zero
partial mappings and zero pending. Raw I/O alone does not complete typed coverage.


[API naming/layout review](src/civi_ic7300/STYLE.md) records 0.13.1 changes.

<!-- BEGIN GENERATED COMPLIANCE -->

# Compliance status — client 0.13.1

## Compliance Category

**Not IVI-conformant; not registered.** Target specifications: IVI Generation 2026, Driver Core 1.0 and Driver Python 1.0. Verification and registration are tracked in the [completion plan](https://github.com/7m4mon/civi/blob/main/docs/IVI_6_1_COMPLETION_2026-11-12.md).

## Driver Identification

- **Driver Version:** 0.13.1, initial pre-release.
- **Driver Vendor:** 7M4MON (nomulabo identity proposal: NAMING.md).
- **Driver Bitness:** 64-bit Python process.
- **Source Code:** Included; build and distribution instructions are in Introduction.md and project metadata.
- **Identifier:** CiviIc7300; distribution/import: civi-ic7300 / civi_ic7300.

## Hardware Information

- **Instrument Manufacturer:** CIVI Project.
- **Supported Instrument Models:** CIVI/IC-7300.
- **Supported Bus Interfaces:** IPv4/hostname TCP SOCKET, LF ASCII, default 5025.

The gateway controls the USB CI-V radio. Gateway identity and physical Icom identity are separate.

## Software Prerequisites

- **Supported Operating Systems:** Verification environment: Windows11 (25H2, build26200.9711), x64.
- **Driver Dependencies:** Python>=3.11, standard library only; recorded runtime CPython3.14.5 x64.
- Build frontend: setuptools>=68 and `build`. VISA and IVI Shared Components are not used.

## Unit Testing

### Test Setup

| Item | Recorded environment |
|---|---|
| Instrument Model (Firmware Version) | CIVI/IC-7300 gateway 0.1.0; IC-7300 MAIN 1.41 and MAIN 1.42, with campaign scope in EVIDENCE.md |
| Bus Interface | Windows TCP SOCKET → Pi gateway → USB CI-V |
| Operating System | Windows11 (25H2, build26200.9711) |
| Driver Bitness | 64-bit CPython3.14.5 |
| Simulation | Independent logical simulator and loopback TCP gateway MockBackend |

Recorded full repository regression:619 passed, one Linux-only skip. Physical campaign results and restoration conditions are summarized in EVIDENCE.md. Automated tests use simulated radios/fake serial ports.

## Driver Installation Testing

- **Operating System:** Windows11 (25H2), Python 3.14.5 x64.
- Clean wheel installation, isolated simulation, packaged help/type-marker checks and recorded physical read-only smoke succeeded.

## Driver Buildability

- **Operating System:** Windows11 (25H2), Python 3.14.5 x64.
- Source→sdist→wheel and clean installation succeeded. Rebuild instructions: Introduction.md.

## Driver Test Failures

- **Known Issues:** No failing test in the recorded automated run. API mode/firmware conditions and hardware quantization are documented in API.md.

## Additional Compliance Information

[The completion plan](https://github.com/7m4mon/civi/blob/main/docs/IVI_6_1_COMPLETION_2026-11-12.md) records the final release verification criteria and external procedures. Its execution ledgers distinguish current evidence from the final complete test setup.

<!-- END GENERATED COMPLIANCE -->
