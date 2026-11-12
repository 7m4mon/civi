"""Validated transmit-band records and the gateway's existing
calibration gate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .controls import Control, boolean, integer
from .errors import ProtocolError


@dataclass(frozen=True)
class BandEdges:
    """Two whole-Hz boundaries, 0..74800000, including literal CI-V 2D
    separator.
    """

    lower_hz: int
    upper_hz: int

    def __post_init__(self) -> None:
        integer(self.lower_hz, 0, 74800000)
        integer(self.upper_hz, self.lower_hz, 74800000)

    def to_hex(self) -> str:
        def bcd(hz: int) -> str:
            return bytes.fromhex(f"{hz:010d}")[::-1].hex().upper()

        return bcd(self.lower_hz) + "2D" + bcd(self.upper_hz)

    @classmethod
    def from_hex(cls, text: str) -> BandEdges:
        if (
            not isinstance(text, str)
            or re.fullmatch(r"[0-9A-Fa-f]{10}2[Dd][0-9A-Fa-f]{10}", text)
            is None
        ):
            raise ValueError("Expected 11 band-edge bytes with 2D separator")
        digits = [
            bytes.fromhex(part)[::-1].hex() for part in (text[:10], text[12:])
        ]
        if any(not part.isdecimal() for part in digits):
            raise ValueError("Invalid band-edge BCD")
        return cls(int(digits[0]), int(digits[1]))


class Bands(Control):
    @property
    def default_edges(self) -> BandEdges:
        return self._get("RAD:BAND:EDGES", BandEdges.from_hex)

    @staticmethod
    def _count(text: str) -> int:
        if re.fullmatch(r"[0-9]+", text) is None:
            raise ValueError("Expected a band count")
        return integer(int(text), 0, 30)

    @property
    def factory_count(self) -> int:
        return self._get("RAD:TXBAND:COUNT", self._count)

    @property
    def user_count(self) -> int:
        return self._get("RAD:TXBAND:USERCOUNT", self._count)

    def _read_index(self, header: str, index: int) -> BandEdges | None:
        index = integer(index, 1, 30)
        text = self._driver._operation(f"{header}? {index}", True)
        if header == "RAD:TXBAND:USER" and text == "FF":
            return None
        try:
            return BandEdges.from_hex(text)
        except (ValueError, TypeError) as exc:
            raise ProtocolError("Invalid indexed band-edge response") from exc

    def read_factory(self, index: int) -> BandEdges:
        value = self._read_index("RAD:TXBAND:READ", index)
        assert value is not None
        return value

    def read_user(self, index: int) -> BandEdges | None:
        """Read a user slot; None means the radio reports unprogrammed FF."""
        return self._read_index("RAD:TXBAND:USER", index)

    def write_user(self, index: int, edges: BandEdges) -> None:
        integer(index, 1, 30)
        if not isinstance(edges, BandEdges):
            raise TypeError("Use BandEdges")
        self._driver._write_operation(
            f"RAD:TXBAND:USER {index},{edges.to_hex()}"
        )

    def write_and_read_user(self, index: int, edges: BandEdges) -> BandEdges | None:
        with self._driver._lock:
            self.write_user(index, edges)
            return self.read_user(index)

    def set_simulated_calibration_permission(self, enabled: bool) -> None:
        """Shared with menu calibration writes. Never changes a real
        gateway.
        """
        boolean(enabled)
        with self._driver._lock:
            self._driver._ensure_open()
            if self._driver._simulation is None:
                raise RuntimeError(
                    "Simulation only; configure calibration "
                    "permission on the CIVI gateway"
                )
            self._driver._simulation.menus.permissions["calibration"] = enabled


class BandSimulation:
    """Canned baseline matching the gateway mock, not a radio-region
    band plan.
    """

    def __init__(self) -> None:
        self.users: dict[int, BandEdges | None] = {}
        self.default = BandEdges(7100000, 7200000)

    def command(
        self, header: str, query: bool, argument: str, calibration: bool
    ) -> str | None:
        if header in (
            "RAD:BAND:EDGES",
            "RAD:TXBAND:COUNT",
            "RAD:TXBAND:USERCOUNT",
        ):
            if not query or argument:
                raise ValueError("Read-only band query takes no arguments")
            return self.default.to_hex() if header == "RAD:BAND:EDGES" else "0"
        fields = argument.split(",")
        if len(fields) != (1 if query else 2):
            raise ValueError("Expected index and optional band edges")
        index = integer(int(fields[0]), 1, 30)
        if query:
            value = (
                self.users.get(index, self.default)
                if header == "RAD:TXBAND:USER"
                else self.default
            )
            return "FF" if value is None else value.to_hex()
        if header != "RAD:TXBAND:USER":
            raise ValueError("Factory band is read only")
        value = BandEdges.from_hex(fields[1])
        if not calibration:
            # The caller maps this to the same -203 code as menu
            # permissions.
            raise PermissionError(
                "calibration writes disabled in configuration"
            )
        self.users[index] = value
        return None
