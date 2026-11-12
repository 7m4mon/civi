# IVI Core/Python review — 2026-11-09, client 0.13.1

**Experimental; not IVI-conformant or registered.** This is a first source and
release-material review, not a certification report. The first review did not
operate a Pi or radio; later limited physical checks are recorded in EVIDENCE.md.
The controlled instrument is the CIVI gateway, not an Icom USB transceiver.

Sources checked on 2026-11-09:

- [IVI official specification index](https://www.ivifoundation.org/specifications/default.html)
- [Core 1.0](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverCore/1.0/Spec/IviDriverCore.md), revision notes through 2026-04-02
- [Python 1.0](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverPython/1.0/Spec/IviDriverPython.md), approved 2026-02-26

The links follow the upstream main branch; record immutable upstream revisions
before a formal submission. Section anchors below identify the reviewed subject.
Requirements and implementation status are distinct; tests are developer evidence.

## Core review

| Core anchor | Strength | Current evidence / remaining work |
|---|---|---|
| availability-and-installation | Required | Source, sdist, wheel, help and py.typed supplied; no installer registry action for this pure-Python client |
| operating-systems-and-bitness | Required documentation | This release records Windows 11 (25H2, build 26200.9711), Python 3.14.5 x64; broader platform claims remain unverified |
| source-code-availability | Conditional required | Client source and rebuild instructions supplied; license/distribution terms need release review |
| repeated-capabilities | Design rules | Band-stack hierarchy added in 0.11.0: bands[band].slots[slot], physical names and read-only references. Legacy tuple facade remains; STYLE.md inventories all groups and recommended spelling exceptions |
| simulation | Required | Initialization selects offline mode; no socket/gateway imports needed; logical output models and limitations documented |
| multithread-safety | Required | Session locks and concurrent tests exist. Separate raw write/read pairs require caller synchronization; review the documented boundary |
| extent-of-instrument-functionality-covered-by-ivi-drivers | Required with exclusions | Unified SCPI_COVERAGE.md / JSON now covers 339 extended plus eleven base/special headers, accepted documented spellings and unsupported forms. Parser tests validate directions/aliases; this does not establish all hardware behavior |
| direct-io-requirement / direct-io | Required for ASCII device | Timeout and four ASCII methods supplied. Binary data is outside this gateway contract |
| query-instrument-status-on-api-call / query-instrument-status-enabled | Required | Addressed in 0.10.0: OFF sends no automatic queue queries; ON/checked() checks results. Traffic tests cover typed groups and raw ERROR replies. This is developer evidence, not formal compliance |
| initialization-construction | Required | Four base constructor parameters plus optional timeout; defaults and mock ID/reset tested |
| driver-version / driver-vendor | Required | ASCII pre-release 0.13.1 and 7M4MON; distribution/import/runtime version checked |
| error-query | Required | Per-session queue APIs supplied. Malformed CSV/code/count replies now consistently raise ProtocolError; quoted/signed valid replies are tested |
| instrument-manufacturer / instrument-model / supported-instrument-models | Required | Gateway identity and metadata keywords agree; physical radio firmware is not fabricated |
| reset | Required | Defined receive baseline, constructor reset, earlier physical evidence; review whether the documented scope covers every driver dependency |
| simulate-enabled | Required | Read-only initialization setting, plus compatibility alias |
| driver-introduction-documentation | Required | Draft prescribed filename generated using provisional CiviIc7300 identifier; final filename depends on naming resolution |
| help-documentation | Required | REFERENCE.md/public-api.json index 43 types and 311 member/field entries with signatures, access, SCPI and detailed-guide links; new unclassified members fail generation. Common exceptions/ADE limits and EVIDENCE.md are supplied. Final semantic/IVI review remains |
| copyright-notice | Required | Prescribed notice copied from the official Core source into IVI_NOTICE.md and visible REFERENCE.md, with source/date/hash record and integrity checks. This grants no conformance claim |
| compliance-documentation | Required | Sections/items, tested OS/build, mock scope and remaining gaps now explicit; no full physical unit-test setup claimed |
| readmemd-documentation | Required | Complete compliance text now embedded in distribution/package READMEs; deterministic sync checked |
| file-versioning | Conditional / version format | No Windows DLL supplied; pre-release numeric runtime version is synchronized with metadata |
| unit-test-procedure / driver-conformance | Required | Developer mock suites and artifact checks exist; complete procedure and supported-hardware matrix not completed; no registration |

## Python review

| Python anchor | Strength | Current evidence / remaining work |
|---|---|---|
| driver-identifier-and-driver-class-name | Required | **Open:** NAMING.md reviews VPP-9 4.35 and Python 1.0, with conditional NL/NM proposals. Abbreviations are not registered; the unregistered manufacturer requires a driver-vendor suffix. Keep existing imports provisional |
| style-guide / ivi-python-naming | Required | STYLE.md: twelve-module E/W/N and independent layout review; public member/type naming checked. Final registered identifier remains open |
| bitness / target-python-versions | Required | No Python-specific OS/bitness mandate; release scope records the actual tested runtime. Minimum 3.11 is a requirement, not proof of testing every version |
| ivi-python-packages / ivi-python-distribution-package-naming | Required | One root driver/package; distribution civi-ic7300 matches import civi_ic7300 by separator normalization. This does not establish the full identifier grammar; final naming and registration remain open (NAMING.md) |
| ivi-python-package-versioning | Recommended | Numeric 0.x releases; new API advances minor version |
| ivi-python-package-type-hinting | Required | Empty py.typed and strict source/installed-consumer checks; broader public API type review remains |
| ivi-python-driver-classes / ivi-python-hierarchy | Required | Root and read-only child references, instantiated utility inheriting IviUtility; final root naming open |
| repeated-capability-reference-property-naming | Mostly recommended | STYLE.md inventories all groups; KeyerItem.name added. Recommended item-class spellings retained for compatibility; explicit indexed APIs/facade exceptions documented |
| ivi-python-error-handling | Required | Exceptions used; ErrorQueryResult is the documented queue-reading exception to error-as-return concerns |
| constructor | Required + recommendation | Signature retained; DriverOptions TypedDict added as recommended, ordinary dict/string still supported |
| ivi-python-utility-interface / additional-driver-api | Required | ABC implementation, both naming variants used by mapping table/example, collection of errors and raise helper supplied |
| direct-io-properties-and-methods | ASCII methods required; session noted optional | Existing four methods/timeout retained. No session handle added merely because the example ABC shows one: its following note calls it optional |
| package-metadata / package-contents | Required | Identity keywords, source, help, READMEs, compliance and typing marker checked in built artifacts |
| ivi-python-driver-conformance / driver-registration | Required | **Not completed / not submitted.** No logo or conformant package classifier used |

## Changes in 0.9.0

- Added exported DriverOptions with the two existing boolean options; runtime
  validation and constructor behavior remain unchanged.
- Added reproducible introduction/README compliance synchronization and a
  wheel/sdist integrity checker. These are packaging checks, not conformance tests.
- Added named compliance items and the actual Windows build/runtime evidence.

## Next work

The status-policy finding is addressed in 0.10.0 with checked() and traffic tests.
Band/slot hierarchy and the unified base/alias inventory are now implemented.
STYLE.md records the completed local style/repeated-capability review.
Next finalize naming/VPP-9, perform the remaining semantic documentation review,
and define the supported-platform/hardware verification matrix. Registration is a separate
external step after the driver and compliance material are complete.

## 0.10.0 status follow-up

STATUS.md documents the OFF/ON policy, checked() context, raw/unchecked QueryError
and migration from prior protected APIs. Eleven new developer tests inspect
actual outgoing traffic and queue preservation, constructor combinations,
exception/nesting restoration and same-session thread isolation. The repository
run passed 450 tests with one Linux-only skip; no hardware/Pi change occurred.
The status-policy finding is addressed in this scope; remaining rows above are
not automatically considered passed.

## 0.11.0 hierarchy follow-up

HIERARCHY.md records the new band/slot hierarchy and compatibility facade.
band_stacks.bands is an eleven-band collection, each band has three slots, and
integer shorthand/legacy tuple indexing share slot objects. Names/selectors and
reference properties are read-only; old length/iteration contracts remain.
Eight new tests cover all 33 changed/read/restored slots in both mocks, actual
selector bytes, permission/status behavior, concurrency and no-I/O metadata.
The full run passed 458 tests with one Linux-only skip. This addresses the
band/slot item above without asserting that every other repeated capability or
the overall IVI requirements have passed.

## 0.12.0 command follow-up

SCPI_COVERAGE.md and its JSON unify all supported canonical gateway headers,
documented aliases/directions and explicitly rejected common-command forms.
The eleven base/special definitions are counted separately from the unchanged
339 extended definitions. Dedicated IDN/clear/completion/firmware/PTT APIs now
close the former raw-only base directions. Parser hashes are normalized text.
Thirteen new tests validate parser agreement and base semantics; the repository
run passed 471 tests with one Linux-only skip. No physical transmission/Pi test
occurred. This addresses the gateway command-inventory item, not the remaining
hardware or formal IVI applicability/registration review.

## 0.12.1 help follow-up

REFERENCE.md/public-api.json index all 43 public/returned types and 310
driver-defined member/field entries. Each has type/access/signature metadata as
applicable, explicit direct-SCPI or local classification, and detailed guide links.
Unclassified exports/members fail generation. Common exceptions/ADE limits are
included. This index does not prove every semantic documentation requirement.

The official prescribed notice is now supplied locally and visible in the
reference, with source/hash checks. EVIDENCE.md separates implementation, mock
scenarios and explicitly dated hardware results. Malformed queue replies now
consistently raise the documented ProtocolError. Eleven new tests pass; the full
repository result is 482 passed, one Linux-only skip. No Pi/radio operation took
place, and the remaining audit/registration findings are not implied to pass.

## 0.13.0 naming/layout follow-up — 2026-11-10

STYLE.md closes the local naming/layout review and inventories repeated groups.
KeyerItem now exposes its physical M1..M8 name. Recommended item-type naming
exceptions are explicit, not misclassified as mandatory failures. Registration,
final package identity, semantic help review and the supported-platform/full
hardware verification matrix remain open. No Pi/radio operation occurred.

## 0.13.1 location follow-up

The 2026-11-10 Device 6.2 location finding is addressed by raw-TCP resolution
of the permitted network-resource forms; see API.md and the repository
test_lxi_fixes.py. This closes a code finding, not IVI/LXI registration or
physical validation. Other gaps remain recorded in the LXI matrix.
