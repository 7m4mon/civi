# Unified SCPI inventory (client 0.13.1)

Generated from the gateway catalog/parser inventory and typed client mappings.
A header is counted once; query/set directions are separate. Spelling aliases do not add features.

**339 extended + 11 base/special = 350 canonical headers.**
**350 mapped, 0 pending** in supported gateway directions.

This is software coverage, not radio verification or IVI conformity. Scope is the CIVI ASCII
gateway, not every IC-7300 function. Parser hashes in the JSON trigger re-review after changes.

## Reading the table

R means append ?, W means set/action. A missing direction is not implemented by the gateway.
Aliases list the documented short/full tokens independently; case is ignored and leading colon
is accepted. No arbitrary intermediate abbreviation is promised. Compound/relative SCPI syntax
is a gateway parser feature, not a separate typed command. Simulation supports typed APIs,
not every raw alias or compound form.

Core commands now have dedicated IDN/clear/completion/firmware/PTT APIs. *OPC? is also used
internally after setters; SYST:ERR? follows STATUS.md. PTT start requires explicit gateway
transmit permission and ownership; PTT OFF attempts to stop CIVI-owned paths.

| Canonical header | Source | Gateway | Typed | API | Accepted spellings | Scope / notes |
|---|---|---|---|---|---|---|
| `*IDN` | base/special | R | R | `ivi_utility.instrument_manufacturer/model`, `ivi_utility.identification` | `*IDN` | Constructor and identity properties |
| `*CLS` | base/special | W | W | `ivi_utility.clear_status()` | `*CLS` | Explicit queue clear only; not quarantine recovery |
| `*OPC` | base/special | R | R | `ivi_utility.wait_for_complete()` | `*OPC` | Setter completion and explicit wait; does not prove success |
| `SYST:ERR` | base/special | R | R | `ivi_utility.error_query/all/raise_on_device_error()` | `SYST:ERR`, `SYST:ERROR`, `SYSTEM:ERR`, `SYSTEM:ERROR` | Explicit/error-policy queue queries |
| `SENS:FREQ` | base/special | RW | RW | `radio.frequency_hz` | `SENS:FREQ`, `SENS:FREQUENCY`, `SENSE:FREQ`, `SENSE:FREQUENCY` | Selected VFO/memory working frequency |
| `RAD:MODE` | base/special | RW | RW | `radio.mode` | `RAD:MODE`, `RADIO:MODE` | Basic mode; use VfoMode for DATA/filter |
| `READ:SMET` | base/special | R | R | `meters.smeter_raw`, `radio.smeter_raw` | `READ:SMET`, `READ:SMETER` | Uncalibrated raw meter |
| `RAD:PTT` | base/special | RW | RW | `radio.transmitting`, `operations.start_transmit() / stop_transmit()` | `RAD:PTT`, `RADIO:PTT` | Explicit start/stop; gateway guards and ownership apply |
| `RAD:FIRM` | base/special | R | R | `radio.firmware_revision` | `RAD:FIRM`, `RAD:FIRMWARE`, `RADIO:FIRM`, `RADIO:FIRMWARE` | Manual metadata or Unknown; not CI-V firmware auto-read |
| `RAD:RESET` | base/special | W | W | `ivi_utility.reset()` | `RAD:RESET`, `RADIO:RESET` | Receive baseline; distinct from *RST/Partial/LAN RESET |
| `RAD:SCOPE:WAVE` | base/special | R | R | `scope.read_sweep()` | `RAD:SCOPE:WAVE`, `RADIO:SCOPE:WAVE` | Latest complete gateway sweep |
| `RAD:AFGAIN` | extended | RW | RW | `gains.af_raw` | `RAD:AFGAIN`, `RADIO:AFGAIN` | AF gain |
| `RAD:RFGAIN` | extended | RW | RW | `gains.rf_raw` | `RAD:RFGAIN`, `RADIO:RFGAIN` | RF gain |
| `RAD:SQL` | extended | RW | RW | `gains.squelch_raw` | `RAD:SQL`, `RADIO:SQL` | Squelch level |
| `RAD:NR:LEVEL` | extended | RW | RW | `gains.noise_reduction_raw` | `RAD:NR:LEVEL`, `RADIO:NR:LEVEL` | Noise reduction level |
| `RAD:PBT:INNER` | extended | RW | RW | `gains.pbt_inner_raw` | `RAD:PBT:INNER`, `RADIO:PBT:INNER` | Inner PBT |
| `RAD:PBT:OUTER` | extended | RW | RW | `gains.pbt_outer_raw` | `RAD:PBT:OUTER`, `RADIO:PBT:OUTER` | Outer PBT |
| `RAD:CW:PITCH` | extended | RW | RW | `gains.cw_pitch_raw` | `RAD:CW:PITCH`, `RADIO:CW:PITCH` | CW pitch code |
| `RAD:POWER` | extended | RW | RW | `gains.rf_power_raw` | `RAD:POWER`, `RADIO:POWER` | RF power code |
| `RAD:MICGAIN` | extended | RW | RW | `gains.microphone_raw` | `RAD:MICGAIN`, `RADIO:MICGAIN` | Microphone gain |
| `RAD:CW:SPEED` | extended | RW | RW | `gains.cw_speed_raw` | `RAD:CW:SPEED`, `RADIO:CW:SPEED` | Key speed code |
| `RAD:NOTCH:LEVEL` | extended | RW | RW | `gains.notch_raw` | `RAD:NOTCH:LEVEL`, `RADIO:NOTCH:LEVEL` | Notch position |
| `RAD:COMP:LEVEL` | extended | RW | RW | `gains.compression_raw` | `RAD:COMP:LEVEL`, `RADIO:COMP:LEVEL` | Compression level |
| `RAD:CW:DELAY` | extended | RW | RW | `gains.cw_delay_raw` | `RAD:CW:DELAY`, `RADIO:CW:DELAY` | Break-in delay code |
| `RAD:NB:LEVEL` | extended | RW | RW | `gains.noise_blanker_raw` | `RAD:NB:LEVEL`, `RADIO:NB:LEVEL` | Noise blanker level |
| `RAD:MONITOR:LEVEL` | extended | RW | RW | `gains.monitor_raw` | `RAD:MONITOR:LEVEL`, `RADIO:MONITOR:LEVEL` | Monitor gain |
| `RAD:VOX:GAIN` | extended | RW | RW | `gains.vox_raw` | `RAD:VOX:GAIN`, `RADIO:VOX:GAIN` | VOX gain |
| `RAD:VOX:ANTIGAIN` | extended | RW | RW | `gains.anti_vox_raw` | `RAD:VOX:ANTIGAIN`, `RADIO:VOX:ANTIGAIN` | Anti-VOX gain |
| `RAD:BACKLIGHT` | extended | RW | RW | `gains.backlight_raw` | `RAD:BACKLIGHT`, `RADIO:BACKLIGHT` | LCD brightness |
| `READ:SQL` | extended | R | R | `meters.squelch_open` | `READ:SQL` | SQL status |
| `READ:SQL:ALL` | extended | R | R | `meters.all_squelches_open` | `READ:SQL:ALL` | SQL:ALL status |
| `READ:OVF` | extended | R | R | `meters.overflow` | `READ:OVF` | OVF status |
| `READ:POWER` | extended | R | R | `meters.power_raw` | `READ:POWER` | POWER meter (raw, uncalibrated) |
| `READ:SWR` | extended | R | R | `meters.swr_raw` | `READ:SWR` | SWR meter (raw, uncalibrated) |
| `READ:ALC` | extended | R | R | `meters.alc_raw` | `READ:ALC` | ALC meter (raw, uncalibrated) |
| `READ:COMP` | extended | R | R | `meters.compression_raw` | `READ:COMP` | COMP meter (raw, uncalibrated) |
| `READ:VOLTAGE` | extended | R | R | `meters.voltage_raw` | `READ:VOLTAGE` | VOLTAGE meter (raw, uncalibrated) |
| `READ:CURRENT` | extended | R | R | `meters.current_raw` | `READ:CURRENT` | CURRENT meter (raw, uncalibrated) |
| `RAD:NB` | extended | RW | RW | `radio.noise_blanker_enabled` | `RAD:NB`, `RADIO:NB` | NB enable |
| `RAD:NR` | extended | RW | RW | `radio.noise_reduction_enabled` | `RAD:NR`, `RADIO:NR` | NR enable |
| `RAD:ANOTCH` | extended | RW | RW | `radio.automatic_notch_enabled` | `RAD:ANOTCH`, `RADIO:ANOTCH` | ANOTCH enable |
| `RAD:TONE` | extended | RW | RW | `radio.tone_enabled` | `RAD:TONE`, `RADIO:TONE` | TONE enable |
| `RAD:TSQL` | extended | RW | RW | `radio.tone_squelch_enabled` | `RAD:TSQL`, `RADIO:TSQL` | TSQL enable |
| `RAD:COMP` | extended | RW | RW | `radio.compressor_enabled` | `RAD:COMP`, `RADIO:COMP` | COMP enable |
| `RAD:MONITOR` | extended | RW | RW | `radio.monitor_enabled` | `RAD:MONITOR`, `RADIO:MONITOR` | MONITOR enable |
| `RAD:VOX` | extended | RW | RW | `operations.vox_enabled` | `RAD:VOX`, `RADIO:VOX` | VOX enable |
| `RAD:NOTCH` | extended | RW | RW | `radio.manual_notch_enabled` | `RAD:NOTCH`, `RADIO:NOTCH` | NOTCH enable |
| `RAD:TPF` | extended | RW | RW | `radio.twin_peak_filter_enabled` | `RAD:TPF`, `RADIO:TPF` | TPF enable |
| `RAD:LOCK` | extended | RW | RW | `radio.lock_enabled` | `RAD:LOCK`, `RADIO:LOCK` | LOCK enable |
| `RAD:IPPLUS` | extended | RW | RW | `radio.ip_plus_enabled` | `RAD:IPPLUS`, `RADIO:IPPLUS` | IPPLUS enable |
| `RAD:TXINHIBIT` | extended | RW | RW | `operations.transmit_inhibited` | `RAD:TXINHIBIT`, `RADIO:TXINHIBIT` | TXINHIBIT enable |
| `RAD:PREAMP` | extended | RW | RW | `radio.preamp` | `RAD:PREAMP`, `RADIO:PREAMP` | Preamplifier |
| `RAD:AGC` | extended | RW | RW | `radio.agc` | `RAD:AGC`, `RADIO:AGC` | AGC speed |
| `RAD:BKIN` | extended | RW | RW | `operations.break_in` | `RAD:BKIN`, `RADIO:BKIN` | CW break-in |
| `RAD:FILTER:SHAPE` | extended | RW | RW | `radio.filter_shape` | `RAD:FILTER:SHAPE`, `RADIO:FILTER:SHAPE` | DSP filter shape |
| `RAD:NOTCH:WIDTH` | extended | RW | RW | `radio.notch_width` | `RAD:NOTCH:WIDTH`, `RADIO:NOTCH:WIDTH` | Notch width |
| `RAD:TXBANDWIDTH` | extended | RW | RW | `radio.tx_bandwidth` | `RAD:TXBANDWIDTH`, `RADIO:TXBANDWIDTH` | SSB TX bandwidth |
| `RAD:ATT` | extended | RW | RW | `radio.attenuator_db` | `RAD:ATT`, `RADIO:ATT` | Attenuator code |
| `RAD:STEP` | extended | RW | RW | `radio.tuning_step_code` | `RAD:STEP`, `RADIO:STEP` | Tuning step code |
| `RAD:SPLIT` | extended | RW | RW | `radio.split_enabled` | `RAD:SPLIT`, `RADIO:SPLIT` | Split enable |
| `RAD:RIT:FREQ` | extended | RW | RW | `radio.rit_offset_hz` | `RAD:RIT:FREQ`, `RAD:RIT:FREQUENCY`, `RADIO:RIT:FREQ`, `RADIO:RIT:FREQUENCY` | RIT offset (Hz) |
| `RAD:RIT` | extended | RW | RW | `radio.rit_enabled` | `RAD:RIT`, `RADIO:RIT` | RIT enable |
| `RAD:XIT` | extended | RW | RW | `radio.xit_enabled` | `RAD:XIT`, `RADIO:XIT` | Delta TX enable |
| `RAD:TXFREQ` | extended | R | R | `radio.tx_frequency_hz` | `RAD:TXFREQ`, `RADIO:TXFREQ` | Transmit frequency |
| `RAD:XFC` | extended | RW | RW | `radio.frequency_check_enabled` | `RAD:XFC`, `RADIO:XFC` | Transmit frequency check |
| `RAD:ANTOUTPUT` | extended | RW | RW | `operations.antenna_output_enabled` | `RAD:ANTOUTPUT`, `RADIO:ANTOUTPUT` | Antenna controller output |
| `RAD:TUNER` | extended | RW | RW | `operations.tuner` | `RAD:TUNER`, `RADIO:TUNER` | Antenna tuner (TUNE transmits) |
| `RAD:DATA` | extended | RW | RW | `radio.data_filter` | `RAD:DATA`, `RADIO:DATA` | DATA/filter bytes |
| `RAD:IPPLUS:ALT` | extended | RW | RW | `radio.ip_plus_alternate_enabled` | `RAD:IPPLUS:ALT`, `RADIO:IPPLUS:ALT` | IP+ alternate CI-V command |
| `RAD:FILTER:WIDTH` | extended | RW | RW | `radio.filter_width_code` | `RAD:FILTER:WIDTH`, `RADIO:FILTER:WIDTH` | Filter width index (mode dependent) |
| `RAD:AGC:TIME` | extended | RW | RW | `radio.agc_time_code` | `RAD:AGC:TIME`, `RADIO:AGC:TIME` | AGC time index (mode dependent) |
| `RAD:VFO:SELECT` | extended | W | W | `vfos.select()` | `RAD:VFO:SELECT`, `RADIO:VFO:SELECT` | Select VFO A/B |
| `RAD:VFO:ENABLE` | extended | W | W | `vfos.enable()` | `RAD:VFO:ENABLE`, `RADIO:VFO:ENABLE` | Enter VFO mode |
| `RAD:VFO:COPY` | extended | W | W | `vfos.copy_selected_to_other()` | `RAD:VFO:COPY`, `RADIO:VFO:COPY` | Copy selected VFO to the other VFO |
| `RAD:VFO:SWAP` | extended | W | W | `vfos.swap()` | `RAD:VFO:SWAP`, `RADIO:VFO:SWAP` | Swap VFO contents |
| `RAD:VFO:FREQ` | extended | RW | RW | `vfos[SELECTED/OTHER].frequency_hz` | `RAD:VFO:FREQ`, `RAD:VFO:FREQUENCY`, `RADIO:VFO:FREQ`, `RADIO:VFO:FREQUENCY` | Selected/other VFO frequency (Hz) |
| `RAD:VFO:MODE` | extended | RW | RW | `vfos[SELECTED/OTHER].mode` | `RAD:VFO:MODE`, `RADIO:VFO:MODE` | Selected/other VFO mode/DATA/filter bytes |
| `RAD:TONE:FREQ` | extended | RW | RW | `radio.repeater_tone_hz` | `RAD:TONE:FREQ`, `RAD:TONE:FREQUENCY`, `RADIO:TONE:FREQ`, `RADIO:TONE:FREQUENCY` | Repeater tone frequency (Hz) |
| `RAD:TSQL:FREQ` | extended | RW | RW | `radio.tone_squelch_hz` | `RAD:TSQL:FREQ`, `RAD:TSQL:FREQUENCY`, `RADIO:TSQL:FREQ`, `RADIO:TSQL:FREQUENCY` | Tone squelch frequency (Hz) |
| `RAD:SCAN:STOP` | extended | W | W | `scan.stop()` | `RAD:SCAN:STOP`, `RADIO:SCAN:STOP` | Scan STOP |
| `RAD:SCAN:PROGRAM` | extended | W | W | `scan.start(PROGRAM)` | `RAD:SCAN:PROGRAM`, `RADIO:SCAN:PROGRAM` | Scan PROGRAM |
| `RAD:SCAN:MEMORY` | extended | W | W | `scan.start(MEMORY)` | `RAD:SCAN:MEMORY`, `RADIO:SCAN:MEMORY` | Scan MEMORY |
| `RAD:SCAN:AUTO` | extended | W | W | `scan.start(AUTO)` | `RAD:SCAN:AUTO`, `RADIO:SCAN:AUTO` | Scan AUTO |
| `RAD:SCAN:DELTA` | extended | W | W | `scan.start(DELTA)` | `RAD:SCAN:DELTA`, `RADIO:SCAN:DELTA` | Scan DELTA |
| `RAD:SCAN:FINEPROGRAM` | extended | W | W | `scan.start(FINEPROGRAM)` | `RAD:SCAN:FINEPROGRAM`, `RADIO:SCAN:FINEPROGRAM` | Scan FINEPROGRAM |
| `RAD:SCAN:FINEDELTA` | extended | W | W | `scan.start(FINEDELTA)` | `RAD:SCAN:FINEDELTA`, `RADIO:SCAN:FINEDELTA` | Scan FINEDELTA |
| `RAD:SCAN:SELECTMEM` | extended | W | W | `scan.start(SELECTMEM)` | `RAD:SCAN:SELECTMEM`, `RADIO:SCAN:SELECTMEM` | Scan SELECTMEM |
| `RAD:SCAN:SPAN5K` | extended | W | W | `scan.set_delta_span_hz()` | `RAD:SCAN:SPAN5K`, `RADIO:SCAN:SPAN5K` | Scan SPAN5K |
| `RAD:SCAN:SPAN10K` | extended | W | W | `scan.set_delta_span_hz()` | `RAD:SCAN:SPAN10K`, `RADIO:SCAN:SPAN10K` | Scan SPAN10K |
| `RAD:SCAN:SPAN20K` | extended | W | W | `scan.set_delta_span_hz()` | `RAD:SCAN:SPAN20K`, `RADIO:SCAN:SPAN20K` | Scan SPAN20K |
| `RAD:SCAN:SPAN50K` | extended | W | W | `scan.set_delta_span_hz()` | `RAD:SCAN:SPAN50K`, `RADIO:SCAN:SPAN50K` | Scan SPAN50K |
| `RAD:SCAN:SPAN100K` | extended | W | W | `scan.set_delta_span_hz()` | `RAD:SCAN:SPAN100K`, `RADIO:SCAN:SPAN100K` | Scan SPAN100K |
| `RAD:SCAN:SPAN500K` | extended | W | W | `scan.set_delta_span_hz()` | `RAD:SCAN:SPAN500K`, `RADIO:SCAN:SPAN500K` | Scan SPAN500K |
| `RAD:SCAN:SPAN1M` | extended | W | W | `scan.set_delta_span_hz()` | `RAD:SCAN:SPAN1M`, `RADIO:SCAN:SPAN1M` | Scan SPAN1M |
| `RAD:SCAN:SELECTOFF` | extended | W | W | `scan.set_select_enabled()` | `RAD:SCAN:SELECTOFF`, `RADIO:SCAN:SELECTOFF` | Scan SELECTOFF |
| `RAD:SCAN:SELECTON` | extended | W | W | `scan.set_select_enabled()` | `RAD:SCAN:SELECTON`, `RADIO:SCAN:SELECTON` | Scan SELECTON |
| `RAD:SCAN:RESUMEOFF` | extended | W | W | `scan.set_resume_enabled()` | `RAD:SCAN:RESUMEOFF`, `RADIO:SCAN:RESUMEOFF` | Scan RESUMEOFF |
| `RAD:SCAN:RESUMEON` | extended | W | W | `scan.set_resume_enabled()` | `RAD:SCAN:RESUMEON`, `RADIO:SCAN:RESUMEON` | Scan RESUMEON |
| `RAD:SCAN:SELECT` | extended | W | W | `scan.assign_selected_memory_group()` | `RAD:SCAN:SELECT`, `RADIO:SCAN:SELECT` | Assign memory select group |
| `RAD:SCAN:GROUP` | extended | W | W | `scan.set_memory_group()` | `RAD:SCAN:GROUP`, `RADIO:SCAN:GROUP` | Select memory scan group |
| `RAD:MEM:SELECT` | extended | W | W | `memories.select()` | `RAD:MEM:SELECT`, `RADIO:MEM:SELECT` | Select memory channel (100=P1,101=P2) |
| `RAD:MEM:ENABLE` | extended | W | W | `memories.enable()` | `RAD:MEM:ENABLE`, `RADIO:MEM:ENABLE` | Enter memory mode |
| `RAD:MEM:WRITE` | extended | W | W | `memories.store_current_in_selected()` | `RAD:MEM:WRITE`, `RADIO:MEM:WRITE` | Write selected memory |
| `RAD:MEM:TOVFO` | extended | W | W | `memories.copy_selected_to_vfo()` | `RAD:MEM:TOVFO`, `RADIO:MEM:TOVFO` | Copy memory to VFO |
| `RAD:MEM:CLEAR` | extended | W | W | `memories.clear_selected()` | `RAD:MEM:CLEAR`, `RADIO:MEM:CLEAR` | Clear selected memory |
| `RAD:MEM:CONTENT` | extended | RW | RW | `memories[number].record / clear()` | `RAD:MEM:CONTENT`, `RADIO:MEM:CONTENT` | Memory record hex (channel selector omitted from payload) |
| `RAD:BAND:STACK` | extended | RW | RW | `band_stacks[band, slot].settings`, `band_stacks.bands[band].slots[slot].settings (shorthand: band_stacks[band].slots[slot])` | `RAD:BAND:STACK`, `RADIO:BAND:STACK` | Band stack record (band*100+slot selector) |
| `RAD:KEYER:TEXT` | extended | RW | RW | `keyers[number].text` | `RAD:KEYER:TEXT`, `RADIO:KEYER:TEXT` | Keyer memory text |
| `RAD:CW:SEND` | extended | W | W | `operations.send_cw()` | `RAD:CW:SEND`, `RADIO:CW:SEND` | Send CW text (up to 30 characters) |
| `RAD:CW:STOP` | extended | W | W | `operations.stop_cw()` | `RAD:CW:STOP`, `RADIO:CW:STOP` | Stop CI-V CW output |
| `RAD:VOICE` | extended | W | W | `operations.play_voice() / stop_voice()` | `RAD:VOICE`, `RADIO:VOICE` | Play voice memory; STOP or 1-8 |
| `RAD:SPEECH` | extended | W | W | `operations.speak()` | `RAD:SPEECH`, `RADIO:SPEECH` | Announce S/frequency/mode |
| `RAD:POWER:OFF` | extended | W | W | `operations.power_off()` | `RAD:POWER:OFF`, `RADIO:POWER:OFF` | Power off radio |
| `RAD:POWER:ON` | extended | W | W | `operations.power_on()` | `RAD:POWER:ON`, `RADIO:POWER:ON` | Power on radio (wake preamble) |
| `RAD:BAND:EDGES` | extended | R | R | `bands.default_edges` | `RAD:BAND:EDGES`, `RADIO:BAND:EDGES` | Read default band edges (validated BCD pair) |
| `RAD:TXBAND:COUNT` | extended | R | R | `bands.factory_count` | `RAD:TXBAND:COUNT`, `RADIO:TXBAND:COUNT` | Number of factory transmit bands |
| `RAD:TXBAND:READ` | extended | R | R | `bands.read_factory()` | `RAD:TXBAND:READ`, `RADIO:TXBAND:READ` | Read transmit band edge |
| `RAD:TXBAND:USERCOUNT` | extended | R | R | `bands.user_count` | `RAD:TXBAND:USERCOUNT`, `RADIO:TXBAND:USERCOUNT` | Number of user transmit bands |
| `RAD:TXBAND:USER` | extended | RW | RW | `bands.read_user() / write_user() / write_and_read_user()` | `RAD:TXBAND:USER`, `RADIO:TXBAND:USER` | User transmit band edge (FF on read means unprogrammed) |
| `RAD:SCOPE:ENABLE` | extended | RW | RW | `scope.enabled` | `RAD:SCOPE:ENABLE`, `RADIO:SCOPE:ENABLE` | Scope ENABLE |
| `RAD:SCOPE:STREAM` | extended | RW | RW | `scope.streaming_enabled` | `RAD:SCOPE:STREAM`, `RADIO:SCOPE:STREAM` | Scope STREAM |
| `RAD:SCOPE:DISPLAY` | extended | RW | RW | `scope.display_code` | `RAD:SCOPE:DISPLAY`, `RADIO:SCOPE:DISPLAY` | Scope DISPLAY |
| `RAD:SCOPE:DUAL` | extended | RW | RW | `scope.dual_scope_code` | `RAD:SCOPE:DUAL`, `RADIO:SCOPE:DUAL` | Scope DUAL |
| `RAD:SCOPE:MODE` | extended | RW | RW | `scope.mode_code` | `RAD:SCOPE:MODE`, `RADIO:SCOPE:MODE` | Scope MODE |
| `RAD:SCOPE:SPAN` | extended | RW | RW | `scope.span_hz` | `RAD:SCOPE:SPAN`, `RADIO:SCOPE:SPAN` | Scope SPAN |
| `RAD:SCOPE:EDGE` | extended | RW | RW | `scope.edge_number` | `RAD:SCOPE:EDGE`, `RADIO:SCOPE:EDGE` | Scope EDGE |
| `RAD:SCOPE:HOLD` | extended | RW | RW | `scope.hold_enabled` | `RAD:SCOPE:HOLD`, `RADIO:SCOPE:HOLD` | Scope HOLD |
| `RAD:SCOPE:REFERENCE` | extended | RW | RW | `scope.reference_db` | `RAD:SCOPE:REFERENCE`, `RADIO:SCOPE:REFERENCE` | Scope REFERENCE |
| `RAD:SCOPE:SPEED` | extended | RW | RW | `scope.speed_code` | `RAD:SCOPE:SPEED`, `RADIO:SCOPE:SPEED` | Scope SPEED |
| `RAD:SCOPE:TXDISPLAY` | extended | RW | RW | `scope.tx_display_enabled` | `RAD:SCOPE:TXDISPLAY`, `RADIO:SCOPE:TXDISPLAY` | Scope TXDISPLAY |
| `RAD:SCOPE:CENTER` | extended | RW | RW | `scope.center_mode_code` | `RAD:SCOPE:CENTER`, `RADIO:SCOPE:CENTER` | Scope CENTER |
| `RAD:SCOPE:VBW` | extended | RW | RW | `scope.vbw_enabled` | `RAD:SCOPE:VBW`, `RADIO:SCOPE:VBW` | Scope VBW |
| `RAD:SCOPE:MARKER` | extended | RW | RW | `scope.marker_enabled` | `RAD:SCOPE:MARKER`, `RADIO:SCOPE:MARKER` | Scope MARKER |
| `RAD:SCOPE:FIXEDGE` | extended | RW | RW | `scope.read_fixed_edges()`, `scope.write_fixed_edges()` | `RAD:SCOPE:FIXEDGE`, `RADIO:SCOPE:FIXEDGE` | Scope FIX edge (band*100+edge selector) |
| `RAD:MENU:0001` | extended | RW | RW | `menus[1].value` | `RAD:MENU:0001`, `RADIO:MENU:0001` | SSB RX HPF/LPF [0001] |
| `RAD:MENU:0002` | extended | RW | RW | `menus[2].value` | `RAD:MENU:0002`, `RADIO:MENU:0002` | SSB RX bass [0002] |
| `RAD:MENU:0003` | extended | RW | RW | `menus[3].value` | `RAD:MENU:0003`, `RADIO:MENU:0003` | SSB RX treble [0003] |
| `RAD:MENU:0004` | extended | RW | RW | `menus[4].value` | `RAD:MENU:0004`, `RADIO:MENU:0004` | AM RX HPF/LPF [0004] |
| `RAD:MENU:0005` | extended | RW | RW | `menus[5].value` | `RAD:MENU:0005`, `RADIO:MENU:0005` | AM RX bass [0005] |
| `RAD:MENU:0006` | extended | RW | RW | `menus[6].value` | `RAD:MENU:0006`, `RADIO:MENU:0006` | AM RX treble [0006] |
| `RAD:MENU:0007` | extended | RW | RW | `menus[7].value` | `RAD:MENU:0007`, `RADIO:MENU:0007` | FM RX HPF/LPF [0007] |
| `RAD:MENU:0008` | extended | RW | RW | `menus[8].value` | `RAD:MENU:0008`, `RADIO:MENU:0008` | FM RX bass [0008] |
| `RAD:MENU:0009` | extended | RW | RW | `menus[9].value` | `RAD:MENU:0009`, `RADIO:MENU:0009` | FM RX treble [0009] |
| `RAD:MENU:0010` | extended | RW | RW | `menus[10].value` | `RAD:MENU:0010`, `RADIO:MENU:0010` | CW RX HPF/LPF [0010] |
| `RAD:MENU:0011` | extended | RW | RW | `menus[11].value` | `RAD:MENU:0011`, `RADIO:MENU:0011` | RTTY RX HPF/LPF [0011] |
| `RAD:MENU:0012` | extended | RW | RW | `menus[12].value` | `RAD:MENU:0012`, `RADIO:MENU:0012` | Transmit audio EQ/bandwidth [0012] |
| `RAD:MENU:0013` | extended | RW | RW | `menus[13].value` | `RAD:MENU:0013`, `RADIO:MENU:0013` | Transmit audio EQ/bandwidth [0013] |
| `RAD:MENU:0014` | extended | RW | RW | `menus[14].value` | `RAD:MENU:0014`, `RADIO:MENU:0014` | Transmit audio EQ/bandwidth [0014] |
| `RAD:MENU:0015` | extended | RW | RW | `menus[15].value` | `RAD:MENU:0015`, `RADIO:MENU:0015` | Transmit audio EQ/bandwidth [0015] |
| `RAD:MENU:0016` | extended | RW | RW | `menus[16].value` | `RAD:MENU:0016`, `RADIO:MENU:0016` | Transmit audio EQ/bandwidth [0016] |
| `RAD:MENU:0017` | extended | RW | RW | `menus[17].value` | `RAD:MENU:0017`, `RADIO:MENU:0017` | Transmit audio EQ/bandwidth [0017] |
| `RAD:MENU:0018` | extended | RW | RW | `menus[18].value` | `RAD:MENU:0018`, `RADIO:MENU:0018` | Transmit audio EQ/bandwidth [0018] |
| `RAD:MENU:0019` | extended | RW | RW | `menus[19].value` | `RAD:MENU:0019`, `RADIO:MENU:0019` | Transmit audio EQ/bandwidth [0019] |
| `RAD:MENU:0020` | extended | RW | RW | `menus[20].value` | `RAD:MENU:0020`, `RADIO:MENU:0020` | Transmit audio EQ/bandwidth [0020] |
| `RAD:MENU:0021` | extended | RW | RW | `menus[21].value` | `RAD:MENU:0021`, `RADIO:MENU:0021` | Beep [0021] |
| `RAD:MENU:0022` | extended | RW | RW | `menus[22].value` | `RAD:MENU:0022`, `RADIO:MENU:0022` | Beep [0022] |
| `RAD:MENU:0023` | extended | RW | RW | `menus[23].value` | `RAD:MENU:0023`, `RADIO:MENU:0023` | Beep [0023] |
| `RAD:MENU:0024` | extended | RW | RW | `menus[24].value` | `RAD:MENU:0024`, `RADIO:MENU:0024` | Band edge beep/limit [0024] |
| `RAD:MENU:0025` | extended | RW | RW | `menus[25].value` | `RAD:MENU:0025`, `RADIO:MENU:0025` | RF/SQL control [0025] |
| `RAD:MENU:0026` | extended | RW | RW | `menus[26].value` | `RAD:MENU:0026`, `RADIO:MENU:0026` | Transmit delay [0026] |
| `RAD:MENU:0027` | extended | RW | RW | `menus[27].value` | `RAD:MENU:0027`, `RADIO:MENU:0027` | Transmit delay [0027] |
| `RAD:MENU:0029` | extended | RW | RW | `menus[29].value` | `RAD:MENU:0029`, `RADIO:MENU:0029` | CI-V TX timeout [0029] |
| `RAD:MENU:0030` | extended | RW | RW | `menus[30].value` | `RAD:MENU:0030`, `RADIO:MENU:0030` | Split/tuner setup [0030] |
| `RAD:MENU:0031` | extended | RW | RW | `menus[31].value` | `RAD:MENU:0031`, `RADIO:MENU:0031` | HF repeater split offset [0031] |
| `RAD:MENU:0032` | extended | RW | RW | `menus[32].value` | `RAD:MENU:0032`, `RADIO:MENU:0032` | 50 MHz repeater split offset [0032] |
| `RAD:MENU:0033` | extended | RW | RW | `menus[33].value` | `RAD:MENU:0033`, `RADIO:MENU:0033` | Split/tuner setup [0033] |
| `RAD:MENU:0034` | extended | RW | RW | `menus[34].value` | `RAD:MENU:0034`, `RADIO:MENU:0034` | Split/tuner setup [0034] |
| `RAD:MENU:0035` | extended | RW | RW | `menus[35].value` | `RAD:MENU:0035`, `RADIO:MENU:0035` | Split/tuner setup [0035] |
| `RAD:MENU:0036` | extended | RW | RW | `menus[36].value` | `RAD:MENU:0036`, `RADIO:MENU:0036` | RTTY signal [0036] |
| `RAD:MENU:0037` | extended | RW | RW | `menus[37].value` | `RAD:MENU:0037`, `RADIO:MENU:0037` | RTTY signal [0037] |
| `RAD:MENU:0038` | extended | RW | RW | `menus[38].value` | `RAD:MENU:0038`, `RADIO:MENU:0038` | RTTY signal [0038] |
| `RAD:MENU:0039` | extended | RW | RW | `menus[39].value` | `RAD:MENU:0039`, `RADIO:MENU:0039` | Speech/lock setup [0039] |
| `RAD:MENU:0040` | extended | RW | RW | `menus[40].value` | `RAD:MENU:0040`, `RADIO:MENU:0040` | Speech/lock setup [0040] |
| `RAD:MENU:0041` | extended | RW | RW | `menus[41].value` | `RAD:MENU:0041`, `RADIO:MENU:0041` | Speech/lock setup [0041] |
| `RAD:MENU:0042` | extended | RW | RW | `menus[42].value` | `RAD:MENU:0042`, `RADIO:MENU:0042` | Speech/lock setup [0042] |
| `RAD:MENU:0043` | extended | RW | RW | `menus[43].value` | `RAD:MENU:0043`, `RADIO:MENU:0043` | Speech/lock setup [0043] |
| `RAD:MENU:0044` | extended | RW | RW | `menus[44].value` | `RAD:MENU:0044`, `RADIO:MENU:0044` | Speech/lock setup [0044] |
| `RAD:MENU:0045` | extended | RW | RW | `menus[45].value` | `RAD:MENU:0045`, `RADIO:MENU:0045` | Speech/lock setup [0045] |
| `RAD:MENU:0046` | extended | RW | RW | `menus[46].value` | `RAD:MENU:0046`, `RADIO:MENU:0046` | Memo/dial/key behavior [0046] |
| `RAD:MENU:0047` | extended | RW | RW | `menus[47].value` | `RAD:MENU:0047`, `RADIO:MENU:0047` | Memo/dial/key behavior [0047] |
| `RAD:MENU:0048` | extended | RW | RW | `menus[48].value` | `RAD:MENU:0048`, `RADIO:MENU:0048` | Memo/dial/key behavior [0048] |
| `RAD:MENU:0049` | extended | RW | RW | `menus[49].value` | `RAD:MENU:0049`, `RADIO:MENU:0049` | Memo/dial/key behavior [0049] |
| `RAD:MENU:0050` | extended | RW | RW | `menus[50].value` | `RAD:MENU:0050`, `RADIO:MENU:0050` | Notch/CW behavior [0050] |
| `RAD:MENU:0051` | extended | RW | RW | `menus[51].value` | `RAD:MENU:0051`, `RADIO:MENU:0051` | Notch/CW behavior [0051] |
| `RAD:MENU:0052` | extended | RW | RW | `menus[52].value` | `RAD:MENU:0052`, `RADIO:MENU:0052` | Notch/CW behavior [0052] |
| `RAD:MENU:0053` | extended | RW | RW | `menus[53].value` | `RAD:MENU:0053`, `RADIO:MENU:0053` | Notch/CW behavior [0053] |
| `RAD:MENU:0054` | extended | RW | RW | `menus[54].value` | `RAD:MENU:0054`, `RADIO:MENU:0054` | Screenshot/keyboard [0054] |
| `RAD:MENU:0055` | extended | RW | RW | `menus[55].value` | `RAD:MENU:0055`, `RADIO:MENU:0055` | Screenshot/keyboard [0055] |
| `RAD:MENU:0056` | extended | RW | RW | `menus[56].value` | `RAD:MENU:0056`, `RADIO:MENU:0056` | Screenshot/keyboard [0056] |
| `RAD:MENU:0057` | extended | RW | RW | `menus[57].value` | `RAD:MENU:0057`, `RADIO:MENU:0057` | Reference calibration [0057] |
| `RAD:MENU:0058` | extended | RW | RW | `menus[58].value` | `RAD:MENU:0058`, `RADIO:MENU:0058` | Reference frequency adjustment [0058] |
| `RAD:MENU:0059` | extended | RW | RW | `menus[59].value` | `RAD:MENU:0059`, `RADIO:MENU:0059` | ACC/USB audio routing/levels [0059] |
| `RAD:MENU:0060` | extended | RW | RW | `menus[60].value` | `RAD:MENU:0060`, `RADIO:MENU:0060` | ACC/USB audio routing/levels [0060] |
| `RAD:MENU:0061` | extended | RW | RW | `menus[61].value` | `RAD:MENU:0061`, `RADIO:MENU:0061` | ACC/USB audio routing/levels [0061] |
| `RAD:MENU:0062` | extended | RW | RW | `menus[62].value` | `RAD:MENU:0062`, `RADIO:MENU:0062` | ACC/USB audio routing/levels [0062] |
| `RAD:MENU:0063` | extended | RW | RW | `menus[63].value` | `RAD:MENU:0063`, `RADIO:MENU:0063` | ACC/USB audio routing/levels [0063] |
| `RAD:MENU:0064` | extended | RW | RW | `menus[64].value` | `RAD:MENU:0064`, `RADIO:MENU:0064` | ACC/USB audio routing/levels [0064] |
| `RAD:MENU:0065` | extended | RW | RW | `menus[65].value` | `RAD:MENU:0065`, `RADIO:MENU:0065` | ACC/USB audio routing/levels [0065] |
| `RAD:MENU:0066` | extended | RW | RW | `menus[66].value` | `RAD:MENU:0066`, `RADIO:MENU:0066` | Modulation source [0066] |
| `RAD:MENU:0067` | extended | RW | RW | `menus[67].value` | `RAD:MENU:0067`, `RADIO:MENU:0067` | Modulation source [0067] |
| `RAD:MENU:0068` | extended | RW | RW | `menus[68].value` | `RAD:MENU:0068`, `RADIO:MENU:0068` | External memory keypad [0068] |
| `RAD:MENU:0069` | extended | RW | RW | `menus[69].value` | `RAD:MENU:0069`, `RADIO:MENU:0069` | External memory keypad [0069] |
| `RAD:MENU:0070` | extended | RW | RW | `menus[70].value` | `RAD:MENU:0070`, `RADIO:MENU:0070` | External memory keypad [0070] |
| `RAD:MENU:0071` | extended | RW | RW | `menus[71].value` | `RAD:MENU:0071`, `RADIO:MENU:0071` | CI-V transceive [0071] |
| `RAD:MENU:0072` | extended | RW | RW | `menus[72].value` | `RAD:MENU:0072`, `RADIO:MENU:0072` | USB-to-REMOTE transceive address [0072] |
| `RAD:MENU:0073` | extended | RW | RW | `menus[73].value` | `RAD:MENU:0073`, `RADIO:MENU:0073` | Antenna CI-V output [0073] |
| `RAD:MENU:0074` | extended | R | R | `menus[74].value` | `RAD:MENU:0074`, `RADIO:MENU:0074` | CI-V USB port mode (read only) [0074] |
| `RAD:MENU:0075` | extended | RW | RW | `menus[75].value` | `RAD:MENU:0075`, `RADIO:MENU:0075` | USB CI-V echo [0075] |
| `RAD:MENU:0076` | extended | RW | RW | `menus[76].value` | `RAD:MENU:0076`, `RADIO:MENU:0076` | USB serial function [0076] |
| `RAD:MENU:0077` | extended | RW | RW | `menus[77].value` | `RAD:MENU:0077`, `RADIO:MENU:0077` | RTTY serial baud code [0077] |
| `RAD:MENU:0078` | extended | RW | RW | `menus[78].value` | `RAD:MENU:0078`, `RADIO:MENU:0078` | USB SEND pin [0078] |
| `RAD:MENU:0079` | extended | RW | RW | `menus[79].value` | `RAD:MENU:0079`, `RADIO:MENU:0079` | USB CW keying pin [0079] |
| `RAD:MENU:0080` | extended | RW | RW | `menus[80].value` | `RAD:MENU:0080`, `RADIO:MENU:0080` | USB FSK pin [0080] |
| `RAD:MENU:0081` | extended | RW | RW | `menus[81].value` | `RAD:MENU:0081`, `RADIO:MENU:0081` | Display/UI [0081] |
| `RAD:MENU:0082` | extended | RW | RW | `menus[82].value` | `RAD:MENU:0082`, `RADIO:MENU:0082` | Display/UI [0082] |
| `RAD:MENU:0083` | extended | RW | RW | `menus[83].value` | `RAD:MENU:0083`, `RADIO:MENU:0083` | Display/UI [0083] |
| `RAD:MENU:0084` | extended | RW | RW | `menus[84].value` | `RAD:MENU:0084`, `RADIO:MENU:0084` | Display/UI [0084] |
| `RAD:MENU:0085` | extended | RW | RW | `menus[85].value` | `RAD:MENU:0085`, `RADIO:MENU:0085` | Display/UI [0085] |
| `RAD:MENU:0086` | extended | RW | RW | `menus[86].value` | `RAD:MENU:0086`, `RADIO:MENU:0086` | Display/UI [0086] |
| `RAD:MENU:0087` | extended | RW | RW | `menus[87].value` | `RAD:MENU:0087`, `RADIO:MENU:0087` | Display/UI [0087] |
| `RAD:MENU:0088` | extended | RW | RW | `menus[88].value` | `RAD:MENU:0088`, `RADIO:MENU:0088` | Display/UI [0088] |
| `RAD:MENU:0089` | extended | RW | RW | `menus[89].value` | `RAD:MENU:0089`, `RADIO:MENU:0089` | Display/UI [0089] |
| `RAD:MENU:0090` | extended | RW | RW | `menus[90].value` | `RAD:MENU:0090`, `RADIO:MENU:0090` | Display/UI [0090] |
| `RAD:MENU:0091` | extended | RW | RW | `menus[91].value` | `RAD:MENU:0091`, `RADIO:MENU:0091` | Opening screen text [0091] |
| `RAD:MENU:0092` | extended | RW | RW | `menus[92].value` | `RAD:MENU:0092`, `RADIO:MENU:0092` | Display/UI [0092] |
| `RAD:MENU:0093` | extended | RW | RW | `menus[93].value` | `RAD:MENU:0093`, `RADIO:MENU:0093` | Display/UI [0093] |
| `RAD:MENU:0094` | extended | RW | RW | `menus[94].value` | `RAD:MENU:0094`, `RADIO:MENU:0094` | Date [0094] |
| `RAD:MENU:0095` | extended | RW | RW | `menus[95].value` | `RAD:MENU:0095`, `RADIO:MENU:0095` | Time [0095] |
| `RAD:MENU:0096` | extended | RW | RW | `menus[96].value` | `RAD:MENU:0096`, `RADIO:MENU:0096` | UTC offset [0096] |
| `RAD:MENU:0097` | extended | RW | RW | `menus[97].value` | `RAD:MENU:0097`, `RADIO:MENU:0097` | Scope display [0097] |
| `RAD:MENU:0098` | extended | RW | RW | `menus[98].value` | `RAD:MENU:0098`, `RADIO:MENU:0098` | Scope display [0098] |
| `RAD:MENU:0099` | extended | RW | RW | `menus[99].value` | `RAD:MENU:0099`, `RADIO:MENU:0099` | Scope display [0099] |
| `RAD:MENU:0100` | extended | RW | RW | `menus[100].value` | `RAD:MENU:0100`, `RADIO:MENU:0100` | Scope display [0100] |
| `RAD:MENU:0101` | extended | RW | RW | `menus[101].value` | `RAD:MENU:0101`, `RADIO:MENU:0101` | Scope display [0101] |
| `RAD:MENU:0102` | extended | RW | RW | `menus[102].value` | `RAD:MENU:0102`, `RADIO:MENU:0102` | Scope display [0102] |
| `RAD:MENU:0103` | extended | RW | RW | `menus[103].value` | `RAD:MENU:0103`, `RADIO:MENU:0103` | Scope display [0103] |
| `RAD:MENU:0104` | extended | RW | RW | `menus[104].value` | `RAD:MENU:0104`, `RADIO:MENU:0104` | Scope display [0104] |
| `RAD:MENU:0105` | extended | RW | RW | `menus[105].value` | `RAD:MENU:0105`, `RADIO:MENU:0105` | Scope display [0105] |
| `RAD:MENU:0106` | extended | RW | RW | `menus[106].value` | `RAD:MENU:0106`, `RADIO:MENU:0106` | Scope display [0106] |
| `RAD:MENU:0107` | extended | RW | RW | `menus[107].value` | `RAD:MENU:0107`, `RADIO:MENU:0107` | Scope display [0107] |
| `RAD:MENU:0108` | extended | RW | RW | `menus[108].value` | `RAD:MENU:0108`, `RADIO:MENU:0108` | Scope display [0108] |
| `RAD:MENU:0109` | extended | RW | RW | `menus[109].value` | `RAD:MENU:0109`, `RADIO:MENU:0109` | Scope display [0109] |
| `RAD:MENU:0110` | extended | RW | RW | `menus[110].value` | `RAD:MENU:0110`, `RADIO:MENU:0110` | Scope display [0110] |
| `RAD:MENU:0111` | extended | RW | RW | `menus[111].value` | `RAD:MENU:0111`, `RADIO:MENU:0111` | Scope display [0111] |
| `RAD:MENU:0112` | extended | RW | RW | `menus[112].value` | `RAD:MENU:0112`, `RADIO:MENU:0112` | Scope band 1 edge 1 (0.03-1.6 MHz) [0112] |
| `RAD:MENU:0113` | extended | RW | RW | `menus[113].value` | `RAD:MENU:0113`, `RADIO:MENU:0113` | Scope band 1 edge 2 (0.03-1.6 MHz) [0113] |
| `RAD:MENU:0114` | extended | RW | RW | `menus[114].value` | `RAD:MENU:0114`, `RADIO:MENU:0114` | Scope band 1 edge 3 (0.03-1.6 MHz) [0114] |
| `RAD:MENU:0115` | extended | RW | RW | `menus[115].value` | `RAD:MENU:0115`, `RADIO:MENU:0115` | Scope band 2 edge 1 (1.6-2 MHz) [0115] |
| `RAD:MENU:0116` | extended | RW | RW | `menus[116].value` | `RAD:MENU:0116`, `RADIO:MENU:0116` | Scope band 2 edge 2 (1.6-2 MHz) [0116] |
| `RAD:MENU:0117` | extended | RW | RW | `menus[117].value` | `RAD:MENU:0117`, `RADIO:MENU:0117` | Scope band 2 edge 3 (1.6-2 MHz) [0117] |
| `RAD:MENU:0118` | extended | RW | RW | `menus[118].value` | `RAD:MENU:0118`, `RADIO:MENU:0118` | Scope band 3 edge 1 (2-6 MHz) [0118] |
| `RAD:MENU:0119` | extended | RW | RW | `menus[119].value` | `RAD:MENU:0119`, `RADIO:MENU:0119` | Scope band 3 edge 2 (2-6 MHz) [0119] |
| `RAD:MENU:0120` | extended | RW | RW | `menus[120].value` | `RAD:MENU:0120`, `RADIO:MENU:0120` | Scope band 3 edge 3 (2-6 MHz) [0120] |
| `RAD:MENU:0121` | extended | RW | RW | `menus[121].value` | `RAD:MENU:0121`, `RADIO:MENU:0121` | Scope band 4 edge 1 (6-8 MHz) [0121] |
| `RAD:MENU:0122` | extended | RW | RW | `menus[122].value` | `RAD:MENU:0122`, `RADIO:MENU:0122` | Scope band 4 edge 2 (6-8 MHz) [0122] |
| `RAD:MENU:0123` | extended | RW | RW | `menus[123].value` | `RAD:MENU:0123`, `RADIO:MENU:0123` | Scope band 4 edge 3 (6-8 MHz) [0123] |
| `RAD:MENU:0124` | extended | RW | RW | `menus[124].value` | `RAD:MENU:0124`, `RADIO:MENU:0124` | Scope band 5 edge 1 (8-11 MHz) [0124] |
| `RAD:MENU:0125` | extended | RW | RW | `menus[125].value` | `RAD:MENU:0125`, `RADIO:MENU:0125` | Scope band 5 edge 2 (8-11 MHz) [0125] |
| `RAD:MENU:0126` | extended | RW | RW | `menus[126].value` | `RAD:MENU:0126`, `RADIO:MENU:0126` | Scope band 5 edge 3 (8-11 MHz) [0126] |
| `RAD:MENU:0127` | extended | RW | RW | `menus[127].value` | `RAD:MENU:0127`, `RADIO:MENU:0127` | Scope band 6 edge 1 (11-15 MHz) [0127] |
| `RAD:MENU:0128` | extended | RW | RW | `menus[128].value` | `RAD:MENU:0128`, `RADIO:MENU:0128` | Scope band 6 edge 2 (11-15 MHz) [0128] |
| `RAD:MENU:0129` | extended | RW | RW | `menus[129].value` | `RAD:MENU:0129`, `RADIO:MENU:0129` | Scope band 6 edge 3 (11-15 MHz) [0129] |
| `RAD:MENU:0130` | extended | RW | RW | `menus[130].value` | `RAD:MENU:0130`, `RADIO:MENU:0130` | Scope band 7 edge 1 (15-20 MHz) [0130] |
| `RAD:MENU:0131` | extended | RW | RW | `menus[131].value` | `RAD:MENU:0131`, `RADIO:MENU:0131` | Scope band 7 edge 2 (15-20 MHz) [0131] |
| `RAD:MENU:0132` | extended | RW | RW | `menus[132].value` | `RAD:MENU:0132`, `RADIO:MENU:0132` | Scope band 7 edge 3 (15-20 MHz) [0132] |
| `RAD:MENU:0133` | extended | RW | RW | `menus[133].value` | `RAD:MENU:0133`, `RADIO:MENU:0133` | Scope band 8 edge 1 (20-22 MHz) [0133] |
| `RAD:MENU:0134` | extended | RW | RW | `menus[134].value` | `RAD:MENU:0134`, `RADIO:MENU:0134` | Scope band 8 edge 2 (20-22 MHz) [0134] |
| `RAD:MENU:0135` | extended | RW | RW | `menus[135].value` | `RAD:MENU:0135`, `RADIO:MENU:0135` | Scope band 8 edge 3 (20-22 MHz) [0135] |
| `RAD:MENU:0136` | extended | RW | RW | `menus[136].value` | `RAD:MENU:0136`, `RADIO:MENU:0136` | Scope band 9 edge 1 (22-26 MHz) [0136] |
| `RAD:MENU:0137` | extended | RW | RW | `menus[137].value` | `RAD:MENU:0137`, `RADIO:MENU:0137` | Scope band 9 edge 2 (22-26 MHz) [0137] |
| `RAD:MENU:0138` | extended | RW | RW | `menus[138].value` | `RAD:MENU:0138`, `RADIO:MENU:0138` | Scope band 9 edge 3 (22-26 MHz) [0138] |
| `RAD:MENU:0139` | extended | RW | RW | `menus[139].value` | `RAD:MENU:0139`, `RADIO:MENU:0139` | Scope band 10 edge 1 (26-30 MHz) [0139] |
| `RAD:MENU:0140` | extended | RW | RW | `menus[140].value` | `RAD:MENU:0140`, `RADIO:MENU:0140` | Scope band 10 edge 2 (26-30 MHz) [0140] |
| `RAD:MENU:0141` | extended | RW | RW | `menus[141].value` | `RAD:MENU:0141`, `RADIO:MENU:0141` | Scope band 10 edge 3 (26-30 MHz) [0141] |
| `RAD:MENU:0142` | extended | RW | RW | `menus[142].value` | `RAD:MENU:0142`, `RADIO:MENU:0142` | Scope band 11 edge 1 (30-45 MHz) [0142] |
| `RAD:MENU:0143` | extended | RW | RW | `menus[143].value` | `RAD:MENU:0143`, `RADIO:MENU:0143` | Scope band 11 edge 2 (30-45 MHz) [0143] |
| `RAD:MENU:0144` | extended | RW | RW | `menus[144].value` | `RAD:MENU:0144`, `RADIO:MENU:0144` | Scope band 11 edge 3 (30-45 MHz) [0144] |
| `RAD:MENU:0145` | extended | RW | RW | `menus[145].value` | `RAD:MENU:0145`, `RADIO:MENU:0145` | Scope band 12 edge 1 (45-60 MHz) [0145] |
| `RAD:MENU:0146` | extended | RW | RW | `menus[146].value` | `RAD:MENU:0146`, `RADIO:MENU:0146` | Scope band 12 edge 2 (45-60 MHz) [0146] |
| `RAD:MENU:0147` | extended | RW | RW | `menus[147].value` | `RAD:MENU:0147`, `RADIO:MENU:0147` | Scope band 12 edge 3 (45-60 MHz) [0147] |
| `RAD:MENU:0148` | extended | RW | RW | `menus[148].value` | `RAD:MENU:0148`, `RADIO:MENU:0148` | Scope band 13 edge 1 (60-74.8 MHz) [0148] |
| `RAD:MENU:0149` | extended | RW | RW | `menus[149].value` | `RAD:MENU:0149`, `RADIO:MENU:0149` | Scope band 13 edge 2 (60-74.8 MHz) [0149] |
| `RAD:MENU:0150` | extended | RW | RW | `menus[150].value` | `RAD:MENU:0150`, `RADIO:MENU:0150` | Scope band 13 edge 3 (60-74.8 MHz) [0150] |
| `RAD:MENU:0151` | extended | RW | RW | `menus[151].value` | `RAD:MENU:0151`, `RADIO:MENU:0151` | Audio scope display [0151] |
| `RAD:MENU:0152` | extended | RW | RW | `menus[152].value` | `RAD:MENU:0152`, `RADIO:MENU:0152` | Audio scope display [0152] |
| `RAD:MENU:0153` | extended | RW | RW | `menus[153].value` | `RAD:MENU:0153`, `RADIO:MENU:0153` | Audio scope display [0153] |
| `RAD:MENU:0154` | extended | RW | RW | `menus[154].value` | `RAD:MENU:0154`, `RADIO:MENU:0154` | Audio scope display [0154] |
| `RAD:MENU:0155` | extended | RW | RW | `menus[155].value` | `RAD:MENU:0155`, `RADIO:MENU:0155` | CW contest counter [0155] |
| `RAD:MENU:0156` | extended | RW | RW | `menus[156].value` | `RAD:MENU:0156`, `RADIO:MENU:0156` | Counter trigger memory [0156] |
| `RAD:MENU:0157` | extended | RW | RW | `menus[157].value` | `RAD:MENU:0157`, `RADIO:MENU:0157` | Contest counter [0157] |
| `RAD:MENU:0158` | extended | RW | RW | `menus[158].value` | `RAD:MENU:0158`, `RADIO:MENU:0158` | CW sidetone/keyer [0158] |
| `RAD:MENU:0159` | extended | RW | RW | `menus[159].value` | `RAD:MENU:0159`, `RADIO:MENU:0159` | CW sidetone/keyer [0159] |
| `RAD:MENU:0160` | extended | RW | RW | `menus[160].value` | `RAD:MENU:0160`, `RADIO:MENU:0160` | Keyer repeat seconds [0160] |
| `RAD:MENU:0161` | extended | RW | RW | `menus[161].value` | `RAD:MENU:0161`, `RADIO:MENU:0161` | Keyer dot/dash weight [0161] |
| `RAD:MENU:0162` | extended | RW | RW | `menus[162].value` | `RAD:MENU:0162`, `RADIO:MENU:0162` | CW sidetone/keyer [0162] |
| `RAD:MENU:0163` | extended | RW | RW | `menus[163].value` | `RAD:MENU:0163`, `RADIO:MENU:0163` | CW sidetone/keyer [0163] |
| `RAD:MENU:0164` | extended | RW | RW | `menus[164].value` | `RAD:MENU:0164`, `RADIO:MENU:0164` | CW sidetone/keyer [0164] |
| `RAD:MENU:0165` | extended | RW | RW | `menus[165].value` | `RAD:MENU:0165`, `RADIO:MENU:0165` | CW sidetone/keyer [0165] |
| `RAD:MENU:0166` | extended | RW | RW | `menus[166].value` | `RAD:MENU:0166`, `RADIO:MENU:0166` | RTTY decoder/log [0166] |
| `RAD:MENU:0167` | extended | RW | RW | `menus[167].value` | `RAD:MENU:0167`, `RADIO:MENU:0167` | RTTY decoder/log [0167] |
| `RAD:MENU:0168` | extended | RW | RW | `menus[168].value` | `RAD:MENU:0168`, `RADIO:MENU:0168` | RTTY decoder/log [0168] |
| `RAD:MENU:0169` | extended | RW | RW | `menus[169].value` | `RAD:MENU:0169`, `RADIO:MENU:0169` | RTTY decoder/log [0169] |
| `RAD:MENU:0170` | extended | RW | RW | `menus[170].value` | `RAD:MENU:0170`, `RADIO:MENU:0170` | RTTY decoder/log [0170] |
| `RAD:MENU:0171` | extended | RW | RW | `menus[171].value` | `RAD:MENU:0171`, `RADIO:MENU:0171` | RTTY decoder/log [0171] |
| `RAD:MENU:0172` | extended | RW | RW | `menus[172].value` | `RAD:MENU:0172`, `RADIO:MENU:0172` | RTTY decoder/log [0172] |
| `RAD:MENU:0173` | extended | RW | RW | `menus[173].value` | `RAD:MENU:0173`, `RADIO:MENU:0173` | RTTY decoder/log [0173] |
| `RAD:MENU:0174` | extended | RW | RW | `menus[174].value` | `RAD:MENU:0174`, `RADIO:MENU:0174` | RTTY decoder/log [0174] |
| `RAD:MENU:0175` | extended | RW | RW | `menus[175].value` | `RAD:MENU:0175`, `RADIO:MENU:0175` | RTTY decoder/log [0175] |
| `RAD:MENU:0176` | extended | RW | RW | `menus[176].value` | `RAD:MENU:0176`, `RADIO:MENU:0176` | RTTY decoder/log [0176] |
| `RAD:MENU:0177` | extended | RW | RW | `menus[177].value` | `RAD:MENU:0177`, `RADIO:MENU:0177` | RTTY decoder/log [0177] |
| `RAD:MENU:0178` | extended | RW | RW | `menus[178].value` | `RAD:MENU:0178`, `RADIO:MENU:0178` | Scan behavior [0178] |
| `RAD:MENU:0179` | extended | RW | RW | `menus[179].value` | `RAD:MENU:0179`, `RADIO:MENU:0179` | Scan behavior [0179] |
| `RAD:MENU:0180` | extended | RW | RW | `menus[180].value` | `RAD:MENU:0180`, `RADIO:MENU:0180` | Voice memory playback [0180] |
| `RAD:MENU:0181` | extended | RW | RW | `menus[181].value` | `RAD:MENU:0181`, `RADIO:MENU:0181` | Voice repeat seconds [0181] |
| `RAD:MENU:0182` | extended | RW | RW | `menus[182].value` | `RAD:MENU:0182`, `RADIO:MENU:0182` | QSO recording [0182] |
| `RAD:MENU:0183` | extended | RW | RW | `menus[183].value` | `RAD:MENU:0183`, `RADIO:MENU:0183` | QSO recording [0183] |
| `RAD:MENU:0184` | extended | RW | RW | `menus[184].value` | `RAD:MENU:0184`, `RADIO:MENU:0184` | QSO recording [0184] |
| `RAD:MENU:0185` | extended | RW | RW | `menus[185].value` | `RAD:MENU:0185`, `RADIO:MENU:0185` | QSO recording [0185] |
| `RAD:MENU:0186` | extended | RW | RW | `menus[186].value` | `RAD:MENU:0186`, `RADIO:MENU:0186` | QSO recording [0186] |
| `RAD:MENU:0187` | extended | RW | RW | `menus[187].value` | `RAD:MENU:0187`, `RADIO:MENU:0187` | QSO recording [0187] |
| `RAD:MENU:0188` | extended | RW | RW | `menus[188].value` | `RAD:MENU:0188`, `RADIO:MENU:0188` | QSO recording [0188] |
| `RAD:MENU:0189` | extended | RW | RW | `menus[189].value` | `RAD:MENU:0189`, `RADIO:MENU:0189` | Noise blanker shape [0189] |
| `RAD:MENU:0190` | extended | RW | RW | `menus[190].value` | `RAD:MENU:0190`, `RADIO:MENU:0190` | Noise blanker shape [0190] |
| `RAD:MENU:0191` | extended | RW | RW | `menus[191].value` | `RAD:MENU:0191`, `RADIO:MENU:0191` | VOX timing [0191] |
| `RAD:MENU:0192` | extended | RW | RW | `menus[192].value` | `RAD:MENU:0192`, `RADIO:MENU:0192` | VOX timing [0192] |
| `RAD:MENU:0193` | extended | RW | RW | `menus[193].value` | `RAD:MENU:0193`, `RADIO:MENU:0193` | Medium-wave attenuator [0193] |
| `RAD:MENU:0194` | extended | RW | RW | `menus[194].value` | `RAD:MENU:0194`, `RADIO:MENU:0194` | Keyboard layout [0194] |
| `RAD:MENU:0195` | extended | RW | RW | `menus[195].value` | `RAD:MENU:0195`, `RADIO:MENU:0195` | Voice TX level [0195] |
| `RAD:MENU:0196` | extended | RW | RW | `menus[196].value` | `RAD:MENU:0196`, `RADIO:MENU:0196` | SSB DATA transmit bandwidth [0196] |
| `RAD:MENU:0197` | extended | RW | RW | `menus[197].value` | `RAD:MENU:0197`, `RADIO:MENU:0197` | USB input inhibit [0197] |
| `RAD:MENU:0198` | extended | RW | RW | `menus[198].value` | `RAD:MENU:0198`, `RADIO:MENU:0198` | Front/microphone key assignment [0198] |
| `RAD:MENU:0199` | extended | RW | RW | `menus[199].value` | `RAD:MENU:0199`, `RADIO:MENU:0199` | Front/microphone key assignment [0199] |
| `RAD:MENU:0200` | extended | RW | RW | `menus[200].value` | `RAD:MENU:0200`, `RADIO:MENU:0200` | Front/microphone key assignment [0200] |
| `RAD:MENU:0201` | extended | RW | RW | `menus[201].value` | `RAD:MENU:0201`, `RADIO:MENU:0201` | Front/microphone key assignment [0201] |
| `RAD:MENU:0202` | extended | RW | RW | `menus[202].value` | `RAD:MENU:0202`, `RADIO:MENU:0202` | Front/microphone key assignment [0202] |
| `RAD:MENU:0203` | extended | RW | RW | `menus[203].value` | `RAD:MENU:0203`, `RADIO:MENU:0203` | Front/microphone key assignment [0203] |
| `RAD:MENU:0204` | extended | RW | RW | `menus[204].value` | `RAD:MENU:0204`, `RADIO:MENU:0204` | Scope band 1 edge 4 (0.03-1.6 MHz) [0204] |
| `RAD:MENU:0205` | extended | RW | RW | `menus[205].value` | `RAD:MENU:0205`, `RADIO:MENU:0205` | Scope band 2 edge 4 (1.6-2 MHz) [0205] |
| `RAD:MENU:0206` | extended | RW | RW | `menus[206].value` | `RAD:MENU:0206`, `RADIO:MENU:0206` | Scope band 3 edge 4 (2-6 MHz) [0206] |
| `RAD:MENU:0207` | extended | RW | RW | `menus[207].value` | `RAD:MENU:0207`, `RADIO:MENU:0207` | Scope band 4 edge 4 (6-8 MHz) [0207] |
| `RAD:MENU:0208` | extended | RW | RW | `menus[208].value` | `RAD:MENU:0208`, `RADIO:MENU:0208` | Scope band 5 edge 4 (8-11 MHz) [0208] |
| `RAD:MENU:0209` | extended | RW | RW | `menus[209].value` | `RAD:MENU:0209`, `RADIO:MENU:0209` | Scope band 6 edge 4 (11-15 MHz) [0209] |
| `RAD:MENU:0210` | extended | RW | RW | `menus[210].value` | `RAD:MENU:0210`, `RADIO:MENU:0210` | Scope band 7 edge 4 (15-20 MHz) [0210] |
| `RAD:MENU:0211` | extended | RW | RW | `menus[211].value` | `RAD:MENU:0211`, `RADIO:MENU:0211` | Scope band 8 edge 4 (20-22 MHz) [0211] |
| `RAD:MENU:0212` | extended | RW | RW | `menus[212].value` | `RAD:MENU:0212`, `RADIO:MENU:0212` | Scope band 9 edge 4 (22-26 MHz) [0212] |
| `RAD:MENU:0213` | extended | RW | RW | `menus[213].value` | `RAD:MENU:0213`, `RADIO:MENU:0213` | Scope band 10 edge 4 (26-30 MHz) [0213] |
| `RAD:MENU:0214` | extended | RW | RW | `menus[214].value` | `RAD:MENU:0214`, `RADIO:MENU:0214` | Scope band 11 edge 4 (30-45 MHz) [0214] |
| `RAD:MENU:0215` | extended | RW | RW | `menus[215].value` | `RAD:MENU:0215`, `RADIO:MENU:0215` | Scope band 12 edge 4 (45-60 MHz) [0215] |
| `RAD:MENU:0216` | extended | RW | RW | `menus[216].value` | `RAD:MENU:0216`, `RADIO:MENU:0216` | Scope band 13 edge 4 (60-74.8 MHz) [0216] |
| `RAD:MENU:0217` | extended | RW | RW | `menus[217].value` | `RAD:MENU:0217`, `RADIO:MENU:0217` | PTT terminal function [0217] |

## Unsupported forms and reasons

These are gateway omissions/unsupported directions, not features secretly provided by raw I/O.
They are outside the supported-header count above; parser tests verify rejection.

| Unsupported probe | Reason / alternative |
|---|---|
| `*RST` | Gateway has no *RST; reset() uses documented RAD:RESET, not an Icom Partial/All Reset |
| `*OPC` | Non-query common command is not provided; use *OPC? / wait_for_complete() |
| `*IDN` | Identification is query-only |
| `*CLS?` | Clear is action-only |
| `*STB?` | No status-byte/SRQ subsystem in this gateway |
| `*ESR?` | No event-status-register subsystem in this gateway |
| `*ESE?` | No event-status-enable register in this gateway |
| `*SRE?` | No service-request-enable register in this gateway |
| `*TST?` | No gateway self-test command; health/connection state is not fabricated as self-test |
| `*WAI` | No standalone wait action; use *OPC? |

## Other interfaces outside this ASCII scope

No VXI-11, HiSLIP, binary-block/audio transport, SRQ or arbitrary outbound CI-V passthrough is
provided. OS/LAN/authentication administration remains outside this client SCPI inventory.
Protected menu/calibration/link commands that the gateway does provide are included, not
removed from coverage merely because their write gates default OFF.

BASIC.md documents base APIs; EVIDENCE.md summarizes results. The verification
completion plan is linked from COMPLIANCE.md.
