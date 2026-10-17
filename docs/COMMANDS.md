# IC-7300 command implementation inventory

339 extended command definitions, including 216 menu items. Generated from the runtime catalog.
These are software implementations verified with a simulated backend and selected independent wire vectors. New commands have not been verified on physical hardware.

Reference: [Icom IC-7300 supplement A7290-2J-8 (202312)](https://www.icom.co.jp/support/manual/2557/), printed pages 3-15. The vendor PDF is not redistributed.

## Usage

All extended headers below are CIVI-defined SCPI commands. Use their full spelling; RADio is also accepted for RAD. Query appends `?` to the header, followed by any selector. Settings use the same header without `?`. One command and its readback can share a semicolon-separated line.
Numbers for gain, meters, enumerated menus and tuning steps are CI-V protocol codes unless a physical unit is stated. Meter outputs are uncalibrated raw codes, not dBm/W/A/V measurements.
For commands with selectors, pass `selector,value` when writing, and only the selector when reading. VFO selectors are SELECTED/OTHER, not absolute A/B. The command explorer in the Web UI provides query and setting examples for every entry.

```text
RAD:AFGAIN 128;AFGAIN?
READ:SWR?
RAD:VFO:FREQ OTHER,14.074MHz;FREQ? OTHER
RAD:VFO:MODE OTHER,010102
RAD:RIT:FREQ -1200;FREQ?
RAD:MENU:0094?
```

## Permissions and transmit ownership

Reads are available without write permissions. Each persistent-menu/memory/power/link/calibration write class defaults to disabled in `[permissions]`. Enable only the classes you intend to use in config.toml. A radio NAK or an uncertain timeout remains an error, including power/USB commands that can disconnect the device.
CW output, voice playback, VOX, break-in and tuner enable/TUNE additionally use the existing `[transmit] enabled` gate, client ownership and maximum duration. When stopped/timed out/disconnected, CIVI attempts to disable the paths it enabled and sends PTT OFF. Stop commands remain available while transmit enable is false. Stop attempts are serialized; several active paths may require several serial timeouts. An uncertain quarantined ACK is not reported as successful stop. USB/power loss or external/manual transmission cannot be guaranteed by software.
Link-menu writes can change USB routing/SEND/keying and prevent subsequent control. They require explicit link permission. Reference-frequency and user transmit-band writes require calibration permission. None of these permissions are automatically enabled by the Web UI.

```toml
[permissions]
menu = false
memory = false
power = false
link = false
calibration = false
```

## Complex payloads

| Format | Value representation |
|---|---|
| frequency | Whole Hz or Hz/kHz/MHz text |
| signed | RIT offset in Hz, -9999..9999 |
| repeater_offset | Signed Hz in 1000 Hz steps, magnitude <=9999000 |
| tone | Tone frequency in Hz, one decimal digit; unsupported tone choices are rejected by radio NAK |
| mode | Exactly 3 hex bytes: mode, DATA(00/01), filter(01/02/03) |
| data | Exactly 2 hex bytes: DATA, filter; OFF requires 0000 |
| memory | 39-byte hex record excluding the 2-byte channel selector; FF clears channels 1-99 only. Two validated frequency/mode/tone records and 10 name bytes. P1/P2 require split/select flags zero |
| stack | 28-byte hex dual frequency/mode/tone record; selector is band*100+slot, band 1-11, slot 1-3 |
| color | 6 hex bytes: three big-endian 2-byte BCD components, each 0-255 |
| hpf | 2 hex BCD index bytes: HPF 00-20, LPF 05-25; HPF < LPF unless either side is bypassed |
| bandwidth | 1 hex byte, high nibble upper-edge index 0-3, low nibble lower-edge index 0-3 |
| edge | 10 hex BCD bytes for scope FIX edges: low and high frequencies, 5 bytes each, little endian, whole kHz |
| menu_edge | 6 hex BCD bytes for stored scope edges: low/high 3 bytes each, little endian in 100 Hz units, whole kHz |
| bandedge | 11 hex bytes for transmit band edges: low frequency (5 little-endian BCD bytes), literal 2D separator, high frequency (5 bytes) |
| scope_span | 5 hex little-endian BCD bytes; 2500/5000/10000/25000/50000/100000/250000/500000 Hz |
| scope_ref | 3 hex bytes after main-scope selector: whole dB (BCD 00-20), tenths byte 00/05, sign 00/01; magnitude <=20 dB |
| date / time / timezone | YYYY-MM-DD / HH:MM / +/-HH:MM |
| opening / keyer / text | ASCII text, quote text containing commas; field-specific character/length checks apply |

Mode-dependent limits are ultimately checked by the radio (for example IF width and AGC timing). A documented CI-V range does not imply that every value is supported in every mode or firmware/region.

## Spectrum and waterfall

`RAD:SCOPE:STREAM 0,ON` requires 115200 baud and an unlinked CI-V USB port on IC-7300. CIVI checks the configured baud and menu 0074 before enabling. The selector 0 is the only main scope supported by this radio.
`RAD:SCOPE:WAVE?` returns the latest complete sweep as JSON, or an error if no fresh sweep exists. The Web UI plots a spectrum and waterfall history. The receiver checks packet order/count, BCD headers, raw levels 0-160 and 475 samples. Dropped/incomplete sweeps are discarded. Cached sweeps expire after 5 seconds.
Receive data are drained by the single worker between commands and during transactions. Ordinary command replies are never satisfied by scope packets. The Web refresh rate is 2 seconds, so the browser shows sampled sweeps rather than every incoming RF sweep.

## CI-V family coverage

| CI-V family | Implementation route |
|---|---|
| 00/01 transceive | Receive notifications separated from replies; normal acknowledged frequency/mode setting uses 05/06. CIVI does not provide a second outbound broadcast-setting API |
| 03/04/05/06, 15 02, 19 00, 1C 00 | Existing frequency/mode/S-meter/model-ID/PTT implementation; see SCPI.md |
| 02, 07-0B, 0E, 0F, 10, 11, 13-18 | Catalog below |
| 1A 00-07 | Memory, stack, keyer, IF/AGC, every documented menu, DATA and alternate IP+ |
| 1B, 1C 01-04, 1E, 21, 25, 26 | Catalog below |
| 27 00 | Scope receive/reassembly and WAVE query |
| 27 10-20 documented subcommands, 28 00 | Catalog below |
| Firmware auto-read / USB audio | No firmware-query command or audio transport is specified in this reference; manual firmware metadata and a separate audio transport would be needed |

## Extended command table

R = query; W = set/action. An empty parameter example means the action takes no argument. All new entries are hardware-unverified.

| Header | CI-V | Access | Description | Format | Write gate | Query parameters | Set/action parameters |
|---|---|---|---|---|---|---|---|
| RAD:AFGAIN | 1401 | RW | AF gain | number | - | - | 0 |
| RAD:RFGAIN | 1402 | RW | RF gain | number | - | - | 0 |
| RAD:SQL | 1403 | RW | Squelch level | number | - | - | 0 |
| RAD:NR:LEVEL | 1406 | RW | Noise reduction level | number | - | - | 0 |
| RAD:PBT:INNER | 1407 | RW | Inner PBT | number | - | - | 0 |
| RAD:PBT:OUTER | 1408 | RW | Outer PBT | number | - | - | 0 |
| RAD:CW:PITCH | 1409 | RW | CW pitch code | number | - | - | 0 |
| RAD:POWER | 140A | RW | RF power code | number | - | - | 0 |
| RAD:MICGAIN | 140B | RW | Microphone gain | number | - | - | 0 |
| RAD:CW:SPEED | 140C | RW | Key speed code | number | - | - | 0 |
| RAD:NOTCH:LEVEL | 140D | RW | Notch position | number | - | - | 0 |
| RAD:COMP:LEVEL | 140E | RW | Compression level | number | - | - | 0 |
| RAD:CW:DELAY | 140F | RW | Break-in delay code | number | - | - | 0 |
| RAD:NB:LEVEL | 1412 | RW | Noise blanker level | number | - | - | 0 |
| RAD:MONITOR:LEVEL | 1415 | RW | Monitor gain | number | - | - | 0 |
| RAD:VOX:GAIN | 1416 | RW | VOX gain | number | - | - | 0 |
| RAD:VOX:ANTIGAIN | 1417 | RW | Anti-VOX gain | number | - | - | 0 |
| RAD:BACKLIGHT | 1419 | RW | LCD brightness | number | - | - | 0 |
| READ:SQL | 1501 | R | SQL status | number | - | - | - |
| READ:SQL:ALL | 1505 | R | SQL:ALL status | number | - | - | - |
| READ:OVF | 1507 | R | OVF status | number | - | - | - |
| READ:POWER | 1511 | R | POWER meter (raw, uncalibrated) | number | - | - | - |
| READ:SWR | 1512 | R | SWR meter (raw, uncalibrated) | number | - | - | - |
| READ:ALC | 1513 | R | ALC meter (raw, uncalibrated) | number | - | - | - |
| READ:COMP | 1514 | R | COMP meter (raw, uncalibrated) | number | - | - | - |
| READ:VOLTAGE | 1515 | R | VOLTAGE meter (raw, uncalibrated) | number | - | - | - |
| READ:CURRENT | 1516 | R | CURRENT meter (raw, uncalibrated) | number | - | - | - |
| RAD:NB | 1622 | RW | NB enable | number | - | - | OFF |
| RAD:NR | 1640 | RW | NR enable | number | - | - | OFF |
| RAD:ANOTCH | 1641 | RW | ANOTCH enable | number | - | - | OFF |
| RAD:TONE | 1642 | RW | TONE enable | number | - | - | OFF |
| RAD:TSQL | 1643 | RW | TSQL enable | number | - | - | OFF |
| RAD:COMP | 1644 | RW | COMP enable | number | - | - | OFF |
| RAD:MONITOR | 1645 | RW | MONITOR enable | number | - | - | OFF |
| RAD:VOX | 1646 | RW | VOX enable | number | autotx | - | OFF |
| RAD:NOTCH | 1648 | RW | NOTCH enable | number | - | - | OFF |
| RAD:TPF | 164F | RW | TPF enable | number | - | - | OFF |
| RAD:LOCK | 1650 | RW | LOCK enable | number | - | - | OFF |
| RAD:IPPLUS | 1665 | RW | IPPLUS enable | number | - | - | OFF |
| RAD:TXINHIBIT | 1666 | RW | TXINHIBIT enable | number | - | - | OFF |
| RAD:PREAMP | 1602 | RW | Preamplifier | number | - | - | OFF |
| RAD:AGC | 1612 | RW | AGC speed | number | - | - | FAST |
| RAD:BKIN | 1647 | RW | CW break-in | number | autotx | - | OFF |
| RAD:FILTER:SHAPE | 1656 | RW | DSP filter shape | number | - | - | SHARP |
| RAD:NOTCH:WIDTH | 1657 | RW | Notch width | number | - | - | WIDE |
| RAD:TXBANDWIDTH | 1658 | RW | SSB TX bandwidth | number | - | - | WIDE |
| RAD:ATT | 11 | RW | Attenuator code | number | - | - | 0 |
| RAD:STEP | 10 | RW | Tuning step code | number | - | - | 0 |
| RAD:SPLIT | 0F | RW | Split enable | number | - | - | OFF |
| RAD:RIT:FREQ | 2100 | RW | RIT offset (Hz) | signed | - | - | 0 |
| RAD:RIT | 2101 | RW | RIT enable | number | - | - | OFF |
| RAD:XIT | 2102 | RW | Delta TX enable | number | - | - | OFF |
| RAD:TXFREQ | 1C03 | R | Transmit frequency | frequency | - | - | - |
| RAD:XFC | 1C02 | RW | Transmit frequency check | number | - | - | OFF |
| RAD:ANTOUTPUT | 1C04 | RW | Antenna controller output | number | link | - | OFF |
| RAD:TUNER | 1C01 | RW | Antenna tuner (TUNE transmits) | number | autotx | - | OFF |
| RAD:DATA | 1A06 | RW | DATA/filter bytes | data | - | - | 0000 |
| RAD:IPPLUS:ALT | 1A07 | RW | IP+ alternate CI-V command | number | - | - | OFF |
| RAD:FILTER:WIDTH | 1A03 | RW | Filter width index (mode dependent) | number | - | - | 0 |
| RAD:AGC:TIME | 1A04 | RW | AGC time index (mode dependent) | number | - | - | 0 |
| RAD:VFO:SELECT | 07 | W | Select VFO A/B | number | - | - | A |
| RAD:VFO:ENABLE | 07 | W | Enter VFO mode | number | - | - | - |
| RAD:VFO:COPY | 07 | W | Copy selected VFO to the other VFO | number | - | - | - |
| RAD:VFO:SWAP | 07 | W | Swap VFO contents | number | - | - | - |
| RAD:VFO:FREQ | 25 | RW | Selected/other VFO frequency (Hz) | frequency | - | SELECTED | SELECTED,7100000 |
| RAD:VFO:MODE | 26 | RW | Selected/other VFO mode/DATA/filter bytes | mode | - | SELECTED | SELECTED,010001 |
| RAD:TONE:FREQ | 1B00 | RW | Repeater tone frequency (Hz) | tone | - | - | 88.5 |
| RAD:TSQL:FREQ | 1B01 | RW | Tone squelch frequency (Hz) | tone | - | - | 88.5 |
| RAD:SCAN:STOP | 0E | W | Scan STOP | number | - | - | - |
| RAD:SCAN:PROGRAM | 0E | W | Scan PROGRAM | number | - | - | - |
| RAD:SCAN:MEMORY | 0E | W | Scan MEMORY | number | - | - | - |
| RAD:SCAN:AUTO | 0E | W | Scan AUTO | number | - | - | - |
| RAD:SCAN:DELTA | 0E | W | Scan DELTA | number | - | - | - |
| RAD:SCAN:FINEPROGRAM | 0E | W | Scan FINEPROGRAM | number | - | - | - |
| RAD:SCAN:FINEDELTA | 0E | W | Scan FINEDELTA | number | - | - | - |
| RAD:SCAN:SELECTMEM | 0E | W | Scan SELECTMEM | number | - | - | - |
| RAD:SCAN:SPAN5K | 0E | W | Scan SPAN5K | number | - | - | - |
| RAD:SCAN:SPAN10K | 0E | W | Scan SPAN10K | number | - | - | - |
| RAD:SCAN:SPAN20K | 0E | W | Scan SPAN20K | number | - | - | - |
| RAD:SCAN:SPAN50K | 0E | W | Scan SPAN50K | number | - | - | - |
| RAD:SCAN:SPAN100K | 0E | W | Scan SPAN100K | number | - | - | - |
| RAD:SCAN:SPAN500K | 0E | W | Scan SPAN500K | number | - | - | - |
| RAD:SCAN:SPAN1M | 0E | W | Scan SPAN1M | number | - | - | - |
| RAD:SCAN:SELECTOFF | 0E | W | Scan SELECTOFF | number | - | - | - |
| RAD:SCAN:SELECTON | 0E | W | Scan SELECTON | number | - | - | - |
| RAD:SCAN:RESUMEOFF | 0E | W | Scan RESUMEOFF | number | - | - | - |
| RAD:SCAN:RESUMEON | 0E | W | Scan RESUMEON | number | - | - | - |
| RAD:SCAN:SELECT | 0EB1 | W | Assign memory select group | number | - | - | 1 |
| RAD:SCAN:GROUP | 0EB2 | W | Select memory scan group | number | - | - | 0 |
| RAD:MEM:SELECT | 08 | W | Select memory channel (100=P1,101=P2) | number | - | - | 1 |
| RAD:MEM:ENABLE | 08 | W | Enter memory mode | number | - | - | - |
| RAD:MEM:WRITE | 09 | W | Write selected memory | number | memory | - | - |
| RAD:MEM:TOVFO | 0A | W | Copy memory to VFO | number | - | - | - |
| RAD:MEM:CLEAR | 0B | W | Clear selected memory | number | memory | - | - |
| RAD:MEM:CONTENT | 1A00 | RW | Memory record hex (channel selector omitted from payload) | memory | memory | 1 | 1,000000100700010100000885000885000010070001010000088500088520202020202020202020 |
| RAD:BAND:STACK | 1A01 | RW | Band stack record (band*100+slot selector) | stack | memory | 101 | 101,00001007000101000008850008850000100700010100000885000885 |
| RAD:KEYER:TEXT | 1A02 | RW | Keyer memory text | keyer | memory | 1 | 1,CQ |
| RAD:CW:SEND | 17 | W | Send CW text (up to 30 characters) | text | tx | - | TEST |
| RAD:CW:STOP | 17 | W | Stop CI-V CW output | number | - | - | - |
| RAD:VOICE | 2800 | W | Play voice memory; STOP or 1-8 | number | tx | - | STOP |
| RAD:SPEECH | 13 | W | Announce S/frequency/mode | number | - | - | 0 |
| RAD:POWER:OFF | 18 | W | Power off radio | number | power | - | - |
| RAD:POWER:ON | 18 | W | Power on radio (wake preamble) | number | power | - | - |
| RAD:BAND:EDGES | 02 | R | Read default band edges (validated BCD pair) | bandedge | - | - | - |
| RAD:TXBAND:COUNT | 1E00 | R | Number of factory transmit bands | number | - | - | - |
| RAD:TXBAND:READ | 1E01 | R | Read transmit band edge | bandedge | - | 1 | - |
| RAD:TXBAND:USERCOUNT | 1E02 | R | Number of user transmit bands | number | - | - | - |
| RAD:TXBAND:USER | 1E03 | RW | User transmit band edge | bandedge | calibration | 1 | 1,00001007002D0000200700 |
| RAD:SCOPE:ENABLE | 2710 | RW | Scope ENABLE | number | - | 0 | 0,OFF |
| RAD:SCOPE:STREAM | 2711 | RW | Scope STREAM | number | stream | 0 | 0,OFF |
| RAD:SCOPE:DISPLAY | 2712 | RW | Scope DISPLAY | number | - | 0 | 0,0 |
| RAD:SCOPE:DUAL | 2713 | RW | Scope DUAL | number | - | 0 | 0,0 |
| RAD:SCOPE:MODE | 2714 | RW | Scope MODE | number | - | 0 | 0,0 |
| RAD:SCOPE:SPAN | 2715 | RW | Scope SPAN | scope_span | - | 0 | 0,0000250000 |
| RAD:SCOPE:EDGE | 2716 | RW | Scope EDGE | number | - | 0 | 0,1 |
| RAD:SCOPE:HOLD | 2717 | RW | Scope HOLD | number | - | 0 | 0,OFF |
| RAD:SCOPE:REFERENCE | 2719 | RW | Scope REFERENCE | scope_ref | - | 0 | 0,000000 |
| RAD:SCOPE:SPEED | 271A | RW | Scope SPEED | number | - | 0 | 0,0 |
| RAD:SCOPE:TXDISPLAY | 271B | RW | Scope TXDISPLAY | number | - | 0 | 0,OFF |
| RAD:SCOPE:CENTER | 271C | RW | Scope CENTER | number | - | 0 | 0,0 |
| RAD:SCOPE:VBW | 271D | RW | Scope VBW | number | - | 0 | 0,OFF |
| RAD:SCOPE:MARKER | 2720 | RW | Scope MARKER | number | - | 0 | 0,OFF |
| RAD:SCOPE:FIXEDGE | 271E | RW | Scope FIX edge (band*100+edge selector) | edge | - | 101 | 101,00000000000000000100 |
| RAD:MENU:0001 | 1A050001 | RW | SSB RX HPF/LPF [0001] | hpf | menu | - | 0005 |
| RAD:MENU:0002 | 1A050002 | RW | SSB RX bass [0002] | number | menu | - | 0 |
| RAD:MENU:0003 | 1A050003 | RW | SSB RX treble [0003] | number | menu | - | 0 |
| RAD:MENU:0004 | 1A050004 | RW | AM RX HPF/LPF [0004] | hpf | menu | - | 0005 |
| RAD:MENU:0005 | 1A050005 | RW | AM RX bass [0005] | number | menu | - | 0 |
| RAD:MENU:0006 | 1A050006 | RW | AM RX treble [0006] | number | menu | - | 0 |
| RAD:MENU:0007 | 1A050007 | RW | FM RX HPF/LPF [0007] | hpf | menu | - | 0005 |
| RAD:MENU:0008 | 1A050008 | RW | FM RX bass [0008] | number | menu | - | 0 |
| RAD:MENU:0009 | 1A050009 | RW | FM RX treble [0009] | number | menu | - | 0 |
| RAD:MENU:0010 | 1A050010 | RW | CW RX HPF/LPF [0010] | hpf | menu | - | 0005 |
| RAD:MENU:0011 | 1A050011 | RW | RTTY RX HPF/LPF [0011] | hpf | menu | - | 0005 |
| RAD:MENU:0012 | 1A050012 | RW | Transmit audio EQ/bandwidth [0012] | number | menu | - | 0 |
| RAD:MENU:0013 | 1A050013 | RW | Transmit audio EQ/bandwidth [0013] | number | menu | - | 0 |
| RAD:MENU:0014 | 1A050014 | RW | Transmit audio EQ/bandwidth [0014] | bandwidth | menu | - | 00 |
| RAD:MENU:0015 | 1A050015 | RW | Transmit audio EQ/bandwidth [0015] | bandwidth | menu | - | 00 |
| RAD:MENU:0016 | 1A050016 | RW | Transmit audio EQ/bandwidth [0016] | bandwidth | menu | - | 00 |
| RAD:MENU:0017 | 1A050017 | RW | Transmit audio EQ/bandwidth [0017] | number | menu | - | 0 |
| RAD:MENU:0018 | 1A050018 | RW | Transmit audio EQ/bandwidth [0018] | number | menu | - | 0 |
| RAD:MENU:0019 | 1A050019 | RW | Transmit audio EQ/bandwidth [0019] | number | menu | - | 0 |
| RAD:MENU:0020 | 1A050020 | RW | Transmit audio EQ/bandwidth [0020] | number | menu | - | 0 |
| RAD:MENU:0021 | 1A050021 | RW | Beep [0021] | number | menu | - | 0 |
| RAD:MENU:0022 | 1A050022 | RW | Beep [0022] | number | menu | - | OFF |
| RAD:MENU:0023 | 1A050023 | RW | Beep [0023] | number | menu | - | OFF |
| RAD:MENU:0024 | 1A050024 | RW | Band edge beep/limit [0024] | number | menu | - | 0 |
| RAD:MENU:0025 | 1A050025 | RW | RF/SQL control [0025] | number | menu | - | 0 |
| RAD:MENU:0026 | 1A050026 | RW | Transmit delay [0026] | number | menu | - | 0 |
| RAD:MENU:0027 | 1A050027 | RW | Transmit delay [0027] | number | menu | - | 0 |
| RAD:MENU:0029 | 1A050029 | RW | CI-V TX timeout [0029] | number | menu | - | 0 |
| RAD:MENU:0030 | 1A050030 | RW | Split/tuner setup [0030] | number | menu | - | OFF |
| RAD:MENU:0031 | 1A050031 | RW | HF repeater split offset [0031] | repeater_offset | menu | - | 0 |
| RAD:MENU:0032 | 1A050032 | RW | 50 MHz repeater split offset [0032] | repeater_offset | menu | - | 0 |
| RAD:MENU:0033 | 1A050033 | RW | Split/tuner setup [0033] | number | menu | - | OFF |
| RAD:MENU:0034 | 1A050034 | RW | Split/tuner setup [0034] | number | menu | - | OFF |
| RAD:MENU:0035 | 1A050035 | RW | Split/tuner setup [0035] | number | menu | - | OFF |
| RAD:MENU:0036 | 1A050036 | RW | RTTY signal [0036] | number | menu | - | 0 |
| RAD:MENU:0037 | 1A050037 | RW | RTTY signal [0037] | number | menu | - | 0 |
| RAD:MENU:0038 | 1A050038 | RW | RTTY signal [0038] | number | menu | - | OFF |
| RAD:MENU:0039 | 1A050039 | RW | Speech/lock setup [0039] | number | menu | - | OFF |
| RAD:MENU:0040 | 1A050040 | RW | Speech/lock setup [0040] | number | menu | - | OFF |
| RAD:MENU:0041 | 1A050041 | RW | Speech/lock setup [0041] | number | menu | - | OFF |
| RAD:MENU:0042 | 1A050042 | RW | Speech/lock setup [0042] | number | menu | - | OFF |
| RAD:MENU:0043 | 1A050043 | RW | Speech/lock setup [0043] | number | menu | - | 0 |
| RAD:MENU:0044 | 1A050044 | RW | Speech/lock setup [0044] | number | menu | - | OFF |
| RAD:MENU:0045 | 1A050045 | RW | Speech/lock setup [0045] | number | menu | - | OFF |
| RAD:MENU:0046 | 1A050046 | RW | Memo/dial/key behavior [0046] | number | menu | - | OFF |
| RAD:MENU:0047 | 1A050047 | RW | Memo/dial/key behavior [0047] | number | menu | - | 0 |
| RAD:MENU:0048 | 1A050048 | RW | Memo/dial/key behavior [0048] | number | menu | - | OFF |
| RAD:MENU:0049 | 1A050049 | RW | Memo/dial/key behavior [0049] | number | menu | - | OFF |
| RAD:MENU:0050 | 1A050050 | RW | Notch/CW behavior [0050] | number | menu | - | 0 |
| RAD:MENU:0051 | 1A050051 | RW | Notch/CW behavior [0051] | number | menu | - | 0 |
| RAD:MENU:0052 | 1A050052 | RW | Notch/CW behavior [0052] | number | menu | - | OFF |
| RAD:MENU:0053 | 1A050053 | RW | Notch/CW behavior [0053] | number | menu | - | OFF |
| RAD:MENU:0054 | 1A050054 | RW | Screenshot/keyboard [0054] | number | menu | - | OFF |
| RAD:MENU:0055 | 1A050055 | RW | Screenshot/keyboard [0055] | number | menu | - | OFF |
| RAD:MENU:0056 | 1A050056 | RW | Screenshot/keyboard [0056] | number | menu | - | OFF |
| RAD:MENU:0057 | 1A050057 | RW | Reference calibration [0057] | number | calibration | - | OFF |
| RAD:MENU:0058 | 1A050058 | RW | Reference frequency adjustment [0058] | number | calibration | - | 0 |
| RAD:MENU:0059 | 1A050059 | RW | ACC/USB audio routing/levels [0059] | number | menu | - | OFF |
| RAD:MENU:0060 | 1A050060 | RW | ACC/USB audio routing/levels [0060] | number | menu | - | 0 |
| RAD:MENU:0061 | 1A050061 | RW | ACC/USB audio routing/levels [0061] | number | menu | - | OFF |
| RAD:MENU:0062 | 1A050062 | RW | ACC/USB audio routing/levels [0062] | number | menu | - | OFF |
| RAD:MENU:0063 | 1A050063 | RW | ACC/USB audio routing/levels [0063] | number | menu | - | 0 |
| RAD:MENU:0064 | 1A050064 | RW | ACC/USB audio routing/levels [0064] | number | menu | - | 0 |
| RAD:MENU:0065 | 1A050065 | RW | ACC/USB audio routing/levels [0065] | number | menu | - | 0 |
| RAD:MENU:0066 | 1A050066 | RW | Modulation source [0066] | number | menu | - | 0 |
| RAD:MENU:0067 | 1A050067 | RW | Modulation source [0067] | number | menu | - | 0 |
| RAD:MENU:0068 | 1A050068 | RW | External memory keypad [0068] | number | menu | - | OFF |
| RAD:MENU:0069 | 1A050069 | RW | External memory keypad [0069] | number | menu | - | OFF |
| RAD:MENU:0070 | 1A050070 | RW | External memory keypad [0070] | number | menu | - | OFF |
| RAD:MENU:0071 | 1A050071 | RW | CI-V transceive [0071] | number | link | - | OFF |
| RAD:MENU:0072 | 1A050072 | RW | USB-to-REMOTE transceive address [0072] | number | link | - | 0 |
| RAD:MENU:0073 | 1A050073 | RW | Antenna CI-V output [0073] | number | link | - | OFF |
| RAD:MENU:0074 | 1A050074 | R | CI-V USB port mode (read only) [0074] | number | link | - | - |
| RAD:MENU:0075 | 1A050075 | RW | USB CI-V echo [0075] | number | link | - | OFF |
| RAD:MENU:0076 | 1A050076 | RW | USB serial function [0076] | number | link | - | OFF |
| RAD:MENU:0077 | 1A050077 | RW | RTTY serial baud code [0077] | number | link | - | 0 |
| RAD:MENU:0078 | 1A050078 | RW | USB SEND pin [0078] | number | link | - | 0 |
| RAD:MENU:0079 | 1A050079 | RW | USB CW keying pin [0079] | number | link | - | 0 |
| RAD:MENU:0080 | 1A050080 | RW | USB FSK pin [0080] | number | link | - | 0 |
| RAD:MENU:0081 | 1A050081 | RW | Display/UI [0081] | number | menu | - | 0 |
| RAD:MENU:0082 | 1A050082 | RW | Display/UI [0082] | number | menu | - | OFF |
| RAD:MENU:0083 | 1A050083 | RW | Display/UI [0083] | number | menu | - | OFF |
| RAD:MENU:0084 | 1A050084 | RW | Display/UI [0084] | number | menu | - | OFF |
| RAD:MENU:0085 | 1A050085 | RW | Display/UI [0085] | number | menu | - | OFF |
| RAD:MENU:0086 | 1A050086 | RW | Display/UI [0086] | number | menu | - | OFF |
| RAD:MENU:0087 | 1A050087 | RW | Display/UI [0087] | number | menu | - | OFF |
| RAD:MENU:0088 | 1A050088 | RW | Display/UI [0088] | number | menu | - | OFF |
| RAD:MENU:0089 | 1A050089 | RW | Display/UI [0089] | number | menu | - | 0 |
| RAD:MENU:0090 | 1A050090 | RW | Display/UI [0090] | number | menu | - | OFF |
| RAD:MENU:0091 | 1A050091 | RW | Opening screen text [0091] | opening | menu | - | CIVI |
| RAD:MENU:0092 | 1A050092 | RW | Display/UI [0092] | number | menu | - | OFF |
| RAD:MENU:0093 | 1A050093 | RW | Display/UI [0093] | number | menu | - | OFF |
| RAD:MENU:0094 | 1A050094 | RW | Date [0094] | date | menu | - | 2026-01-01 |
| RAD:MENU:0095 | 1A050095 | RW | Time [0095] | time | menu | - | 00:00 |
| RAD:MENU:0096 | 1A050096 | RW | UTC offset [0096] | timezone | menu | - | +00:00 |
| RAD:MENU:0097 | 1A050097 | RW | Scope display [0097] | number | menu | - | OFF |
| RAD:MENU:0098 | 1A050098 | RW | Scope display [0098] | number | menu | - | 0 |
| RAD:MENU:0099 | 1A050099 | RW | Scope display [0099] | number | menu | - | 0 |
| RAD:MENU:0100 | 1A050100 | RW | Scope display [0100] | number | menu | - | OFF |
| RAD:MENU:0101 | 1A050101 | RW | Scope display [0101] | number | menu | - | OFF |
| RAD:MENU:0102 | 1A050102 | RW | Scope display [0102] | number | menu | - | 0 |
| RAD:MENU:0103 | 1A050103 | RW | Scope display [0103] | number | menu | - | OFF |
| RAD:MENU:0104 | 1A050104 | RW | Scope display [0104] | color | menu | - | 012801280128 |
| RAD:MENU:0105 | 1A050105 | RW | Scope display [0105] | color | menu | - | 012801280128 |
| RAD:MENU:0106 | 1A050106 | RW | Scope display [0106] | color | menu | - | 012801280128 |
| RAD:MENU:0107 | 1A050107 | RW | Scope display [0107] | number | menu | - | OFF |
| RAD:MENU:0108 | 1A050108 | RW | Scope display [0108] | number | menu | - | 0 |
| RAD:MENU:0109 | 1A050109 | RW | Scope display [0109] | number | menu | - | 0 |
| RAD:MENU:0110 | 1A050110 | RW | Scope display [0110] | number | menu | - | 0 |
| RAD:MENU:0111 | 1A050111 | RW | Scope display [0111] | number | menu | - | OFF |
| RAD:MENU:0112 | 1A050112 | RW | Scope band 1 edge 1 (0.03-1.6 MHz) [0112] | menu_edge | menu | - | 000300006001 |
| RAD:MENU:0113 | 1A050113 | RW | Scope band 1 edge 2 (0.03-1.6 MHz) [0113] | menu_edge | menu | - | 000300006001 |
| RAD:MENU:0114 | 1A050114 | RW | Scope band 1 edge 3 (0.03-1.6 MHz) [0114] | menu_edge | menu | - | 000300006001 |
| RAD:MENU:0115 | 1A050115 | RW | Scope band 2 edge 1 (1.6-2 MHz) [0115] | menu_edge | menu | - | 006001000002 |
| RAD:MENU:0116 | 1A050116 | RW | Scope band 2 edge 2 (1.6-2 MHz) [0116] | menu_edge | menu | - | 006001000002 |
| RAD:MENU:0117 | 1A050117 | RW | Scope band 2 edge 3 (1.6-2 MHz) [0117] | menu_edge | menu | - | 006001000002 |
| RAD:MENU:0118 | 1A050118 | RW | Scope band 3 edge 1 (2-6 MHz) [0118] | menu_edge | menu | - | 000002000006 |
| RAD:MENU:0119 | 1A050119 | RW | Scope band 3 edge 2 (2-6 MHz) [0119] | menu_edge | menu | - | 000002000006 |
| RAD:MENU:0120 | 1A050120 | RW | Scope band 3 edge 3 (2-6 MHz) [0120] | menu_edge | menu | - | 000002000006 |
| RAD:MENU:0121 | 1A050121 | RW | Scope band 4 edge 1 (6-8 MHz) [0121] | menu_edge | menu | - | 000006000008 |
| RAD:MENU:0122 | 1A050122 | RW | Scope band 4 edge 2 (6-8 MHz) [0122] | menu_edge | menu | - | 000006000008 |
| RAD:MENU:0123 | 1A050123 | RW | Scope band 4 edge 3 (6-8 MHz) [0123] | menu_edge | menu | - | 000006000008 |
| RAD:MENU:0124 | 1A050124 | RW | Scope band 5 edge 1 (8-11 MHz) [0124] | menu_edge | menu | - | 000008000011 |
| RAD:MENU:0125 | 1A050125 | RW | Scope band 5 edge 2 (8-11 MHz) [0125] | menu_edge | menu | - | 000008000011 |
| RAD:MENU:0126 | 1A050126 | RW | Scope band 5 edge 3 (8-11 MHz) [0126] | menu_edge | menu | - | 000008000011 |
| RAD:MENU:0127 | 1A050127 | RW | Scope band 6 edge 1 (11-15 MHz) [0127] | menu_edge | menu | - | 000011000015 |
| RAD:MENU:0128 | 1A050128 | RW | Scope band 6 edge 2 (11-15 MHz) [0128] | menu_edge | menu | - | 000011000015 |
| RAD:MENU:0129 | 1A050129 | RW | Scope band 6 edge 3 (11-15 MHz) [0129] | menu_edge | menu | - | 000011000015 |
| RAD:MENU:0130 | 1A050130 | RW | Scope band 7 edge 1 (15-20 MHz) [0130] | menu_edge | menu | - | 000015000020 |
| RAD:MENU:0131 | 1A050131 | RW | Scope band 7 edge 2 (15-20 MHz) [0131] | menu_edge | menu | - | 000015000020 |
| RAD:MENU:0132 | 1A050132 | RW | Scope band 7 edge 3 (15-20 MHz) [0132] | menu_edge | menu | - | 000015000020 |
| RAD:MENU:0133 | 1A050133 | RW | Scope band 8 edge 1 (20-22 MHz) [0133] | menu_edge | menu | - | 000020000022 |
| RAD:MENU:0134 | 1A050134 | RW | Scope band 8 edge 2 (20-22 MHz) [0134] | menu_edge | menu | - | 000020000022 |
| RAD:MENU:0135 | 1A050135 | RW | Scope band 8 edge 3 (20-22 MHz) [0135] | menu_edge | menu | - | 000020000022 |
| RAD:MENU:0136 | 1A050136 | RW | Scope band 9 edge 1 (22-26 MHz) [0136] | menu_edge | menu | - | 000022000026 |
| RAD:MENU:0137 | 1A050137 | RW | Scope band 9 edge 2 (22-26 MHz) [0137] | menu_edge | menu | - | 000022000026 |
| RAD:MENU:0138 | 1A050138 | RW | Scope band 9 edge 3 (22-26 MHz) [0138] | menu_edge | menu | - | 000022000026 |
| RAD:MENU:0139 | 1A050139 | RW | Scope band 10 edge 1 (26-30 MHz) [0139] | menu_edge | menu | - | 000026000030 |
| RAD:MENU:0140 | 1A050140 | RW | Scope band 10 edge 2 (26-30 MHz) [0140] | menu_edge | menu | - | 000026000030 |
| RAD:MENU:0141 | 1A050141 | RW | Scope band 10 edge 3 (26-30 MHz) [0141] | menu_edge | menu | - | 000026000030 |
| RAD:MENU:0142 | 1A050142 | RW | Scope band 11 edge 1 (30-45 MHz) [0142] | menu_edge | menu | - | 000030000045 |
| RAD:MENU:0143 | 1A050143 | RW | Scope band 11 edge 2 (30-45 MHz) [0143] | menu_edge | menu | - | 000030000045 |
| RAD:MENU:0144 | 1A050144 | RW | Scope band 11 edge 3 (30-45 MHz) [0144] | menu_edge | menu | - | 000030000045 |
| RAD:MENU:0145 | 1A050145 | RW | Scope band 12 edge 1 (45-60 MHz) [0145] | menu_edge | menu | - | 000045000060 |
| RAD:MENU:0146 | 1A050146 | RW | Scope band 12 edge 2 (45-60 MHz) [0146] | menu_edge | menu | - | 000045000060 |
| RAD:MENU:0147 | 1A050147 | RW | Scope band 12 edge 3 (45-60 MHz) [0147] | menu_edge | menu | - | 000045000060 |
| RAD:MENU:0148 | 1A050148 | RW | Scope band 13 edge 1 (60-74.8 MHz) [0148] | menu_edge | menu | - | 000060008074 |
| RAD:MENU:0149 | 1A050149 | RW | Scope band 13 edge 2 (60-74.8 MHz) [0149] | menu_edge | menu | - | 000060008074 |
| RAD:MENU:0150 | 1A050150 | RW | Scope band 13 edge 3 (60-74.8 MHz) [0150] | menu_edge | menu | - | 000060008074 |
| RAD:MENU:0151 | 1A050151 | RW | Audio scope display [0151] | number | menu | - | OFF |
| RAD:MENU:0152 | 1A050152 | RW | Audio scope display [0152] | color | menu | - | 012801280128 |
| RAD:MENU:0153 | 1A050153 | RW | Audio scope display [0153] | number | menu | - | OFF |
| RAD:MENU:0154 | 1A050154 | RW | Audio scope display [0154] | color | menu | - | 012801280128 |
| RAD:MENU:0155 | 1A050155 | RW | CW contest counter [0155] | number | menu | - | 0 |
| RAD:MENU:0156 | 1A050156 | RW | Counter trigger memory [0156] | number | menu | - | 1 |
| RAD:MENU:0157 | 1A050157 | RW | Contest counter [0157] | number | menu | - | 1 |
| RAD:MENU:0158 | 1A050158 | RW | CW sidetone/keyer [0158] | number | menu | - | 0 |
| RAD:MENU:0159 | 1A050159 | RW | CW sidetone/keyer [0159] | number | menu | - | OFF |
| RAD:MENU:0160 | 1A050160 | RW | Keyer repeat seconds [0160] | number | menu | - | 1 |
| RAD:MENU:0161 | 1A050161 | RW | Keyer dot/dash weight [0161] | number | menu | - | 28 |
| RAD:MENU:0162 | 1A050162 | RW | CW sidetone/keyer [0162] | number | menu | - | 0 |
| RAD:MENU:0163 | 1A050163 | RW | CW sidetone/keyer [0163] | number | menu | - | OFF |
| RAD:MENU:0164 | 1A050164 | RW | CW sidetone/keyer [0164] | number | menu | - | 0 |
| RAD:MENU:0165 | 1A050165 | RW | CW sidetone/keyer [0165] | number | menu | - | OFF |
| RAD:MENU:0166 | 1A050166 | RW | RTTY decoder/log [0166] | number | menu | - | 0 |
| RAD:MENU:0167 | 1A050167 | RW | RTTY decoder/log [0167] | color | menu | - | 012801280128 |
| RAD:MENU:0168 | 1A050168 | RW | RTTY decoder/log [0168] | number | menu | - | OFF |
| RAD:MENU:0169 | 1A050169 | RW | RTTY decoder/log [0169] | number | menu | - | OFF |
| RAD:MENU:0170 | 1A050170 | RW | RTTY decoder/log [0170] | number | menu | - | OFF |
| RAD:MENU:0171 | 1A050171 | RW | RTTY decoder/log [0171] | color | menu | - | 012801280128 |
| RAD:MENU:0172 | 1A050172 | RW | RTTY decoder/log [0172] | color | menu | - | 012801280128 |
| RAD:MENU:0173 | 1A050173 | RW | RTTY decoder/log [0173] | number | menu | - | OFF |
| RAD:MENU:0174 | 1A050174 | RW | RTTY decoder/log [0174] | number | menu | - | OFF |
| RAD:MENU:0175 | 1A050175 | RW | RTTY decoder/log [0175] | number | menu | - | OFF |
| RAD:MENU:0176 | 1A050176 | RW | RTTY decoder/log [0176] | number | menu | - | OFF |
| RAD:MENU:0177 | 1A050177 | RW | RTTY decoder/log [0177] | number | menu | - | OFF |
| RAD:MENU:0178 | 1A050178 | RW | Scan behavior [0178] | number | menu | - | OFF |
| RAD:MENU:0179 | 1A050179 | RW | Scan behavior [0179] | number | menu | - | OFF |
| RAD:MENU:0180 | 1A050180 | RW | Voice memory playback [0180] | number | menu | - | OFF |
| RAD:MENU:0181 | 1A050181 | RW | Voice repeat seconds [0181] | number | menu | - | 1 |
| RAD:MENU:0182 | 1A050182 | RW | QSO recording [0182] | number | menu | - | OFF |
| RAD:MENU:0183 | 1A050183 | RW | QSO recording [0183] | number | menu | - | OFF |
| RAD:MENU:0184 | 1A050184 | RW | QSO recording [0184] | number | menu | - | OFF |
| RAD:MENU:0185 | 1A050185 | RW | QSO recording [0185] | number | menu | - | OFF |
| RAD:MENU:0186 | 1A050186 | RW | QSO recording [0186] | number | menu | - | OFF |
| RAD:MENU:0187 | 1A050187 | RW | QSO recording [0187] | number | menu | - | 0 |
| RAD:MENU:0188 | 1A050188 | RW | QSO recording [0188] | number | menu | - | 0 |
| RAD:MENU:0189 | 1A050189 | RW | Noise blanker shape [0189] | number | menu | - | 0 |
| RAD:MENU:0190 | 1A050190 | RW | Noise blanker shape [0190] | number | menu | - | 0 |
| RAD:MENU:0191 | 1A050191 | RW | VOX timing [0191] | number | menu | - | 0 |
| RAD:MENU:0192 | 1A050192 | RW | VOX timing [0192] | number | menu | - | 0 |
| RAD:MENU:0193 | 1A050193 | RW | Medium-wave attenuator [0193] | number | menu | - | OFF |
| RAD:MENU:0194 | 1A050194 | RW | Keyboard layout [0194] | number | menu | - | 0 |
| RAD:MENU:0195 | 1A050195 | RW | Voice TX level [0195] | number | menu | - | 0 |
| RAD:MENU:0196 | 1A050196 | RW | SSB DATA transmit bandwidth [0196] | bandwidth | menu | - | 00 |
| RAD:MENU:0197 | 1A050197 | RW | USB input inhibit [0197] | number | link | - | OFF |
| RAD:MENU:0198 | 1A050198 | RW | Front/microphone key assignment [0198] | number | menu | - | 0 |
| RAD:MENU:0199 | 1A050199 | RW | Front/microphone key assignment [0199] | number | menu | - | 0 |
| RAD:MENU:0200 | 1A050200 | RW | Front/microphone key assignment [0200] | number | menu | - | 0 |
| RAD:MENU:0201 | 1A050201 | RW | Front/microphone key assignment [0201] | number | menu | - | 0 |
| RAD:MENU:0202 | 1A050202 | RW | Front/microphone key assignment [0202] | number | menu | - | 0 |
| RAD:MENU:0203 | 1A050203 | RW | Front/microphone key assignment [0203] | number | menu | - | 0 |
| RAD:MENU:0204 | 1A050204 | RW | Scope band 1 edge 4 (0.03-1.6 MHz) [0204] | menu_edge | menu | - | 000300006001 |
| RAD:MENU:0205 | 1A050205 | RW | Scope band 2 edge 4 (1.6-2 MHz) [0205] | menu_edge | menu | - | 006001000002 |
| RAD:MENU:0206 | 1A050206 | RW | Scope band 3 edge 4 (2-6 MHz) [0206] | menu_edge | menu | - | 000002000006 |
| RAD:MENU:0207 | 1A050207 | RW | Scope band 4 edge 4 (6-8 MHz) [0207] | menu_edge | menu | - | 000006000008 |
| RAD:MENU:0208 | 1A050208 | RW | Scope band 5 edge 4 (8-11 MHz) [0208] | menu_edge | menu | - | 000008000011 |
| RAD:MENU:0209 | 1A050209 | RW | Scope band 6 edge 4 (11-15 MHz) [0209] | menu_edge | menu | - | 000011000015 |
| RAD:MENU:0210 | 1A050210 | RW | Scope band 7 edge 4 (15-20 MHz) [0210] | menu_edge | menu | - | 000015000020 |
| RAD:MENU:0211 | 1A050211 | RW | Scope band 8 edge 4 (20-22 MHz) [0211] | menu_edge | menu | - | 000020000022 |
| RAD:MENU:0212 | 1A050212 | RW | Scope band 9 edge 4 (22-26 MHz) [0212] | menu_edge | menu | - | 000022000026 |
| RAD:MENU:0213 | 1A050213 | RW | Scope band 10 edge 4 (26-30 MHz) [0213] | menu_edge | menu | - | 000026000030 |
| RAD:MENU:0214 | 1A050214 | RW | Scope band 11 edge 4 (30-45 MHz) [0214] | menu_edge | menu | - | 000030000045 |
| RAD:MENU:0215 | 1A050215 | RW | Scope band 12 edge 4 (45-60 MHz) [0215] | menu_edge | menu | - | 000045000060 |
| RAD:MENU:0216 | 1A050216 | RW | Scope band 13 edge 4 (60-74.8 MHz) [0216] | menu_edge | menu | - | 000060008074 |
| RAD:MENU:0217 | 1A050217 | RW | PTT terminal function [0217] | number | menu | - | OFF |
