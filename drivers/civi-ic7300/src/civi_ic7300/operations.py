"""Guarded radio operations. Permission enforcement belongs to the CIVI
service.
"""

from __future__ import annotations

import csv
import math
import time

from .controls import (
    Control,
    Setting,
    boolean,
    bool_setting,
    choice_setting,
    integer,
    parse_bool,
)


def _cw_quote(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("CW text must be a string")
    allowed = (
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz/?.-,:'()=+\"@ ^"
    )
    if not 1 <= len(text) <= 30 or any(c not in allowed for c in text):
        raise ValueError(
            "CW text must contain 1..30 supported ASCII characters"
        )
    return '"' + text.replace('"', '""') + '"'


class RadioOperations(Control):
    vox_enabled = bool_setting("RAD:VOX")
    transmit_inhibited = bool_setting("RAD:TXINHIBIT")
    break_in = choice_setting("RAD:BKIN", "OFF", "SEMI", "FULL")
    antenna_output_enabled = bool_setting("RAD:ANTOUTPUT")
    tuner = choice_setting("RAD:TUNER", "OFF", "ON", "TUNE")

    def _checked(self, command: str, *, stopping: bool = False) -> None:
        self._driver._write_operation(command, stopping=stopping)

    def _set(self, header: str, text: str) -> None:
        stopping = (
            header in ("RAD:VOX", "RAD:BKIN", "RAD:TUNER") and text == "OFF"
        )
        self._checked(header + " " + text, stopping=stopping)

    def send_cw(self, text: str) -> None:
        self._checked("RAD:CW:SEND " + _cw_quote(text))

    def stop_cw(self) -> None:
        self._checked("RAD:CW:STOP", stopping=True)

    def play_voice(self, slot: int) -> None:
        self._checked("RAD:VOICE T" + str(integer(slot, 1, 8)))

    def stop_voice(self) -> None:
        self._checked("RAD:VOICE STOP", stopping=True)

    def speak(self, code: int) -> None:
        """Speech synthesizer code 0..2, as defined by the gateway/CI-V
        catalog.
        """
        self._checked("RAD:SPEECH " + str(integer(code, 0, 2)))

    def power_on(self) -> None:
        self._checked("RAD:POWER:ON")

    def power_off(self) -> None:
        self._checked("RAD:POWER:OFF")

    def start_transmit(self) -> None:
        """Request PTT ON; gateway transmit permission, ownership and
        deadline apply.
        """
        self._checked("RAD:PTT ON")

    def stop_transmit(self) -> None:
        """PTT OFF attempts to stop all CIVI-owned transmit paths."""
        self._checked("RAD:PTT OFF", stopping=True)

    def set_simulated_permissions(
        self,
        *,
        transmit: bool = False,
        power: bool = False,
        link: bool = False,
        max_transmit_seconds: float = 10.0,
    ) -> None:
        for value in (transmit, power, link):
            boolean(value)
        if isinstance(max_transmit_seconds, bool) or not isinstance(
            max_transmit_seconds, (int, float)
        ):
            raise TypeError("Maximum transmit time must be numeric seconds")
        if (
            not math.isfinite(max_transmit_seconds)
            or max_transmit_seconds <= 0
        ):
            raise ValueError(
                "Maximum transmit time must be finite and positive"
            )
        with self._driver._lock:
            self._driver._ensure_open()
            if self._driver._simulation is None:
                raise RuntimeError(
                    "Simulation only; configure "
                    "permissions on the CIVI gateway"
                )
            state = self._driver._simulation.operations
            state.transmit, state.power = transmit, power
            self._driver._simulation.menus.permissions["link"] = link
            state.max_seconds = float(max_transmit_seconds)


class OperationSimulationError(Exception):
    def __init__(self, code: int, message: str) -> None:
        self.code, self.message = code, message
        super().__init__(message)


class OperationSimulation:
    """Logical owned paths only, without RF, audio, USB wake or
    background tasks.
    """

    def __init__(self) -> None:
        self.transmit = self.power = False
        self.max_seconds = 10.0
        self.started: float | None = None
        self.actions: set[str] = set()
        self.cw_text = ""
        self.voice_slot = 0
        self.speech_code: int | None = None
        self.powered_on = True
        self._clock = time.monotonic
        self.parameters = {
            v.header: v
            for v in vars(RadioOperations).values()
            if isinstance(v, Setting)
        }

    def stop(self, values: dict[str, str]) -> None:
        values["RAD:PTT"] = "OFF"
        for action, header in [
            ("vox", "RAD:VOX"),
            ("bkin", "RAD:BKIN"),
            ("tuner", "RAD:TUNER"),
        ]:
            if action in self.actions:
                values[header] = "OFF"
        self.actions.clear()
        self.started = None
        self.cw_text = ""
        self.voice_slot = 0

    def expire(self, values: dict[str, str]) -> None:
        if (
            self.started is not None
            and self._clock() - self.started >= self.max_seconds
        ):
            self.stop(values)

    def command(
        self,
        header: str,
        query: bool,
        argument: str,
        values: dict[str, str],
        link: bool,
    ) -> str | None:
        parameter = self.parameters.get(header)
        if query:
            if header == "RAD:PTT" and not argument:
                return values["RAD:PTT"]
            if parameter is None:
                raise OperationSimulationError(-113, "Action has no query")
            if argument:
                raise ValueError("Parameter not allowed")
            return values[header]
        canonical = argument
        if parameter is not None:
            canonical = parameter.encode(parameter.decode(argument))
        elif header == "RAD:PTT":
            canonical = boolean(parse_bool(argument))
        cw_text = ""
        if header == "RAD:CW:SEND":
            try:
                fields = next(csv.reader([argument], strict=True))
            except (csv.Error, StopIteration) as exc:
                raise ValueError("Expected one CW string") from exc
            if len(fields) != 1:
                raise ValueError("Expected one CW string")
            cw_text = fields[0]
            _cw_quote(cw_text)
        if header == "RAD:VOICE" and argument not in (
            "STOP",
            *(f"T{n}" for n in range(1, 9)),
        ):
            raise ValueError("Use STOP or T1..T8")
        if header == "RAD:CW:STOP" and argument:
            raise ValueError("CW stop takes no argument")
        action = {
            "RAD:VOX": "vox",
            "RAD:BKIN": "bkin",
            "RAD:TUNER": "tuner",
            "RAD:CW:SEND": "cw",
            "RAD:CW:STOP": "cw",
            "RAD:VOICE": "voice",
            "RAD:PTT": "ptt",
        }.get(header)
        enabled = canonical not in ("OFF", "STOP") and header != "RAD:CW:STOP"
        if header == "RAD:ANTOUTPUT" and not link:
            raise OperationSimulationError(
                -203, "link writes disabled in configuration"
            )
        if header.startswith("RAD:POWER:"):
            if argument:
                raise ValueError("Power action takes no argument")
            if not self.power:
                raise OperationSimulationError(
                    -203, "power writes disabled in configuration"
                )
            if self.actions:
                raise OperationSimulationError(
                    -200, "Stop CIVI transmit operations before changing power"
                )
            self.powered_on = header.endswith(":ON")
            return None
        if action and enabled:
            if not self.transmit:
                raise OperationSimulationError(
                    -203, "Transmit control disabled"
                )
            if self.started is None:
                self.started = self._clock()
            self.actions.add(action)
        if header == "RAD:PTT":
            if enabled:
                values[header] = "ON"
            else:
                self.stop(values)
        elif header == "RAD:CW:SEND":
            self.cw_text = cw_text
        elif header == "RAD:CW:STOP":
            if argument:
                raise ValueError("CW stop takes no argument")
            self.cw_text = ""
        elif header == "RAD:VOICE":
            if argument == "STOP":
                self.voice_slot = 0
            elif argument in tuple("T" + str(n) for n in range(1, 9)):
                self.voice_slot = int(argument[1:])
            else:
                raise ValueError("Use STOP or T1..T8")
        elif header == "RAD:SPEECH":
            self.speech_code = integer(int(argument), 0, 2)
        elif parameter is not None:
            values[header] = canonical
        else:
            raise NotImplementedError(header)
        if action and not enabled:
            self.actions.discard(action)
            if not self.actions:
                self.stop(values)
        return None
