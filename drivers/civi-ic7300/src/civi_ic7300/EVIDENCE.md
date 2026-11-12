# Driver verification results — 0.13.1

Windows x64 source client → Pi TCP SOCKET gateway → USB IC-7300.

| Firmware / campaign | Final result |
|---|---|
| MAIN 1.41 core / receive | 40 core/receive checks, 65 receive-setting checks and all 216 menu reads passed |
| MAIN 1.42 TX Inhibit | Five setting/readback/invalid-type checks passed; original state restored |
| MAIN 1.42 VFO / scope | 57 VFO checks; 72 scope checks, 475-point sweep and 52 fixed-edge reads |
| MAIN 1.42 memory | 24 full-record checks, 29 selected-memory checks, 23 VFO-copy checks passed |
| MAIN 1.42 storage | 33 band-stack slots and 8 keyer texts written/read/restored; 89 checks passed |
| MAIN 1.42 scan | All seven start enums, eight runs, all seven ΔF widths and four select filters checked |
| Windows regression | 619 passed, one Linux-only skip; strict typing passed for 12 driver modules |
| Distribution | Clean wheel installation/read-only smoke and source→sdist→wheel builds succeeded for the recorded artifacts |

Counts belong to separate campaigns and are not a unique-test total. Setting changes were read back and restored. Raw NR/PBT quantization and mode-dependent settings are documented in API.md.

[Dated procedures, conditions and results](https://github.com/7m4mon/civi/blob/main/docs/IMPLEMENTATION_AND_TEST_RESULTS.md) provide the evidence. [The completion plan](https://github.com/7m4mon/civi/blob/main/docs/IVI_6_1_COMPLETION_2026-11-12.md) is the single list of subsequent verification and procedures.
