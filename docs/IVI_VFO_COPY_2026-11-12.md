# VFO COPY acceptance — 2026-11-12

Source Python driver 0.13.1 exercised `vfos.copy_selected_to_other()` through
the running Pi TCP SOCKET gateway and IC-7300 MAIN 1.42 (owner-reported).
The initial absolute selection A was retained from the owner's confirmation
in this ongoing session; CI-V does not independently report absolute A/B.
Both relative frequency/mode/DATA/filter records were read before changes.
Initial PTT, VOX, break-in, tuner and Split were OFF.

**23 checks passed in logical simulation and 23 on the physical radio.**

| Copy source | Selected source | Distinct destination before COPY | Result |
|---|---|---|---|
| A | 7100000 Hz, LSB, DATA OFF, FIL1 | 14100000 Hz, USB, DATA ON, FIL3 | B matched source; A unchanged |
| B | 14100000 Hz, USB, DATA ON, FIL3 | 7100000 Hz, LSB, DATA OFF, FIL1 | A matched source; B unchanged |

Both cases verified the displayed source frequency/mode and continued idle
state. Repeating COPY after each successful copy was idempotent for all recorded
fields. Cleanup reselected A and restored the two original records exactly:
selected 927000 Hz / AM / DATA OFF / FIL2, other 14100000 Hz / USB / DATA OFF /
FIL2. Split remained OFF and PTT/VOX/break-in/tuner remained OFF.

This test verifies frequency, mode, DATA and filter number only. It does not
establish COPY semantics for every other receiver parameter or test arbitrary
operating-mode combinations. The source setup/readback commands and COPY itself
all used the driver. No memory, keyer, band-stack, calibration, power, permission
or transmission-start writes were allowed by the wire guard.

Manual tool: `tools/ivi_vfo_copy_acceptance.py`, requiring explicit
`--allow-vfo-copy` and an owner-confirmed `--initial-vfo`. It saves baseline
state before mutations, uses an allowlist and restores in final cleanup.
It cannot lock out front-panel or other client changes; the owner was asked to
pause such operations during the procedure. It is not run by startup or pytest.

Private evidence: `tmp/ivi-vfo-copy-20261112/simulation.json` and `physical.json`,
including command history, per-direction before/after snapshots and restoration.
No production source behavior was changed for this test. Prior full-suite
results are retained; a new complete automated run is not claimed here.
This closes the scoped positive COPY procedure, not whole-driver IVI testing
or LXI registration/conformance.
