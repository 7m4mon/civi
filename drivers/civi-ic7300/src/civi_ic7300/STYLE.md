# API naming and repeated-capability review — 0.13.0, 2026-11-10

## Scope and method

Reviewed all twelve client Python source modules, the 43-type public help
inventory, root child references and repeated-capability selectors. Function,
parameter and class naming is checked with Ruff's N rules; E/W rules check code
layout. Module names and public help names were also inspected. Public names
use snake_case for members and PascalCase for types. Existing acronym spelling
and exception identities are retained. Formatting does not alter SCPI strings.

The [Python 1.0 specification](https://github.com/IviFoundation/IviDrivers/blob/main/IviDriverPython/1.0/Spec/IviDriverPython.md#repeated-capability-reference-property-naming)
recommends collection/item naming, plural collection references and physical
item names. These are recommendations, not additional mandatory APIs. Typed
menu helpers choose a value type; they are not interchangeable item selectors.

## Repeated-capability findings

| Reference | Items / physical name | Finding |
|---|---|---|
| vfos | Vfo; SELECTED / OTHER | Names are relative selectors, never inferred A/B identities; matching VfoCollection |
| menus | MenuItem; four-digit menu number | Local read-only identity; plural reference. Item suffix retained for compatibility |
| memories | MemoryItem; 01..99, P1, P2 | Physical channel name differs from editable record.name; item suffix retained |
| keyers | KeyerItem; M1..M8 | Missing name added in 0.13.0; read-only, local. Item suffix retained |
| band_stacks.bands | BandStackBand; 1..11 | Nested bands/slots; names and child references read-only |
| bands[band].slots | BandStackItem; 1..3 within band | Name local to containing band; recommended BandStackSlot class spelling deferred |
| band_stacks compatibility facade | 33 (band, slot) pairs | Old indexing/length/iteration retained; canonical hierarchy is .bands[band].slots[slot] |

Root collection references are read-only. Memory/keyer view objects may be
freshly constructed on access; object identity caching is not promised there.
Their selectors identify records, while current values are queried each time.
Band and VFO views keep their existing caching behavior. Invalid selectors are
validated before I/O by existing tests. Closing a session prevents value I/O;
local physical names can still be read.

Scope fixed-edge and transmit-band functions retain explicit indexed arguments;
they do not claim collection-style child APIs. A future collection facade is
optional design work. Renaming MenuItem/MemoryItem/KeyerItem/BandStackItem just
to match recommended type spelling is deferred to preserve annotations/imports.
No recommendation above is represented as a mandatory requirement already met.

## Reproducing style checks

From the repository root, with development tools available:

```text
python -m ruff check drivers/civi-ic7300/src/civi_ic7300
python -m ruff format --check drivers/civi-ic7300/src/civi_ic7300
python -m pycodestyle drivers/civi-ic7300/src/civi_ic7300 --ignore E203,E704,W503,W504 --max-doc-length 72
python -m mypy --strict drivers/civi-ic7300/src/civi_ic7300
```

Reviewed with Ruff 0.17.4, pycodestyle 2.15.0 and mypy 2.4.1. Ruff configuration
is in the client pyproject.toml: Python 3.11 syntax, 79-column code, E/W/N rules.
Docstrings/comments use 72-column wrapping. Ruff check is a subset of style
review, not an exhaustive semantic PEP 8 or IVI validator.

The independent pycodestyle run excludes formatter differences: E203 for complex
slice spacing; E704 for compact abstract/overload ellipsis declarations; W503
and W504 for operator-break placement. These are explicit tool accommodations,
not blanket suppression of line length or public naming. PEP 8 permits locally
consistent operator breaks and discusses symmetric complex-slice spacing:
[PEP 8](https://peps.python.org/pep-0008/).

## Verification boundaries

test_python_repeated.py checks local names without any instrument I/O and all
eight addressed keyer changes/readbacks/restores in independent simulation and
loopback gateway mocks. Stored text does not emit CW. Existing storage, hierarchy,
controls, help and command-audit tests exercise compatibility. No physical Pi or
radio was operated for 0.13.0; the limited 0.12.1 hardware record remains history.
