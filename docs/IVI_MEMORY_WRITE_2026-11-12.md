# Single-channel memory write acceptance — 2026-11-12

The owner authorized use of an unused memory channel. Source driver 0.13.1
connected through TCP SOCKET to the Pi CIVI gateway and IC-7300 MAIN 1.42
(owner-reported firmware). Channel **99** was read and verified empty before
the first write. P1/P2 and existing populated entries were not modified.

## Result

**24 checks passed in logical simulation and 24 on the physical radio.**
Eight records covered LSB, USB, AM, CW, RTTY, FM, CW-R and RTTY-R, with filter
numbers 1–3, DATA values, all three tone-mode codes, Split OFF/ON, select groups
0–3, distinct receive/transmit frequencies, and ten-character ASCII names.
Each readback matched the complete expected 39-byte record exactly. Each record
was then cleared and read back as empty. This covers the recorded combinations,
not every possible Cartesian combination or RF behavior of those settings.

The test alternated the `record` property setter/getter and `write_and_read()`;
`clear()` was checked after every record and again in final cleanup. Invalid
record type and attempts to clear P1/P2 were rejected before I/O.

Both VFO frequency/mode/DATA/filter snapshots were identical before and after.
PTT, VOX, break-in and tuner were OFF in preconditions and final checks. No
transmission start was issued. Channel 99 ended empty.

## Temporary permission and execution

The gateway initially had `[permissions].memory = false`. A private, mode-0600
backup preserved the original configuration bytes; only that permission was
temporarily enabled, with a controlled restart of CIVI. After the test, the
original bytes were restored and CIVI restarted with memory permission **false**.
Helper and panel were reused. No autostart setting or Web password was changed.

An earlier precondition check found the serial link quarantined. No memory or
permission write occurred in that attempt. The owner restarted CIVI, after which
the test connected normally. This is not recorded as a successful recovery API
test.

## Evidence and limits

Manual opt-in tool: `tools/ivi_memory_write_acceptance.py`, requiring
`--allow-memory-write`; channel range is restricted to ordinary memories 1–99.
The initial slot must be empty. Its wire guard allows only addressed content
writes to the selected test slot; no VFO changes, scan, keyer, band-stack,
calibration or transmission writes are allowed.

Private session evidence: `tmp/ivi-memory-write-20261112/simulation.json` and
`physical.json`. The physical file contains before/after VFO snapshots, exact
record vectors, command history and all 24 check results.

The selected-memory actions `enable()`, `select()`,
`store_current_in_selected()`, `copy_selected_to_vfo()` and `clear_selected()`
were not exercised by this addressed-record procedure. Their positive hardware
tests remain separate work. This result does not complete IVI verification or
registration and does not establish LXI conformance.

## Post-test connection issue

The final trial's own cleanup confirmed empty channel 99, unchanged VFOs and
idle conditions. After restoring the original configuration and restarting CIVI,
a separate final read encountered `-365,"Link quarantined; reset radio/link and
recover explicitly"`. Helper, server and panel processes remained running and
memory permission was verified false, but current radio values could no longer
be read. The restart-related connection issue is under investigation; this
post-restart failure is not presented as a successful final connection check.

## Controlled repeat and successful final connection

The owner subsequently reported operating the front panel during the earlier
sequence and requested a repeat. No causal conclusion is drawn from that report.
With front-panel and Web operations paused, the same physical test passed all
24 checks again. Channel 99 was empty before and after. The gateway's memory
permission was restored to false and CIVI restarted. Three subsequent samples,
three seconds apart, all returned:

- `RAD:MEM:CONTENT? 99`: `FF` (empty).
- PTT: OFF; displayed frequency/mode: 927000 Hz / AM.
- Selected/other VFO frequencies: 927000 / 14100000 Hz.
- Error queue: `0,"No error"`.

The provided initial log contains a complete matched `03 FF` frame; it is not a
memory-clear ACK or an unmatched memory-content response. Its cause remains
unconfirmed and it did not recur in the controlled repeat. A provisional local
change to retry that sentinel as unavailable frequency data was considered but
withdrawn; it was never deployed to the Pi. The repeat ran the existing strict
frequency decoder, and no gateway behavior change was needed for this result.

Additional private evidence: `physical-repeat.json` and
`post-restart-repeat.json` under `tmp/ivi-memory-write-20261112/`. The original
failure and first successful write/read/clear result are retained.

## Empty-channel displayed-state reproduction

At the owner's request, the empty-channel condition was reproduced explicitly.
With CIVI temporarily stopped to maintain exclusive serial access, the test
selected channel 99 (`08 00 99`) and entered memory mode (`08`). Three raw `03`
queries each returned `FE FE E0 94 03 FF FD`. Raw mode query `04` likewise
returned `FE FE E0 94 04 FF FD`. PTT remained OFF. This confirms that empty
displayed memory is a reproducible source of these sentinels on this MAIN 1.42
unit; it does not prove the precise timing of the owner's earlier operation.

Sending `07` returned to VFO mode. Displayed frequency/mode and both relative
VFO frequency/mode records exactly matched their saved baseline (927000 Hz / AM
selected, 14100000 Hz / USB other). No memory contents or permissions were
changed. The remembered memory selection is now 99; CI-V provides no readback
of the previous selected channel in the implemented interface. CIVI was then
restarted. Evidence: `tmp/ivi-memory-write-20261112/empty-frequency-raw.json`.

The first exclusive-access attempt stalled during CIVI shutdown before serial
test operations began. Its pending diagnostic/launcher were stopped; the server
then required termination after a further bounded graceful-stop attempt. The
second diagnostic completed with normal VFO restoration and app restart. This
shutdown observation is separate from the confirmed empty-memory response.

The subsequent [empty-memory fix](EMPTY_MEMORY_2026-11-12.md) now keeps the
connection running and automatically resumes ordinary values on return to VFO.
