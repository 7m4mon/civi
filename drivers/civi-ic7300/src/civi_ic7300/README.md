# CIVI IC-7300 Python driver

Version 0.13.1 · Author 7M4MON · Python 3.11+ · standard-library runtime.

```python
from civi_ic7300 import CiviIc7300

with CiviIc7300("TCPIP::192.168.73.2::5025::SOCKET") as device:
    print(device.radio.frequency_hz, device.radio.mode, device.radio.smeter_raw)
```

Use `options={"simulate": True}` for offline operation and `options={"query_instrument_status": True}` for automatic typed-operation error checks. Default timeout is5 seconds; ID query is ON, simulation/status checks are OFF. `reset=True` applies the receive baseline in Reset.md.

| Guide | Content |
|---|---|
| Introduction.md | Install, build, examples and support |
| REFERENCE.md / API.md | Public signatures, types, values and contracts |
| CONTROLS.md / MENUS.md | Receiver, scope and menu mapping |
| STORAGE.md / HIERARCHY.md | Memories, keyers and band-stack collections |
| SCAN.md / BANDS.md / OPERATIONS.md | Scan, band records and guarded operations |
| EVIDENCE.md | Completed verification results |
| COMPLIANCE.md | Distribution and verification metadata |

Source and support: https://github.com/7m4mon/civi.

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
