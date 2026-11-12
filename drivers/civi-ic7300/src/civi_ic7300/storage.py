"""Lossless IC-7300 memory records, band stacks and keyer text."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Callable, Iterator, TypeVar, overload

from .controls import MODE_CODES, boolean, choice, integer, mode_name
from .errors import ProtocolError

if TYPE_CHECKING:
    from .driver import CiviIc7300

T = TypeVar("T")
TONE_MODES = ("OFF", "TONE", "TSQL")


def _bcd(value: int, size: int, little: bool = False) -> bytes:
    integer(value, 0, 100**size - 1)
    data = bytes.fromhex(f"{value:0{size * 2}d}")
    return data[::-1] if little else data


def _unbcd(data: bytes, little: bool = False) -> int:
    if not data or any(b >> 4 > 9 or b & 15 > 9 for b in data):
        raise ValueError("Invalid BCD data")
    return int((data[::-1] if little else data).hex())


def _tone(value: float) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Tone must be numeric Hz")
    number = Decimal(str(value)) * 10
    if (
        not number.is_finite()
        or not 670 <= number <= 2541
        or number != number.to_integral_value()
    ):
        raise ValueError("Tone must be 67.0..254.1 Hz in 0.1 Hz increments")
    return int(number)


@dataclass(frozen=True)
class MemorySettings:
    """One complete 14-byte frequency/mode/DATA/tone block.

    The record envelope supports 30000..74800000 Hz. Writes are
    additionally constrained by the gateway's selected radio profile.
    """

    frequency_hz: int
    mode: str
    filter_number: int = 1
    data: bool = False
    tone_mode: str = "OFF"
    repeater_tone_hz: float = 88.5
    tone_squelch_hz: float = 88.5

    def __post_init__(self) -> None:
        integer(self.frequency_hz, 30000, 74800000)
        object.__setattr__(self, "mode", mode_name(self.mode))
        integer(self.filter_number, 1, 3)
        boolean(self.data)
        object.__setattr__(
            self, "tone_mode", choice(self.tone_mode, TONE_MODES)
        )
        object.__setattr__(
            self, "repeater_tone_hz", _tone(self.repeater_tone_hz) / 10
        )
        object.__setattr__(
            self, "tone_squelch_hz", _tone(self.tone_squelch_hz) / 10
        )

    def to_bytes(self) -> bytes:
        return (
            _bcd(self.frequency_hz, 5, True)
            + bytes(
                (
                    MODE_CODES[self.mode],
                    self.filter_number,
                    int(self.data) << 4 | TONE_MODES.index(self.tone_mode),
                )
            )
            + _bcd(_tone(self.repeater_tone_hz), 3)
            + _bcd(_tone(self.tone_squelch_hz), 3)
        )

    def to_hex(self) -> str:
        return self.to_bytes().hex().upper()

    @classmethod
    def from_bytes(cls, data: bytes) -> MemorySettings:
        if not isinstance(data, bytes) or len(data) != 14:
            raise ValueError("Expected exactly 14 memory-setting bytes")
        mode = next((k for k, v in MODE_CODES.items() if v == data[5]), None)
        if (
            mode is None
            or data[7] >> 4 not in (0, 1)
            or data[7] & 15 not in (0, 1, 2)
        ):
            raise ValueError("Invalid memory mode/DATA/tone flags")
        return cls(
            _unbcd(data[:5], True),
            mode,
            data[6],
            bool(data[7] >> 4),
            TONE_MODES[data[7] & 15],
            _unbcd(data[8:11]) / 10,
            _unbcd(data[11:14]) / 10,
        )

    @classmethod
    def from_hex(cls, text: str) -> MemorySettings:
        if (
            not isinstance(text, str)
            or re.fullmatch(r"[0-9A-Fa-f]{28}", text) is None
        ):
            raise ValueError("Expected exactly 28 hexadecimal characters")
        return cls.from_bytes(bytes.fromhex(text))


@dataclass(frozen=True)
class MemoryRecord:
    """Complete 39-byte M-CH payload, excluding its channel selector.

    The secondary block is used for transmit when Split is ON, and
    preserved even when Split is OFF. Name is normalized to ten valid
    single-byte chars; display_name strips trailing spaces without
    changing the stored bytes.
    """

    receive: MemorySettings
    transmit: MemorySettings
    split_enabled: bool = False
    select_group: int = 0
    name: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.receive, MemorySettings) or not isinstance(
            self.transmit, MemorySettings
        ):
            raise TypeError("Use MemorySettings for both memory blocks")
        boolean(self.split_enabled)
        integer(self.select_group, 0, 3)
        if not isinstance(self.name, str):
            raise TypeError("Memory name must be text")
        encoded = self.name.encode("cp932")
        if len(encoded) > 10 or any(
            not (32 <= b <= 126 or 0xA1 <= b <= 0xDF) for b in encoded
        ):
            raise ValueError(
                "Memory name: at most 10 ASCII/half-width kana bytes"
            )
        object.__setattr__(
            self, "name", encoded.ljust(10, b" ").decode("cp932")
        )

    @property
    def display_name(self) -> str:
        return self.name.rstrip(" ")

    def to_bytes(self) -> bytes:
        flags = int(self.split_enabled) << 4 | self.select_group
        return (
            bytes((flags,))
            + self.receive.to_bytes()
            + self.transmit.to_bytes()
            + self.name.encode("cp932")
        )

    def to_hex(self) -> str:
        return self.to_bytes().hex().upper()

    @classmethod
    def simple(cls, settings: MemorySettings, name: str = "") -> MemoryRecord:
        return cls(settings, settings, name=name)

    @classmethod
    def from_bytes(cls, data: bytes) -> MemoryRecord:
        if not isinstance(data, bytes) or len(data) != 39:
            raise ValueError("Expected exactly 39 memory-record bytes")
        if data[0] >> 4 not in (0, 1) or data[0] & 15 not in (0, 1, 2, 3):
            raise ValueError("Invalid memory Split/select flags")
        return cls(
            MemorySettings.from_bytes(data[1:15]),
            MemorySettings.from_bytes(data[15:29]),
            bool(data[0] >> 4),
            data[0] & 15,
            data[29:].decode("cp932"),
        )

    @classmethod
    def from_hex(cls, text: str) -> MemoryRecord:
        if (
            not isinstance(text, str)
            or re.fullmatch(r"[0-9A-Fa-f]{78}", text) is None
        ):
            raise ValueError("Expected exactly 78 hexadecimal characters")
        return cls.from_bytes(bytes.fromhex(text))


def _memory_number(key: int | str) -> int:
    if isinstance(key, str):
        text = key.upper()
        if text in ("P1", "P2"):
            return 100 if text == "P1" else 101
        if re.fullmatch(r"[0-9]{1,4}", text) is None:
            raise ValueError("Use channel 1..99, P1 or P2")
        key = int(text)
    return integer(key, 1, 101)


def _keyer_text(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("Keyer text must be a string")
    if re.fullmatch(r"[0-9A-Za-z /?.,@^*]{0,70}", value) is None:
        raise ValueError("Keyer text: at most 70 supported ASCII characters")
    return '"' + value + '"'


def _read_keyer(text: str) -> str:
    if not text.startswith('"') or not text.endswith('"'):
        raise ValueError("Expected quoted keyer text")
    fields = next(csv.reader([text], strict=True))
    if len(fields) != 1:
        raise ValueError("Expected one keyer string")
    _keyer_text(fields[0])
    return fields[0]


class StoredControl:
    def __init__(self, driver: CiviIc7300) -> None:
        self._driver = driver

    def _read(self, command: str, decode: Callable[[str], T]) -> T:
        reply = self._driver._operation(command, True)
        try:
            return decode(reply)
        except (
            ValueError,
            TypeError,
            KeyError,
            OverflowError,
            csv.Error,
            StopIteration,
        ) as exc:
            raise ProtocolError(
                "Invalid stored-data response to " + command
            ) from exc

    def _write(self, command: str) -> None:
        self._driver._write_operation(command)

    def set_simulated_write_permission(self, enabled: bool) -> None:
        """Set the shared offline memory-write gate; never alters a real
        gateway.
        """
        boolean(enabled)
        with self._driver._lock:
            self._driver._ensure_open()
            if self._driver._simulation is None:
                raise RuntimeError(
                    "Simulation only; configure memory "
                    "permission on the CIVI gateway"
                )
            self._driver._simulation.storage.write_enabled = enabled


class MemoryItem(StoredControl):
    def __init__(self, driver: CiviIc7300, number: int) -> None:
        super().__init__(driver)
        self._number = integer(number, 1, 101)

    @property
    def number(self) -> int:
        return self._number

    @property
    def name(self) -> str:
        return {100: "P1", 101: "P2"}.get(self._number, f"{self._number:02d}")

    @property
    def record(self) -> MemoryRecord | None:
        return self._read(
            f"RAD:MEM:CONTENT? {self._number}",
            lambda s: None if s.upper() == "FF" else MemoryRecord.from_hex(s),
        )

    @record.setter
    def record(self, record: MemoryRecord) -> None:
        if not isinstance(record, MemoryRecord):
            raise TypeError(
                "Use MemoryRecord; clear ordinary "
                "channels explicitly with clear()"
            )
        if self._number >= 100 and (
            record.split_enabled or record.select_group
        ):
            raise ValueError("P1/P2 require Split OFF and select group zero")
        self._write(f"RAD:MEM:CONTENT {self._number},{record.to_hex()}")

    def write_and_read(self, record: MemoryRecord) -> MemoryRecord | None:
        with self._driver._lock:
            self.record = record
            return self.record

    def clear(self) -> None:
        """Address-specific 1A 00 FF clear; P1/P2 are not allowed."""
        integer(self._number, 1, 99)
        self._write(f"RAD:MEM:CONTENT {self._number},FF")


class MemoryCollection(StoredControl):
    def __getitem__(self, key: int | str) -> MemoryItem:
        return MemoryItem(self._driver, _memory_number(key))

    def __len__(self) -> int:
        return 101

    def __iter__(self) -> Iterator[int]:
        return iter(range(1, 102))

    def select(self, key: int | str) -> None:
        self._write(f"RAD:MEM:SELECT {_memory_number(key)}")

    def enable(self) -> None:
        self._write("RAD:MEM:ENABLE")

    def store_current_in_selected(self) -> None:
        self._write("RAD:MEM:WRITE")

    def copy_selected_to_vfo(self) -> None:
        self._write("RAD:MEM:TOVFO")

    def clear_selected(self) -> None:
        """Legacy 0B action on the radio's current memory selection, not
        a cached ID. Enter memory mode explicitly with enable() first.
        """
        self._write("RAD:MEM:CLEAR")


class BandStackItem(StoredControl):
    def __init__(self, driver: CiviIc7300, band: int, slot: int) -> None:
        super().__init__(driver)
        self._band, self._slot = integer(band, 1, 11), integer(slot, 1, 3)

    @property
    def band(self) -> int:
        return self._band

    @property
    def slot(self) -> int:
        return self._slot

    @property
    def name(self) -> str:
        """Physical slot identifier within its band, as decimal text."""
        return str(self._slot)

    @property
    def settings(self) -> MemorySettings:
        return self._read(
            f"RAD:BAND:STACK? {self._band * 100 + self._slot}",
            MemorySettings.from_hex,
        )

    @settings.setter
    def settings(self, value: MemorySettings) -> None:
        if not isinstance(value, MemorySettings):
            raise TypeError("Use MemorySettings")
        self._write(
            f"RAD:BAND:STACK {self._band * 100 + self._slot},{value.to_hex()}"
        )

    def write_and_read(self, value: MemorySettings) -> MemorySettings:
        with self._driver._lock:
            self.settings = value
            return self.settings


class BandStackSlotCollection(StoredControl):
    """Three slots within one band; construction/selection performs no
    I/O.
    """

    def __init__(self, driver: CiviIc7300, band: int) -> None:
        super().__init__(driver)
        self._band = integer(band, 1, 11)
        self._items = {
            slot: BandStackItem(driver, self._band, slot)
            for slot in range(1, 4)
        }

    @property
    def band(self) -> int:
        return self._band

    def __getitem__(self, slot: int) -> BandStackItem:
        return self._items[integer(slot, 1, 3)]

    def __len__(self) -> int:
        return 3

    def __iter__(self) -> Iterator[int]:
        return iter(range(1, 4))


class BandStackBand(StoredControl):
    """One physical band with a read-only slots reference."""

    def __init__(self, driver: CiviIc7300, number: int) -> None:
        super().__init__(driver)
        self._number = integer(number, 1, 11)
        self._slots = BandStackSlotCollection(driver, self._number)

    @property
    def number(self) -> int:
        return self._number

    @property
    def name(self) -> str:
        return str(self._number)

    @property
    def slots(self) -> BandStackSlotCollection:
        return self._slots


class BandStackBandCollection(StoredControl):
    """Canonical band level: eleven bands with three slots each."""

    def __init__(self, driver: CiviIc7300) -> None:
        super().__init__(driver)
        self._items = {
            band: BandStackBand(driver, band) for band in range(1, 12)
        }

    def __getitem__(self, band: int) -> BandStackBand:
        return self._items[integer(band, 1, 11)]

    def __len__(self) -> int:
        return 11

    def __iter__(self) -> Iterator[int]:
        return iter(range(1, 12))


class BandStackCollection(StoredControl):
    """Compatibility facade: integer band shorthand plus existing flat
    slot API.

    len/iteration retain the old 33-slot behavior. Use bands for a
    consistently nested collection with eleven band identifiers.
    """

    def __init__(self, driver: CiviIc7300) -> None:
        super().__init__(driver)
        self._bands = BandStackBandCollection(driver)

    @property
    def bands(self) -> BandStackBandCollection:
        return self._bands

    @overload
    def __getitem__(self, key: int) -> BandStackBand: ...

    @overload
    def __getitem__(self, key: tuple[int, int]) -> BandStackItem: ...

    def __getitem__(
        self, key: int | tuple[int, int]
    ) -> BandStackBand | BandStackItem:
        if type(key) is int:
            return self._bands[key]
        if not isinstance(key, tuple) or len(key) != 2:
            raise TypeError(
                "Use band_stacks[band].slots[slot] or band_stacks[band, slot]"
            )
        return self._bands[key[0]].slots[key[1]]

    def __len__(self) -> int:
        return 33

    def __iter__(self) -> Iterator[tuple[int, int]]:
        return iter(
            (band, slot) for band in range(1, 12) for slot in range(1, 4)
        )


class KeyerItem(StoredControl):
    def __init__(self, driver: CiviIc7300, number: int) -> None:
        super().__init__(driver)
        self._number = integer(number, 1, 8)

    @property
    def number(self) -> int:
        return self._number

    @property
    def name(self) -> str:
        """Physical keyer identifier M1..M8; no instrument I/O."""
        return f"M{self._number}"

    @property
    def text(self) -> str:
        return self._read(f"RAD:KEYER:TEXT? {self._number}", _read_keyer)

    @text.setter
    def text(self, value: str) -> None:
        self._write(f"RAD:KEYER:TEXT {self._number},{_keyer_text(value)}")

    def write_and_read(self, value: str) -> str:
        with self._driver._lock:
            self.text = value
            return self.text


class KeyerCollection(StoredControl):
    def __getitem__(self, number: int) -> KeyerItem:
        return KeyerItem(self._driver, number)

    def __len__(self) -> int:
        return 8

    def __iter__(self) -> Iterator[int]:
        return iter(range(1, 9))
