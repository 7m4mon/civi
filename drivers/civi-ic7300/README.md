# CIVI IC-7300 Python client 0.13.1

Version 0.13.1 fixes LXI network-resource location parsing. SOCKET keeps its
explicit port; INSTR locations map to raw TCP 5025 without HiSLIP or credentials.
See [API.md](src/civi_ic7300/API.md) for the complete mapping and limitations.

Version 0.12.1 added the [public-member reference](src/civi_ic7300/REFERENCE.md),
[evidence scope](src/civi_ic7300/EVIDENCE.md) and the prescribed
[IVI notice](src/civi_ic7300/IVI_NOTICE.md). The reference indexes signatures,
types, access, SCPI and detailed value/usage guides, without promoting mock or
parser tests to hardware verification. Invalid error replies now consistently
raise ProtocolError. Initial development tests were mock-only; a subsequent limited
physical check is recorded in EVIDENCE.md and COMPLIANCE.md.

Version 0.12.0 adds a [unified SCPI inventory](src/civi_ic7300/SCPI_COVERAGE.md):
339 extended plus eleven base/special headers, documented aliases and explicit
unsupported forms. New [base APIs](src/civi_ic7300/BASIC.md) expose full gateway
identification, clear/completion, manual firmware metadata and guarded PTT
start/stop. Mock tests only; no physical transmission or Pi changes.

Version 0.11.0 adds `band_stacks[band].slots[slot]`, with a pure band-level
collection at `band_stacks.bands`. Existing tuple indexing, 33-slot length and
flat iteration are preserved. Both paths share stable slot views and live
readbacks. See [HIERARCHY.md](src/civi_ic7300/HIERARCHY.md) for typed interfaces,
iteration and permission/status behavior. No new Pi or radio tests were performed.

Version 0.10.0 makes every typed API follow the status-check option. Use
`with device.checked():` to temporarily enable checks for a protected sequence.
With checks OFF, queued write failures are not automatically raised; inspect
errors explicitly. A gateway ERROR query reply now raises QueryError and preserves
the queue. See [STATUS.md](src/civi_ic7300/STATUS.md) for migration, STOP/reset and
raw-I/O semantics. Gateway permissions/watchdog behavior remain unchanged.

Version 0.9.0 adds typed constructor options and a first
[Core/Python review](src/civi_ic7300/AUDIT.md), with explicit remaining deviations.
The draft introduction is [___Introduction to CiviIc7300___.md](src/civi_ic7300/___Introduction%20to%20CiviIc7300___.md).
The identifier remains provisional. Full compliance text is embedded below and
in the package README; release tooling checks wheel/sdist consistency.
This is still an experimental client, not a conformant or registered driver.

Version 0.8.0 adds guarded VOX/break-in/tuner, transmit inhibit, antenna output,
CW/voice/speech and power operations. See [OPERATIONS.md](src/civi_ic7300/OPERATIONS.md)
for permissions, ownership, error handling and simulation limits. All 339 extended
gateway definitions now have typed APIs in every catalog direction; this is not
an IVI compliance result. Windows offline/mock tests only, with no physical
transmission, radio power operation or Pi changes.

Version 0.7.0 adds band-edge queries and calibration-gated user records, typed
DATA/filter settings and the alternate IP+ command. See
[BANDS.md](src/civi_ic7300/BANDS.md) for complete signatures, permission sharing,
DATA OFF read/write differences and mock limitations. Windows offline/mock
verification only; no new Pi/radio changes.

Version 0.6.0 adds all 21 scan command definitions, repeater/tone-squelch
frequencies and the two scope code-zero setters. Scan methods always check
errors; acceptance does not imply scan completion. See [SCAN.md](src/civi_ic7300/SCAN.md)
for context requirements, write-only limitations and simulation boundaries.
Windows offline/mock verification only; no new Pi/radio changes.

Version 0.5.0 adds complete memory records (101 channels including P1/P2),
33 band-stack entries and eight stored keyer texts. Both memory blocks, flags,
tones and ten-byte ASCII/half-width kana names are retained. All writes use the
existing memory permission gate and always check errors. See
[stored-data API and offline example](src/civi_ic7300/STORAGE.md).
Windows offline/mock verification only; no new Pi/radio changes.

Version 0.4.0 adds all **216 menu definitions**: 216 readable, 215 writable,
with bool/integer and typed filter/color/edge/date/time values. See
[the menu list](src/civi_ic7300/MENUS.md) and the menu section of API.md.
Writes retain the gateway's normal/link/calibration permission gates and always
check errors. Offline simulation defaults to denying all three write groups.

Version 0.3.0 adds typed VFO selection/mode records, Split/RIT/XIT, receiver
settings, raw gains/meters and scope controls/sweeps. See
[API.md](src/civi_ic7300/API.md) and the generated
[control list](src/civi_ic7300/CONTROLS.md). Offline simulation covers these APIs
without importing the CIVI gateway or opening a socket. New controls have been
tested against the gateway mock on Windows; no new Pi/hardware test is claimed.

`device.ivi_utility.reset()` and constructor `reset=True` now select CIVI's
[documented receive baseline](src/civi_ic7300/Reset.md). This changes radio
operating settings and requires an updated CIVI server. Physical IC-7300 reset
and readback were verified on 2026-11-08 against the captured Partial Reset state.

An experimental client for the **CIVI gateway**, written by **7M4MON**.
It targets the IVI Generation 2026 Core/Python API design. **It is not yet an
IVI-conformant or registered driver.** See the packaged
[compliance report](src/civi_ic7300/COMPLIANCE.md) for unmet requirements.
The controlled instrument identity is `CIVI Project`, model `CIVI/IC-7300`;
the client does not connect directly to an Icom USB serial port.

Install from the repository root with Python 3.11 or newer:

```console
python -m pip install ./drivers/civi-ic7300
```

No VISA runtime or third-party Python runtime dependency is needed. The client
implements the TCP SOCKET subset of VISA resource naming; it does not implement
VXI-11, HiSLIP, logical names, IPv6 literals, GPIB or USB resources. Omit the VISA
board number, or use board zero.

```python
from civi_ic7300 import CiviIc7300

with CiviIc7300("TCPIP::192.168.73.2::5025::SOCKET") as device:
    print(device.ivi_utility.instrument_model)
    print(device.radio.frequency_hz, device.radio.mode, device.radio.smeter_raw)
```

Construction checks `*IDN?` by default. Start CIVI and prepare/recover the radio
before connecting. `id_query=False` skips identity verification, but hardware
queries can still fail if the radio is unavailable. The initial timeout is five
seconds. A transport timeout/disconnection closes the session; explicitly open
a new instance after fixing the connection. This prevents reusing a timed-out
session with a late reply. Radio recovery remains CIVI's existing explicit
procedure, not a side effect of constructing this client.

For offline operation, simulation opens no sockets:

```python
with CiviIc7300("TCPIP::unused::5025::SOCKET",
                options={"simulate": True}) as device:
    device.radio.frequency_hz = 14000000
    device.radio.mode = "USB"
    print(device.radio.frequency_hz)
```

Hardware setting example (changes the selected VFO):

```python
with CiviIc7300("TCPIP::192.168.73.2::5025::SOCKET",
                options={"query_instrument_status": True}) as device:
    old_frequency = device.radio.frequency_hz
    try:
        device.radio.frequency_hz = 14000000
        assert device.radio.frequency_hz == 14000000
    finally:
        device.radio.frequency_hz = old_frequency
```

Automatic status checking defaults to false, as specified by IVI Core. Enable
it to raise gateway errors after ordinary typed scalar operations.
All typed APIs follow the option; use checked() for an explicit checked block.
See STATUS.md for OFF behavior and migration. Explicit `error_query()` /
`raise_on_device_error()` work regardless of the setting. Raw I/O never adds
status queries because doing so would consume user-managed responses.

The PTT property remains read-only; operations.start_transmit()/stop_transmit()
provide explicit guarded actions (BASIC.md). Direct I/O can send any SCPI command supported
by CIVI; CIVI's transmit authorization and timeout rules still apply. Automated
driver tests never transmit. S-meter values are raw 0–255, not dBm.

API, installation/build instructions, limitations and source information are in
the packaged [introduction](src/civi_ic7300/Introduction.md),
[API help](src/civi_ic7300/API.md), and
[compliance report](src/civi_ic7300/COMPLIANCE.md).
Support/source: [7m4mon/civi](https://github.com/7m4mon/civi).

For a complete offline controls example, see the API help. The current catalog
mapping is 339 of 339 extended definitions in all catalog directions, zero
partial mappings and zero pending. Raw I/O alone does not complete typed coverage.


[API naming/layout review](src/civi_ic7300/STYLE.md) records 0.13.1 changes.

<!-- BEGIN GENERATED COMPLIANCE -->

# Compliance status — experimental client 0.13.1

## Compliance Category

**Not IVI-conformant; not registered.** Development targets IVI Generation 2026,
IVI Driver Core 1.0 and IVI Driver Python 1.0. It does not claim any Generation
2014 instrument class, interoperability with a class driver, or certification.
Do not apply IVI or LXI logos to this package.

Official requirements:

- [IVI specifications](https://www.ivifoundation.org/specifications/default.html)
- [Core 1.0](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverCore/1.0/Spec/IviDriverCore.md)
- [Python 1.0](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverPython/1.0/Spec/IviDriverPython.md)

## Driver Identification

- **Driver Version:** 0.13.1 (initial pre-release).
- **Driver Vendor:** 7M4MON.
- **Driver Bitness:** 64-bit Python process tested; 32-bit unverified.
- **Source Code:** Included in sdist/wheel and public repository. Distribution/license terms require final release review.

Author/vendor: 7M4MON. Version: 0.13.1. Distribution/import: civi-ic7300 /
civi_ic7300. Main class: CiviIc7300. Identifier is **experimental**: VPP-9 vendor
abbreviation registration and final driver naming remain open. NAMING.md records
the official-table review and conditional NL/NM proposals; no rename was made.
Supported gateway identity: manufacturer `CIVI Project`, model `CIVI/IC-7300`.
Gateway identity is not the Icom transceiver manufacturer's identity.
Implementation is portable Python; supported/tested platform records follow.

## Hardware Information

- **Instrument Manufacturer:** CIVI Project.
- **Supported Instrument Models:** CIVI/IC-7300.
- **Supported Bus Interfaces:** TCP SOCKET over IPv4/hostname, ASCII LF on port 5025 by default.

Targets CIVI 0.1.0 with the IC-7300 profile, TCP 5025. Mock tests use CIVI's actual
ControlService and SCPI handler. Live read-only results, when available, are
recorded separately in the repository validation log. No transmit, memory write,
adjustment/calibration or radio reset on physical hardware is part of automated
unit verification; simulated writes and separately recorded manual hardware
checks have their own scope.

## Software Prerequisites

- **Supported Operating Systems:** Development verification on Windows 11 (25H2, build 26200.9711), x64. No broader release support matrix is established.
- **Driver Dependencies:** Python >=3.11, stdlib runtime only; actual current test runtime is CPython 3.14.5 x64.

Python >=3.11, stdlib runtime only. Build: setuptools>=68; recommended frontend
`build`. No gateway dependencies are imported by the separately installed client.
TCP SOCKET address syntax is supported; INSTR network locations resolve to raw TCP 5025; SOCKET keeps its explicit port. Other buses are rejected.

## Unit Testing

### Test Setup

- **Instrument Model (Firmware Version):** CIVI/IC-7300 mock gateway 0.1.0 / independent logical simulator; physical firmware not applicable, physical complete unit-test setup not claimed.
- **Bus Interface:** Loopback TCP SOCKET for gateway mock; no instrument I/O in independent simulation.
- **Operating System:** Windows 11 (25H2, build 26200.9711).
- **Driver Bitness:** 64-bit CPython 3.14.5.
- VISA/IVI shared components are not used by the client.


From the CIVI repository with gateway test dependencies installed:
`python -m pytest tests -k 'python_' -q` (all client/release test modules).
The client tests cover offline
simulation without any socket creation, identity, controls/readback against the
mock gateway, per-session error queries, concurrent queries, rejected arguments,
and closure after timeout. Simulation covers the documented typed API; it is not a full raw SCPI parser
or a hardware/RF model. Tests do not use radio hardware or cause transmission.

## Driver Installation Testing

- **Operating System:** Windows 11 (25H2, build 26200.9711), Python 3.14.5 x64; clean offline wheel installation.

Build a wheel, install into a clean virtual environment, and run the README
simulation example outside the repository. Record actual results in VALIDATION.md.
Platform/bitness coverage beyond recorded environments remains unverified.

2026-11-08: Windows x64 / Python 3.14 built both an sdist and a wheel from that
sdist. A separate clean venv installed the wheel offline and ran simulation
with Python isolated mode; bundled help and py.typed were present. The
repository suite passed 283 tests with one pre-existing Linux-only skip. Live
Pi TCP read-only checks returned CIVI/IC-7300, 774000 Hz, AM, raw S-meter 72 and
an empty client error queue. Hardware settings were not changed in that check.

## Driver Buildability

- **Operating System:** Windows 11 (25H2, build 26200.9711), Python 3.14.5 x64; setuptools/build frontend, sdist then wheel.

Source is supplied. Build instructions are in Introduction.md. No compiler or
proprietary build environment is required. A source distribution and wheel must
both be checked before a conformant release.

## Driver Test Failures

- **Known Issues:** No unresolved failing automated test in the recorded run; formal compliance is unverified. AUDIT.md records provisional identifiers, remaining repeated-capability review, full notice/help and hardware/platform gaps. HIERARCHY.md documents the new band/slot interface. STATUS.md records the corrected 0.10.0 status policy.

No formal IVI compliance run has been completed. Passing the listed client tests
does not mean the requirements below have passed.

## Additional Compliance Information

2026-11-11 scoped source-client physical acceptance: IC-7300 MAIN 1.41 via Pi
TCP SOCKET; core/receive 40 checks, 16 receive-setting properties / 65 checks,
and 290 successful reads out of 292 including all 216 menu selectors. Firmware
and mode-dependent NAKs, NR/PBT quantization and restored state are documented
in EVIDENCE.md and the repository physical report. This is not a complete
instrument-connected unit-test setup covering every public entry point.

| Requirement | Status / next action |
|---|---|
| Construction, ID query, simulation, metadata, errors, timeout | Basic implementation and mock tests |
| IVI Python utility hierarchy | Concrete Utility/DirectIo inherit exported ABCs; root references are read-only properties. Final specification audit remains |
| Typed instrument controls | VFO/receiver/gain/meter/scope and all 216 menu APIs plus stored records/stack/keyer APIs. 339 extended plus eleven base/special headers mapped. Unified directions/aliases/exclusions in SCPI_COVERAGE.md; see BASIC.md, OPERATIONS.md, BANDS.md, SCAN.md, STORAGE.md, CONTROLS.md, MENUS.md and repository coverage table |
| Direct I/O | ASCII LF programs only; API/SCPI protocol coverage audit remains |
| Thread safety | Typed/query calls serialized; low-level write/read pairs require caller locking |
| Reset | Captured receive baseline implemented via RAD:RESET and verified with physical IC-7300 on 2026-11-08. Both VFOs and 57 settings restored; 214 non-clock menus unchanged. Final IVI coverage/requirement audit remains. See Reset.md |
| Naming | Final VPP-9 abbreviations and package/class naming must be checked |
| Type hints | py.typed included; all twelve source modules pass mypy 2.4.1 --strict. Final API/specification audit remains |
| Documentation | Draft introduction, embedded compliance, prescribed notice and generated public-member reference supplied; final identifier and semantic/IVI review remain. EVIDENCE.md separates implementation/mock/physical scope |
| Verification | Core's complete unit-test, supported-platform, clean installation and build verification still required |
| Registration | **Not submitted** to IVI Foundation; no public registry entry |

LXI 1.6.2 sections 6.1/6.2 and 11.1/11.2 therefore remain **incomplete**.
Submitting to the IVI Foundation is a separate external action after the driver
and reviewable compliance material are complete.

## Version 0.3.0 verification

Windows x64 / Python 3.14: 27 client tests passed (independent offline simulation
and the actual gateway TCP handler with MockBackend). Covers VFO operations,
all declared scalar mappings, units/BCD vectors, input and reply validation,
scope startup failure restoration, concurrent access and cross-client selection.
Complete repository run: 312 passed, one Linux-only panel socket test skipped.
That Linux-only test separately passed on the Pi earlier (1 passed in 0.59s);
this is not a claim that the whole suite was run on Linux.
New controls were not tested against radio hardware. Existing physical reset
evidence above remains specific to the earlier reset implementation.

Offline simulation ships reset-profile.json and has no gateway imports or
third-party runtime dependencies. It does not model RF physics, actual meter
calibration, packet timing/loss, or all raw SCPI aliases. The gateway mock's
TXFREQ response is a canned value; the client simulation derives it from split
VFO state. Neither is evidence for real transmitter operation.

The 0.3.0 source distribution built successfully; a wheel was then built from
that distribution. A clean venv installed the wheel offline with no third-party
runtime dependencies. Python isolated mode exercised VFO records, gains, fixed
edges, a 475-point scope sweep, captured reset and the bundled help successfully.

## Version 0.4.0 verification

Windows x64 / Python 3.14: 59 client tests passed. All 216 menu definitions were
read, and all 215 writable definitions were changed, read back and restored in
both the independent offline simulator and the real gateway TCP handler with
MockBackend. Menu 0074 remained read-only. Coverage includes independent CI-V
wire vectors for all menu value formats, group-isolated default-deny permissions,
NAK/serial failure/preexisting errors, rounded and normalized readback, metadata,
and concurrent write/read pairs. Static checking passes for all seven source
modules with mypy 2.4.1 --strict. Repository run: 344 passed, one Linux-only skip.
No menu writes or new tests were performed on a physical radio/Pi.

Menu write permissions are enforced by the existing gateway configuration. The
client cannot enable real gateway permissions. Simulation models all three
groups independently and defaults them OFF; it stores clock/link settings as
data without wall-clock advancement, USB disconnects or RF side effects.

The 0.4.0 sdist and wheel built successfully. A clean venv installed the wheel
offline; Python isolated mode exercised default-deny permissions, explicit
normal-menu permission, scalar/filter/color/date/offset readbacks and bundled
schema/help with no gateway imports. A separate consumer type check accepted
valid typed accessors and rejected two deliberately invalid assignments using
the installed wheel's py.typed information.

## Version 0.5.0 verification

Windows x64 / Python 3.14: 85 client tests passed, including 26 storage tests.
The full repository run passed 370 tests, with one Linux-only skip (30.25s).
All 101 memory channels, 33 band-stack slots and eight keyer texts were changed,
read back and restored in both independent offline simulation and mock TCP.
P1/P2 start from seeded valid records in disposable mocks; restoring empty
P1/P2 through addressed clear is unsupported and is not claimed. Complete
record byte vectors, kana/padding, default-deny permissions, NAK/serial errors,
preexisting errors, concurrent pairs and reset preservation were checked.
All nine source modules pass mypy 2.4.1 --strict. No new hardware/Pi test occurred.

The 0.5.0 sdist and wheel built successfully. A clean offline wheel installation
passed isolated-mode stored-record/stack/keyer operations, permission checks and
bundled help checks without gateway imports or third-party runtime dependencies.
Installed-package type checking accepted valid storage use and rejected three
deliberately invalid assignments. STORAGE.md documents selection-relative
actions, P1/P2 limitations and simulation/hardware boundaries.

## Version 0.6.0 verification

Windows x64 / Python 3.14: 101 client tests passed, including 16 new scan/tone
tests. Repository run: 386 passed, one Linux-only skip (29.73s). All 21 scan
definitions were exercised in independent offline simulation and mock TCP;
fixed and parameterized CI-V bytes were checked against independent constants.
Tone boundaries/intermediate values were written, read and restored. Tone
requests and replies have different BCD lengths. Both scope code-zero setters,
input/reply rejection, NAK/serial errors, preexisting errors and concurrent
meter/scan access were checked. All ten source modules pass mypy --strict.

The 0.6.0 sdist/wheel built and installed offline in a separate venv. Isolated
mode exercised scan, tone, scope, reset and bundled documentation with no gateway
imports. Installed-package type checking accepted valid use and rejected three
deliberately incorrect calls/assignments. No new Pi or physical-radio test took
place. SCAN.md describes write-only semantics and simulation limits: no modeled
scan frequency motion, signal search, timing or persisted memory-group updates.

## Version 0.7.0 verification

Windows x64 / Python 3.14: 126 client tests passed, including 25 new band/DATA
tests. Repository run: 411 passed, one Linux-only skip (30.70s). Both mocks
exercised indexed band reads and 30 user record changes/readbacks/restores,
default-deny/shared calibration gates, independent wire vectors, boundaries,
malformed replies, NAK/serial/preexisting errors, reset preservation and concurrent
write/read pairs. Mock counts are zero and indexed replies are canned values:
this does not establish a real device's band count or country/region band plan.
All eleven source modules pass mypy --strict.

DATA OFF permits filter-bearing readbacks but requires zero on writes. These
directions, DATA ON filters, VFO-mode restoration and alternate IP+ alias state
were checked. The standalone simulator couples DATA to VFO/memory working state;
the gateway mock stores DATA separately from VFO mode. Neither proves real
mode-dependent behavior or persisted calibration settings.

The sdist and wheel built, and a separate venv installed the wheel offline.
Isolated-mode tests exercised records, permissions, DATA, IP+ and bundled docs
without gateway imports. Installed type information accepted valid use and
rejected three deliberately incorrect calls/assignments. No radio or Pi was
operated; physical behavior, complete IVI compliance and registration remain open.

## Version 0.8.0 verification

Windows x64 / Python 3.14: 147 client tests passed, including 21 new operation
tests. Full repository: 432 passed, one Linux-only skip (31.66s). All eleven
remaining definitions were exercised in offline simulation and mock TCP. Tests
cover default denial, typed scalar changes/readbacks/restores, independent CI-V
bytes, quoted CW text, voice T1..T8, speech and simulated power actions.
STOP/OFF attempts despite prior device errors, combined prior/stop errors,
NAK/serial failures, invalid input/replies, ownership exclusion, power exclusion,
aged-deadline CW/VOX stops and disconnect-triggered voice stop were checked.
All twelve source modules pass mypy --strict.

The sdist and wheel built and installed offline in a separate venv. Isolated
mode exercised operations, permissions, stops, power exclusion and bundled help
without gateway imports. Installed type information accepted valid use and
rejected three deliberately incorrect calls/assignments. No physical transmit,
audio, radio power operation or Pi changes occurred. Mock expiration/ownership
does not prove RF shutdown: see OPERATIONS.md for physical and simulator limits.

Every extended catalog direction now has a dedicated typed mapping (339/339).
Formal IVI requirement/naming/documentation audits, hardware verification scope,
supported-platform verification and registration are still incomplete. Catalog
coverage is not an IVI conformance determination.

## Version 0.9.0 review

AUDIT.md maps the first Core/Python review to sources and remaining work. The
339-direction mapping remains unchanged; it is not a compliance determination.
The OFF-status policy still deviates for protected operations, and naming,
nested repeated capabilities, full notice/help and supported-hardware/platform
verification remain open. The Direct I/O session note is optional; existing
ASCII methods are retained without exposing an unguarded socket.

DriverOptions improves static constructor options without changing runtime
authorization. The draft introduction and embedded compliance text are generated
from the canonical files. Artifact checks validate identity metadata, version,
typing marker, required documents/source, inline compliance and wheel/sdist
agreement, and are not formal IVI tests. No Pi or radio was operated.

Verification: Windows 11 (25H2, build 26200.9711), CPython 3.14.5 x64.
154 client/release tests passed; complete repository run: 439 passed, one
Linux-only skip (31.70s). Strict source typing passed for twelve modules.
Seven added tests cover typed options without network I/O, deterministic release
docs, and rejection of corrupt version/identity/typing/compliance artifacts.
The final sdist/wheel contents and metadata were checked together. A separate
venv installed the wheel offline; isolated-mode checks verified typed options,
representative APIs, bundled audit/introduction and embedded compliance text.
Installed-package type checking accepted valid DriverOptions use and rejected
three deliberately invalid option assignments. These results do not resolve the
deviations listed in AUDIT.md.

## Version 0.10.0 status-policy correction

All typed APIs, including initialization, protected mutations, scope start/stop
and reset, now follow Query Instrument Status Enabled. OFF produces no automatic
SYST:ERR? traffic. ON checks results; protected mutations retain preflight checks.
checked() temporarily selects ON under the session lock, restoring the previous
setting after nested blocks/exceptions. With checks ON, STOP/OFF attempts still
run with prior device errors and report both prior/new errors afterward.

Raw query ERROR replies now raise QueryError and preserve the queue. Unchecked
typed failed queries also raise QueryError; checked typed queries obtain detailed
DeviceError information. Explicit error queries remain independent of the flag.
With OFF, a completed setter/readback sequence can leave a device error queued;
use checked() or enable the option for verified sequences. Gateway permissions,
ownership, watchdog and disconnect stops are unchanged. STATUS.md is the migration
guide; previous version sections above record their historical behavior.

Windows 11 (25H2, build 26200.9711), CPython 3.14.5 x64: 165 client/release tests
passed, including eleven new policy/traffic tests. Full repository: 450 passed,
one Linux-only skip (32.27s). Strict typing passes for twelve source modules.
Traffic tests cover constructor ID/status combinations, every protected API
group with OFF, raw/typed failed queries, preserved errors, explicit checks,
nested/exception restoration and thread isolation. Earlier failure/permission
tests now explicitly select ON/checked() rather than depending on hidden checks.

The final sdist/wheel passed artifact consistency checks. An offline clean-venv
installation passed isolated-mode OFF/ON/checked/reset/error-queue/help checks.
Installed type information accepted checked() yielding the typed driver and
rejected an intentionally wrong setter value. No Pi or radio was operated.
This addresses the audit's status-policy finding with developer evidence; naming,
nested repeated capabilities, full notice/help, platform/hardware verification
and registration still prevent an IVI conformance claim.

## Version 0.11.0 band-stack hierarchy

Added band_stacks[band].slots[slot] and a pure band-level collection at
band_stacks.bands. Legacy tuple indexing, length 33 and flat pair iteration
remain. All paths resolve stable band/slot views with read-only local physical
names/selectors; settings still query the device rather than caching records.
HIERARCHY.md documents types, iteration, permissions, status policy and examples.

Windows 11 (25H2, build 26200.9711), CPython 3.14.5 x64: 173 client/release tests
passed, including eight new hierarchy tests. Full repository: 458 passed, one
Linux-only skip (33.07s). All 33 slots were changed, read back across flat/nested
views and restored in offline simulation and mock TCP. Independent CI-V selector
bytes, local metadata without I/O, invalid indices, read-only references, closed
session rejection, memory permissions, OFF/checked() semantics and concurrent
flat/nested write/read pairs were checked. Twelve source modules pass mypy strict.

The sdist/wheel passed consistency checks and installed offline in a separate
venv. Isolated mode verified typed nested/flat views, checked change/read/restore
and bundled help. Installed type information accepted both indexing styles and
rejected four deliberately invalid uses, including assigning a band node to a
slot type. No Pi or radio was operated. This addresses the band/slot hierarchy
finding; remaining repeated capabilities, naming, documentation/notice, platform
and hardware verification and registration remain open.

## Version 0.12.0 unified command audit

SCPI_COVERAGE.md / scpi-coverage.json combine 339 extended and eleven base/special
headers. All 350 have typed mappings in their supported gateway directions.
Documented independent short/full token spellings, case and leading-colon forms
are checked through the real parser. Unsupported common-command forms and
status/self-test omissions have explicit reasons; *RST is not translated into
the distinct RAD:RESET baseline. Source/parser hashes trigger inventory re-review.

Added immutable GatewayIdentification with all four gateway IDN fields, explicit
clear_status()/wait_for_complete(), manual radio firmware metadata, and guarded
PTT start/stop methods. The PTT property stays read-only. Stop uses the gateway's
existing all-owned-path cleanup; permissions, ownership/deadlines and serial
execution are not reimplemented in the hardware client. BASIC.md documents scope.

Windows 11 (25H2, build 26200.9711), CPython 3.14.5 x64: 186 client/release tests
passed, including thirteen new audit/base tests. Full repository: 471 passed,
one Linux-only skip (32.02s). Tests cover inventory/direction/alias agreement,
explicit unsupported-form rejection, immutable/quoted/malformed identity,
completion versus success, manual firmware metadata, client-local clear,
default-denied/owned PTT, stop of owned CW/VOX paths, ownership competition and
disconnect cleanup, plus logical offline timeout/close. No physical RF, radio
power operation or Pi changes occurred. Twelve modules pass strict source typing.

The sdist/wheel passed consistency checks and installed offline in a separate
venv. Isolated mode verified base APIs, logical PTT guards/stops and the bundled
350-header inventory/exclusions/help. Installed type information accepted valid
usage and rejected three intentionally invalid identity/PTT uses. This is a
gateway software coverage audit, not proof of every hardware function or final
IVI applicability. Remaining naming, repeated-capability details, full notice/help,
supported-platform/hardware verification and registration remain open.

## Version 0.12.1 help and evidence review

REFERENCE.md/public-api.json index 43 public/returned types and 310 driver-defined
member/field entries, including constructor/overload signatures, access, direct
SCPI contracts, local-only classification and detailed value/usage guide links.
Common exceptions, context-manager behavior, standard-library inherited scope
and development-environment limitations are documented. New unclassified exports
or members fail generation. This is an implementation/help inventory, not an
automated proof that every semantic IVI documentation obligation is satisfied.

The prescribed Foundation notice is supplied from the official Core source in
IVI_NOTICE.md and visible REFERENCE.md, with source/date/hash metadata. Artifact
checks verify notice integrity/visibility and public-help version consistency.
EVIDENCE.md standardizes implemented, mock-verified, dated hardware and unverified
labels. No generated member or parser success is promoted to hardware evidence.
Earlier physical receive-reset/gateway evidence is explicitly historical.

An error-response review also fixed malformed CSV/code/field-count handling:
error_query() now consistently raises ProtocolError for malformed responses;
signed integer codes and correctly quoted messages remain accepted.

Windows 11 (25H2, build 26200.9711), CPython 3.14.5 x64: 197 client/release tests
passed, including eleven new help/error-response tests. Full repository: 482
passed, one Linux-only skip (31.75s). Twelve source modules pass mypy strict.
Tests cover help synchronization, overload/default/type rendering, missing
export/member detection, notice hash/visibility and malformed/valid error replies.
The final sdist/wheel passed consistency checks. A clean offline installation
verified bundled reference/JSON/evidence/notice and runtime error behavior in
isolated mode, without gateway imports. No Pi or physical radio was operated.

Final naming/VPP-9 identifiers, remaining repeated-capability/style details,
semantic documentation review, supported-platform/hardware verification and
registration remain open; IVI conformity is not claimed.

## 2026-11-09 physical receive-only smoke follow-up

After the mock-only development run, installed client 0.12.1 connected to the
user's IC-7300 through the Pi gateway at TCP 192.168.73.2:5025 (gateway 0.1.0).
It read IDN/manual firmware metadata, current/other VFO settings, raw S-meter,
one nested band-stack record (3/1), scope STREAM/ENABLE flags and completion.
Frequency changed 774000 -> 775000 -> 774000 Hz with readback at each step.
Selected mode changed AM -> USB -> AM with DATA OFF and filter 2, then the full
selected/other display/VFO snapshot matched the baseline. Other VFO remained
14100000 Hz USB/DATA OFF/FIL2; PTT remained OFF and the final error queue was empty.

Only four mutation programs were sent: the two frequency settings and selected
VFO mode set/restore. No transmit, power, persistent storage/calibration, scope
start, reset, gateway deployment or Pi configuration operation was performed.
This limited result is recorded in repository docs/PYTHON_HARDWARE_2026-11-09.md
and EVIDENCE.md, not promoted to all modes/selectors or a full physical unit-test
setup. The original tested wheel and code hashes are retained in the local JSON;
the documentation-only rebuild keeps the tested Python code unchanged.

## 0.13.0 style and repeated-capability follow-up — 2026-11-10

Added read-only local KeyerItem.name (M1..M8); existing classes and imports
remain compatible. STYLE.md records the twelve-module public naming/layout
review, recommended type-spelling exceptions and explicit indexed APIs. Ruff
E/W/N and independent pycodestyle checks use documented settings. This is not
formal conformance. Driver vendor runtime remains 7M4MON; nomulabo/NL is the
planned registration identity. No physical-device test was performed for this
version; the 0.12.1 record above is not automatically inherited.

Validation for 0.13.0: full repository suite 485 passed, one Linux-only skip
(31.98 seconds). New local-name and addressed-keyer scenarios pass in independent
simulation and loopback gateway mocks. Twelve source modules pass strict mypy;
Ruff format/E/W/N and the documented independent pycodestyle checks pass.
Public inventory: 43 types, 311 member/field entries. Wheel/sdist contents (40
package files), isolated clean offline installation and local metadata access
were verified. No physical-device verification occurred for 0.13.0.

## 0.13.1 LXI audit fixes — 2026-11-10

Device 6.2 network location forms now accept arbitrary board numbers, omitted
INSTR class/device and HiSLIP location/credential references, using raw TCP
5025. Explicit SOCKET ports are retained. Unused credentials are never passed
to sockets; this adds no secure/HiSLIP/VXI-11 transport. API.md documents the
mapping. Malformed forms fail before I/O without including input in errors.
Mock-server traffic verifies resolution and queries. The gateway also normalizes
UTF-8 service names, limits Pi LXI NIC claims/advertisements to its wired target
and prioritizes LAN faults over Identify. No Pi deployment or physical-device
verification occurred for this version. The dated LXI audit retains other gaps.

0.13.1 validation: 37 new regression cases; full repository 522 passed and one
Linux-only skip (32.64s). Raw mock TCP, Unicode persistence/reload, Pi NIC
selection, local panel model and actual Web JavaScript priority were verified.
Twelve source modules pass strict mypy and the documented style checks.
No physical Pi deployment or radio verification is claimed for 0.13.1.

## 2026-11-10 limited 0.13.1 physical follow-up

After the development run, the installed Windows 0.13.1 wheel was used to read
IC-7300 via Pi using three INSTR location forms, including board/subaddress and
HiSLIP-style names mapped to raw TCP. Results: 774000 Hz, AM, PTT OFF, empty
queue. No radio mutation was sent. Pi gateway fixes for wired NIC declaration,
63-byte service-name persistence/advertisement and Identify/fault/recovery were
checked on hardware and restored. On Pi Linux/aarch64 Python 3.13.5, 72 selected
mock tests passed, one Node-only test skipped. This is a limited record, not a
complete Linux support claim. See EVIDENCE.md and repository
docs/RPI_LXI_FIXES_2026-11-10.md. Earlier no-physical-test statements above
describe the development stage. Final conformance/registration remain open.

<!-- END GENERATED COMPLIANCE -->
