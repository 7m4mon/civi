# Band-stack hierarchy (client 0.11.0)

Follow-up: STYLE.md records the 0.13.0 review of all repeated-capability groups,
including the added local KeyerItem.name and retained compatibility spellings.

Each band is now a distinct node with a slots collection:

```python
band = device.band_stacks[3]
slot = band.slots[1]
value = slot.settings
```

The fully nested collection path is `device.band_stacks.bands[3].slots[1]`.
`device.band_stacks[3].slots[1]` is its shorthand. Existing
`device.band_stacks[3, 1]` remains supported and returns the same slot object.
All views share the same driver, control queue, status policy and memory-write
permission. No band/VFO selection command is sent when obtaining a view.

## Types and local identity

| API | Type / meaning |
|---|---|
| `band_stacks.bands` | Read-only BandStackBandCollection reference |
| `bands[band: int]` | BandStackBand, band code 1..11 |
| `band.number: int` | Read-only band code |
| `band.name: str` | Read-only decimal band identifier, e.g. '3'; no inferred MHz label |
| `band.slots` | Read-only BandStackSlotCollection reference |
| `slots.band: int` | Read-only containing band code |
| `slots[slot: int]` | BandStackItem, slot code 1..3 |
| `item.band: int`, `item.slot: int` | Read-only physical selectors |
| `item.name: str` | Read-only slot identifier within its band, e.g. '1' |
| `item.settings: MemorySettings` | Read/write full settings block, RAD:BAND:STACK[?] band*100+slot |
| `item.write_and_read(settings: MemorySettings) -> MemorySettings` | Write and actual readback under the session lock |

All indices are strict integers: booleans, strings and floats are rejected before
I/O. Resolving collections, names and selectors performs no instrument I/O.
Repeated access returns stable view references for this driver instance. Values
are not cached: each settings getter queries the current record. Views cannot
perform settings I/O after their driver session closes.

The new node/collection/item classes are exported for type annotations. Overloaded
indexing distinguishes an integer band index from the existing tuple slot index.

## Iteration and compatibility

The outer BandStackCollection remains a compatibility facade. Its old length of
33 and iteration over `(band, slot)` pairs are unchanged. Use `.bands` for a pure
band-level collection with length 11 and integer band identifiers; each `.slots`
has length 3 and integer slot identifiers:

```python
for band_number in device.band_stacks.bands:
    band = device.band_stacks[band_number]
    for slot_number in band.slots:
        slot = band.slots[slot_number]
        print(band.name, slot.name, slot.settings)
```

No old tuple keys, public methods or iteration contracts were removed. Metadata
references are read-only; saved settings and permissions behave as in STORAGE.md.
The hierarchy does not add a new CI-V command, band entry or cache of radio state.

## Checked offline change/readback/restore

```python
from civi_ic7300 import CiviIc7300, MemorySettings

with CiviIc7300(
    "TCPIP::unused::5025::SOCKET", options={"simulate": True}
) as d:
    d.band_stacks.set_simulated_write_permission(True)
    with d.checked():
        slot = d.band_stacks[3].slots[1]
        old = slot.settings
        try:
            value = MemorySettings(7100000, "USB", 2)
            assert slot.write_and_read(value) == value
            assert d.band_stacks[3, 1].settings == value
        finally:
            slot.settings = old
```

Real writes still require the gateway's existing memory permission. The offline
permission method cannot enable it over TCP. STATUS.md describes OFF/ON checks;
OFF can leave a denied write queued and return unchanged data on readback.
Nested and flat APIs hold the same session lock, without locking other clients
or front-panel controls. No Pi/radio operation was performed for this release.
This addresses the band/slot hierarchy finding; final IVI conformance and the
remaining repeated-capability, naming and documentation audit are still open.
