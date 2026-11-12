# Selected-memory actions — 2026-11-12

The owner authorized using unused ordinary memory channels. The source Python
driver exercised empty channel 99 through the Pi gateway with IC-7300 MAIN 1.42.
No front-panel/Web operation was requested during the procedure. Initial PTT,
VOX, break-in, tuner and Split were OFF. The initial display matched the selected
VFO. Both relative VFO frequency/mode/DATA/filter records were saved before any
mutation, and the initial addressed channel-99 record was confirmed empty.

## Successful procedure

**29 checks passed on the physical radio and 29 in logical simulation.**

1. Select memory 99, return to VFO mode, and set the selected VFO to
   7100000 Hz / LSB / DATA OFF / FIL1.
2. `store_current_in_selected()` (09) saved the current state. Addressed
   readback confirmed a populated record with matching receive frequency,
   mode, DATA and filter, and Split OFF. The full returned record was saved.
3. Set the selected VFO to a distinct 7150000 Hz / USB / DATA ON / FIL3.
4. `enable()` (08) displayed the stored 7100000 Hz / LSB memory.
5. `copy_selected_to_vfo()` (0A), then VFO mode, produced the stored
   7100000 Hz / LSB / DATA OFF / FIL1 in the selected VFO. The other VFO was
   unchanged.
6. Reselect 99 and explicitly enter memory mode. `clear_selected()` (0B)
   succeeded, and addressed readback returned empty.
7. Return to VFO mode and restore both VFO records. Final channel 99 was empty,
   Split remained OFF and the radio was idle. Invalid selectors were rejected
   before I/O.

The final saved/read VFO states were 927000 Hz / AM / DATA OFF / FIL2 selected
and 14100000 Hz / USB / DATA OFF / FIL2 other. Absolute A/B was not changed by
this procedure. The remembered selected memory is 99; the implemented interface
does not query the previous memory selection.

## Discovered mode precondition

The first physical run successfully saved, displayed and copied the record but
received `-200,"Radio rejected CI-V 0B (NAK)"` on clear after returning to VFO
mode and merely reselecting the channel. Cleanup used the addressed clear,
restored both VFOs and restored the gateway configuration. That failure record
is retained. A second run explicitly entered memory mode before 0B and passed.

A separate read-only-content probe confirmed the distinction: while VFO mode
showed 927000 Hz, `RAD:MEM:SELECT 99` alone preserved that displayed frequency.
Only `RAD:MEM:ENABLE` entered the empty memory, yielding the expected -230 on
display-frequency query. Returning to VFO restored 927000 Hz without recovery.

The gateway mock and logical driver simulator previously entered memory mode
implicitly on channel selection. Both now preserve the existing mode and reject
0B in VFO mode. The driver method documents the explicit `enable()` precondition;
it does not insert unrequested mode changes. Regression tests cover rejection
without deletion and subsequent successful clear after entering memory mode.

## Permissions, limits and evidence

Only `[permissions].memory` was temporarily enabled using a private backup.
After each physical run, original configuration bytes were restored and CIVI
restarted with memory writes disabled. Helper/panel were reused; no autostart
or authentication changes were made. No RF start, calibration, keyer or
band-stack writes were sent. P1/P2 were untouched.

Manual tool: `tools/ivi_selected_memory_acceptance.py`, requiring explicit
`--allow-memory-write`. Its mutation allowlist permits only the selected test
channel's memory actions, VFO mode changes, relative frequency/mode changes and
addressed empty cleanup of channel 99. It does not coordinate other clients;
the operator must avoid concurrent local/Web changes during the trial.

Private files under `tmp/ivi-selected-memory-20261112/`:
`physical.json` (initial VFO-mode clear rejection), `physical-memory-mode.json`
(29 successful checks), `simulation.json` (29 checks on corrected simulation),
and `selection-mode.json` (mode probe). Full wire history and before/after
snapshots are preserved. This closes the recorded positive tests of these five
selected-memory actions on this setup; it does not prove every channel,
parameter combination, persistent-reboot behavior or complete IVI conformance.

Software verification after the simulation corrections: Windows full suite
619 passed with one Linux-specific skip; Pi related suite 122 passed and its
manual logical procedure passed all 29 checks. Strict mypy passed all twelve
driver source files, and generated help/command audit/release-doc checks passed.
Final live queries after restoring memory permission and restarting CIVI showed
empty 99, 927000 Hz / AM selected, 14100000 Hz other, PTT OFF and no SCPI error.
CIVI, helper and panel remained running.
