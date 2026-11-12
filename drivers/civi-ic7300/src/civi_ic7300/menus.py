"""Typed values and metadata for all 216 IC-7300 menu definitions."""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Generic, Iterator, TypeVar, cast

from .controls import ScopeEdges, boolean, integer, parse_bool
from .errors import ProtocolError

if TYPE_CHECKING:
    from .driver import CiviIc7300


@dataclass(frozen=True)
class AudioFilter:
    """HPF code 0..20 and LPF code 5..25; bypass codes are 0 and 25."""

    high_pass_code: int
    low_pass_code: int

    def __post_init__(self) -> None:
        integer(self.high_pass_code, 0, 20)
        integer(self.low_pass_code, 5, 25)
        if (
            self.high_pass_code
            and self.low_pass_code != 25
            and self.high_pass_code >= self.low_pass_code
        ):
            raise ValueError(
                "HPF must be below LPF unless either side is bypassed"
            )


@dataclass(frozen=True)
class Bandwidth:
    """Transmit HPF/LPF edge index codes 0..3, not frequencies in Hz."""

    high_pass_code: int
    low_pass_code: int

    def __post_init__(self) -> None:
        integer(self.high_pass_code, 0, 3)
        integer(self.low_pass_code, 0, 3)


@dataclass(frozen=True)
class RgbColor:
    """RGB component codes, each 0..255."""

    red: int
    green: int
    blue: int

    def __post_init__(self) -> None:
        for value in (self.red, self.green, self.blue):
            integer(value, 0, 255)


class MenuKind(StrEnum):
    BOOLEAN = "boolean"
    INTEGER = "integer"
    AUDIO_FILTER = "audio_filter"
    BANDWIDTH = "bandwidth"
    RGB = "rgb"
    SCOPE_EDGES = "scope_edges"
    TEXT = "text"
    DATE = "date"
    TIME = "time"
    UTC_OFFSET = "utc_offset"


MenuValue = (
    bool
    | int
    | AudioFilter
    | Bandwidth
    | RgbColor
    | ScopeEdges
    | str
    | dt.date
    | dt.time
    | dt.timedelta
)
MenuKey = int | str
T = TypeVar("T")


@dataclass(frozen=True)
class MenuDefinition:
    number: int
    header: str
    description: str
    kind: MenuKind
    permission: str
    writable: bool
    minimum: int | None
    maximum: int | None
    step: int | None
    unit: str
    choices: tuple[int | str, ...]
    sample_response: str


@lru_cache(maxsize=1)
def definitions() -> tuple[MenuDefinition, ...]:
    data = json.loads(
        Path(__file__)
        .with_name("menu-catalog.json")
        .read_text(encoding="utf-8")
    )
    if data["schema_version"] != 1 or data["model"] != "IC-7300":
        raise ValueError("Unsupported packaged menu schema")
    result = []
    kinds = {
        "hpf": MenuKind.AUDIO_FILTER,
        "bandwidth": MenuKind.BANDWIDTH,
        "color": MenuKind.RGB,
        "menu_edge": MenuKind.SCOPE_EDGES,
        "opening": MenuKind.TEXT,
        "date": MenuKind.DATE,
        "time": MenuKind.TIME,
        "timezone": MenuKind.UTC_OFFSET,
    }
    for item in data["items"]:
        codec = item["codec"]
        minimum = maximum = step = None
        unit = ""
        choices: tuple[int | str, ...] = ()
        if codec["names"] == ["OFF", "ON"]:
            kind = MenuKind.BOOLEAN
            choices = ("OFF", "ON")
        elif codec["kind"] in ("number", "repeater_offset"):
            kind = MenuKind.INTEGER
            minimum, maximum = codec["minimum"], codec["maximum"]
            step = 1000 if codec["kind"] == "repeater_offset" else 1
            unit = "Hz" if step == 1000 else "protocol code"
            if item["number"] in (160, 181):
                unit = "s"
            choices = tuple(codec["choices"])
        else:
            kind = kinds[codec["kind"]]
            if kind == MenuKind.TEXT:
                minimum, maximum, step, unit = 0, 10, 1, "characters"
            elif kind == MenuKind.UTC_OFFSET:
                minimum, maximum, step, unit = -840, 840, 1, "minutes"
        definition = MenuDefinition(
            item["number"],
            item["header"],
            item["description"],
            kind,
            item["permission"],
            "w" in item["access"],
            minimum,
            maximum,
            step,
            unit,
            choices,
            item["sample"],
        )
        if (
            definition.header != f"RAD:MENU:{definition.number:04d}"
            or definition.permission not in ("menu", "link", "calibration")
        ):
            raise ValueError("Invalid packaged menu definition")
        result.append(definition)
    if len(result) != 216 or {x.number for x in result} != set(
        range(1, 218)
    ) - {28}:
        raise ValueError("Incomplete packaged menu schema")
    return tuple(result)


def _require(value: object, cls: type[T]) -> T:
    if type(value) is not cls:
        raise TypeError(f"Expected {cls.__name__}")
    return value


def encode(definition: MenuDefinition, value: MenuValue) -> str:
    kind = definition.kind
    if kind == MenuKind.BOOLEAN:
        return boolean(_require(value, bool))
    if kind == MenuKind.INTEGER:
        assert (
            definition.minimum is not None and definition.maximum is not None
        )
        number = integer(
            _require(value, int), definition.minimum, definition.maximum
        )
        if definition.step and number % definition.step:
            raise ValueError(
                f"Value must be a multiple of {definition.step} "
                f"{definition.unit}"
            )
        if definition.choices and number not in definition.choices:
            raise ValueError("Unsupported protocol choice")
        return str(number)
    if kind == MenuKind.AUDIO_FILTER:
        audio = _require(value, AudioFilter)
        return f"{audio.high_pass_code:02d}{audio.low_pass_code:02d}"
    if kind == MenuKind.BANDWIDTH:
        bandwidth = _require(value, Bandwidth)
        return f"{bandwidth.high_pass_code:X}{bandwidth.low_pass_code:X}"
    if kind == MenuKind.RGB:
        color = _require(value, RgbColor)
        return f"{color.red:04d}{color.green:04d}{color.blue:04d}"
    if kind == MenuKind.SCOPE_EDGES:
        edges = _require(value, ScopeEdges)
        return "".join(
            bytes.fromhex(f"{v // 100:06d}")[::-1].hex().upper()
            for v in (edges.lower_hz, edges.upper_hz)
        )
    if kind == MenuKind.TEXT:
        text = _require(value, str)
        if re.fullmatch(r"[A-Z0-9 ./@-]{0,10}", text) is None:
            raise ValueError(
                "Opening text: up to 10 uppercase "
                "letters, digits or space ./@-"
            )
        return '"' + text + '"'
    if kind == MenuKind.DATE:
        date = _require(value, dt.date)
        integer(date.year, 2000, 2099)
        return date.isoformat()
    if kind == MenuKind.TIME:
        clock = _require(value, dt.time)
        if (
            clock.second
            or clock.microsecond
            or clock.tzinfo is not None
            or clock.fold
        ):
            raise ValueError("Clock uses a naive HH:MM value with no seconds")
        return clock.strftime("%H:%M")
    offset = _require(value, dt.timedelta)
    seconds = offset.total_seconds()
    if seconds % 60 or not -14 * 3600 <= seconds <= 14 * 3600:
        raise ValueError("UTC offset must be -14:00..+14:00 in whole minutes")
    minutes = int(abs(seconds) // 60)
    return (
        "-" if seconds < 0 else "+"
    ) + f"{minutes // 60:02d}:{minutes % 60:02d}"


def _decimal_hex(text: str, digits: int) -> str:
    if re.fullmatch(r"[0-9]{" + str(digits) + "}", text) is None:
        raise ValueError("Invalid BCD response")
    return text


def decode(definition: MenuDefinition, text: str) -> MenuValue:
    kind = definition.kind
    value: MenuValue
    if kind == MenuKind.BOOLEAN:
        value = parse_bool(text)
    elif kind == MenuKind.INTEGER:
        if re.fullmatch(r"[+-]?\d+", text) is None:
            raise ValueError("Expected integer response")
        value = int(text)
    elif kind == MenuKind.AUDIO_FILTER:
        _decimal_hex(text, 4)
        value = AudioFilter(int(text[:2]), int(text[2:]))
    elif kind == MenuKind.BANDWIDTH:
        if re.fullmatch(r"[0-9A-Fa-f]{2}", text) is None:
            raise ValueError("Expected one bandwidth byte")
        value = Bandwidth(int(text[0], 16), int(text[1], 16))
    elif kind == MenuKind.RGB:
        _decimal_hex(text, 12)
        value = RgbColor(*(int(text[i : i + 4]) for i in (0, 4, 8)))
    elif kind == MenuKind.SCOPE_EDGES:
        if re.fullmatch(r"[0-9]{12}", text) is None:
            raise ValueError("Expected two three-byte BCD edges")
        value = ScopeEdges(
            *(
                int(bytes.fromhex(text[i : i + 6])[::-1].hex()) * 100
                for i in (0, 6)
            )
        )
    elif kind == MenuKind.TEXT:
        if not text.startswith('"') or not text.endswith('"'):
            raise ValueError("Expected quoted opening text")
        fields = next(csv.reader([text], strict=True))
        if len(fields) != 1:
            raise ValueError("Expected one text value")
        value = fields[0]
    elif kind == MenuKind.DATE:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) is None:
            raise ValueError("Expected YYYY-MM-DD")
        value = dt.date.fromisoformat(text)
    elif kind == MenuKind.TIME:
        if re.fullmatch(r"\d{2}:\d{2}", text) is None:
            raise ValueError("Expected HH:MM")
        value = dt.time.fromisoformat(text)
    else:
        if re.fullmatch(r"[+-]\d{2}:\d{2}", text) is None:
            raise ValueError("Expected signed HH:MM offset")
        minutes = int(text[1:3]) * 60 + integer(int(text[4:]), 0, 59)
        value = dt.timedelta(minutes=minutes * (-1 if text[0] == "-" else 1))
    encode(
        definition, value
    )  # Apply the same semantic range checks to replies.
    return value


class MenuItem(Generic[T]):
    def __init__(self, driver: CiviIc7300, definition: MenuDefinition) -> None:
        self._driver, self._definition = driver, definition

    @property
    def definition(self) -> MenuDefinition:
        return self._definition

    @property
    def name(self) -> str:
        return f"{self._definition.number:04d}"

    @property
    def value(self) -> T:
        reply = self._driver._operation(self._definition.header + "?", True)
        try:
            return cast(T, decode(self._definition, reply))
        except (ValueError, TypeError, csv.Error, StopIteration) as exc:
            raise ProtocolError(
                f"Invalid menu {self.name} response: {reply[:100]!r}"
            ) from exc

    @value.setter
    def value(self, value: T) -> None:
        if not self._definition.writable:
            raise AttributeError(f"Menu {self.name} is read-only")
        text = encode(self._definition, cast(MenuValue, value))
        self._driver._write_operation(self._definition.header + " " + text)

    def write_and_read(self, value: T) -> T:
        """Write then return actual readback; error checks follow the
        status option.
        """
        with self._driver._lock:
            self.value = value
            return self.value


class MenuCollection:
    def __init__(self, driver: CiviIc7300) -> None:
        self._driver = driver
        self._items = {
            d.number: MenuItem[MenuValue](driver, d) for d in definitions()
        }

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[int]:
        return iter(self._items)

    def __getitem__(self, key: MenuKey) -> MenuItem[MenuValue]:
        if type(key) is int:
            number = key
        elif isinstance(key, str) and re.fullmatch(r"[0-9]{1,4}", key):
            number = int(key)
        else:
            raise TypeError("Use a menu number or up to four ASCII digits")
        return self._items[number]

    def _for_kind(self, key: MenuKey, kind: MenuKind) -> MenuItem[MenuValue]:
        item = self[key]
        if item.definition.kind != kind:
            raise TypeError(
                f"Menu {item.name} is {item.definition.kind}, not {kind}"
            )
        return item

    def boolean_item(self, key: MenuKey) -> MenuItem[bool]:
        return cast(MenuItem[bool], self._for_kind(key, MenuKind.BOOLEAN))

    def integer_item(self, key: MenuKey) -> MenuItem[int]:
        return cast(MenuItem[int], self._for_kind(key, MenuKind.INTEGER))

    def audio_filter_item(self, key: MenuKey) -> MenuItem[AudioFilter]:
        return cast(
            MenuItem[AudioFilter], self._for_kind(key, MenuKind.AUDIO_FILTER)
        )

    def bandwidth_item(self, key: MenuKey) -> MenuItem[Bandwidth]:
        return cast(
            MenuItem[Bandwidth], self._for_kind(key, MenuKind.BANDWIDTH)
        )

    def rgb_item(self, key: MenuKey) -> MenuItem[RgbColor]:
        return cast(MenuItem[RgbColor], self._for_kind(key, MenuKind.RGB))

    def scope_edges_item(self, key: MenuKey) -> MenuItem[ScopeEdges]:
        return cast(
            MenuItem[ScopeEdges], self._for_kind(key, MenuKind.SCOPE_EDGES)
        )

    def text_item(self, key: MenuKey) -> MenuItem[str]:
        return cast(MenuItem[str], self._for_kind(key, MenuKind.TEXT))

    def date_item(self, key: MenuKey) -> MenuItem[dt.date]:
        return cast(MenuItem[dt.date], self._for_kind(key, MenuKind.DATE))

    def time_item(self, key: MenuKey) -> MenuItem[dt.time]:
        return cast(MenuItem[dt.time], self._for_kind(key, MenuKind.TIME))

    def utc_offset_item(self, key: MenuKey) -> MenuItem[dt.timedelta]:
        return cast(
            MenuItem[dt.timedelta], self._for_kind(key, MenuKind.UTC_OFFSET)
        )

    def set_simulated_write_permissions(
        self,
        *,
        menu: bool = False,
        link: bool = False,
        calibration: bool = False,
    ) -> None:
        for value in (menu, link, calibration):
            boolean(value)
        with self._driver._lock:
            self._driver._ensure_open()
            if self._driver._simulation is None:
                raise RuntimeError(
                    "Simulation only; configure actual "
                    "permissions on the CIVI gateway"
                )
            self._driver._simulation.menus.permissions = {
                "menu": menu,
                "link": link,
                "calibration": calibration,
            }


class MenuSimulationError(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code, self.message = code, message
        super().__init__(message)


class MenuSimulation:
    def __init__(self) -> None:
        self.definitions = {d.header: d for d in definitions()}
        self.values = {d.number: d.sample_response for d in definitions()}
        self.permissions = {"menu": False, "link": False, "calibration": False}

    def command(
        self,
        header: str,
        query: bool,
        argument: str,
        operating_values: dict[str, str],
    ) -> str | None:
        if header not in self.definitions:
            raise MenuSimulationError(-113, "Undefined menu header")
        definition = self.definitions[header]
        if query:
            if argument:
                raise MenuSimulationError(-108, "Parameter not allowed")
            return (
                operating_values["RAD:BACKLIGHT"]
                if definition.number == 81
                else self.values[definition.number]
            )
        if not definition.writable:
            raise MenuSimulationError(
                -113, "Read/write direction not supported"
            )
        # Validate before checking permissions, as in the gateway
        # parser.
        value = decode(definition, argument)
        if not self.permissions[definition.permission]:
            raise MenuSimulationError(
                -203,
                definition.permission + " writes disabled in configuration",
            )
        canonical = encode(definition, value)
        if definition.kind == MenuKind.TEXT:
            canonical = encode(definition, cast(str, value).rstrip())
        self.values[definition.number] = canonical
        if definition.number == 81:
            operating_values["RAD:BACKLIGHT"] = canonical
        return None
