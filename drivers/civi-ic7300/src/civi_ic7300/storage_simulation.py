"""Offline stored-data model. No RF, serial, clock or filesystem side
effects.
"""

from __future__ import annotations

import csv
from dataclasses import replace
from typing import Protocol

from .controls import VfoMode, integer
from .storage import MemoryRecord, MemorySettings, _keyer_text


class RadioState(Protocol):
    vfos: list[tuple[int, VfoMode]]
    selected: int
    values: dict[str, str]


class StorageSimulationError(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code, self.message = code, message
        super().__init__(message)


class StorageSimulation:
    def __init__(self) -> None:
        self.write_enabled = False
        self.records: dict[int, MemoryRecord] = {}
        self.stacks: dict[tuple[int, int], MemorySettings] = {}
        self.keyers = {number: "CQ" for number in range(1, 9)}
        self.channel = 1
        self.memory_mode = False
        self.working: MemorySettings | None = None

    def current(self, state: RadioState) -> MemorySettings:
        if self.memory_mode and self.working is not None:
            return self.working
        hz, mode = state.vfos[state.selected]
        return MemorySettings(hz, mode.mode, mode.filter_number, mode.data)

    def exit_memory(self) -> None:
        self.memory_mode = False
        self.working = None

    def _load(self, state: RadioState) -> None:
        previous = self.current(state)
        record = self.records.get(self.channel)
        self.working = record.receive if record else previous
        self.memory_mode = True

    def _guard(self) -> None:
        if not self.write_enabled:
            raise StorageSimulationError(
                -203, "memory writes disabled in configuration"
            )

    @staticmethod
    def _profile(settings: MemorySettings) -> None:
        if settings.frequency_hz > 60000000:
            raise StorageSimulationError(
                -222, "Stored frequency outside selected profile range"
            )

    def command(
        self, header: str, query: bool, argument: str, state: RadioState
    ) -> str | None:
        fields = (
            next(csv.reader([argument], skipinitialspace=True, strict=True))
            if argument
            else []
        )
        if header in ("RAD:MEM:CONTENT", "RAD:BAND:STACK", "RAD:KEYER:TEXT"):
            if len(fields) != (1 if query else 2):
                raise ValueError("Expected selector and optional stored value")
            selector = int(fields[0])
            if header == "RAD:MEM:CONTENT":
                integer(selector, 1, 101)
                if query:
                    return (
                        self.records[selector].to_hex()
                        if selector in self.records
                        else "FF"
                    )
                if fields[1].upper() == "FF":
                    integer(selector, 1, 99)
                    self._guard()
                    self.records.pop(selector, None)
                    return None
                record = MemoryRecord.from_hex(fields[1])
                if selector >= 100 and (
                    record.split_enabled or record.select_group
                ):
                    raise ValueError("P1/P2 require zero Split/select flags")
                self._profile(record.receive)
                self._profile(record.transmit)
                self._guard()
                self.records[selector] = record
                if self.memory_mode and self.channel == selector:
                    self.working = record.receive
                return None
            if header == "RAD:BAND:STACK":
                band, slot = (
                    integer(selector // 100, 1, 11),
                    integer(selector % 100, 1, 3),
                )
                if query:
                    return self.stacks.get(
                        (band, slot), MemorySettings(7100000, "USB")
                    ).to_hex()
                settings = MemorySettings.from_hex(fields[1])
                self._profile(settings)
                self._guard()
                self.stacks[band, slot] = settings
                return None
            integer(selector, 1, 8)
            if query:
                return _keyer_text(self.keyers[selector])
            _keyer_text(fields[1])
            self._guard()
            self.keyers[selector] = fields[1].rstrip()
            return None

        if query:
            raise StorageSimulationError(-113, "Action has no query")
        if header == "RAD:MEM:SELECT":
            if len(fields) != 1:
                raise ValueError("Expected one channel number")
            self.channel = integer(int(fields[0]), 1, 101)
            if self.memory_mode:
                self._load(state)
        else:
            if fields:
                raise ValueError("Action takes no arguments")
            if header == "RAD:MEM:ENABLE":
                self._load(state)
            elif header == "RAD:MEM:WRITE":
                self._guard()
                self.records[self.channel] = MemoryRecord.simple(
                    self.current(state)
                )
            elif header == "RAD:MEM:CLEAR":
                self._guard()
                if not self.memory_mode:
                    raise StorageSimulationError(
                        -200, "Memory clear requires memory mode"
                    )
                self.records.pop(self.channel, None)
            elif header == "RAD:MEM:TOVFO":
                selected_record = self.records.get(self.channel)
                if selected_record:
                    r = selected_record.receive
                    state.vfos[state.selected] = (
                        r.frequency_hz,
                        VfoMode(r.mode, r.data, r.filter_number),
                    )
            else:
                raise NotImplementedError(header)
        return None

    def set_frequency(self, state: RadioState, hz: int) -> None:
        self.working = replace(self.current(state), frequency_hz=hz)

    def set_mode(self, state: RadioState, mode: str) -> None:
        self.working = replace(self.current(state), mode=mode, filter_number=1)
