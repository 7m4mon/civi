# Implementation and verification scope (client 0.13.1)

## 2026-11-11 MAIN 1.42 TX Inhibit follow-up

After the owner updated firmware and restarted CIVI, `operations.transmit_inhibited`
get/set/readback worked on MAIN 1.42. True/False and three invalid-type cases
passed, original False restored, both VFO states unchanged and error queue empty.
No PTT start was sent; PTT samples remained OFF. Actual RF suppression was not
tested. Repository docs/IVI_TX_INHIBIT_2026-11-11.md records this focused source
driver check. All other 1.41 results below retain their original firmware scope.

## 2026-11-11 receive/core physical follow-up

Source client 0.13.1 on Windows / CPython 3.14.5 x64 used TCP SOCKET to the Pi
CIVI 0.1.0 gateway and physical IC-7300 MAIN 1.41 (owner-reported display value).
Core/receive 40 checks and receiver-setting 65 checks passed; 290 of 292
descriptor/menu reads succeeded. All 216 menu selectors read successfully.
AM filter shape was unavailable but USB/CW/LSB worked. TX Inhibit requires
firmware 1.42 and was unavailable on 1.41. NR/PBT quantization was explicitly
recorded; requested raw codes need not echo exactly. Both VFOs, saved receive
settings and non-meter readbacks were restored/unchanged. No transmission,
memory/menu/calibration/power write or permission change occurred.

Repository docs/IVI_RECEIVE_ACCEPTANCE_2026-11-11.md records the exact scope,
contexts, initial exact-echo assumption failures and final acceptance criteria.
This is source-driver hardware evidence, not a new wheel-installation test or
the complete Core unit-test procedure. Getters, setters and unavailable firmware
features remain distinct in the worklist. Other APIs do not inherit these results.

0.13.1 has limited physical read-only verification on 2026-11-10: an installed
Windows driver used INSTR location forms to read the IC-7300 through the Pi
gateway. Frequency 774000 Hz, AM, PTT OFF and an empty error queue were checked.
No settings were written. The 0.12.1 results below retain their original scope;
STYLE.md records the separate naming/mock review.

These labels are used consistently in the client help. They are not IVI
conformance/certification labels, and are not interchangeable:

| Label | Meaning |
|---|---|
| Implemented | Code/mapping exists; this alone proves no test or hardware behavior |
| Mock verified | The named scenario passed in independent simulation and/or loopback TCP with MockBackend; values, modes and side effects outside that scenario remain unverified |
| Hardware verified | Only an explicitly dated physical-device record, with its stated version, direction, selectors and conditions; not inherited by newer client versions |
| Unverified / outside scope | No relevant evidence is claimed |

REFERENCE.md/public-api.json index implementation contracts, not per-member test
coverage. A generated row or parser-accepted alias is not a successful CI-V
transaction or a physical RF measurement. Initial 0.12.1 development tests were
mock-only. A subsequent limited physical smoke check on 2026-11-09 verified the
specific current-client cases below; it is not complete hardware verification.

0.13.0 local keyer names and all eight mock record writes/readbacks/restores
are covered by test_python_repeated.py; these are not physical-device results.

## Current evidence map (reconciled 2026-11-12)

The earlier release notes above/below retain their original version/date scope.
The current per-entry review is repository
`docs/IVI_VERIFICATION_WORKLIST_2026-11-11.csv`, with the reviewed additional-test
plan in `docs/IVI_ADDITIONAL_TESTS_2026-11-12.md`. The 352 entries are not 352
independent hardware experiments. Abstract declarations, local values and shared
implementations are linked to their concrete evidence. No placeholder is turned
into a blanket pass, and no getter proves a setter.

| Group | Recorded physical scope | Remaining scope |
|---|---|---|
| Core / Direct I/O | MAIN 1.41 receive/core procedure: identity, queue, metadata, timeout property, string/bytes I/O; older typed reset success retained | Consolidate current checked/status/constructor paths and current-artifact reset; reuse shared concrete interfaces |
| Receiver / gains / meters | Current getter inventory and 65 receiver-setting cases; historical SCPI setters also recorded | 31 current typed setter paths/bounds/enums, plus scoped NR/PBT coercion gaps; read-only meters need no full-scale RF test |
| Menus | 216 current typed reads; historical SCPI changed/read/restored 189 selectors (186 ordinary, three link) | Current typed write/method evidence and missing values; 17 side-effect-sensitive ordinary selectors, link/calibration kept separate; mock 215 writes are not hardware passes |
| Memory / nested views | All 101 memory properties read, methods on 94-99; 29 selected-memory cases; full 33 stack and eight keyer roundtrips; nested metadata traversal | Remaining memory control-method instances and representative record/text boundary cases; do not repeat all successful stack/keyer normal roundtrips |
| Scope | 72 control checks, 475-point sweep, 52 fixed-edge reads on MAIN 1.42 | Fixed-edge write path and its applicable boundaries; ordinary scope controls already recorded |
| VFO / scan | VFO enum/bounds/swap/select; COPY both ways (23); all scan modes; seven half-spans (33); select flags/filter cases (34), with saved-state restoration | No duplicate normal scan/COPY test scheduled; wide-span full endpoints and all signal conditions are not claimed |
| Band edges / DATA | 40 band records including empty user slots; DATA through VFO mode has separate evidence | No calibration/user-band writes; RAD:DATA typed path still distinct from VFO MODE; old SCPI DATA evidence retained |
| TX / CW / voice / tuner / power | MAIN 1.42 TX Inhibit setting/readback; idle getters; historical idle-stop rejection | Active RF/stop/deadline, audio and power procedures require separately scoped conditions; no active RF proof inferred |
| Local helpers / records / errors | Existing software vectors/metadata/alias tests and decoded physical records | Eight positive typed-menu factory calls were not located; local-only, no new radio mutation needed |
| Package / registration | Earlier clean Windows wheel/install and source hashes recorded | Final artifacts/examples/platform setup and IVI naming/registration remain; later source changes are not a retest of the earlier wheel |

## Where the records live

Repository records include docs/VALIDATION.md, docs/PYTHON_*_2026-11-09.md,
docs/PARTIAL_RESET_CAPTURE_2026-11-08.md and the earlier hardware/TCP reports.
The limited 0.12.1 historical record is docs/PYTHON_HARDWARE_2026-11-09.md; its
local JSON retains before/after snapshots, mutation allowlist and tested-code hashes.
Tests named above are in repository tests/. The package carries the scope of
these results; it does not bundle or run physical-radio test scripts on install.
COMPLIANCE.md records the exact OS/runtime and release test totals.

The supported/tested runtime record is Windows 11 (25H2, build 26200.9711),
CPython 3.14.5 x64. Pure-Python implementation and a >=3.11 requirement do not
prove all Python versions, Linux/Pi or 32-bit execution have passed the complete
client suite. Gateway-only Pi tests remain separate evidence.

0.13.1 location parsing/transport selection is checked against a loopback
MockBackend TCP server. Socket destinations omit credential references; no
physical radio was involved. This is distinct from the retained 0.12.1 record.

## 2026-11-10 Pi deployment and read-only checks

Repository docs/RPI_LXI_FIXES_2026-11-10.md records the 0.13.1 installed-client
location/real TCP readings, wired NIC XML/discovery, name truncation/persistence
and restoration, and actual Identify/cable-fault/recovery/start/stop behavior.
Pi 3.13.5 ran 72 selected mock tests with one Node-only skip; this is not a
complete Pi/client platform-support matrix. The original physically tested
wheel/code hashes remain in local records. A documentation-only rebuild does
not extend the physical results to untested APIs, settings or RF behavior.

## 2026-11-12 additional source-client API verification

Repository docs/IVI_API_ACCEPTANCE_2026-11-12.md records 57 VFO checks,
72 scope checks plus 52 fixed-edge reads, 142 storage reads, 15 safe scan
checks and 40 band reads with 49 checks on MAIN 1.42. Both VFOs and modified
settings were restored. Empty user-band responses (FF) initially quarantined the
link; the gateway and source client now return FF and None respectively.
The successful band rerun used modified source still labeled 0.13.1, not the
earlier installed wheel. No storage/calibration writes or RF start were tested.
Positive scan start/group operations remain unverified. This does not complete
whole-driver IVI testing or registration.

## 2026-11-12 addressed memory writes

Repository docs/IVI_MEMORY_WRITE_2026-11-12.md records 24 checks in simulation
and on MAIN 1.42. Empty channel 99 was used for eight complete record write,
exact readback and clear cycles. The slot ended empty; both VFO snapshots were
unchanged. Gateway memory permission was temporarily enabled then restored to
false, with CIVI running. Selected-memory action APIs were not exercised.
No RF start, keyer/band-stack/calibration writes or complete IVI claim is implied.

## 2026-11-12 selected-memory actions

Repository docs/IVI_SELECTED_MEMORY_2026-11-12.md records 29 checks on MAIN
1.42 and corrected logical simulation: select channel 99, store from VFO, enter
memory mode, copy back to VFO, and clear in memory mode. The initial 0B NAK
in VFO mode is retained. Channel selection alone preserves VFO/memory mode;
both mock models were corrected accordingly. Both VFO records were restored,
99 ended empty, memory permission returned to false, and no RF start was sent.
This is scoped source-client evidence, not a retest of the previous wheel.

## 2026-11-12 VFO COPY

Repository docs/IVI_VFO_COPY_2026-11-12.md records 23 simulation and 23 MAIN
1.42 checks through the source client: A->B and B->A with distinct frequencies,
modes, DATA and filters; source unchanged and repeated COPY idempotent. Both
original frequency/mode/DATA/filter records were restored and owner-confirmed A
reselected. No RF start or stored-record/permission writes. This does not extend
to every other receiver setting or imply a fresh installed-wheel verification.

## 2026-11-12 scan starts, band-stack and keyer writes

Repository docs/IVI_SCAN_STORAGE_2026-11-12.md records all seven scan-start
enums (eight physical runs, AUTO in both contexts), observed frequency motion
and stable samples after STOP. VFO/memory phases passed 23/22 checks; logical
simulation passed 32/25 state checks and does not model motion. SQL, both VFOs
and initially empty scratch channels 94-99 were restored; delta span and scan
group filter were unchanged. Positive span/group/select setting changes remain
unverified. A further 89 checks passed in simulation and on MAIN 1.42 for all
33 band-stack slots and all eight keyer texts: exact write/read and immediate
restoration, then a full backup comparison. No CW or RF start was issued.
Memory permission was restored to false. This is scoped source-client evidence,
not a complete IVI verdict or fresh verification of an installed wheel.

## 2026-11-12 scan settings follow-up

Repository docs/IVI_SCAN_SETTINGS_2026-11-12.md adds all seven delta half-spans
in LSB (33 physical / 41 logical checks), select OFF/ON and assignment 1-3, and
ALL/1/2/3 group filters (34 physical / 35 logical checks). Physical assignments
were read through memory records; filtered scan samples matched eligible
frequencies. Wide-span full endpoints were not measured. The owner provided
original +/-10kHz and star1 filter values and reported visual operation OK.
Restore commands for unreadable span/filter were accepted; effective previous
select group was reread, scratch 94-99 emptied and VFO/SQL restored. Simulation
uses logical state and does not model motion or couple selection to payloads.
This supersedes the earlier positive-test gaps for these four methods, without
claiming whole-driver verification, registration or AM compatibility.
