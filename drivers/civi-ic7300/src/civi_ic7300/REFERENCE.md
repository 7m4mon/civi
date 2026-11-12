# Public API reference (client 0.13.1)

43 public/returned types; 311 member/field entries.

Generated signatures/types/access and explicit SCPI contracts are indexed below. Linked guides
supply argument ranges, units, detailed behavior and examples. New unclassified exports or
members fail generation. EVIDENCE.md summarizes completed verification results.

Scope: driver-defined public members and selected collection/context protocols. Standard
Python exception/string/Enum inherited APIs are not duplicated here.

## Common contracts and exceptions

- Invalid types/values: TypeError/ValueError before I/O where validated; detailed guide lists constraints.
- DeviceError: errors read from this client queue when checks are ON or explicitly requested.
- QueryError: gateway ERROR sentinel, with the queue preserved when not automatically inspected.
- ProtocolError: invalid framing/replies; transport failures use OSError/TimeoutError/ConnectionError.
- RuntimeError: closed-session I/O or a simulation-only permission method used on a real connection.
- AttributeError: attempting a read-only assignment; NotImplementedError: unsupported simulator/raw features.
- STATUS.md governs checks. Setters normally append *OPC?; ON/checked() may add SYST:ERR? queries.
- Local metadata/view construction does not send SCPI. Closing TCP may trigger gateway stop attempts.
- Pure record conversions/constructors return the documented value/record, without instrument I/O.
- Collection constructors take an owning driver; applications normally obtain views through root references.
- Abstract IviUtility/IviDirectIo types describe contracts and cannot be instantiated directly.

## Development environments

Python >=3.11 is required. Current execution/build/type evidence is Windows 11 (25H2),
CPython 3.14.5 x64. Interactive shells, scripts and IDEs use the same Python API; no IDE plugin
is required. The recorded development environment is listed in COMPLIANCE.md.

## CiviIc7300

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `CiviIc7300(resource_name: str, id_query: bool = True, reset: bool = False, options: DriverOptions | dict[str, bool] | str | None = None, *, timeout_ms: int = 5000) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `__enter__(self) -> Self` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__exit__(self, *exc: object) -> None` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `band_stacks getter(self) -> BandStackCollection` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `bands getter(self) -> Bands` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `checked(self) -> ContextManager[CiviIc7300]` | method | None (local metadata/view/configuration or record conversion) | Temporarily enable typed status checks; serialize the entire block. |
| `close(self) -> None` | method | None (local metadata/view/configuration or record conversion) | Close this session. A failed I/O session must be reopened explicitly. |
| `gains getter(self) -> Gains` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `ivi_direct_io getter(self) -> DirectIo` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `ivi_utility getter(self) -> Utility` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `keyers getter(self) -> KeyerCollection` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `memories getter(self) -> MemoryCollection` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `menus getter(self) -> MenuCollection` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `meters getter(self) -> Meters` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `operations getter(self) -> RadioOperations` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `query(self, command: str) -> str` | method | caller-supplied ASCII program | Atomically send one program and read one response; raw status remains explicit. |
| `radio getter(self) -> Radio` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `scan getter(self) -> ScanControl` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `scope getter(self) -> Scope` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `vfos getter(self) -> VfoCollection` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |

## Radio

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `Radio(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `agc: str` | read/write | RAD:AGC | RAD:AGC[?], choices: FAST, MID, SLOW |
| `agc_time_code: int` | read/write | RAD:AGC:TIME | RAD:AGC:TIME[?], integer 0..13. |
| `attenuator_db getter(self) -> int`<br>`attenuator_db setter(self, value: int) -> None` | read/write | RAD:ATT | Read/write 0 or 20 dB attenuator setting, not a meter. |
| `automatic_notch_enabled: bool` | read/write | RAD:ANOTCH | RAD:ANOTCH[?], boolean. |
| `compressor_enabled: bool` | read/write | RAD:COMP | RAD:COMP[?], boolean. |
| `data_filter getter(self) -> DataFilter`<br>`data_filter setter(self, value: DataFilter) -> None` | read/write | RAD:DATA | Read/write DataFilter; DATA OFF reads and writes have different filter constraints (BANDS.md). |
| `filter_shape: str` | read/write | RAD:FILTER:SHAPE | RAD:FILTER:SHAPE[?], choices: SHARP, SOFT |
| `filter_width_code: int` | read/write | RAD:FILTER:WIDTH | RAD:FILTER:WIDTH[?], integer 0..49. |
| `firmware_revision getter(self) -> str` | read-only | RAD:FIRM? | Read manual radio firmware metadata or Unknown; not CI-V auto-read. |
| `frequency_check_enabled: bool` | read/write | RAD:XFC | RAD:XFC[?], boolean. |
| `frequency_hz getter(self) -> int`<br>`frequency_hz setter(self, value: float) -> None` | read/write | SENS:FREQ | Read/write selected operating frequency, whole Hz, 30000..60000000. |
| `ip_plus_alternate_enabled: bool` | read/write | RAD:IPPLUS:ALT | RAD:IPPLUS:ALT[?], boolean. |
| `ip_plus_enabled: bool` | read/write | RAD:IPPLUS | RAD:IPPLUS[?], boolean. |
| `lock_enabled: bool` | read/write | RAD:LOCK | RAD:LOCK[?], boolean. |
| `manual_notch_enabled: bool` | read/write | RAD:NOTCH | RAD:NOTCH[?], boolean. |
| `mode getter(self) -> str`<br>`mode setter(self, value: str) -> None` | read/write | RAD:MODE | Read/write canonical mode; use VfoMode for DATA and filter together. |
| `monitor_enabled: bool` | read/write | RAD:MONITOR | RAD:MONITOR[?], boolean. |
| `noise_blanker_enabled: bool` | read/write | RAD:NB | RAD:NB[?], boolean. |
| `noise_reduction_enabled: bool` | read/write | RAD:NR | RAD:NR[?], boolean. |
| `notch_width: str` | read/write | RAD:NOTCH:WIDTH | RAD:NOTCH:WIDTH[?], choices: WIDE, MID, NARROW |
| `preamp: str` | read/write | RAD:PREAMP | RAD:PREAMP[?], choices: OFF, PRE1, PRE2 |
| `repeater_tone_hz: float` | read/write | RAD:TONE:FREQ | Tone frequency, 67.0..254.1 Hz in 0.1 Hz increments. |
| `rit_enabled: bool` | read/write | RAD:RIT | RAD:RIT[?], boolean. |
| `rit_offset_hz: int` | read/write | RAD:RIT:FREQ | RAD:RIT:FREQ[?], integer -9999..9999. |
| `smeter_raw getter(self) -> int` | read-only | READ:SMET? | Read uncalibrated raw integer 0..255, not dBm. |
| `split_enabled: bool` | read/write | RAD:SPLIT | RAD:SPLIT[?], boolean. |
| `tone_enabled: bool` | read/write | RAD:TONE | RAD:TONE[?], boolean. |
| `tone_squelch_enabled: bool` | read/write | RAD:TSQL | RAD:TSQL[?], boolean. |
| `tone_squelch_hz: float` | read/write | RAD:TSQL:FREQ | Tone squelch frequency, 67.0..254.1 Hz in 0.1 Hz increments. |
| `transmitting: bool` | read-only | RAD:PTT | RAD:PTT[?], boolean. |
| `tuning_step_code: int` | read/write | RAD:STEP | RAD:STEP[?], integer 0..8. |
| `twin_peak_filter_enabled: bool` | read/write | RAD:TPF | RAD:TPF[?], boolean. |
| `tx_bandwidth: str` | read/write | RAD:TXBANDWIDTH | RAD:TXBANDWIDTH[?], choices: WIDE, MID, NARROW |
| `tx_frequency_hz: int` | read-only | RAD:TXFREQ | RAD:TXFREQ[?], integer 30000..60000000. |
| `xit_enabled: bool` | read/write | RAD:XIT | RAD:XIT[?], boolean. |

## Utility

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `Utility(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `clear_status(self) -> None` | method | *CLS | Explicitly clear this client error queue; no serial quarantine recovery. |
| `driver_vendor getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `driver_version getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `error_query(self) -> ErrorQueryResult \| None` | method | SYST:ERR? | Read/consume this client error queue explicitly, independently of the status option. |
| `error_query_all(self) -> tuple[ErrorQueryResult, ...]` | method | SYST:ERR? | Read/consume this client error queue explicitly, independently of the status option. |
| `identification getter(self) -> GatewayIdentification` | read-only | *IDN? | Read gateway identity; the full record is distinct from radio firmware. |
| `instrument_manufacturer getter(self) -> str` | read-only | *IDN? | Read gateway identity; the full record is distinct from radio firmware. |
| `instrument_model getter(self) -> str` | read-only | *IDN? | Read gateway identity; the full record is distinct from radio firmware. |
| `query_instrument_status getter(self) -> bool`<br>`query_instrument_status setter(self, enabled: bool) -> None` | read/write | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `query_instrument_status_enabled getter(self) -> bool`<br>`query_instrument_status_enabled setter(self, enabled: bool) -> None` | read/write | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `raise_on_device_error(self) -> None` | method | SYST:ERR? | Read/consume this client error queue explicitly, independently of the status option. |
| `reset(self, *, timeout_ms: int = 30000) -> None` | method | RAD:RESET | Select the documented receive baseline with a reset-specific timeout; no automatic rollback. |
| `simulate getter(self) -> bool` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `simulation_enabled getter(self) -> bool` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `supported_instrument_models getter(self) -> tuple[str, ...]` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `wait_for_complete(self) -> None` | method | *OPC? | Require completion reply 1; completion alone does not prove prior success. |

## DirectIo

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `DirectIo(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `io_timeout_ms getter(self) -> int`<br>`io_timeout_ms setter(self, timeout_ms: int) -> None` | read/write | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `read_bytes(self) -> bytes` | method | receive pending response; no command sent | Read one LF-framed response; synchronize separate raw write/read pairs externally. |
| `read_string(self) -> str` | method | receive pending response; no command sent | Read one LF-framed response; synchronize separate raw write/read pairs externally. |
| `write_bytes(self, data: bytes) -> None` | method | caller-supplied ASCII program | Write one LF-framed program; raw I/O never adds status queries. |
| `write_string(self, data: str) -> None` | method | caller-supplied ASCII program | Write one LF-framed program; raw I/O never adds status queries. |

## DriverOptions

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

| Field | Type | Access |
|---|---|---|
| `simulate` | `bool` | optional dictionary key |
| `query_instrument_status` | `bool` | optional dictionary key |

## GatewayIdentification

Details/valid values: [BASIC.md](BASIC.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `GatewayIdentification(manufacturer: str, model: str, serial_number: str, software_revision: str) -> None`.

| Field | Type | Access |
|---|---|---|
| `manufacturer` | `str` | read-only |
| `model` | `str` | read-only |
| `serial_number` | `str` | read-only |
| `software_revision` | `str` | read-only |

## Gains

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `Gains(driver: CiviIc7300, selector: str = '') -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `af_raw: int` | read/write | RAD:AFGAIN | RAD:AFGAIN[?], integer 0..255. |
| `anti_vox_raw: int` | read/write | RAD:VOX:ANTIGAIN | RAD:VOX:ANTIGAIN[?], integer 0..255. |
| `backlight_raw: int` | read/write | RAD:BACKLIGHT | RAD:BACKLIGHT[?], integer 0..255. |
| `compression_raw: int` | read/write | RAD:COMP:LEVEL | RAD:COMP:LEVEL[?], integer 0..255. |
| `cw_delay_raw: int` | read/write | RAD:CW:DELAY | RAD:CW:DELAY[?], integer 0..255. |
| `cw_pitch_raw: int` | read/write | RAD:CW:PITCH | RAD:CW:PITCH[?], integer 0..255. |
| `cw_speed_raw: int` | read/write | RAD:CW:SPEED | RAD:CW:SPEED[?], integer 0..255. |
| `microphone_raw: int` | read/write | RAD:MICGAIN | RAD:MICGAIN[?], integer 0..255. |
| `monitor_raw: int` | read/write | RAD:MONITOR:LEVEL | RAD:MONITOR:LEVEL[?], integer 0..255. |
| `noise_blanker_raw: int` | read/write | RAD:NB:LEVEL | RAD:NB:LEVEL[?], integer 0..255. |
| `noise_reduction_raw: int` | read/write | RAD:NR:LEVEL | RAD:NR:LEVEL[?], integer 0..255. |
| `notch_raw: int` | read/write | RAD:NOTCH:LEVEL | RAD:NOTCH:LEVEL[?], integer 0..255. |
| `pbt_inner_raw: int` | read/write | RAD:PBT:INNER | RAD:PBT:INNER[?], integer 0..255. |
| `pbt_outer_raw: int` | read/write | RAD:PBT:OUTER | RAD:PBT:OUTER[?], integer 0..255. |
| `rf_power_raw: int` | read/write | RAD:POWER | RAD:POWER[?], integer 0..255. |
| `rf_raw: int` | read/write | RAD:RFGAIN | RAD:RFGAIN[?], integer 0..255. |
| `squelch_raw: int` | read/write | RAD:SQL | RAD:SQL[?], integer 0..255. |
| `vox_raw: int` | read/write | RAD:VOX:GAIN | RAD:VOX:GAIN[?], integer 0..255. |

## Meters

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `Meters(driver: CiviIc7300, selector: str = '') -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `alc_raw: int` | read-only | READ:ALC | READ:ALC[?], integer 0..255. |
| `all_squelches_open: bool` | read-only | READ:SQL:ALL | READ:SQL:ALL[?], boolean. |
| `compression_raw: int` | read-only | READ:COMP | READ:COMP[?], integer 0..255. |
| `current_raw: int` | read-only | READ:CURRENT | READ:CURRENT[?], integer 0..255. |
| `overflow: bool` | read-only | READ:OVF | READ:OVF[?], boolean. |
| `power_raw: int` | read-only | READ:POWER | READ:POWER[?], integer 0..255. |
| `smeter_raw: int` | read-only | READ:SMET | READ:SMET[?], integer 0..255. |
| `squelch_open: bool` | read-only | READ:SQL | READ:SQL[?], boolean. |
| `swr_raw: int` | read-only | READ:SWR | READ:SWR[?], integer 0..255. |
| `voltage_raw: int` | read-only | READ:VOLTAGE | READ:VOLTAGE[?], integer 0..255. |

## Scope

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `Scope(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `center_mode_code: int` | read/write | RAD:SCOPE:CENTER | RAD:SCOPE:CENTER[?], integer 0..2. |
| `display_code: int` | read/write | RAD:SCOPE:DISPLAY | RAD:SCOPE:DISPLAY[?], integer 0..0. |
| `dual_scope_code: int` | read/write | RAD:SCOPE:DUAL | RAD:SCOPE:DUAL[?], integer 0..0. |
| `edge_number: int` | read/write | RAD:SCOPE:EDGE | RAD:SCOPE:EDGE[?], integer 1..4. |
| `enabled: bool` | read/write | RAD:SCOPE:ENABLE | RAD:SCOPE:ENABLE[?], boolean. |
| `hold_enabled: bool` | read/write | RAD:SCOPE:HOLD | RAD:SCOPE:HOLD[?], boolean. |
| `marker_enabled: bool` | read/write | RAD:SCOPE:MARKER | RAD:SCOPE:MARKER[?], boolean. |
| `mode_code: int` | read/write | RAD:SCOPE:MODE | RAD:SCOPE:MODE[?], integer 0..3. |
| `read_fixed_edges(self, band: int, edge: int) -> ScopeEdges` | method | RAD:SCOPE:FIXEDGE | Read/write stored edges using band 1..13, edge 1..4 and whole-kHz boundaries in Hz. |
| `read_sweep(self) -> ScopeSweep` | method | RAD:SCOPE:WAVE? | Read a complete sweep; does not enable streaming. |
| `reference_db: float` | read/write | RAD:SCOPE:REFERENCE | Relative scope display reference -20..20 dB, step 0.5; not dBm. |
| `span_hz: int` | read/write | RAD:SCOPE:SPAN | Scope span in Hz; 2500/5000/10000/25000/50000/100000/250000/500000. |
| `speed_code: int` | read/write | RAD:SCOPE:SPEED | RAD:SCOPE:SPEED[?], integer 0..2. |
| `start_stream(self) -> None` | method | RAD:SCOPE:STREAM; RAD:SCOPE:ENABLE | Enable transfer then operation; checked mode attempts transfer restoration on second-stage failure. |
| `stop_stream(self) -> None` | method | RAD:SCOPE:STREAM | Disable transfer while preserving scope operation; checks follow STATUS.md. |
| `streaming_enabled: bool` | read/write | RAD:SCOPE:STREAM | RAD:SCOPE:STREAM[?], boolean. |
| `tx_display_enabled: bool` | read/write | RAD:SCOPE:TXDISPLAY | RAD:SCOPE:TXDISPLAY[?], boolean. |
| `vbw_enabled: bool` | read/write | RAD:SCOPE:VBW | RAD:SCOPE:VBW[?], boolean. |
| `write_fixed_edges(self, band: int, edge: int, edges: ScopeEdges) -> None` | method | RAD:SCOPE:FIXEDGE | Read/write stored edges using band 1..13, edge 1..4 and whole-kHz boundaries in Hz. |

## Vfo

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `Vfo(driver: CiviIc7300, selector: str = '') -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `frequency_hz getter(self) -> int`<br>`frequency_hz setter(self, value: float) -> None` | read/write | RAD:VFO:FREQ | Read/write relative SELECTED/OTHER VFO frequency in whole Hz, 30000..60000000. |
| `mode getter(self) -> VfoMode`<br>`mode setter(self, value: VfoMode) -> None` | read/write | RAD:VFO:MODE | Read/write one complete mode/DATA/filter record. |
| `name getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Relative SELECTED/OTHER selector, not a cached absolute VFO identity. |

## VfoCollection

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `VfoCollection(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `__getitem__(self, name: str) -> Vfo` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `copy_selected_to_other(self) -> None` | method | RAD:VFO:COPY | Operate on VFO context; selection is shared with other clients. See API.md for values. |
| `enable(self) -> None` | method | RAD:VFO:ENABLE | Operate on VFO context; selection is shared with other clients. See API.md for values. |
| `select(self, name: str) -> None` | method | RAD:VFO:SELECT | Operate on VFO context; selection is shared with other clients. See API.md for values. |
| `swap(self) -> None` | method | RAD:VFO:SWAP | Operate on VFO context; selection is shared with other clients. See API.md for values. |

## VfoMode

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `VfoMode(mode: str, data: bool = False, filter_number: int = 2) -> None`.

| Field | Type | Access |
|---|---|---|
| `mode` | `str` | read-only |
| `data` | `bool` | read-only |
| `filter_number` | `int` | read-only |

## ScopeEdges

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `ScopeEdges(lower_hz: int, upper_hz: int) -> None`.

| Field | Type | Access |
|---|---|---|
| `lower_hz` | `int` | read-only |
| `upper_hz` | `int` | read-only |

## ScopeSweep

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `ScopeSweep(mode: int, frequency_1_hz: int, frequency_2_hz: int, points: tuple[int, ...], out_of_range: bool, timestamp: float) -> None`.

| Field | Type | Access |
|---|---|---|
| `mode` | `int` | read-only |
| `frequency_1_hz` | `int` | read-only |
| `frequency_2_hz` | `int` | read-only |
| `points` | `tuple[int, ...]` | read-only |
| `out_of_range` | `bool` | read-only |
| `timestamp` | `float` | read-only |

## DataFilter

Details/valid values: [BANDS.md](BANDS.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `DataFilter(enabled: bool, filter_number: int) -> None`.

| Field | Type | Access |
|---|---|---|
| `enabled` | `bool` | read-only |
| `filter_number` | `int` | read-only |

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `from_hex(text: str) -> DataFilter` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `to_write_hex(self) -> str` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |

## MenuItem

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `MenuItem(driver: CiviIc7300, definition: MenuDefinition) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `definition getter(self) -> MenuDefinition` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `name getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `value getter(self) -> T`<br>`value setter(self, value: T) -> None` | read/write | RAD:MENU:nnnn | Read/write item-specific typed value; definition/MENUS.md supplies range, step, unit and write gate. |
| `write_and_read(self, value: T) -> T` | method | RAD:MENU:nnnn | Read/write item-specific typed value; definition/MENUS.md supplies range, step, unit and write gate. |

## MenuCollection

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `MenuCollection(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `__getitem__(self, key: MenuKey) -> MenuItem[MenuValue]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__iter__(self) -> Iterator[int]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__len__(self) -> int` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `audio_filter_item(self, key: MenuKey) -> MenuItem[AudioFilter]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `bandwidth_item(self, key: MenuKey) -> MenuItem[Bandwidth]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `boolean_item(self, key: MenuKey) -> MenuItem[bool]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `date_item(self, key: MenuKey) -> MenuItem[dt.date]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `integer_item(self, key: MenuKey) -> MenuItem[int]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `rgb_item(self, key: MenuKey) -> MenuItem[RgbColor]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `scope_edges_item(self, key: MenuKey) -> MenuItem[ScopeEdges]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `set_simulated_write_permissions(self, *, menu: bool = False, link: bool = False, calibration: bool = False) -> None` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `text_item(self, key: MenuKey) -> MenuItem[str]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `time_item(self, key: MenuKey) -> MenuItem[dt.time]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `utc_offset_item(self, key: MenuKey) -> MenuItem[dt.timedelta]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |

## MenuDefinition

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `MenuDefinition(number: int, header: str, description: str, kind: MenuKind, permission: str, writable: bool, minimum: int | None, maximum: int | None, step: int | None, unit: str, choices: tuple[int | str, ...], sample_response: str) -> None`.

| Field | Type | Access |
|---|---|---|
| `number` | `int` | read-only |
| `header` | `str` | read-only |
| `description` | `str` | read-only |
| `kind` | `MenuKind` | read-only |
| `permission` | `str` | read-only |
| `writable` | `bool` | read-only |
| `minimum` | `int | None` | read-only |
| `maximum` | `int | None` | read-only |
| `step` | `int | None` | read-only |
| `unit` | `str` | read-only |
| `choices` | `tuple[int | str, ...]` | read-only |
| `sample_response` | `str` | read-only |

## MenuKind

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Enum values: `{"BOOLEAN": "boolean", "INTEGER": "integer", "AUDIO_FILTER": "audio_filter", "BANDWIDTH": "bandwidth", "RGB": "rgb", "SCOPE_EDGES": "scope_edges", "TEXT": "text", "DATE": "date", "TIME": "time", "UTC_OFFSET": "utc_offset"}`.

## AudioFilter

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `AudioFilter(high_pass_code: int, low_pass_code: int) -> None`.

| Field | Type | Access |
|---|---|---|
| `high_pass_code` | `int` | read-only |
| `low_pass_code` | `int` | read-only |

## Bandwidth

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `Bandwidth(high_pass_code: int, low_pass_code: int) -> None`.

| Field | Type | Access |
|---|---|---|
| `high_pass_code` | `int` | read-only |
| `low_pass_code` | `int` | read-only |

## RgbColor

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `RgbColor(red: int, green: int, blue: int) -> None`.

| Field | Type | Access |
|---|---|---|
| `red` | `int` | read-only |
| `green` | `int` | read-only |
| `blue` | `int` | read-only |

## MemorySettings

Details/valid values: [STORAGE.md](STORAGE.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `MemorySettings(frequency_hz: int, mode: str, filter_number: int = 1, data: bool = False, tone_mode: str = 'OFF', repeater_tone_hz: float = 88.5, tone_squelch_hz: float = 88.5) -> None`.

| Field | Type | Access |
|---|---|---|
| `frequency_hz` | `int` | read-only |
| `mode` | `str` | read-only |
| `filter_number` | `int` | read-only |
| `data` | `bool` | read-only |
| `tone_mode` | `str` | read-only |
| `repeater_tone_hz` | `float` | read-only |
| `tone_squelch_hz` | `float` | read-only |

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `from_bytes(data: bytes) -> MemorySettings` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `from_hex(text: str) -> MemorySettings` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `to_bytes(self) -> bytes` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `to_hex(self) -> str` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |

## MemoryRecord

Details/valid values: [STORAGE.md](STORAGE.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `MemoryRecord(receive: MemorySettings, transmit: MemorySettings, split_enabled: bool = False, select_group: int = 0, name: str = '') -> None`.

| Field | Type | Access |
|---|---|---|
| `receive` | `MemorySettings` | read-only |
| `transmit` | `MemorySettings` | read-only |
| `split_enabled` | `bool` | read-only |
| `select_group` | `int` | read-only |
| `name` | `str` | read-only |

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `display_name getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `from_bytes(data: bytes) -> MemoryRecord` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `from_hex(text: str) -> MemoryRecord` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `simple(settings: MemorySettings, name: str = '') -> MemoryRecord` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `to_bytes(self) -> bytes` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `to_hex(self) -> str` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |

## MemoryItem

Details/valid values: [STORAGE.md](STORAGE.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `MemoryItem(driver: CiviIc7300, number: int) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `clear(self) -> None` | method | RAD:MEM:CONTENT | Read/write complete memory record; None means empty. Addressed clear supports 1..99, not P1/P2. |
| `name getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `number getter(self) -> int` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `record getter(self) -> MemoryRecord \| None`<br>`record setter(self, record: MemoryRecord) -> None` | read/write | RAD:MEM:CONTENT | Read/write complete memory record; None means empty. Addressed clear supports 1..99, not P1/P2. |
| `set_simulated_write_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Set the shared offline memory-write gate; never alters a real gateway. |
| `write_and_read(self, record: MemoryRecord) -> MemoryRecord \| None` | method | RAD:MEM:CONTENT | Read/write complete memory record; None means empty. Addressed clear supports 1..99, not P1/P2. |

## MemoryCollection

Details/valid values: [STORAGE.md](STORAGE.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `MemoryCollection(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `__getitem__(self, key: int \| str) -> MemoryItem` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__iter__(self) -> Iterator[int]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__len__(self) -> int` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `clear_selected(self) -> None` | method | RAD:MEM:CLEAR | Selection-relative memory operation; use addressed records for exact backup/editing. See STORAGE.md. |
| `copy_selected_to_vfo(self) -> None` | method | RAD:MEM:TOVFO | Selection-relative memory operation; use addressed records for exact backup/editing. See STORAGE.md. |
| `enable(self) -> None` | method | RAD:MEM:ENABLE | Selection-relative memory operation; use addressed records for exact backup/editing. See STORAGE.md. |
| `select(self, key: int \| str) -> None` | method | RAD:MEM:SELECT | Selection-relative memory operation; use addressed records for exact backup/editing. See STORAGE.md. |
| `set_simulated_write_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Set the shared offline memory-write gate; never alters a real gateway. |
| `store_current_in_selected(self) -> None` | method | RAD:MEM:WRITE | Selection-relative memory operation; use addressed records for exact backup/editing. See STORAGE.md. |

## KeyerItem

Details/valid values: [STORAGE.md](STORAGE.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `KeyerItem(driver: CiviIc7300, number: int) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `name getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Physical keyer identifier M1..M8; no instrument I/O. |
| `number getter(self) -> int` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `set_simulated_write_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Set the shared offline memory-write gate; never alters a real gateway. |
| `text getter(self) -> str`<br>`text setter(self, value: str) -> None` | read/write | RAD:KEYER:TEXT | Read/write up to 70 supported ASCII characters in M1..M8; storage only, no CW output. |
| `write_and_read(self, value: str) -> str` | method | RAD:KEYER:TEXT | Read/write up to 70 supported ASCII characters in M1..M8; storage only, no CW output. |

## KeyerCollection

Details/valid values: [STORAGE.md](STORAGE.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `KeyerCollection(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `__getitem__(self, number: int) -> KeyerItem` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__iter__(self) -> Iterator[int]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__len__(self) -> int` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `set_simulated_write_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Set the shared offline memory-write gate; never alters a real gateway. |

## BandStackItem

Details/valid values: [HIERARCHY.md](HIERARCHY.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `BandStackItem(driver: CiviIc7300, band: int, slot: int) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `band getter(self) -> int` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `name getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Physical slot identifier within its band, as decimal text. |
| `set_simulated_write_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Set the shared offline memory-write gate; never alters a real gateway. |
| `settings getter(self) -> MemorySettings`<br>`settings setter(self, value: MemorySettings) -> None` | read/write | RAD:BAND:STACK | Read/write full settings at band 1..11, slot 1..3; flat/nested views share state. |
| `slot getter(self) -> int` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `write_and_read(self, value: MemorySettings) -> MemorySettings` | method | RAD:BAND:STACK | Read/write full settings at band 1..11, slot 1..3; flat/nested views share state. |

## BandStackSlotCollection

Details/valid values: [HIERARCHY.md](HIERARCHY.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `BandStackSlotCollection(driver: CiviIc7300, band: int) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `__getitem__(self, slot: int) -> BandStackItem` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__iter__(self) -> Iterator[int]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__len__(self) -> int` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `band getter(self) -> int` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `set_simulated_write_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Set the shared offline memory-write gate; never alters a real gateway. |

## BandStackBand

Details/valid values: [HIERARCHY.md](HIERARCHY.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `BandStackBand(driver: CiviIc7300, number: int) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `name getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `number getter(self) -> int` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `set_simulated_write_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Set the shared offline memory-write gate; never alters a real gateway. |
| `slots getter(self) -> BandStackSlotCollection` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |

## BandStackBandCollection

Details/valid values: [HIERARCHY.md](HIERARCHY.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `BandStackBandCollection(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `__getitem__(self, band: int) -> BandStackBand` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__iter__(self) -> Iterator[int]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__len__(self) -> int` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `set_simulated_write_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Set the shared offline memory-write gate; never alters a real gateway. |

## BandStackCollection

Details/valid values: [HIERARCHY.md](HIERARCHY.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `BandStackCollection(driver: CiviIc7300) -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `__getitem__(self, key: int) -> BandStackBand`<br>`__getitem__(self, key: tuple[int, int]) -> BandStackItem` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__iter__(self) -> Iterator[tuple[int, int]]` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `__len__(self) -> int` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `bands getter(self) -> BandStackBandCollection` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `set_simulated_write_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Set the shared offline memory-write gate; never alters a real gateway. |

## BandEdges

Details/valid values: [BANDS.md](BANDS.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `BandEdges(lower_hz: int, upper_hz: int) -> None`.

| Field | Type | Access |
|---|---|---|
| `lower_hz` | `int` | read-only |
| `upper_hz` | `int` | read-only |

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `from_hex(text: str) -> BandEdges` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `to_hex(self) -> str` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |

## Bands

Details/valid values: [BANDS.md](BANDS.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `Bands(driver: CiviIc7300, selector: str = '') -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `default_edges getter(self) -> BandEdges` | read-only | RAD:BAND:EDGES? | Read band metadata/counts or indexed record; indices 1..30, count 0..30. User writes require calibration permission; see BANDS.md. |
| `factory_count getter(self) -> int` | read-only | RAD:TXBAND:COUNT? | Read band metadata/counts or indexed record; indices 1..30, count 0..30. User writes require calibration permission; see BANDS.md. |
| `read_factory(self, index: int) -> BandEdges` | method | RAD:TXBAND:READ? | Read band metadata/counts or indexed record; indices 1..30, count 0..30. User writes require calibration permission; see BANDS.md. |
| `read_user(self, index: int) -> BandEdges \| None` | method | RAD:TXBAND:USER? | Read band metadata/counts or indexed record; indices 1..30, count 0..30. User writes require calibration permission; see BANDS.md. |
| `set_simulated_calibration_permission(self, enabled: bool) -> None` | method | None (local metadata/view/configuration or record conversion) | Shared with menu calibration writes. Never changes a real gateway. |
| `user_count getter(self) -> int` | read-only | RAD:TXBAND:USERCOUNT? | Read band metadata/counts or indexed record; indices 1..30, count 0..30. User writes require calibration permission; see BANDS.md. |
| `write_and_read_user(self, index: int, edges: BandEdges) -> BandEdges \| None` | method | RAD:TXBAND:USER | Read band metadata/counts or indexed record; indices 1..30, count 0..30. User writes require calibration permission; see BANDS.md. |
| `write_user(self, index: int, edges: BandEdges) -> None` | method | RAD:TXBAND:USER | Read band metadata/counts or indexed record; indices 1..30, count 0..30. User writes require calibration permission; see BANDS.md. |

## ScanControl

Details/valid values: [SCAN.md](SCAN.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `ScanControl(driver: CiviIc7300, selector: str = '') -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `assign_selected_memory_group(self, group: int) -> None` | method | RAD:SCAN:SELECT | Write-only scan control; arguments/choices in SCAN.md. Acceptance is not scan completion. |
| `set_delta_span_hz(self, span_hz: int) -> None` | method | RAD:SCAN:SPAN* | Write-only scan control; arguments/choices in SCAN.md. Acceptance is not scan completion. |
| `set_memory_group(self, group: int) -> None` | method | RAD:SCAN:GROUP | Write-only scan control; arguments/choices in SCAN.md. Acceptance is not scan completion. |
| `set_resume_enabled(self, enabled: bool) -> None` | method | RAD:SCAN:RESUMEOFF/RESUMEON | Write-only scan control; arguments/choices in SCAN.md. Acceptance is not scan completion. |
| `set_select_enabled(self, enabled: bool) -> None` | method | RAD:SCAN:SELECTOFF/SELECTON | Write-only scan control; arguments/choices in SCAN.md. Acceptance is not scan completion. |
| `start(self, mode: str) -> None` | method | RAD:SCAN:mode action | Write-only scan control; arguments/choices in SCAN.md. Acceptance is not scan completion. |
| `stop(self) -> None` | method | RAD:SCAN:STOP | Write-only scan control; arguments/choices in SCAN.md. Acceptance is not scan completion. |

## RadioOperations

Details/valid values: [OPERATIONS.md](OPERATIONS.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `RadioOperations(driver: CiviIc7300, selector: str = '') -> None`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `antenna_output_enabled: bool` | read/write | RAD:ANTOUTPUT | RAD:ANTOUTPUT[?], boolean. |
| `break_in: str` | read/write | RAD:BKIN | RAD:BKIN[?], choices: OFF, SEMI, FULL |
| `play_voice(self, slot: int) -> None` | method | RAD:VOICE | Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied. |
| `power_off(self) -> None` | method | RAD:POWER:OFF | Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied. |
| `power_on(self) -> None` | method | RAD:POWER:ON | Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied. |
| `send_cw(self, text: str) -> None` | method | RAD:CW:SEND | Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied. |
| `set_simulated_permissions(self, *, transmit: bool = False, power: bool = False, link: bool = False, max_transmit_seconds: float = 10.0) -> None` | method | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `speak(self, code: int) -> None` | method | RAD:SPEECH | Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied. |
| `start_transmit(self) -> None` | method | RAD:PTT ON | Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied. |
| `stop_cw(self) -> None` | method | RAD:CW:STOP | Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied. |
| `stop_transmit(self) -> None` | method | RAD:PTT OFF | Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied. |
| `stop_voice(self) -> None` | method | RAD:VOICE | Explicit guarded radio action. Valid values and stop/permission semantics are in OPERATIONS.md and BASIC.md; no hardware verification is implied. |
| `transmit_inhibited: bool` | read/write | RAD:TXINHIBIT | RAD:TXINHIBIT[?], boolean. |
| `tuner: str` | read/write | RAD:TUNER | RAD:TUNER[?], choices: OFF, ON, TUNE |
| `vox_enabled: bool` | read/write | RAD:VOX | RAD:VOX[?], boolean. |

## IviUtility

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `IviUtility()`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `driver_vendor getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `driver_version getter(self) -> str` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `error_query(self) -> civi_ic7300.errors.ErrorQueryResult \| None` | method | SYST:ERR? | Read/consume this client error queue explicitly, independently of the status option. |
| `error_query_all(self) -> tuple[civi_ic7300.errors.ErrorQueryResult, ...]` | method | SYST:ERR? | Read/consume this client error queue explicitly, independently of the status option. |
| `instrument_manufacturer getter(self) -> str` | read-only | *IDN? | Read gateway identity; the full record is distinct from radio firmware. |
| `instrument_model getter(self) -> str` | read-only | *IDN? | Read gateway identity; the full record is distinct from radio firmware. |
| `query_instrument_status_enabled getter(self) -> bool`<br>`query_instrument_status_enabled setter(self, enabled: bool) -> None` | read/write | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `raise_on_device_error(self) -> None` | method | SYST:ERR? | Read/consume this client error queue explicitly, independently of the status option. |
| `reset(self) -> None` | method | RAD:RESET | Select the documented receive baseline with a reset-specific timeout; no automatic rollback. |
| `simulation_enabled getter(self) -> bool` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `supported_instrument_models getter(self) -> tuple[str, ...]` | read-only | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |

## IviDirectIo

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `IviDirectIo()`.

| Member / prototype | Access | Direct SCPI | Usage (plus linked constraints) |
|---|---|---|---|
| `io_timeout_ms getter(self) -> int`<br>`io_timeout_ms setter(self, timeout_ms: int) -> None` | read/write | None (local metadata/view/configuration or record conversion) | Local operation; argument bounds and returned-view/value semantics are specified in the linked guide. |
| `read_bytes(self) -> bytes` | method | receive pending response; no command sent | Read one LF-framed response; synchronize separate raw write/read pairs externally. |
| `read_string(self) -> str` | method | receive pending response; no command sent | Read one LF-framed response; synchronize separate raw write/read pairs externally. |
| `write_bytes(self, data: bytes) -> None` | method | caller-supplied ASCII program | Write one LF-framed program; raw I/O never adds status queries. |
| `write_string(self, data: str) -> None` | method | caller-supplied ASCII program | Write one LF-framed program; raw I/O never adds status queries. |

## ErrorQueryResult

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `ErrorQueryResult(code: int, message: str) -> None`.

| Field | Type | Access |
|---|---|---|
| `code` | `<class 'int'>` | read-only |
| `message` | `<class 'str'>` | read-only |

## DeviceError

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `DeviceError(errors: tuple[civi_ic7300.errors.ErrorQueryResult, ...]) -> None`.

| Field | Type | Access |
|---|---|---|
| `errors` | `tuple[ErrorQueryResult, ...]` | Python attribute containing extracted device errors |

## ProtocolError

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `ProtocolError(*args) — standard Python exception constructor`.

## QueryError

Details/valid values: [API.md](API.md).
Evidence: implementation indexed; see EVIDENCE.md for scenario-level mock and dated hardware scope.

Constructor: `QueryError(*args) — standard Python exception constructor`.

## Type aliases

`MenuValue = bool | int | civi_ic7300.menus.AudioFilter | civi_ic7300.menus.Bandwidth | civi_ic7300.menus.RgbColor | civi_ic7300.controls.ScopeEdges | str | datetime.date | datetime.time | datetime.timedelta`.

## IVI Foundation notice

Content from the IVI specifications reproduced with permission from the IVI Foundation.

The IVI Foundation and its member companies make no warranty of any kind with regard to this material, including, but not limited to, the implied warranties of merchantability and fitness for a particular purpose. The IVI Foundation and its member companies shall not be liable for errors contained herein or for incidental or consequential damages in connection with the furnishing, performance, or use of this material.

Source: [IVI Driver Core 1.0, Copyright Notice](https://raw.githubusercontent.com/IviFoundation/IviDrivers/main/IviDriverCore/1.0/Spec/IviDriverCore.md#copyright-notice).

Including this notice does not assert IVI conformity or registration.
