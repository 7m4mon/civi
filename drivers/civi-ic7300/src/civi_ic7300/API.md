# Experimental client API 0.13.1

[REFERENCE.md](REFERENCE.md) indexes every driver-defined public member and
returned type, with signatures/types/access/SCPI and links to detailed constraints.
[EVIDENCE.md](EVIDENCE.md) defines implementation/mock/hardware labels and scope.
The full [IVI Foundation notice](IVI_NOTICE.md) is included in the reference help.
This documentation does not establish conformance or registration.

All public operations use Python exceptions. Invalid arguments raise
`ValueError` / `TypeError`; unsupported features raise `NotImplementedError`.
Transport failures raise `OSError` (including `TimeoutError`) or
`ConnectionError` and close the session. `ProtocolError` reports invalid
framing/responses. `DeviceError.errors` is a tuple of `ErrorQueryResult`
objects with read-only `code: int` and `message: str` fields.

## Root CiviIc7300

`CiviIc7300(resource_name: str, id_query: bool = True, reset: bool = False,
options: DriverOptions | dict[str, bool] | str | None = None, *, timeout_ms: int = 5000)`

Accepts `TCPIP[board]::host::port::SOCKET`, port 1–65535, and INSTR locations
with optional resource class and device name (including HiSLIP names/ports and
credential references). Board numbers are ignored by the raw TCP transport.
SOCKET uses its explicit port; INSTR locations use CIVI's raw TCP port 5025.
HiSLIP ports/subaddresses and credential references are ignored, not sent over
TCP or used for authentication. This does not implement HiSLIP, VXI-11, VISA
trigger/status/clear operations or TLS. Use SOCKET for a non-default CIVI port.
Malformed resource names fail before any I/O, without echoing credentials.
`id_query` verifies
manufacturer `CIVI Project` and model `CIVI/IC-7300` using `*IDN?`. A mismatch
raises `ProtocolError`. `reset=True` performs the receive reset after connecting
and optional identity verification; failure closes the newly constructed session.
Options are `simulate` (default false) and `query_instrument_status` (default
false). Timeout is a positive integer in milliseconds. Returns a driver session.

Read-only interface properties: `radio: Radio`, `vfos: VfoCollection`,
`gains: Gains`, `meters: Meters`, `scope: Scope`, `ivi_utility: Utility`,
`menus: MenuCollection`, `memories: MemoryCollection`,
`band_stacks: BandStackCollection`, `keyers: KeyerCollection`, `scan: ScanControl`, `bands: Bands`, `operations: RadioOperations`, `ivi_direct_io: DirectIo`. References cannot be reassigned. Utility and DirectIo
implement the exported `IviUtility` and `IviDirectIo` abstract contracts.

- `close() -> None`: idempotently close; subsequent I/O raises `RuntimeError`.
- `__enter__() -> CiviIc7300`, `__exit__(...) -> None`: context management.
- `query(command: str) -> str`: send one ASCII SCPI program and return one line
  without CR/LF. Embedded line breaks/NUL are rejected. May contain `;` but the
  caller is responsible for expected response contents. Returns textual data,
  does not parse numbers or semicolon-separated results. A lone `ERROR` reply
  raises `QueryError` without consuming the error queue; malformed replies raise
  `ProtocolError`. This raw operation does not run automatic status checks.

## radio

| Property | Type/access | Values and commands |
|---|---|---|
| `frequency_hz` | int read; int/float write | Whole Hz, 30000..60000000; `SENS:FREQ?` / `SENS:FREQ <Hz>;*OPC?` |
| `mode` | str read/write | LSB, USB, AM, CW, RTTY, FM, CW-R, RTTY-R (writes case insensitive); `RAD:MODE?` / `RAD:MODE <mode>;*OPC?` |
| `smeter_raw` | int read only | 0..255 uncalibrated; `READ:SMET?` |

Typed operations automatically query the error queue when status checking is
enabled. They are serialized including completion and status checking. A
transport failure during a setting is an **unknown outcome**; the radio may have
accepted it. Reconnect/recover, then read the state instead of assuming rollback.

## ivi_utility

| Property | Type/access | Meaning / SCPI |
|---|---|---|
| `driver_version` | str read only | `0.13.1`, no I/O |
| `driver_vendor` | str read only | `7M4MON`, no I/O |
| `instrument_manufacturer` | str read only | CIVI gateway manufacturer from `*IDN?` |
| `instrument_model` | str read only | CIVI gateway model from `*IDN?` |
| `supported_instrument_models` | tuple[str, ...] read only | `("CIVI/IC-7300",)` |
| `simulation_enabled` / `simulate` | bool read only | Constructor simulation option |
| `query_instrument_status_enabled` / `query_instrument_status` | bool read/write | Check error queue after typed I/O; default false |

- `error_query() -> ErrorQueryResult | None`: one `SYST:ERR?`; code zero
  returns None, otherwise a signed code and its English message. Never performs
  a recursive automatic status check.
- `error_query_all() -> tuple[ErrorQueryResult, ...]`: drain the queue until zero,
  bounded to 256 entries. A nonterminating queue raises `ProtocolError`.
- `raise_on_device_error() -> None`: drain the queue and raise `DeviceError` if
  nonempty; its `errors` preserves the drained entries.
- `reset(*, timeout_ms: int = 30000) -> None`: select the receive baseline in Reset.md with
  `RAD:RESET;*OPC?`. Queue checks follow the status option. Use checked()
  to check existing errors before reset and obtain detailed result errors.
  This changes radio settings, with no automatic rollback. Requires updated CIVI.
  The positive integer timeout is specific to reset; the normal I/O timeout is
  restored afterwards, including on failure.

The queue belongs to this TCP client. Other clients' errors are not drained.

## ivi_direct_io

- `io_timeout_ms: int` read/write: positive milliseconds, initially 5000 or the
  constructor override. Applies to socket operations, not the entire lifetime.
- `write_bytes(data: bytes) -> None`: one ASCII SCPI program; normalizes an
  optional CR/LF terminator and appends LF. Rejects embedded CR/LF/NUL.
- `write_string(data: str) -> None`: ASCII equivalent of `write_bytes`.
- `read_bytes() -> bytes`: one complete response including LF, up to one MiB.
- `read_string() -> str`: ASCII response with CR/LF removed.

Direct I/O deliberately does not auto-check status or interpret an `ERROR`
response; call the utility explicitly. Unsupported transports and binary blocks
are not silently emulated. Raw write/read pairs need caller synchronization;
use root `query()` when multiple threads share a session.

## Receiver, gains and meters

[CONTROLS.md](CONTROLS.md) lists every scalar property's name, type, access,
SCPI header and accepted values. `radio` also exposes Split/RIT/XIT switches,
RIT offset in Hz, PREAMP/AGC/filter settings, receiver switches, attenuator dB,
and read-only `transmitting` and `tx_frequency_hz`.
Use actual bool values for switches; numeric 0/1 and strings are rejected.
Choice writes are case insensitive and return canonical uppercase strings.
Integer protocol codes reject floats and bools, even when numerically integral.
Read-only scalar writes raise AttributeError. Invalid arguments fail before I/O;
malformed/out-of-range gateway responses raise ProtocolError.

`gains` exposes raw 0..255 settings. `meters` exposes raw 0..255 read-only
readings plus squelch/overflow bools. No dBm, watts, volts, current or SWR-ratio
calibration is implied by the raw API names. Real hardware can round a setting;
always read back if exact code agreement matters. Accepted scope reference and
attenuator dB values are actual display/attenuator settings, not measured power.

## VFO collection

- `vfos[name: str] -> Vfo`: name is SELECTED or OTHER, case insensitive. These
  are live relative views; they follow selections made by another client or the
  front panel. Indexing by A/B is rejected because current A/B cannot be queried.
- `vfos.select(name: str) -> None`: A or B, case insensitive; `RAD:VFO:SELECT`.
- `vfos.enable() -> None`: enter VFO mode; `RAD:VFO:ENABLE`.
- `vfos.copy_selected_to_other() -> None`: copy both VFO contents; `RAD:VFO:COPY`.
- `vfos.swap() -> None`: swap VFO contents; `RAD:VFO:SWAP`.
- `Vfo.name: str` read only: SELECTED or OTHER.
- `Vfo.frequency_hz: int` read/write: whole Hz 30000..60000000;
  `RAD:VFO:FREQ[?] SELECTED/OTHER`.
- `Vfo.mode: VfoMode` read/write: one complete mode/DATA/filter record;
  `RAD:VFO:MODE[?] SELECTED/OTHER`.
- `VfoMode(mode: str, data: bool = False, filter_number: int = 2)`: immutable;
  mode choices match radio.mode, DATA is bool, filter number is 1..3. All three
  values are sent in a single setting; no hidden read/modify/write is performed.

VFO methods and setters affect radio settings. Selecting A then using SELECTED
is two operations: a separate client can change selection between them. This
client does not claim a global radio lock or cache an absolute VFO selection.

## Scope

Scalar settings in CONTROLS.md always use main-scope selector 0. `span_hz` is
one of 2500/5000/10000/25000/50000/100000/250000/500000 Hz. `reference_db` is
-20..20 in 0.5 dB increments, not a calibrated dBm level. Other scope codes are
the documented CI-V code numbers. `display_code` / `dual_scope_code` are read/write
and only accept integer zero, as specified by the IC-7300 gateway catalog.

- `start_stream() -> None`: query prior STREAM state, enable STREAM then ENABLE.
  With status checks ON, it checks errors between stages.
  Existing errors abort before changes; failure at ENABLE attempts to restore
  prior STREAM state; cleanup failure is attached to the original exception.
  Calls are serialized within this session; this is not a multi-client transaction.
- `stop_stream() -> None`: disable STREAM; errors follow the option and ENABLE is preserved.
- `read_sweep() -> ScopeSweep`: `RAD:SCOPE:WAVE?`; does not start transfer. The
  gateway raises a device error if no complete fresh sweep is available.
- `ScopeSweep`: immutable mode code 0..3, frequency_1_hz/frequency_2_hz metadata,
  points tuple (475 raw 0..160 levels), out_of_range bool, timestamp float (gateway
  Unix time). Out-of-range packets have an empty points tuple. Frequency metadata
  meaning depends on scope mode; the client preserves the gateway fields.
- `read_fixed_edges(band: int, edge: int) -> ScopeEdges`: band 1..13, edge 1..4;
  `RAD:SCOPE:FIXEDGE? <band*100+edge>`.
- `write_fixed_edges(band: int, edge: int, edges: ScopeEdges) -> None`: matching
  `RAD:SCOPE:FIXEDGE` setting, persisted by the radio. Invalid selectors fail before I/O.
- `ScopeEdges(lower_hz: int, upper_hz: int)`: immutable whole-kHz boundaries in
  Hz, 0..74800000, lower <= upper. The client performs validated BCD conversion.

Hardware scope transfer still needs USB CI-V 115200 baud and Unlink from REMOTE;
the driver does not change serial/link menus to satisfy this requirement.

## Offline simulation and examples

```python
from civi_ic7300 import CiviIc7300, ScopeEdges, VfoMode

with CiviIc7300(
    "TCPIP::unused::5025::SOCKET",
    options={"simulate": True, "query_instrument_status": True},
) as d:
    d.vfos.select("A")
    d.vfos["SELECTED"].frequency_hz = 14200000
    d.vfos["SELECTED"].mode = VfoMode("USB", data=True, filter_number=2)
    d.vfos["OTHER"].frequency_hz = 7100000
    d.radio.split_enabled = False
    d.radio.rit_offset_hz = -250
    d.gains.rf_raw = 192
    print(d.meters.smeter_raw)
    d.scope.span_hz = 25000
    d.scope.reference_db = -0.5
    d.scope.write_fixed_edges(4, 1, ScopeEdges(7000000, 7300000))
    d.scope.start_stream()
    print(len(d.scope.read_sweep().points))
    d.scope.stop_stream()
```

Simulation uses a local model and the bundled captured reset profile; it imports
no CIVI gateway modules and performs no instrument/network I/O. It models VFO
selection/copy/swap, typed settings and synthetic meters/sweeps. It does not
model full RF behavior, clock/lease timing, CI-V packet loss, mode-dependent
hardware rounding or every SCPI alias. Unsupported raw commands raise
NotImplementedError. Full command coverage and IVI registration remain pending.

## Menu collection (216 definitions)

`menus[number: int | str] -> MenuItem[MenuValue]` accepts decimal menu numbers or
one to four ASCII digits such as 2 or "0002". `len(menus)` is 216; iteration
returns valid integer numbers. Reserved 0028 and unknown numbers raise KeyError.
Bad key types, bools and command fragments raise TypeError before I/O.
`MENUS.md` lists each definition's type, range/step/unit, choices and required
write-permission group. No lookup operation accesses the radio.

`MenuItem` reference properties are read only:

- `name: str`: four decimal digits.
- `definition: MenuDefinition`: immutable number, header, description,
  `kind: MenuKind`, permission group (menu/link/calibration), writable flag,
  minimum/maximum/step, unit, choices and protocol-example response. Bounds
  do not silently convert numeric codes into physical units. The permission
  field says which gateway gate applies, not whether it is currently enabled.
- `value: T`: read, or write when the definition permits it. The generic indexed
  view uses the `MenuValue` union. Typed accessors below narrow T for applications.
- `write_and_read(value: T) -> T`: write and return the actual readback while
  holding this session's lock. It does not invent exact equality when hardware
  rounds. Other network clients/front-panel controls can still change the radio.

All setters validate before I/O. Menu 0074 is read-only and raises AttributeError
on any attempted setter, even when link writes are enabled. Menu writes follow
the status option. With checks ON, preexisting errors abort and result errors
raise DeviceError before readback. With checks OFF, a denied write may leave
an error queued and write_and_read can return the unchanged value. Use checked()
for an explicitly checked sequence. Transport loss has an unknown outcome.

Typed accessors (all take `int | str` and reject a menu of the wrong kind):

| Method | T | Accepted values / representation |
|---|---|---|
| `boolean_item(number)` | bool | actual True/False; SCPI ON/OFF |
| `integer_item(number)` | int | per-definition bounds/choices/step; rejects bool/float. Repeater offsets are signed Hz in 1000 Hz steps |
| `audio_filter_item(number)` | AudioFilter | HPF/LPF index pair; SCPI two BCD bytes |
| `bandwidth_item(number)` | Bandwidth | TX filter-edge index pair; SCPI one packed-nibble byte |
| `rgb_item(number)` | RgbColor | three components 0..255; SCPI three two-byte BCD components |
| `scope_edges_item(number)` | ScopeEdges | ordered whole-kHz edges in Hz, 0..74800000; menu SCPI uses two three-byte BCD values in 100 Hz units |
| `text_item(number)` | str | 0..10 uppercase letters, digits or space ./@-; quotes added by client; trailing spaces can normalize on readback |
| `date_item(number)` | datetime.date | years 2000..2099, SCPI YYYY-MM-DD; datetime.datetime is rejected |
| `time_item(number)` | datetime.time | naive HH:MM, no seconds/microseconds/fold/timezone; SCPI HH:MM |
| `utc_offset_item(number)` | datetime.timedelta | -14:00..+14:00, whole minutes; SCPI signed HH:MM |

New immutable records exported from civi_ic7300:

- `AudioFilter(high_pass_code: int, low_pass_code: int)`: HPF 0..20, LPF 5..25.
  HPF must be below LPF unless HPF=0 or LPF=25 (bypass). These are index codes,
  not Hz; their mapping depends on the radio's documented menu.
- `Bandwidth(high_pass_code: int, low_pass_code: int)`: each index 0..3, not Hz.
- `RgbColor(red: int, green: int, blue: int)`: each integer component 0..255.

Invalid input raises TypeError/ValueError before sending. A malformed menu reply
raises ProtocolError. Permission groups remain enforced by the gateway's existing
configuration; this client provides no method to turn on actual gateway gates.
Menu changes may persist in the radio and some link settings can change the
connection. The client does not bypass quarantine or reconnect automatically.

### Offline menu example and permissions

```python
import datetime as dt
from civi_ic7300 import CiviIc7300, AudioFilter, RgbColor

with CiviIc7300(
    "TCPIP::unused::5025::SOCKET", options={"simulate": True}
) as d:
    # All three permission groups default OFF, matching CIVI's default policy.
    d.menus.set_simulated_write_permissions(menu=True)
    bass = d.menus.integer_item("0002")
    print(bass.definition.minimum, bass.definition.maximum)  # 0, 10 codes
    print(bass.write_and_read(5))
    d.menus.audio_filter_item(1).value = AudioFilter(3, 20)
    d.menus.rgb_item(104).value = RgbColor(1, 128, 255)
    d.menus.date_item(94).value = dt.date(2028, 2, 29)
    d.menus.utc_offset_item(96).value = dt.timedelta(hours=9)
    print(
        d.menus.boolean_item(74).value
    )  # Read-only link menu, no write needed.
```

`set_simulated_write_permissions(*, menu: bool = False, link: bool = False,
calibration: bool = False) -> None` only changes this offline session. All
arguments must be bool. It raises RuntimeError on a real TCP session; configure
actual write permissions on the CIVI gateway instead. Enabling normal menu
writes does not enable link or calibration writes. Clock settings are ordinary
menu writes; the simulator stores them without advancing a wall clock.

Simulation includes all 216 menu definitions, access flags, group denial,
typed values and text normalization, without gateway imports or socket I/O.
Defaults are protocol examples, not factory-state claims. Receive reset keeps
menu state and permissions; operational aliases still share state, for example
menu 0081 and gains.backlight_raw. Resetting that gain also changes its aliased
menu reading. Other physical side effects, USB changes, timing and quantization
are not modeled.

## Stored-data APIs

See [STORAGE.md](STORAGE.md) for complete MemorySettings/MemoryRecord types,
collection signatures, write permissions, selection-relative actions and examples.

## Scan and tones

See [SCAN.md](SCAN.md) for all scan method signatures, context/error semantics,
radio.repeater_tone_hz / tone_squelch_hz and scope code-zero setters.

## Band edges, DATA and alternate IP+

See [BANDS.md](BANDS.md) for BandEdges/Bands, DataFilter and radio.data_filter,
calibration permission sharing, indexed read/write methods and alternate IP+.

## Radio operations

See [OPERATIONS.md](OPERATIONS.md) for VOX/break-in/tuner, transmit inhibit,
antenna output, CW/voice/speech and power APIs, option-controlled error checks,
STOP/OFF handling, gateway ownership/permissions and simulation limits.

## Typed constructor options

`DriverOptions` is an exported `TypedDict` with optional boolean keys `simulate`
and `query_instrument_status`; omitted values are false. For static key/value
validation and editor completion, construct a DriverOptions value explicitly:

```python
from civi_ic7300 import CiviIc7300, DriverOptions

options = DriverOptions(simulate=True, query_instrument_status=True)
with CiviIc7300("TCPIP::unused::5025::SOCKET", options=options) as device:
    print(device.radio.frequency_hz)
```

Ordinary dict and string options remain supported for compatibility. Runtime
validation still rejects unknown keys/non-bool values. Options are copied at
construction. This is a typing improvement, not a change to status-check policy.
STATUS.md documents the status-policy correction and migration in 0.10.0.

## Status policy and migration

`checked()` temporarily enables checks while locking this session; QueryError
reports a failed query without consuming the queue. See [STATUS.md](STATUS.md)
for full OFF/ON, nesting, STOP/OFF, raw I/O and reset contracts.

## Band-stack hierarchy

See [HIERARCHY.md](HIERARCHY.md) for BandStackBandCollection, BandStackBand,
BandStackSlotCollection and BandStackItem, read-only metadata and overloaded
integer/tuple indexing. Nested and old tuple views share state and locks.

## Base commands and unified audit

[BASIC.md](BASIC.md) documents GatewayIdentification, ivi_utility.identification,
clear_status(), wait_for_complete(), radio.firmware_revision and
operations.start_transmit()/stop_transmit(). SCPI_COVERAGE.md and
scpi-coverage.json combine base/extended directions, aliases and unsupported forms.

## Physical context and raw-setting coercion (2026-11-11)

On IC-7300 MAIN 1.41, filter_shape readback was unavailable (NAK) in AM but worked in USB, CW and 7.100 MHz LSB. The supported context must be established before a setting is tested; NAK remains a DeviceError.

Raw 0..255 gain/control codes do not imply an exact echo of every requested code. Physical NR and PBT can select discrete device levels. NR requests 0/128/255 returned 8/136/248; the test verified bounded, nondecreasing, stable/idempotent readbacks. Read back the applied value. Offline simulation is a logical model and does not reproduce all hardware quantization. See the repository physical acceptance report for the exact PBT observations and restored settings.
