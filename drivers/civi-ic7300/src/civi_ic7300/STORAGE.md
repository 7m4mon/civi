# Stored-data API (client 0.11.0)

These APIs read and change stored records through CIVI. They do not send CW or
enable PTT. Validation covers offline simulation and mock TCP on Windows;
physical IC-7300/Pi verification of these client APIs remains outstanding.

## Record values

`MemorySettings(frequency_hz: int, mode: str, filter_number: int = 1,
data: bool = False, tone_mode: str = 'OFF', repeater_tone_hz: float = 88.5,
tone_squelch_hz: float = 88.5)` is an immutable complete 14-byte block.
Frequency is whole Hz, 30000..74800000 in the record format. The current gateway
profile additionally limits writes to 30000..60000000 Hz. Modes use the existing
radio mode names, filter is 1..3, DATA is bool, tone mode is OFF/TONE/TSQL and
both tone frequencies are 67.0..254.1 Hz in 0.1 Hz increments. This range does
not imply every numeric tone is supported by every radio configuration.

`MemoryRecord(receive: MemorySettings, transmit: MemorySettings,
split_enabled: bool = False, select_group: int = 0, name: str = '')` is immutable
and retains all 39 payload bytes, excluding the channel selector. Select group
is 0..3. The secondary block is preserved even with Split OFF and must be valid.
`MemoryRecord.simple(settings, name='')` copies one block into both positions.
Both types expose `to_bytes()`, `to_hex()`, `from_bytes()` and `from_hex()`;
invalid lengths, flags, BCD and values are rejected.

Names allow up to ten single-byte ASCII/half-width kana characters, encoded as
cp932. `name` retains ten bytes including space padding; `display_name` removes
trailing spaces for display. No field is silently discarded when editing a
record; use `dataclasses.replace(old_record, name='NEW')` to retain other fields.

## Collections

Root `memories`, `band_stacks` and `keyers` references are read-only.

| API | Meaning |
|---|---|
| `memories[number_or_name]` | Channels 1..99, P1 (100), P2 (101); numeric strings accepted |
| `item.number`, `item.name` | Read-only channel identity |
| `item.record` | Read `MemoryRecord` or `None` for an empty channel; assign a record to write |
| `item.write_and_read(record)` | Write and return actual readback, potentially `None` if another client clears it |
| `item.clear()` | Address-specific clear, channels 1..99 only |
| `band_stacks[band].slots[slot].settings` | Read/write `MemorySettings`; bands 1..11, slots 1..3 |
| `band_stacks[band, slot].write_and_read(settings)` | Write and return actual settings |
| `keyers[number].text` | Read/write stored text M1..M8 |
| `keyers[number].write_and_read(text)` | Write and return actual text |

Iteration returns channel numbers (101), `(band, slot)` pairs (33), or keyer
numbers (8). P1/P2 record writes require Split OFF and select group zero.
Address-specific clearing of P1/P2 is rejected before I/O. Keyer text permits
up to 70 ASCII letters/digits and ` /?.,@^*`; commas are correctly quoted.
Readback removes trailing spaces. Hardware restrictions on contest-number `*`
placement remain the radio's responsibility; the simulator does not enforce
cross-channel restrictions or model RF effects.

`memories.select(key)` chooses the memory channel without changing VFO/memory
mode. Call `memories.enable()` explicitly to enter memory mode. This distinction
was verified on MAIN 1.42; choosing an empty channel while in VFO mode does not
make the displayed frequency unavailable until memory mode is entered.
`store_current_in_selected()`, `copy_selected_to_vfo()` and `clear_selected()`
are legacy actions on the radio's current memory selection. They do not take a
channel argument or cache a supposedly authoritative selection. Another client
can change the selection between calls. Prefer addressed records for backup
and editing. The P1/P2 protection on `item.clear()` does not apply to the legacy
selection-relative clear action.

On the tested MAIN 1.42 unit, `clear_selected()` (CI-V 0B) was rejected with
NAK in VFO mode and succeeded after `enable()`. The driver does not silently
switch modes on behalf of this method. Both simulation models preserve the
selection/mode distinction and reject selection-relative clear in VFO mode.

## Permissions, errors and concurrency

All stored-data writes use the gateway's existing `[permissions].memory` gate,
which defaults OFF. Menu/link/calibration gates remain independent. The client
cannot enable real gateway permissions. Offline simulation shares one memory
gate across the three collections, enabled explicitly with
`device.memories.set_simulated_write_permission(True)` (the same method is
available on the other two collections). Calling it on a real TCP session
raises `RuntimeError`.

Mutation and selection methods follow the status option. With checks ON,
preexisting errors abort and NAK/serial errors raise DeviceError before readback.
With checks OFF errors remain queued; readback can be unchanged after denial.
Use checked() for an explicitly verified sequence. Bad replies raise ProtocolError
or QueryError for the ERROR sentinel. A transport timeout closes the session and
leaves the actual write outcome unknown; reconnect and read before retrying.
`write_and_read` holds the session lock through both operations, preventing
interleaving on that session. It cannot lock out other clients or local knobs.

Receive reset preserves stored records, band stacks, keyer text and permission
settings in the mock models. Simulation stores values logically, and does not
prove hardware persistence, legacy-action side effects or radio timing.

## Offline example

```python
from dataclasses import replace
from civi_ic7300 import CiviIc7300, MemoryRecord, MemorySettings

with CiviIc7300(
    "TCPIP::unused::5025::SOCKET",
    options={"simulate": True, "query_instrument_status": True},
) as d:
    d.memories.set_simulated_write_permission(True)
    channel = d.memories[99]
    old = channel.record
    try:
        value = MemoryRecord.simple(MemorySettings(7100000, "LSB"), "TEST")
        assert channel.write_and_read(value) == value
        actual = channel.write_and_read(replace(value, name="NEW"))
        assert actual is not None and actual.display_name == "NEW"
    finally:
        if old is None:
            channel.clear()
        else:
            channel.record = old
```

Band-stack/keyer editing uses the same read/save, change, readback, restore
sequence. This is stored-data editing, not an IC-7300 Partial Reset operation.

HIERARCHY.md documents the nested band/slot collections. Tuple indexing and
the old 33-slot length/iteration remain; use band_stacks.bands for eleven-band
iteration. Each band/slot has a read-only local physical name and selector.
