"""Offline state model for the documented typed client API, with no
instrument I/O.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path

from .controls import (
    CONTROL_CLASSES,
    DataFilter,
    Setting,
    ScopeEdges,
    VfoMode,
    boolean,
    choice,
    frequency,
)
from .menus import MenuSimulation, MenuSimulationError
from .storage_simulation import StorageSimulation, StorageSimulationError
from .scan import ScanSimulation
from .bands import BandSimulation
from .operations import (
    OperationSimulation,
    OperationSimulationError,
    RadioOperations,
)


class Simulation:
    def __init__(self) -> None:
        self.parameters = {
            value.header: value
            for cls in (*CONTROL_CLASSES, RadioOperations)
            for value in vars(cls).values()
            if isinstance(value, Setting)
        }
        self.errors: list[tuple[int, str]] = []
        self.fixed_edges: dict[str, ScopeEdges] = {}
        self.menus = MenuSimulation()
        self.storage = StorageSimulation()
        self.bands = BandSimulation()
        self.operations = OperationSimulation()
        self.values: dict[str, str] = {}
        self.reset()

    def reset(self) -> None:
        preserved: dict[str, str] = {
            key: self.values[key]
            for key in ("RAD:TXINHIBIT", "RAD:ANTOUTPUT")
            if key in self.values
        }
        profile = json.loads(
            Path(__file__)
            .with_name("reset-profile.json")
            .read_text(encoding="utf-8")
        )
        self.values = {
            key: value.encode(value.default)
            for key, value in self.parameters.items()
        }
        self.values["RAD:ATT"] = "0"
        self.values.update(preserved)
        for item in profile["settings"]:
            self.values[item["header"]] = item["value"]
        self.vfos = [
            (v["frequency_hz"], VfoMode._decode(v["mode_data_filter"]))
            for v in profile["vfos"]
        ]
        self.selected = 0
        self.storage.exit_memory()
        self.scan = ScanSimulation()
        self.operations.stop(self.values)

    def process(self, data: bytes) -> bytes | None:
        self.operations.expire(self.values)
        replies = []
        for part in data.decode("ascii").strip().split(";"):
            header, _, argument = part.strip().lstrip(":").partition(" ")
            try:
                reply = self._command(header.upper(), argument.strip())
            except (ValueError, TypeError) as exc:
                self.errors.append((-222, str(exc)))
                reply = "ERROR" if header.endswith("?") else None
            if reply is not None:
                replies.append(reply)
        return (";".join(replies) + "\n").encode("ascii") if replies else None

    def _command(self, header: str, argument: str) -> str | None:
        query = header.endswith("?")
        base = header.removesuffix("?")
        if header == "*IDN?":
            return "CIVI Project,CIVI/IC-7300,SIMULATED,0.1.0"
        if header == "*OPC?":
            return "1"
        if header == "RAD:FIRM?":
            return "Unknown"
        if header == "*CLS":
            self.errors.clear()
            return None
        if header == "SYST:ERR?":
            code, message = (
                self.errors.pop(0) if self.errors else (0, "No error")
            )
            return f'{code},"' + message.replace('"', '""') + '"'
        if base.startswith("RAD:MENU:"):
            try:
                return self.menus.command(base, query, argument, self.values)
            except MenuSimulationError as exc:
                self.errors.append((exc.code, exc.message))
                return "ERROR" if query else None
        if base in self.operations.parameters or base in (
            "RAD:CW:SEND",
            "RAD:CW:STOP",
            "RAD:VOICE",
            "RAD:SPEECH",
            "RAD:POWER:ON",
            "RAD:POWER:OFF",
            "RAD:PTT",
        ):
            try:
                return self.operations.command(
                    base,
                    query,
                    argument,
                    self.values,
                    self.menus.permissions["link"],
                )
            except OperationSimulationError as exc:
                self.errors.append((exc.code, exc.message))
                return "ERROR" if query else None
        if base == "RAD:BAND:EDGES" or base.startswith("RAD:TXBAND:"):
            try:
                return self.bands.command(
                    base,
                    query,
                    argument,
                    self.menus.permissions["calibration"],
                )
            except PermissionError as exc:
                self.errors.append((-203, str(exc)))
                return "ERROR" if query else None
        if base == "RAD:IPPLUS:ALT":
            base = "RAD:IPPLUS"
        if base == "RAD:DATA":
            current = self.storage.current(self)
            if query:
                return (
                    bytes((int(current.data), current.filter_number))
                    .hex()
                    .upper()
                )
            value = DataFilter.from_hex(argument)
            value.to_write_hex()
            number = (
                value.filter_number if value.enabled else current.filter_number
            )
            if self.storage.memory_mode:
                self.storage.working = replace(
                    current, data=value.enabled, filter_number=number
                )
            else:
                hz, mode = self.vfos[self.selected]
                self.vfos[self.selected] = (
                    hz,
                    VfoMode(mode.mode, value.enabled, number),
                )
            return None
        if base.startswith("RAD:MEM:") or base in (
            "RAD:BAND:STACK",
            "RAD:KEYER:TEXT",
        ):
            try:
                return self.storage.command(base, query, argument, self)
            except StorageSimulationError as exc:
                self.errors.append((exc.code, exc.message))
                return "ERROR" if query else None
        if header == "RAD:RESET":
            self.reset()
            return None
        if base.startswith("RAD:SCAN:"):
            if query:
                raise ValueError("Scan actions have no query")
            self.scan.command(base.removeprefix("RAD:SCAN:"), argument)
            return None
        if header == "RAD:VFO:SELECT":
            self.selected = ("A", "B").index(choice(argument, ("A", "B")))
            self.storage.exit_memory()
            return None
        if header == "RAD:VFO:ENABLE":
            self.storage.exit_memory()
            return None
        if header == "RAD:VFO:COPY":
            self.vfos[self.selected ^ 1] = self.vfos[self.selected]
            return None
        if header == "RAD:VFO:SWAP":
            self.vfos.reverse()
            return None
        if base in ("RAD:VFO:FREQ", "RAD:VFO:MODE"):
            fields = [s.strip() for s in argument.split(",")]
            if len(fields) != (1 if query else 2):
                raise ValueError(
                    "Expected relative VFO selector and optional value"
                )
            selector = choice(fields[0], ("SELECTED", "OTHER"))
            index = self.selected ^ (selector == "OTHER")
            old_frequency, old_mode = self.vfos[index]
            if base.endswith("FREQ"):
                if query:
                    return str(old_frequency)
                self.vfos[index] = (frequency(float(fields[1])), old_mode)
            else:
                if query:
                    return old_mode._encode()
                self.vfos[index] = (old_frequency, VfoMode._decode(fields[1]))
            return None
        if base in ("SENS:FREQ", "RAD:MODE"):
            current = self.storage.current(self)
            old_frequency = current.frequency_hz
            old_mode = VfoMode(
                current.mode, current.data, current.filter_number
            )
            if base == "SENS:FREQ":
                if query:
                    return str(old_frequency)
                hz = frequency(float(argument))
                if self.storage.memory_mode:
                    self.storage.set_frequency(self, hz)
                else:
                    self.vfos[self.selected] = (hz, old_mode)
            else:
                if query:
                    return old_mode.mode
                if self.storage.memory_mode:
                    self.storage.set_mode(self, argument)
                else:
                    self.vfos[self.selected] = (
                        old_frequency,
                        VfoMode(argument, old_mode.data, 1),
                    )
            return None
        if base == "RAD:TXFREQ":
            if not query:
                raise ValueError("TX frequency is read only")
            if self.storage.memory_mode:
                record = self.storage.records.get(self.storage.channel)
                return str(
                    record.transmit.frequency_hz
                    if record and record.split_enabled
                    else self.storage.current(self).frequency_hz
                )
            index = self.selected ^ (self.values["RAD:SPLIT"] == "ON")
            return str(self.vfos[index][0])
        if header == "RAD:SCOPE:WAVE?":
            if (
                self.values["RAD:SCOPE:STREAM"] != "ON"
                or self.values["RAD:SCOPE:ENABLE"] != "ON"
            ):
                self.errors.append(
                    (
                        -230,
                        "No fresh complete scope sweep; enable stream first",
                    )
                )
                return "ERROR"
            scope_mode = int(self.values["RAD:SCOPE:MODE"])
            return json.dumps(
                {
                    "mode": scope_mode,
                    "frequency_1_hz": self.storage.current(self).frequency_hz,
                    "frequency_2_hz": self.parameters["RAD:SCOPE:SPAN"].decode(
                        self.values["RAD:SCOPE:SPAN"]
                    ),
                    "out_of_range": False,
                    "points": [40 + i % 80 for i in range(475)],
                    "timestamp": time.time(),
                },
                separators=(",", ":"),
            )
        if base == "RAD:SCOPE:FIXEDGE":
            fields = argument.split(",")
            if len(fields) != (1 if query else 2):
                raise ValueError(
                    "Expected band*100+edge selector and optional data"
                )
            edge_selector = int(fields[0])
            if (
                not 1 <= edge_selector // 100 <= 13
                or not 1 <= edge_selector % 100 <= 4
            ):
                raise ValueError("Unsupported scope band/edge")
            if query:
                return self.fixed_edges.get(
                    str(edge_selector), ScopeEdges(0, 100000)
                )._encode()
            self.fixed_edges[str(edge_selector)] = ScopeEdges._decode(
                fields[1]
            )
            return None
        if base == "RAD:ATT":
            if query:
                return self.values[base]
            if argument not in ("0", "20"):
                raise ValueError("Attenuator is 0 or 20 dB")
            self.values[base] = argument
            return None
        if base in self.parameters:
            parameter = self.parameters[base]
            if base.startswith("RAD:SCOPE:"):
                fields = argument.split(",")
                if len(fields) != (1 if query else 2) or fields[0] != "0":
                    raise ValueError("Only main scope selector 0 is supported")
                argument = fields[-1]
            if query:
                return self.values[base]
            if not parameter.writable:
                raise ValueError("Read-only command")
            self.values[base] = parameter.encode(parameter.decode(argument))
            return None
        raise NotImplementedError(f"Simulation does not implement {header}")
