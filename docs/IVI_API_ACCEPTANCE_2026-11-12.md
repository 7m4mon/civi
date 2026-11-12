# Additional IVI API acceptance — 2026-11-12

The source Python client 0.13.1 was exercised through the Pi TCP SOCKET
gateway against the owner's IC-7300 MAIN 1.42. The owner identified the initial
selection as VFO A, since CI-V does not report the absolute selected A/B name.
These are additional API tests, not a repeat of every earlier 1.41 test.

| Procedure | Physical result | Simulation result |
|---|---|---|
| VFO selection, relative views, frequency/mode, swap and restoration | 57 checks passed | 57 checks passed |
| Memory, band-stack and keyer reads | 142 addressed reads; 200 local checks passed | 142 reads; 198 local checks passed |
| Scope controls and complete sweep | 72 checks passed; 475-point sweep; 52 fixed-edge records read | 72 checks passed; 52 fixed-edge reads |
| Scan STOP, resume setting and invalid arguments | 15 checks passed | 15 checks passed |
| Transmit band-edge record reads, after the fix below | All 40 records read; 49 checks passed | Counts were zero; nine local checks passed; empty-slot handling also unit-tested |

## Scope of successful tests

VFO tests covered both relative views, frequency bounds (30 kHz and 60 MHz),
7.1 MHz, all eight supported modes, USB DATA OFF/ON and filters 1–3. Both
frequency/mode records were restored, with A selected. COPY was not tested.

Storage reads covered 101 memories, 33 band-stack slots and eight keyer texts.
The physical memories contained 99 empty and two populated records. Record
serialization and collection selection were checked. Stored contents are omitted
from this report. No stored record was written or cleared.

Scope tests restored all 14 saved controls and verified the VFO records were
unchanged. Fixed-edge records (13 bands, four edges each) were read only.
Legacy property names need care: `vbw_enabled` represents Narrow/Wide, and
`marker_enabled` represents Filter Center/Carrier Point; neither is a visibility
or enable switch. Mode-dependent settings were tested in their applicable modes.

Scan STOP was accepted. The prior running state cannot be queried, so this does
not prove restoration of an ongoing scan. Resume was changed, read through menu
0179, and restored. Positive scan start, span, select/group and memory assignment
operations were not exercised; invalid arguments were checked before I/O.

## Found and fixed: unprogrammed user band-edge records

The radio reported ten factory records and thirty user slots. All ten factory
records and user records 1–16 decoded successfully. Reading user record 17
returned gateway error `-310,"Malformed extended CI-V response"`, and the
backend quarantined the link. The owner supplied the exact terminal response:
`FE FE E0 94 1E 03 17 FF FD`. The matching response contains the single-byte
empty sentinel, not an eleven-byte record. This behavior is observed on this
MAIN 1.42 unit; the local reference's ordinary BCD-pair diagram alone did not
document it sufficiently for the original decoder.

The gateway now accepts exactly `FF` on user-slot reads, while preserving strict
record validation and rejecting `FF` writes. The Python `read_user()` and
`write_and_read_user()` return types now allow `None` for this read result.
`BandEdges.from_hex()` still requires a complete valid record. No delete command
was introduced. Malformed payloads still quarantine the serial link.

After a user-performed USB reconnection and CIVI restart, all ten factory and
thirty user slots read successfully: sixteen populated user slots and fourteen
empty user slots. All 49 checks passed, including rejection of simulation-only
permission changes on a real driver before I/O. No band-edge/calibration writes
occurred. The original partial failure evidence is retained alongside the rerun.

## Reproduction and evidence

Manual tools: `tools/ivi_vfo_acceptance.py`,
`tools/ivi_storage_read_acceptance.py`, `tools/ivi_scope_acceptance.py`,
`tools/ivi_scan_safe_acceptance.py`, and `tools/ivi_band_read_acceptance.py`.
They are not run by startup or the automated test suite. VFO requires the initial
A/B selection; scope and resume modifications require explicit command options.

Session evidence is stored privately under `tmp/ivi-api-next-20261112/`:
`vfo-expanded-physical.json`, `storage-physical.json`, `scope-physical.json`,
`scan-physical.json`, `bands-physical.json`, and corresponding simulation files.
`bands-physical.json` is the initial partial failure; `bands-physical-fixed.json`
is the successful rerun. The latter used the changed source client, still labeled
experimental 0.13.1; it is not evidence for the earlier built/installed wheel.

No RF transmission was started. Successful modifying procedures saved and
restored their applicable baseline. This report does not establish complete IVI
entry-point coverage, registration, or LXI conformance.

## Software verification and final state

After regenerating the packaged menu schema for the added codec metadata,
Windows ran **609 passed, one Linux-specific skip**. The Pi ran all **122**
targeted extended-CI-V/band-driver tests successfully using its existing isolated
test libraries; its normal runtime environment intentionally has no pytest.
Strict mypy passed all twelve driver source files. Generated help, command audit,
control docs, release docs and the LXI audit consistency checks passed.

Pi CIVI/helper/panel were running at the end. Final read-only checks returned
PTT OFF, selected 928000 Hz / AM / DATA OFF / FIL2, other 14100000 Hz / USB /
DATA OFF / FIL2, and `0,"No error"`. The owner-confirmed initial A selection was
restored by the VFO procedure; the final relative queries cannot independently
identify absolute A/B.
