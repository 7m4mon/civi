# Radio operations (client 0.10.0)

`device.operations: RadioOperations` is a read-only interface reference for the
remaining eleven extended gateway definitions. These commands can change radio
operation, initiate transmission or power off a physical radio when the actual
gateway is explicitly configured to allow them. All release tests use offline
simulation or loopback TCP with MockBackend; no RF, audio or power operation on
hardware was performed.

| API | Values / existing gateway gate |
|---|---|
| `vox_enabled: bool` | Read/write; ON requires transmit enabled, OFF does not |
| `transmit_inhibited: bool` | Read/write; IC-7300 firmware 1.42 or later required; no additional gate in the existing gateway |
| `break_in: str` | OFF/SEMI/FULL; non-OFF requires transmit enabled |
| `antenna_output_enabled: bool` | Read/write; every write requires link permission |
| `tuner: str` | OFF/ON/TUNE; the existing gateway requires transmit enabled for both ON and TUNE |
| `send_cw(text: str)` | 1..30 supported ASCII characters; transmit enabled required |
| `stop_cw()` | Send CI-V CW stop; no transmit-enable requirement |
| `play_voice(slot: int)` | T1..T8; transmit enabled required |
| `stop_voice()` | Send voice STOP; no transmit-enable requirement |
| `speak(code: int)` | Speech synthesizer code 0..2; no added transmit gate |
| `power_on()`, `power_off()` | Require power permission and no CIVI-owned transmit operation |

Methods return None after command completion/error checks. Queries return actual
gateway replies; no CW-completion, voice-playback or power-status query is
invented. Command acceptance does not mean a CW message, speech or voice playback
has finished. An idle physical CW STOP may NAK; that is reported as DeviceError.
Power-on wake/preamble support belongs to the existing CI-V backend; this Python
client does not open a serial port or automatically recover a failed radio link.

IC-7300 CI-V `16 66` was added in firmware 1.42, as documented in the official
[firmware update information](https://www.icomamerica.com/uploads/support/firmware_driver/IC-7300_ENG_FirmUpInfo_0.pdf).
The 2026-11-11 physical unit was reported by its owner as MAIN 1.41 and rejected
this query in AM, USB, CW and 7.100 MHz LSB. This is an unavailable firmware
feature, not a successful read or an inferred OFF state. The driver reports the
gateway DeviceError; it does not silently substitute a state. No TX-inhibit writes
or firmware update were performed. Other operation getters were read only.

After the owner updated MAIN to 1.42 on 2026-11-11, the focused physical test
successfully read TX Inhibit, set/read True and False, rejected invalid input
types before I/O and restored the original False value. Both VFOs were unchanged,
PTT samples stayed OFF and the error queue was empty. No actual transmission
was attempted to test RF suppression. See repository
docs/IVI_TX_INHIBIT_2026-11-11.md; other 1.41 results do not become 1.42 evidence.

## Validation and errors

All inputs are validated before I/O. CW accepts ASCII letters/digits, space and
`/?.-,:'()=+"@^`; embedded quotes/commas are correctly quoted for SCPI, while
semicolons, line breaks, non-ASCII and oversized strings are rejected.
All typed writes/actions follow the status option. With checks ON, prior
errors abort ordinary operations; CW/voice STOP and VOX/break-in/tuner OFF are
still attempted, then prior/new errors are reported together. Use checked() to
explicitly select this behavior. With checks OFF, no automatic queue inspection
occurs, so stop NAK/serial errors can remain queued without an exception. A
processing-complete response alone does not prove a successful physical stop.
Malformed error queues, closed sessions and transport failures can prevent
sending. Transport failure closes the session and leaves the physical outcome
uncertain. Direct I/O remains caller-managed. See STATUS.md.

## Permissions, ownership and stopping

Real transmission authorization and maximum time are configured in CIVI's
`[transmit]`; link/power gates are in `[permissions]`. This client cannot enable
them on a real gateway. The gateway serializes all operations, assigns transmit
ownership to a client and rejects another client's transmit start. Its existing
watchdog attempts to stop CIVI-owned paths after the maximum duration or client
disconnect; repeated commands do not renew that ownership deadline. Power
changes are rejected while transmit ownership exists.

Closing a TCP session relies on the gateway detecting disconnect and attempting
stops. The client does not send an additional universal stop sequence from
`close()`. Gateway/RF acknowledgement and a working USB link are needed; USB
disconnection means a physical stop cannot be guaranteed. VOX/break-in enabling
arms an automatic path and does not establish that RF is currently emitted.
The PTT property remains read-only; 0.12.0 adds explicit
operations.start_transmit()/stop_transmit() actions. See BASIC.md for their
guards and shared-path stopping semantics. Raw SCPI remains available.

## Offline simulation

`operations.set_simulated_permissions(*, transmit=False, power=False, link=False,
max_transmit_seconds=10.0)` changes only offline configuration. Booleans are
strict and duration must be numeric, finite and positive. Each call replaces
these three permission settings; other menu/memory/calibration gates are
preserved. Link permission is shared with the menu simulator. All gates default
OFF. On an actual TCP session the method raises RuntimeError.

Simulation records logical CW text, voice slot, speech code and power intent.
It models owned automatic paths and rejects power while those paths are active.
The timeout is checked lazily on subsequent I/O, without a background task;
closing a simulated session also clears owned paths. Receive reset stops modeled
paths and preserves permissions, antenna-output and transmit-inhibit settings.
It does not model multi-session ownership, natural CW/voice completion, RF/audio,
PTT transitions, tuner behavior, USB wake timing, hardware disconnection or
per-mode radio restrictions. The gateway mock also does not emit RF/audio or
physically change power. Its ownership/watchdog/disconnect behavior is exercised
through the real gateway service and loopback TCP.

```python
from civi_ic7300 import CiviIc7300

with CiviIc7300(
    "TCPIP::unused::5025::SOCKET",
    options={"simulate": True, "query_instrument_status": True},
) as d:
    d.operations.set_simulated_permissions(transmit=True)
    try:
        d.operations.send_cw('CQ, "TEST"')
    finally:
        d.operations.stop_cw()
```
