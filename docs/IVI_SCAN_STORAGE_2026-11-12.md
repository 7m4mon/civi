# Scan starts and stored-slot writes — 2026-11-12

Source client 0.13.1 used the Pi TCP SOCKET gateway and IC-7300 MAIN 1.42
(owner-reported). The owner authorized continuing through band-stack and keyer
writes. Front-panel/Web operations were paused during the trials. PTT, VOX,
break-in, tuner and Split were verified OFF. No RF-start command was allowed.

## Scan starts and stops

| Procedure | Physical checks | Logical simulation checks |
|---|---:|---:|
| Five VFO scan modes | 23 | 32 |
| Three memory-context scan modes | 22 | 25 |

All checks passed. Logical counts include simulator-state assertions; the
simulation does not model physical frequency motion.

VFO context exercised PROGRAM, FINEPROGRAM, DELTA, FINEDELTA and AUTO. Memory
context exercised MEMORY, SELECTMEM and AUTO. This covers all seven `start()`
enum values, with AUTO in both contexts. **Frequency motion was observed in all
eight physical runs.** STOP was followed by three stable frequency samples in
each run. Command acceptance alone was not counted as proof of scan motion.
There is no scan-status query; stability is the measured stop evidence, not a
claim of direct status readback or signal-detection performance.

Existing P1/P2 records were read before and after VFO scans and remained
unchanged (500000 Hz / 29999999 Hz endpoints on this unit). The current delta
span, scan speed, resume behavior and scan-group filter were not changed. The
squelch code was temporarily raised from 65 to 255, then restored exactly to 65.
Both relative VFO frequency/mode/DATA/filter records were restored after each
procedure.

For memory scans, ordinary channels 94–99 were all verified empty before any
write. Six temporary 7.100–7.105 MHz LSB records were written, two per select
group 1–3, so whichever existing select-group filter was active had eligible
records. No group-filter command was sent. All six channels were addressed-
cleared and reread as empty during cleanup; remembered memory selection was
returned to 99 and the display returned to VFO mode.

Write-only delta-span changes, group-filter changes, select ON/OFF and explicit
selected-memory group assignment were not newly tested positively. Their prior
invalid-argument checks remain separate evidence. Unknown prior configuration
was not guessed for restoration. This is not a claim that every scan method
and every scan condition is fully verified.

## Band-stack and keyer writes

**89 checks passed on the physical radio and 89 in logical simulation.** All
33 complete band-stack records and all eight keyer texts were backed up to a
private file before the first write. No old text contents are reproduced here.

For each of eleven band groups and three slots, the test wrote a distinct
in-band frequency with USB / DATA ON / FIL2 while retaining the original tone
fields. The complete 14-byte readback matched the expected record. The original
record was immediately restored and reread. Representative frequencies used
the ordinary 1.8/3.7/7.1/10.1/14.1/18.1/21.1/24.9/28.5/50.1 MHz bands and
2.5 MHz general-coverage group, with a small slot-dependent offset.

Each keyer M1–M8 was given a distinct `CQ TEST, Mn ^AR` string, read back exactly,
then restored and reread. Only the keyer text storage command was allowed: no
CW send/play, key-down, VOX, break-in or PTT-start command was sent. Maximum-
length, empty-text and contest-number `*` combinations were not tested physically
by this procedure.

Final verification reread **all 33 original stack records and all eight original
keyer texts**, not only the last modified slot. All matched their backups. Both
VFO records also matched their saved baseline. No restoration errors occurred.

## Permissions, restoration and reproduction

The gateway's memory-write permission was enabled only for the memory-scan and
stored-slot phases. Its original configuration bytes were preserved privately,
restored afterwards, and CIVI restarted with memory permission false. No auth,
autostart or calibration policy was changed. Helper/panel were reused.

Manual opt-in tools:

- `tools/ivi_vfo_scan_acceptance.py` — `--allow-scan`.
- `tools/ivi_memory_scan_acceptance.py` — `--allow-memory-write`.
- `tools/ivi_stack_keyer_write_acceptance.py` — `--allow-storage-write`.

Each uses a wire mutation allowlist, saves its baseline before changes, and
performs cleanup in `finally`. They are not startup tasks or pytest tests. The
storage backup includes exact user text, so its private session file must not be
published without reviewing its contents.

Private evidence: `tmp/ivi-scan-20261112/{vfo,memory}-{physical,simulation}.json`
and `tmp/ivi-storage-write-20261112/{physical,simulation}.json`. These records
contain raw driver command histories, measured frequencies, complete backups
and restoration results. This work adds scoped physical evidence without
claiming complete IVI verification, registration or LXI conformance.

## Final checks and Pi reproduction

The three new manual tools also completed on Pi in logical simulation with
32 / 25 / 89 checks respectively. This reproduces command/state logic on the
Pi; it does not turn the motion-free simulator into scan-motion evidence.
No production source behavior changed in this work, so the prior complete
automated suite result was not rerun or relabeled as a new run.

Final live reads after the permission restoration and CIVI restart confirmed
all six scratch memories empty; SQL 65; selected 927000 Hz / AM / DATA OFF /
FIL2; other 14100000 Hz / USB / DATA OFF / FIL2; PTT OFF; and `0,"No error"`.
Configuration readback confirmed memory writes disabled. CIVI, helper and panel
were running, and the 101-active-rule/175-row audit consistency check passed.
Final readback evidence is `tmp/ivi-storage-write-20261112/final-state.json`.
