# IVI driver: receive/core physical acceptance — 2026-11-11

This is scoped evidence for experimental client **0.13.1**, not completion of the
IVI Core unit-test procedure or a conformance claim. The tests called the actual
Python driver API from the Windows checkout over TCP SOCKET to the Pi gateway;
they were not a raw-SCPI-only test and did not test a newly installed wheel.

## Setup and safeguards

- Gateway CIVI 0.1.0 / physical IC-7300; the owner read MAIN firmware **1.41** from
  the radio display. This is manually supplied evidence, not a CI-V firmware query.
- Pi wired 192.168.73.2 / TCP5025, Windows client, CPython 3.14.5 x64.
- CIVI/helper/panel were started manually. Before writes, PTT, VOX, break-in and
  tuner were all verified OFF. Mutation allowlists reject other command headers.
- Original selected VFO: **927000 Hz, AM, DATA OFF, FIL2**. Other VFO:
  **14100000 Hz, USB, DATA OFF, FIL2**. Snapshots were written before changes.
- No PTT, VOX, break-in, tuner, memory, menu, calibration, power or permission
  writes occurred. AF/audio volume was not tested at maximum. No RF was transmitted.

## Completed checks

| Group | Simulation | Physical IC-7300 |
|---|---|---|
| Core/receive procedure | 39 checks | 40 checks; extra real parser error injection |
| Receiver enum/range/rejection procedure | 65 checks | 65 checks across 16 properties |
| Read-only descriptor/menu inventory | 292 reads | 290 successful; 2 NAK contexts explained below |
| Final state comparison | Baseline restored | Both VFOs and saved LSB settings restored; 66 non-meter read results unchanged, including 2 expected NAK results |

These are check counts, not counts of IVI clauses or distinct public entry points.
The [worklist](IVI_VERIFICATION_WORKLIST_2026-11-11.csv) now maps evidence to 110
API entries, preserving getter-only, setter and unavailable-feature distinctions.

Core checks included whole-Hz frequency 30000 / 14000000 / 60000000 set/readback,
local rejection below/above the supported range and of invalid types as
specified by the procedure, all eight mode set/readbacks, invalid mode rejection,
identity/utility metadata, local timeout values, completion, empty/error queues,
DeviceError, Direct I/O string and byte write/read pairs. One deliberately unknown
SCPI header generated -113 on the real gateway without radio I/O. The logical
simulator does not implement arbitrary raw headers; that injection was not
reported as a simulation success. Direct I/O pairs were completed before typed I/O.

The 16 receive-setting properties were preamp, AGC, filter shape, attenuation,
RIT offset/enabled, NB/NR, automatic/manual notch, notch width, RF gain, squelch,
NR level and inner/outer PBT. Tests ran at **7.100 MHz LSB**, used enum choices,
numeric endpoints/midpoints and invalid samples as listed in the tool, and
restored each property. This is not coverage of every property in the driver.

All **216 menu selectors** read successfully. Menu writes were not performed.
Readback of transmit meters while receiving is protocol verification only, not
RF-meter calibration or evidence of transmission.

## Mode and firmware dependencies

- Filter shape (CI-V 16 56) NAKed in AM at both 927 kHz and 14 MHz. It read
  correctly in USB, CW and 7.100 MHz LSB. Both SHARP/SOFT setters were verified
  in LSB and restored. The AM NAK is not replaced by a fabricated value.
- TX Inhibit (CI-V 16 66) NAKed in AM/USB/CW/LSB on this MAIN 1.41 unit.
  The official [IC-7300 1.42 update information](https://www.icomamerica.com/uploads/support/firmware_driver/IC-7300_ENG_FirmUpInfo_0.pdf)
  documents introduction of that command in **1.42**. This feature is unavailable
  on the tested firmware; no successful get/set or OFF state is claimed.
  No firmware update or TX-inhibit write was attempted.

## Quantization observations

| Raw setting | Requested codes | Actual stable readbacks |
|---|---|---|
| NR level | 0 / 128 / 255 | 8 / 136 / 248 |
| Inner PBT | 0 / 128 / 255 | 2 / 128 / 253 |
| Outer PBT | 0 / 128 / 255 | 2 / 128 / 253 |

Initial exact-echo assumptions stopped the procedure at NR, then PBT. Every stop
restored settings and VFOs. Those initial failed-assumption artifacts are kept.
The final procedure explicitly checks bounded, nondecreasing and stable/idempotent
device levels for these three controls; it does not assert arbitrary equality or
infer physical dB/Hz calibration. The simulation remains a logical model and
does not reproduce all hardware quantization. All discrete quantization intervals
have not been exhaustively swept; full IVI coercion verification remains scoped.

## Reproduction and records

Opt-in tools, never launched by startup or pytest:

```sh
python tools/ivi_receive_acceptance.py --simulate --write-receive --output tmp/ivi-sim.json
python tools/ivi_receive_acceptance.py --write-receive --output tmp/ivi-physical.json
python tools/ivi_readonly_acceptance.py --menus --output tmp/ivi-reads.json
python tools/ivi_receiver_settings_acceptance.py --write-receive --output tmp/ivi-settings.json
```

Run from the checkout and verify the target radio is safe and idle. These tools
use the source client with no gateway imports in the client package. They record
wire programs, results and original states; source hashes are retained in the
core/read reports. Private artifacts are below `tmp/ivi-receive-20261111`.
Do not rerun destructive or transmit operations by extrapolating from this scope.

Remaining Core/Python work includes other writable properties/methods, applicable
value/coercion ranges and repeated capabilities, release/semantic review and
formal naming/registration. Existing dated evidence can be reused when its code
and setup match; this report does not supersede all earlier hardware records.

## Clean installation follow-up

The updated documentation was built into an sdist and a wheel built from that sdist. Artifact checks passed for 40 packaged files, metadata, embedded compliance and notice integrity. A new virtual environment installed the wheel offline with no dependencies. Python isolated mode imported that installed copy, and all 12 Python source hashes matched the bulk physical-test source. Installed-driver read-only calls returned CIVI/IC-7300, 927000 Hz, AM, PTT OFF and an empty error queue. This is an installation/transport smoke check; the full bulk procedure was source-based. Related driver/help/release regression tests: 26 passed.

## MAIN 1.42 follow-up

The owner subsequently updated MAIN to 1.42. The [focused TX Inhibit test](IVI_TX_INHIBIT_2026-11-11.md) passed get/set/readbacks, invalid types and restoration. The preceding 1.41 measurements retain that firmware scope.
