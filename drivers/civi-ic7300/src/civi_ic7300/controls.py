"""Typed receiver, VFO, gain, meter and scope interfaces (no gateway
imports).
"""

from __future__ import annotations

import json
import math
import re
from decimal import Decimal
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Generic, TypeVar, overload

from .errors import ProtocolError

if TYPE_CHECKING:
    from .driver import CiviIc7300

T = TypeVar("T")
MODE_CODES = {
    "LSB": 0,
    "USB": 1,
    "AM": 2,
    "CW": 3,
    "RTTY": 4,
    "FM": 5,
    "CW-R": 7,
    "RTTY-R": 8,
}
SPANS = (2500, 5000, 10000, 25000, 50000, 100000, 250000, 500000)


def integer(value: int, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError("Expected an integer protocol code")
    if not low <= value <= high:
        raise ValueError(f"Value must be in {low}..{high}")
    return value


def frequency(value: float) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Frequency must be numeric Hz")
    if (
        not math.isfinite(value)
        or not 30000 <= value <= 60000000
        or int(value) != value
    ):
        raise ValueError("Frequency must be whole Hz in 30000..60000000")
    return int(value)


def choice(value: str, values: tuple[str, ...]) -> str:
    if not isinstance(value, str):
        raise TypeError("Expected a string choice")
    result = value.upper()
    if result not in values:
        raise ValueError("Choose one of " + ", ".join(values))
    return result


def mode_name(value: str) -> str:
    return choice(value, tuple(MODE_CODES))


def boolean(value: bool) -> str:
    if type(value) is not bool:
        raise TypeError("Expected bool, not a numeric or textual switch")
    return "ON" if value else "OFF"


def parse_bool(text: str) -> bool:
    if text not in ("OFF", "ON"):
        raise ValueError("Expected OFF or ON")
    return text == "ON"


class Control:
    def __init__(self, driver: CiviIc7300, selector: str = "") -> None:
        self._driver = driver
        self._selector = selector

    def _get(self, header: str, decode: Callable[[str], T]) -> T:
        command = (
            header + "?" + (" " + self._selector if self._selector else "")
        )
        result = self._driver._operation(command, True)
        try:
            return decode(result)
        except (ValueError, TypeError, KeyError, OverflowError) as exc:
            raise ProtocolError(
                f"Invalid {header} response: {result[:100]!r}"
            ) from exc

    def _set(self, header: str, text: str) -> None:
        argument = self._selector + "," + text if self._selector else text
        self._driver._operation(header + " " + argument, False)


class Setting(Generic[T]):
    """A statically typed descriptor carrying its SCPI mapping and
    simulation default.
    """

    def __init__(
        self,
        header: str,
        decode: Callable[[str], T],
        encode: Callable[[T], str],
        default: T,
        description: str,
        *,
        writable: bool = True,
    ) -> None:
        self.header, self.decode, self.encode = header, decode, encode
        self.default, self.writable = default, writable
        self.__doc__ = description

    @overload
    def __get__(
        self, instance: None, owner: type | None = None
    ) -> Setting[T]: ...

    @overload
    def __get__(self, instance: Control, owner: type | None = None) -> T: ...

    def __get__(
        self, instance: Control | None, owner: type | None = None
    ) -> T | Setting[T]:
        if instance is None:
            return self
        return instance._get(self.header, self.decode)

    def __set__(self, instance: Control, value: T) -> None:
        if not self.writable:
            raise AttributeError("This instrument value is read-only")
        instance._set(self.header, self.encode(value))


def int_setting(
    header: str,
    low: int,
    high: int,
    default: int = 0,
    *,
    writable: bool = True,
) -> Setting[int]:
    def decode(text: str) -> int:
        if re.fullmatch(r"[+-]?\d+", text) is None:
            raise ValueError("Expected integer reply")
        return integer(int(text), low, high)

    return Setting(
        header,
        decode,
        lambda v: str(integer(v, low, high)),
        default,
        f"{header}[?], integer {low}..{high}.",
        writable=writable,
    )


def bool_setting(
    header: str, default: bool = False, *, writable: bool = True
) -> Setting[bool]:
    return Setting(
        header,
        parse_bool,
        boolean,
        default,
        f"{header}[?], boolean.",
        writable=writable,
    )


def choice_setting(header: str, *values: str) -> Setting[str]:
    def convert(value: str) -> str:
        return choice(value, values)

    return Setting(
        header,
        convert,
        convert,
        values[0],
        f"{header}[?], choices: " + ", ".join(values),
    )


def _tone_encode(value: float) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Tone must be numeric Hz")
    number = Decimal(str(value)) * 10
    if (
        not number.is_finite()
        or not 670 <= number <= 2541
        or number != number.to_integral_value()
    ):
        raise ValueError("Tone must be 67.0..254.1 Hz in 0.1 Hz increments")
    return f"{number / 10:.1f}"


def _tone_decode(text: str) -> float:
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", text) is None:
        raise ValueError("Expected decimal tone frequency in Hz")
    # Decimal validation avoids silently rounding malformed device
    # replies.
    number = Decimal(text) * 10
    if not 670 <= number <= 2541 or number != number.to_integral_value():
        raise ValueError("Invalid tone response")
    return float(text)


class ReceiverSettings(Control):
    """Receiver settings; protocol codes have no implied physical
    calibration.
    """

    split_enabled = bool_setting("RAD:SPLIT")
    rit_enabled = bool_setting("RAD:RIT")
    xit_enabled = bool_setting("RAD:XIT")
    rit_offset_hz = int_setting("RAD:RIT:FREQ", -9999, 9999)
    preamp = choice_setting("RAD:PREAMP", "OFF", "PRE1", "PRE2")
    agc = choice_setting("RAD:AGC", "FAST", "MID", "SLOW")
    agc_time_code = int_setting("RAD:AGC:TIME", 0, 13)
    noise_blanker_enabled = bool_setting("RAD:NB")
    noise_reduction_enabled = bool_setting("RAD:NR")
    automatic_notch_enabled = bool_setting("RAD:ANOTCH")
    manual_notch_enabled = bool_setting("RAD:NOTCH")
    twin_peak_filter_enabled = bool_setting("RAD:TPF")
    compressor_enabled = bool_setting("RAD:COMP")
    monitor_enabled = bool_setting("RAD:MONITOR")
    lock_enabled = bool_setting("RAD:LOCK")
    ip_plus_enabled = bool_setting("RAD:IPPLUS")
    ip_plus_alternate_enabled = bool_setting("RAD:IPPLUS:ALT")
    tone_enabled = bool_setting("RAD:TONE")
    tone_squelch_enabled = bool_setting("RAD:TSQL")
    repeater_tone_hz = Setting(
        "RAD:TONE:FREQ",
        _tone_decode,
        _tone_encode,
        88.5,
        "Tone frequency, 67.0..254.1 Hz in 0.1 Hz increments.",
    )
    tone_squelch_hz = Setting(
        "RAD:TSQL:FREQ",
        _tone_decode,
        _tone_encode,
        88.5,
        "Tone squelch frequency, 67.0..254.1 Hz in 0.1 Hz increments.",
    )
    tuning_step_code = int_setting("RAD:STEP", 0, 8)
    filter_shape = choice_setting("RAD:FILTER:SHAPE", "SHARP", "SOFT")
    filter_width_code = int_setting("RAD:FILTER:WIDTH", 0, 49)
    notch_width = choice_setting("RAD:NOTCH:WIDTH", "WIDE", "MID", "NARROW")
    tx_bandwidth = choice_setting("RAD:TXBANDWIDTH", "WIDE", "MID", "NARROW")
    frequency_check_enabled = bool_setting("RAD:XFC")
    transmitting = bool_setting("RAD:PTT", writable=False)
    tx_frequency_hz = int_setting(
        "RAD:TXFREQ", 30000, 60000000, 14100000, writable=False
    )

    @property
    def attenuator_db(self) -> int:
        """RAD:ATT[?], 0 or 20 dB; this is an attenuator setting, not a
        meter.
        """
        value = self._get("RAD:ATT", int)
        if value not in (0, 20):
            raise ProtocolError("Unsupported attenuator response")
        return value

    @attenuator_db.setter
    def attenuator_db(self, value: int) -> None:
        integer(value, 0, 20)
        if value not in (0, 20):
            raise ValueError("Attenuator is 0 or 20 dB")
        self._set("RAD:ATT", str(value))

    @property
    def data_filter(self) -> DataFilter:
        return self._get("RAD:DATA", DataFilter.from_hex)

    @data_filter.setter
    def data_filter(self, value: DataFilter) -> None:
        if not isinstance(value, DataFilter):
            raise TypeError("Use DataFilter")
        self._set("RAD:DATA", value.to_write_hex())


class Gains(Control):
    """Read/write raw protocol codes (0..255), not percentages or dB."""

    af_raw = int_setting("RAD:AFGAIN", 0, 255)
    rf_raw = int_setting("RAD:RFGAIN", 0, 255)
    squelch_raw = int_setting("RAD:SQL", 0, 255)
    noise_reduction_raw = int_setting("RAD:NR:LEVEL", 0, 255)
    pbt_inner_raw = int_setting("RAD:PBT:INNER", 0, 255)
    pbt_outer_raw = int_setting("RAD:PBT:OUTER", 0, 255)
    cw_pitch_raw = int_setting("RAD:CW:PITCH", 0, 255)
    rf_power_raw = int_setting("RAD:POWER", 0, 255)
    microphone_raw = int_setting("RAD:MICGAIN", 0, 255)
    cw_speed_raw = int_setting("RAD:CW:SPEED", 0, 255)
    notch_raw = int_setting("RAD:NOTCH:LEVEL", 0, 255)
    compression_raw = int_setting("RAD:COMP:LEVEL", 0, 255)
    cw_delay_raw = int_setting("RAD:CW:DELAY", 0, 255)
    noise_blanker_raw = int_setting("RAD:NB:LEVEL", 0, 255)
    monitor_raw = int_setting("RAD:MONITOR:LEVEL", 0, 255)
    vox_raw = int_setting("RAD:VOX:GAIN", 0, 255)
    anti_vox_raw = int_setting("RAD:VOX:ANTIGAIN", 0, 255)
    backlight_raw = int_setting("RAD:BACKLIGHT", 0, 255)


class Meters(Control):
    """Read-only raw uncalibrated meters, plus receiver status flags."""

    smeter_raw = int_setting("READ:SMET", 0, 255, 96, writable=False)
    power_raw = int_setting("READ:POWER", 0, 255, writable=False)
    swr_raw = int_setting("READ:SWR", 0, 255, writable=False)
    alc_raw = int_setting("READ:ALC", 0, 255, writable=False)
    compression_raw = int_setting("READ:COMP", 0, 255, writable=False)
    voltage_raw = int_setting("READ:VOLTAGE", 0, 255, writable=False)
    current_raw = int_setting("READ:CURRENT", 0, 255, writable=False)
    squelch_open = bool_setting("READ:SQL", writable=False)
    all_squelches_open = bool_setting("READ:SQL:ALL", writable=False)
    overflow = bool_setting("READ:OVF", writable=False)


@dataclass(frozen=True)
class DataFilter:
    """DATA readback may contain OFF/FIL1..3; OFF writes must use filter
    zero.
    """

    enabled: bool
    filter_number: int

    def __post_init__(self) -> None:
        boolean(self.enabled)
        integer(self.filter_number, 1 if self.enabled else 0, 3)

    def to_write_hex(self) -> str:
        if not self.enabled and self.filter_number != 0:
            raise ValueError(
                "DATA OFF writes require filter zero; use "
                "VfoMode to restore a specific OFF filter"
            )
        return bytes((int(self.enabled), self.filter_number)).hex().upper()

    @classmethod
    def from_hex(cls, text: str) -> DataFilter:
        if (
            not isinstance(text, str)
            or re.fullmatch(r"0[01]0[0-3]", text) is None
        ):
            raise ValueError("Expected two DATA/filter bytes")
        return cls(text[:2] == "01", int(text[2:]))


@dataclass(frozen=True)
class VfoMode:
    """Mode name, DATA switch and filter number 1..3; one complete 26
    command.
    """

    mode: str
    data: bool = False
    filter_number: int = 2

    def __post_init__(self) -> None:
        object.__setattr__(self, "mode", mode_name(self.mode))
        boolean(self.data)
        integer(self.filter_number, 1, 3)

    def _encode(self) -> str:
        return (
            bytes((MODE_CODES[self.mode], int(self.data), self.filter_number))
            .hex()
            .upper()
        )

    @classmethod
    def _decode(cls, text: str) -> VfoMode:
        data = bytes.fromhex(text)
        if len(data) != 3 or data[1] not in (0, 1):
            raise ValueError("Expected three mode/DATA/filter bytes")
        mode = next((k for k, v in MODE_CODES.items() if v == data[0]), None)
        if mode is None:
            raise ValueError("Unknown mode code")
        return cls(mode, bool(data[1]), data[2])


class Vfo(Control):
    @property
    def name(self) -> str:
        """Relative SELECTED/OTHER selector, not a cached absolute VFO
        identity.
        """
        return self._selector

    @property
    def frequency_hz(self) -> int:
        return self._get("RAD:VFO:FREQ", lambda s: frequency(int(s)))

    @frequency_hz.setter
    def frequency_hz(self, value: float) -> None:
        self._set("RAD:VFO:FREQ", str(frequency(value)))

    @property
    def mode(self) -> VfoMode:
        return self._get("RAD:VFO:MODE", VfoMode._decode)

    @mode.setter
    def mode(self, value: VfoMode) -> None:
        if not isinstance(value, VfoMode):
            raise TypeError("Use VfoMode(mode, data, filter_number)")
        self._set("RAD:VFO:MODE", value._encode())


class VfoCollection(Control):
    """Two relative VFO views; select A/B explicitly, never infer
    current A/B.
    """

    def __init__(self, driver: CiviIc7300) -> None:
        super().__init__(driver)
        self._items = {
            name: Vfo(driver, name) for name in ("SELECTED", "OTHER")
        }

    def __getitem__(self, name: str) -> Vfo:
        return self._items[choice(name, ("SELECTED", "OTHER"))]

    def select(self, name: str) -> None:
        self._set("RAD:VFO:SELECT", choice(name, ("A", "B")))

    def enable(self) -> None:
        self._driver._operation("RAD:VFO:ENABLE", False)

    def copy_selected_to_other(self) -> None:
        self._driver._operation("RAD:VFO:COPY", False)

    def swap(self) -> None:
        self._driver._operation("RAD:VFO:SWAP", False)


def _bcd_frequency(text: str) -> int:
    data = bytes.fromhex(text)
    digits = data[::-1].hex()
    if len(data) != 5 or not digits.isdecimal():
        raise ValueError("Expected five little-endian BCD frequency bytes")
    return int(digits)


def _span_encode(value: int) -> str:
    integer(value, min(SPANS), max(SPANS))
    if value not in SPANS:
        raise ValueError("Unsupported scope span")
    return bytes.fromhex(f"{value:010d}")[::-1].hex().upper()


def _span_decode(text: str) -> int:
    value = _bcd_frequency(text)
    _span_encode(value)
    return value


def _reference_encode(value: float) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Reference level must be numeric dB")
    if (
        not math.isfinite(value)
        or not -20 <= value <= 20
        or value * 2 != int(value * 2)
    ):
        raise ValueError("Reference level is -20..20 dB in 0.5 dB increments")
    half_steps = int(abs(value) * 2)
    return (
        f"{half_steps // 2:02d}"
        + ("50" if half_steps % 2 else "00")
        + ("01" if value < 0 else "00")
    )


def _reference_decode(text: str) -> float:
    if re.fullmatch(r"[0-9]{2}(00|50)(00|01)", text) is None:
        raise ValueError("Invalid scope reference encoding")
    value = (int(text[:2]) + (0.5 if text[2:4] == "50" else 0)) * (
        -1 if text[4:] == "01" else 1
    )
    _reference_encode(value)
    return value


@dataclass(frozen=True)
class ScopeSweep:
    """Gateway scope metadata and 475 raw levels 0..160, or empty
    out-of-range data.
    """

    mode: int
    frequency_1_hz: int
    frequency_2_hz: int
    points: tuple[int, ...]
    out_of_range: bool
    timestamp: float

    @classmethod
    def _decode(cls, text: str) -> ScopeSweep:
        data = json.loads(text)
        integer(data["mode"], 0, 3)
        for key in ("frequency_1_hz", "frequency_2_hz"):
            integer(data[key], -9999999999, 9999999999)
        boolean(data["out_of_range"])
        if not isinstance(data["points"], list):
            raise ValueError("Expected level array")
        points = tuple(integer(p, 0, 160) for p in data["points"])
        if len(points) != (0 if data["out_of_range"] else 475):
            raise ValueError("Incomplete scope sweep")
        timestamp = data["timestamp"]
        if (
            isinstance(timestamp, bool)
            or not isinstance(timestamp, (int, float))
            or not math.isfinite(timestamp)
        ):
            raise ValueError("Invalid scope timestamp")
        return cls(
            data["mode"],
            data["frequency_1_hz"],
            data["frequency_2_hz"],
            points,
            data["out_of_range"],
            float(timestamp),
        )


@dataclass(frozen=True)
class ScopeEdges:
    """Stored fixed-scope edges in whole kHz, represented in Hz."""

    lower_hz: int
    upper_hz: int

    def __post_init__(self) -> None:
        for value in (self.lower_hz, self.upper_hz):
            integer(value, 0, 74800000)
            if value % 1000:
                raise ValueError("Scope edges must be whole kHz")
        if self.lower_hz > self.upper_hz:
            raise ValueError("Lower edge exceeds upper edge")

    def _encode(self) -> str:
        return "".join(
            bytes.fromhex(f"{v:010d}")[::-1].hex().upper()
            for v in (self.lower_hz, self.upper_hz)
        )

    @classmethod
    def _decode(cls, text: str) -> ScopeEdges:
        if len(text) != 20:
            raise ValueError("Expected two five-byte frequencies")
        return cls(_bcd_frequency(text[:10]), _bcd_frequency(text[10:]))


class Scope(Control):
    enabled = bool_setting("RAD:SCOPE:ENABLE")
    streaming_enabled = bool_setting("RAD:SCOPE:STREAM")
    hold_enabled = bool_setting("RAD:SCOPE:HOLD")
    tx_display_enabled = bool_setting("RAD:SCOPE:TXDISPLAY")
    vbw_enabled = bool_setting("RAD:SCOPE:VBW")
    marker_enabled = bool_setting("RAD:SCOPE:MARKER")
    mode_code = int_setting("RAD:SCOPE:MODE", 0, 3)
    edge_number = int_setting("RAD:SCOPE:EDGE", 1, 4, 1)
    speed_code = int_setting("RAD:SCOPE:SPEED", 0, 2)
    center_mode_code = int_setting("RAD:SCOPE:CENTER", 0, 2)
    display_code = int_setting("RAD:SCOPE:DISPLAY", 0, 0)
    dual_scope_code = int_setting("RAD:SCOPE:DUAL", 0, 0)
    span_hz = Setting(
        "RAD:SCOPE:SPAN",
        _span_decode,
        _span_encode,
        25000,
        "Scope span in Hz; 2500/5000/10000/25000/50000/100000/250000/500000.",
    )
    reference_db = Setting(
        "RAD:SCOPE:REFERENCE",
        _reference_decode,
        _reference_encode,
        0.0,
        "Relative scope display reference -20..20 dB, step 0.5; not dBm.",
    )

    def __init__(self, driver: CiviIc7300) -> None:
        super().__init__(driver, "0")

    def start_stream(self) -> None:
        """Enable USB transfer then scope operation; checks follow the
        status option.

        With checks ON a failed second step attempts to restore prior
        transfer state. Calls are serialized for this driver session,
        not across separate clients.
        """
        with self._driver._lock:
            if not self._driver._check_status:
                self.streaming_enabled = True
                self.enabled = True
                return
            self._driver.ivi_utility.raise_on_device_error()
            previous = self.streaming_enabled
            self.streaming_enabled = True
            self._driver.ivi_utility.raise_on_device_error()
            try:
                self.enabled = True
                self._driver.ivi_utility.raise_on_device_error()
            except Exception as exc:
                try:
                    self.streaming_enabled = previous
                    self._driver.ivi_utility.raise_on_device_error()
                except Exception as cleanup:
                    exc.add_note(
                        "Could not restore scope transfer state: "
                        + str(cleanup)
                    )
                raise

    def stop_stream(self) -> None:
        """Disable transfer, preserving scope-display operation; check
        device errors.
        """
        with self._driver._lock:
            self.streaming_enabled = False

    def read_sweep(self) -> ScopeSweep:
        """Read the latest complete gateway sweep; does not enable
        streaming.
        """
        return Control(self._driver)._get("RAD:SCOPE:WAVE", ScopeSweep._decode)

    def read_fixed_edges(self, band: int, edge: int) -> ScopeEdges:
        selector = str(integer(band, 1, 13) * 100 + integer(edge, 1, 4))
        return Control(self._driver, selector)._get(
            "RAD:SCOPE:FIXEDGE", ScopeEdges._decode
        )

    def write_fixed_edges(
        self, band: int, edge: int, edges: ScopeEdges
    ) -> None:
        selector = str(integer(band, 1, 13) * 100 + integer(edge, 1, 4))
        if not isinstance(edges, ScopeEdges):
            raise TypeError("Use ScopeEdges(lower_hz, upper_hz)")
        Control(self._driver, selector)._set(
            "RAD:SCOPE:FIXEDGE", edges._encode()
        )


CONTROL_CLASSES = (ReceiverSettings, Gains, Meters, Scope)
