# Band edges, DATA and alternate IP+ (client 0.10.0)

`device.bands: Bands` is a read-only interface reference. It wraps five existing
gateway definitions without identifying a country/region band plan or enabling
transmission. Factory/default values always come from the gateway response.

## Band values and methods

`BandEdges(lower_hz: int, upper_hz: int)` is immutable. Both values are whole Hz,
0..74800000, with lower <= upper. This is the record format's range, independent
of the gateway's narrower operating-frequency limits. `to_hex()` and
`from_hex(text)` preserve the eleven-byte CI-V record: two five-byte little-endian
BCD values separated by literal 2D. A single-frequency or zero-valued record is
accepted by the codec; actual hardware may impose additional restrictions.

| API | Direction / result |
|---|---|
| `default_edges` | Read-only BandEdges, RAD:BAND:EDGES? |
| `factory_count` | Read-only int 0..30, RAD:TXBAND:COUNT? |
| `user_count` | Read-only int 0..30, RAD:TXBAND:USERCOUNT? |
| `read_factory(index: int)` | BandEdges, RAD:TXBAND:READ? index |
| `read_user(index: int)` | BandEdges or None for an unprogrammed slot, RAD:TXBAND:USER? index |
| `write_user(index: int, edges: BandEdges)` | None, RAD:TXBAND:USER index,record |
| `write_and_read_user(index: int, edges: BandEdges)` | Actual readback BandEdges or None |

Indexed methods accept protocol indices 1..30. Consult current counts and the
radio documentation before operating on real entries. Counts are not cached;
the client does not infer insert/delete operations or expand a band table.
No new factory-band write or user-band delete command is provided.

An unprogrammed user slot returns the single byte `FF` on the tested MAIN 1.42
radio (observed at slot 17). The gateway preserves it as `FF`; `read_user()`
returns `None`. A slot count can include unprogrammed slots. This is distinct
from a valid zero-frequency record. `BandEdges.from_hex("FF")` and writing
`None`/`FF` remain invalid. The sentinel is accepted only for user-slot reads;
malformed payloads still fail. Do not overwrite an empty slot merely to test it:
the API does not provide a matching delete operation to restore emptiness.

User writes use the existing gateway `[permissions].calibration` gate, default
OFF. Writes follow the status option. With checks ON, prior/result errors
are checked and stop readback; OFF can leave errors queued and return unchanged
data. Use checked() for an explicitly checked sequence. Malformed records/counts
raise ProtocolError; the ERROR sentinel raises QueryError while OFF. Transport
failure closes the session and leaves the actual write outcome uncertain.

The write/readback pair holds the session lock, but cannot exclude local knobs
or other clients. Save the previous record and restore it explicitly when testing.

```python
from civi_ic7300 import BandEdges, CiviIc7300

with CiviIc7300(
    "TCPIP::unused::5025::SOCKET",
    options={"simulate": True, "query_instrument_status": True},
) as d:
    d.bands.set_simulated_calibration_permission(True)
    old = d.bands.read_user(1)
    try:
        value = BandEdges(7000000, 7300000)
        assert d.bands.write_and_read_user(1, value) == value
    finally:
        d.bands.write_user(1, old)
```

`set_simulated_calibration_permission(enabled: bool)` changes only calibration,
sharing that gate with the menu simulator. Other permission groups are preserved.
It raises RuntimeError on a real TCP session and cannot authorize real writes.
The existing `menus.set_simulated_write_permissions(...)` can also set or revoke
this shared permission.

Both mock systems use a canned 7.1..7.2 MHz record and zero counts, while still
accepting bounded indexed codec tests. This is not a real region band plan or
evidence that a device has thirty usable bands. User records persist across
receive reset in the simulation; writes do not insert entries or change counts.
Hardware persistence, legal operating limits and actual RF behavior are untested.

## DATA/filter

`radio.data_filter: DataFilter` reads/writes CI-V 1A06.
`DataFilter(enabled: bool, filter_number: int)` is immutable. DATA ON requires
filter 1..3. DATA OFF readback can report filter 0..3, but an OFF write must use
zero. Use `DataFilter(False, 0)` to disable DATA. Writing an OFF record containing
filter 1..3 raises ValueError before I/O; its value is not silently discarded.
`DataFilter.from_hex()` validates two reply bytes; `to_write_hex()` validates
the stricter write format.

```python
from civi_ic7300 import DataFilter

device.radio.data_filter = DataFilter(True, 2)
actual = device.radio.data_filter
device.radio.data_filter = DataFilter(False, 0)
```

To preserve a specific filter while returning to DATA OFF, back up the complete
`vfos['SELECTED'].mode: VfoMode` and restore that through its existing API.
The radio's OFF readback need not equal the `DataFilter(False, 0)` request.
Scalar error checking follows `query_instrument_status`; enable it for device
error checks on these writes. Wrong input types/values fail before I/O, and
malformed replies raise ProtocolError.

The independent simulator shares DATA/filter with selected VFO and memory working
state. OFF preserves the current filter, and receive reset restores the captured
mode/DATA/filter baseline. The gateway mock stores the 1A06 value independently
of its VFO-mode record; it verifies codec traffic, not full radio side effects.

## Alternate IP+

`radio.ip_plus_alternate_enabled: bool` reads/writes the existing 1A07 command.
It aliases `radio.ip_plus_enabled` (1665), including simulation state. It follows
the same scalar status-check option and does not add a new radio feature.

All new APIs were tested on Windows in independent simulation and mock TCP.
No physical radio/Pi was operated for this release; IVI conformity and registration
remain unclaimed.
