# IVI submission preparation — nomulabo / 7M4MON

Status: preparation only; no inquiry or registration has been sent. This is not
an IVI compliance declaration or an instruction to publish an unverified driver.

## Proposed identity

| Item | Value / status |
|---|---|
| Applicant trading/development name | nomulabo, individual developer |
| Author / current driver vendor metadata | 7M4MON |
| Preferred VPP-9 abbreviation | NL; NM fallback; neither reserved nor registered |
| Current experimental identifier | CiviIc7300 |
| Conditional final identifier | CiviIc7300_NL, subject to approved vendor identity |
| Current package/import | civi-ic7300 / civi_ic7300 |
| Driver version | 0.13.1 |
| Target | IVI Generation 2026, Core 1.0 and Python 1.0 |
| Controlled instrument | CIVI Project, CIVI/IC-7300 gateway, TCP SOCKET |
| Project | https://github.com/7m4mon/civi |

The current public repository may not contain this working tree's latest changes.
Final package identity, immutable distribution/source URL and release review must
precede driver registration. Do not silently claim NL acceptance or rename now.

## Material already available

- Source and gateway command inventory; independent simulation and TCP mock tests.
- Public API reference, detailed operation guides, prescribed introduction,
  embedded compliance text, official notice and package-integrity checks.
- Recorded installed-driver physical smoke checks and receive-reset evidence,
  with explicit scope in package EVIDENCE.md.
- The generated [verification worklist](IVI_VERIFICATION_WORKLIST_2026-11-11.csv)
  lists current exported constructors, members and data fields for evidence review.
  It is not a claim that each row passed a physical test.
  The [2026-11-12 reconciliation and additional-test plan](IVI_ADDITIONAL_TESTS_2026-11-12.md) maps every row to scoped evidence and separates local helpers, historical protocol tests, current-driver gaps and controlled operations.

## Actual prerequisites still open

1. Confirm VPP-9 applicant/vendor abbreviation with the Foundation, then finalize
   the package/class/document naming and compatibility facade consistently.
2. Complete Core's unit-test procedure for the published API: simulation and a
   supported instrument with simulation off; legal/illegal range boundaries,
   discrete values, repeated capabilities, methods and properties as applicable.
   Reuse recorded cases when code, hardware and conditions match. Representative
   smoke checks and passing mock tests alone are insufficient. Transmission,
   adjustment/calibration and destructive operations require a separately scoped
   safe setup; none is authorized by this document.
3. Finish semantic help/release review; build, clean-install and verify the final
   named artifacts; record exact instrument/firmware, OS/runtime and bus setup.
4. Submit compliant final materials through the Foundation's current registry
   process, with the applicant's actual contact information, and verify listing.

The [Core specification](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverCore/1.0/Spec/IviDriverCore.md#unit-test-procedure)
defines the unit-test procedure. The [Python specification](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverPython/1.0/Spec/IviDriverPython.md#ivi-python-driver-conformance)
requires registration for an IVI-Python conformance claim. LXI Device 1.6.2 rule
11.2 independently requires listing in the IVI driver registry.

Reviewed official source snapshots on 2026-11-11:

- Core 1.0 SHA-256: cab7e93878277213fd543af4b2dcf0daa3d670b81be0d7012acec8e876ecfa67
- Python 1.0 SHA-256: 3e2aaa8e472a71a17332af185ea8503ae4c1f2d913d565262c8603321ea558fe

## Current next step: inquiry before more physical trials

The owner paused further functional trials on 2026-11-12. The next step is the
[shortest-path review](LXI_SHORTEST_PATH_2026-11-12.md): clarify vendor identity,
permitted scope/exclusions and submission/evidence expectations, then finalize
materials and close the requirements for the retained API. Existing unverified
rows remain unverified; this is not a completed-driver registration application.
No API was removed and no naming reservation was assumed.

## Unsent identity and compliance-process inquiry draft

Recipient: admin@ivifoundation.org

Subject: nomulabo / NL vendor abbreviation and IVI-Python gateway driver inquiry

Hello,

I am an individual developer working under the name nomulabo (author: 7M4MON).
I am developing CIVI, an open-source SCPI-over-TCP gateway for an Icom IC-7300,
and a separate Python instrument driver targeting IVI Generation 2026 Core 1.0
and Python 1.0. The controlled gateway identity is CIVI Project / CIVI/IC-7300.
The public project is https://github.com/7m4mon/civi; the latest verification
materials are being prepared in a development working tree.

Could you please advise on these points?

1. Can an individual developer using the name nomulabo register a VPP-9 vendor
   abbreviation? Our preference is NL, with NM as an alternative. Please let us
   know availability, required applicant details and the reservation procedure.
2. Core 1.0 describes functionality-coverage exceptions such as service/factory
   calibration and communication configuration. For this gateway driver, how
   should such exclusions be reflected consistently in the Python API and
   compliance document? The current experimental API includes protected
   calibration/communication controls; they have not yet been removed or
   declared conformant.
3. We have scoped physical SCPI gateway records, current Python-driver physical
   tests, and independent simulation/mock-transport tests. Some controlled RF
   and calibration operations remain unverified. Before expanding the test
   campaign, could you clarify how existing records and repeated-capability
   coverage should be presented or reused for a Core/Python submission? We
   understand that requirements for retained APIs still need to be satisfied.
4. What is the current registration process and required submission material
   for an IVI-Python driver controlling a gateway of this type? In particular,
   is paid Foundation membership required to register a driver as a non-member
   individual developer, and are there any initial registration or ongoing fees?
   We distinguish these questions from the no-cost VPP-9 abbreviation process.

We have not submitted the driver for registration and do not claim IVI or LXI
conformance or use either conformant logo. We can provide the API inventory,
scoped evidence matrix and draft compliance document when appropriate.

Thank you,
7M4MON / nomulabo

## Membership and fees clarification — 2026-11-12

The public [membership page](https://www.ivifoundation.org/About-the-Foundation/How-To-Join.html)
lists paid organizational membership levels. The separate
[driver registry instructions](https://www.ivifoundation.org/DriverRegistry/default.html)
describe compliance-document/contact submission but do not explicitly settle
non-member individual eligibility or registration/ongoing fees. Free vendor
abbreviation assignment is not evidence that every driver-registration step is
free. These questions have been added explicitly to the unsent inquiry. No paid
membership or registration has been started.
