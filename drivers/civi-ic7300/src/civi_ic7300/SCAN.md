# Scan and tone APIs (client 0.10.0)

`device.scan: ScanControl` is a read-only interface reference. All methods return
None after command completion and error checks; there is no scan-state query.
Completion means the gateway/radio accepted the instruction, not that a scan
has finished or that signals have been found.

| Method | Arguments / effect |
|---|---|
| `start(mode: str)` | PROGRAM, MEMORY, AUTO, DELTA, FINEPROGRAM, FINEDELTA, SELECTMEM; case insensitive |
| `stop()` | Stop scan |
| `set_delta_span_hz(span_hz: int)` | Half-span: center ± 5000, 10000, 20000, 50000, 100000, 500000, 1000000 Hz; not receive-filter bandwidth |
| `set_select_enabled(enabled: bool)` | SELECTOFF / SELECTON |
| `set_resume_enabled(enabled: bool)` | RESUMEOFF / RESUMEON |
| `assign_selected_memory_group(group: int)` | Assign select group 1..3 to the radio's current memory |
| `set_memory_group(group: int)` | Set memory scan group code 0..3 |

These map to all 21 existing gateway scan definitions. Prerequisites such as
VFO/memory mode, programmed scan edges and populated memories remain the radio's
responsibility. No automatic context switch, retry or remembered scan status is
provided. Settings/selection are shared with other clients and local controls.
Assignment operates on the radio's current memory selection and may change
stored selection metadata. It follows the existing gateway command, which has
no memory permission gate; this API does not introduce a new permission policy.

Inputs are validated before I/O. Scan methods hold the session lock and
follow the status option. With checks ON, preexisting errors abort and result
errors raise DeviceError. With checks OFF, command errors stay queued. Use
checked() for explicit checks. Transport failures close the session, leaving
execution uncertain. There is no readback or automatic restoration of unknown
scan configuration. Explicitly call stop() when finished; another client can
start a new scan later. This is not a global radio lock.

```python
from civi_ic7300 import CiviIc7300

with CiviIc7300(
    "TCPIP::unused::5025::SOCKET",
    options={"simulate": True, "query_instrument_status": True},
) as d:
    try:
        d.scan.set_delta_span_hz(10000)
        d.scan.set_resume_enabled(True)
        d.scan.start("DELTA")
        print(d.meters.smeter_raw)
    finally:
        d.scan.stop()
```

Offline simulation accepts these commands and records their logical values.
It does not move frequency, search signals, time scan/resume, or apply scan
group assignment to stored memory payloads. Receive reset stops the modeled scan
and resets its logical scan options. Mock TCP verifies command bytes and errors,
not physical scan behavior. Neither model establishes hardware persistence.

## Tone frequencies

`radio.repeater_tone_hz: float` and `radio.tone_squelch_hz: float` are read/write
frequencies in Hz, 67.0..254.1 in exact 0.1 Hz increments. Setting a frequency
does not enable the tone; use the existing `tone_enabled` / `tone_squelch_enabled`
properties separately. Tone scalars follow the existing automatic status option;
use `query_instrument_status=True` to check queued device errors after each write.
The numeric protocol range does not imply that every tenth-Hz value is supported
by the hardware. Invalid input is rejected before I/O and invalid replies raise
ProtocolError. Tests include the different request/response tone BCD lengths.
Simulation stores selected tone values logically; it does not couple them to
memory-record tone blocks or model per-mode/VFO tone persistence.

`scope.display_code` and `scope.dual_scope_code` now accept writes of integer
zero, the only supported code in the IC-7300 gateway profile. This is not a new
dual-scope capability. Other codes and booleans are rejected before I/O. Their
logical main-scope selector 0 is not an extra CI-V selector byte on the wire.

No Pi or radio was operated for this release. Windows offline/mock verification
does not establish IVI conformity or registration.

Later source-client hardware trials are recorded in repository
`docs/IVI_SCAN_SETTINGS_2026-11-12.md`: all seven delta half-spans, select OFF/ON,
assignment 1–3 and filters ALL/1/2/3 were exercised on MAIN 1.42 with scoped
readback/motion evidence and restoration. The span trials used LSB; they do not
establish AM-mode support or full wide-span endpoint coverage.
