# Naming proposal — 2026-11-09

Experimental proposal only; no abbreviation, driver registration or package
rename has been submitted. The original proposal used 0.12.1; current runtime is 0.13.1.

## Project identity

| Role | Current value | Meaning for this client |
|---|---|---|
| Instrument manufacturer | CIVI Project | Producer of the controlled SCPI gateway |
| Instrument model | CIVI/IC-7300 | Gateway with IC-7300 profile |
| Driver vendor (planned registration) | nomulabo | Activity name of the individual developer |
| Author / current runtime driver_vendor | 7M4MON | Author; runtime metadata unchanged until formalization |
| Physical radio | Icom IC-7300 | Connected device behind the gateway |

The planned applicant is an individual developer operating as nomulabo,
author 7M4MON. This is not a claim of incorporation. Current runtime identity
remains unchanged; registration and canonical package naming are pending.

## Requirements reviewed

[IVI Driver Python 1.0, Driver Identifier and Driver Class Name](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverPython/1.0/Spec/IviDriverPython.md#driver-identifier-and-driver-class-name)
requires manufacturer/model tokens, with a driver-vendor suffix when the
manufacturer is unregistered or differs from the driver vendor. The suffix may
have an underscore; the model token may not. The root class excludes the vendor
suffix. Registered vendor abbreviations are used, with an exception for the
unregistered manufacturer token. Distribution/import separators may differ;
their other characters must agree. Existing-driver exemptions are not assumed
to validate this experimental package.

[VPP-9 revision 4.35, cover dated 2024-08-08, sections 2.1, 3.1–3.2](https://www.ivifoundation.org/downloads/VPP/vpp9_4.35_2024-08-08.pdf)
was the revision linked by the official specification index on 2026-11-09.
Its table assigns CI to Cambridge Instruments and IC to Integrated Control
Systems. It contains no CIVI Project, 7M4MON or Icom entry, and no HN or CV
two-character entry. Absence is not availability or reservation. It describes
registration through the Foundation, without requiring membership. Python 1.0
also mentions indefinite-length abbreviations, but this VPP-9 table lists only
two-character abbreviations; obtain Foundation confirmation before relying on
Civi or Mon as a registered long form. Do not use digit-leading 7M4MON as a
Python identifier token.

## Candidate plan

User-selected first choice: request **NL** for driver vendor **nomulabo**, subject to
Foundation acceptance. The manufacturer remains the unregistered CIVI Project
and its chosen first token is Civi. This avoids deciding that the two display
names constitute one registered vendor.

| Item | Current development name | Proposed after NL acceptance |
|---|---|---|
| Driver identifier | Provisional CiviIc7300 | CiviIc7300_NL |
| Distribution | civi-ic7300 | civiic7300-nl |
| Import package | civi_ic7300 | civiic7300_nl |
| Root class | CiviIc7300 | CiviIc7300 |
| Prescribed introduction filename | ___Introduction to CiviIc7300___.md | ___Introduction to CiviIc7300_NL___.md |

The filename uses DriverIdentifier, including its suffix, per
[Core 1.0, Driver Introduction Documentation](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverCore/1.0/Spec/IviDriverCore.md#driver-introduction-documentation).

Second-choice abbreviation: **NM** if NL is unavailable. CV is no longer an
active registration proposal. NL and NM are not claimed as registered or reserved;
current availability must be confirmed by the Foundation.

## Individual applicant

NL was selected by the author on 2026-11-09 for nomulabo, replacing HN and
the earlier MM proposal. NM is the fallback choice. The preceding table review
is historical evidence, not confirmation of current NL availability.
Sections 2.1 and 3.1 explicitly permit non-member vendors to obtain a prefix.
They do not state a corporation-only rule, nor explicitly guarantee individual
applicants will be accepted. Ask the Foundation about registration as individual
developer operating as nomulabo (author 7M4MON) and current NL availability; neither rejection nor acceptance is
established by this document. No inquiry has been sent.

## Compatibility and release work

Keep the current distribution, imports and class during development. Matching
civi-ic7300 to civi_ic7300 after separator normalization proves only package
consistency, not the complete DriverIdentifier grammar.

After registration confirmation, decide the canonical spelling once and update
metadata, package, help, examples and generated documents together. Provide the
old civi_ic7300 import as a compatibility facade to the same implementation;
do not create a second driver or duplicate session state. Test both import paths,
installed wheel/sdist, type exports, exception identity and mixed use. Review
the legacy distribution's migration and dependency policy before publication.

Abbreviation registration, IVI driver registration and LXI certification are
separate actions. This proposal completes none of them. No rename or
compatibility facade has been implemented in 0.13.1.
