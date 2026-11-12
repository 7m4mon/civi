# Delta span and select settings — 2026-11-12

Source Python client 0.13.1 connected to the Pi TCP SOCKET gateway and IC-7300
MAIN 1.42 (owner-reported). No RF start was allowed. Front-panel/Web operations
were paused during each physical trial. PTT, VOX, break-in and tuner were OFF.

## Operator-confirmed restoration values

The owner reported an original delta half-span of **±10 kHz**. A PROGRAM display
showing 0.500–29.99999 MHz was correctly treated as P1/P2 scan endpoints, not as
evidence of an ALL select filter. Filter changes were initially deferred.
After switching the display to empty memory 99 without changing the filter,
the owner read **`SELECT No.: ★1`**. Only then were filter changes tested.

The saved selected VFO was 7055650 Hz / LSB / DATA OFF / FIL2, and the other VFO
was 14100000 Hz / USB / DATA OFF / FIL2. SQL code was saved before each phase.

## Delta span: 33 physical checks, 41 logical checks passed

All seven half-spans (±5, ±10, ±20, ±50, ±100, ±500 kHz and ±1 MHz) were set
through `scan.set_delta_span_hz()`. These are scan ranges about the center,
**not receive-filter bandwidths**. The physical test used LSB / DATA OFF / FIL1,
a 7.1 MHz center, and temporarily closed squelch (raw 255).

For every setting, the checked command completed, DELTA scan started, twelve
frequency samples showed motion within the requested center ± span, and STOP
was followed by three stable frequency samples. This demonstrates acceptance
and sampled operation at every enum value. The short trials did not measure
both full excursion endpoints for every wide span; in particular, samples for
the wider settings only covered the first few kHz of movement. No complete
wide-span coverage or AM-mode compatibility is claimed.

The original ±10 kHz restore command was sent and accepted in LSB before
restoring the original VFO records and SQL. There is no direct span query;
physical restoration is command-acceptance evidence against the owner-provided
baseline, while logical simulation also asserted its stored span. The owner
reported that delta scanning looked correct on the front panel.

## Select settings: 34 physical checks, 35 logical checks passed

An initial 21-check physical/logical phase verified select flags alone without
changing the then-unknown filter. The complete phase subsequently tested:

- `set_memory_group(0..3)`: ALL, ★1, ★2 and ★3.
- `assign_selected_memory_group(1..3)`.
- `set_select_enabled(False/True)` after each assigned number.

Ordinary memories 94–99 were verified empty before use. Six temporary LSB
records at 7.100–7.105 MHz were written, two per select group. All four filters
accepted the command and produced moving SELECTMEM scans. Frequency samples
were checked against the actual eligible set, not merely against a successful
ACK: ★1 visited 7.100/7.101 MHz, ★2 visited 7.102/7.103 MHz, and ★3 visited
7.104/7.105 MHz. ALL samples included members of different groups. The short
ALL sample does not claim to have visited every memory in a fixed order.

On memory 99, OFF read back select group zero. ON revealed the previously
effective remembered group **1**, using the addressed memory record; this was
not an invented query of the write-only action. Assigning 1, 2 and 3 each read
back exactly, and OFF/ON cleared/reapplied each group as expected. The previous
effective remembered group was restored to 1 and verified with another OFF/ON
plus record read. If the radio had no previous explicit assignment, this
preserves the documented default effective group rather than an unqueryable
internal history marker.

The filter was restored by a checked ★1 command. Its current value cannot be
queried directly by this interface. All six scratch records were then cleared
and reread as empty, selected memory returned to 99, the display returned to
VFO mode, and the original VFO/SQL records were restored. The owner also
reported that the operation looked correct on the radio.

Logical simulation checks its scan state and does not model scan motion or
couple select assignments to stored memory payloads. Physical flag verification
used the radio's memory records. The separate logical and physical sources are
explicit in the reports; simulation is not presented as RF/scan-motion evidence.

## Tools, permissions and evidence

`tools/ivi_scan_span_acceptance.py` requires the operator-known original span.
`tools/ivi_scan_select_acceptance.py` requires explicit opt-in; its optional
`--initial-group` must be owner-confirmed before filter changes. Omitting it
skips all filter commands and limits scratch use to channel 99. Both tools use
mutation allowlists and final cleanup. They are not automatic startup/tests.

The memory-write permission was temporarily enabled with a private original-
configuration backup and restored to false after each memory phase, followed by
CIVI restart. No authentication, autostart, calibration or transmit policy was
changed. P1/P2, keyers and band-stack records were not written in these trials.

Private evidence under `tmp/ivi-scan-settings-20261112/`:
`span-{physical,simulation}.json`, `select-no-filter-{physical,simulation}.json`,
`select-filter-physical.json`, and `select-filter-simulation.json`. Files contain
owner-provided baselines, command history, samples and restoration results.

This completes the recorded positive scan-setting API cases on this setup,
alongside the earlier start/STOP/resume and invalid-argument procedures. It is
not a whole-driver IVI, registration or LXI conformance verdict.

## Final verification

Pi logical reproduction completed all 41 span and 35 select/filter checks. The
existing scan command-byte/validation suite passed all 16 cases on Windows and
all 16 on Pi. Generated help, command/control documentation, release-doc and
LXI audit consistency checks passed. Production scan behavior was unchanged;
the driver docstring now explicitly calls the span a half-span. A new complete
automated-suite run is not claimed for these manual procedures/doc updates.

Final live readbacks: memories 94–99 all empty; SQL 65; selected 7055650 Hz /
LSB / DATA OFF / FIL2; other 14100000 Hz / USB / DATA OFF / FIL2; PTT OFF; and
`0,"No error"`. The gateway's memory permission was false, and CIVI, helper and
panel remained running. The unreadable original span/filter were restored by
the acknowledged ±10 kHz / ★1 commands as described above. Evidence:
`tmp/ivi-scan-settings-20261112/final-state.json`.
