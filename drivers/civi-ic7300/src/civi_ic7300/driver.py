"""CIVI TCP SOCKET client. Copyright 2026 7M4MON.

This is an implementation toward IVI Driver Core/Python 1.0, not a
registered IVI driver. See COMPLIANCE.md for missing requirements.
"""

from __future__ import annotations

import csv
import re
import socket
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, Self, TypedDict, cast

from .controls import (
    Gains,
    Meters,
    ReceiverSettings,
    Scope,
    VfoCollection,
    frequency,
    mode_name,
)
from .errors import (
    DeviceError as DeviceError,
    ErrorQueryResult as ErrorQueryResult,
    ProtocolError as ProtocolError,
    QueryError,
)
from .interfaces import IviDirectIo, IviUtility
from .menus import MenuCollection
from .storage import BandStackCollection, KeyerCollection, MemoryCollection
from .simulation import Simulation
from .scan import ScanControl
from .bands import Bands
from .operations import RadioOperations


def _address(resource_name: str) -> tuple[str, int]:
    """Resolve a VISA location to CIVI's raw TCP transport.

    Board and INSTR/HiSLIP fields do not select another transport.
    Credential references are discarded. SOCKET keeps its explicit port.
    """
    error = "Invalid TCPIP VISA resource name"
    if not isinstance(resource_name, str):
        raise TypeError(error)
    if any(ord(c) < 33 or ord(c) > 126 for c in resource_name):
        raise ValueError(error)
    parts = resource_name.split("::")
    if not 2 <= len(parts) <= 4 or not re.fullmatch(
        r"TCPIP[0-9]*", parts[0], re.I
    ):
        raise ValueError(error)
    host = parts[1]
    credential = "@" in host
    if credential:
        token, host = host.rsplit("@", 1)
        if not token or token in ("#", "$"):
            raise ValueError(error)
    if not host or any(c in host for c in ":@/\\?#,$"):
        raise ValueError(error)
    if len(parts) == 4 and parts[-1].upper() == "SOCKET":
        if credential or not re.fullmatch(r"[0-9]+", parts[2]):
            raise ValueError(error)
        port = int(parts[2])
        if not 1 <= port <= 65535:
            raise ValueError(error)
        return host, port
    tail = parts[2:]
    if tail and tail[-1].upper() == "INSTR":
        tail = tail[:-1]
    if len(tail) > 1 or any(not item for item in tail):
        raise ValueError(error)
    device = tail[0] if tail else ""
    if device.upper() in ("INSTR", "SOCKET"):
        raise ValueError(error)
    if credential and not device.lower().startswith("hislip"):
        raise ValueError(error)
    if device.lower().startswith("hislip") and "," in device:
        match = re.fullmatch(r"hislip[^,]+,([0-9]+)", device, re.I)
        if match is None or not 1 <= int(match[1]) <= 65535:
            raise ValueError(error)
    return host, 5025


@dataclass(frozen=True)
class GatewayIdentification:
    """Four *IDN? fields. software_revision is CIVI's version, not radio
    firmware.
    """

    manufacturer: str
    model: str
    serial_number: str
    software_revision: str

    @classmethod
    def _decode(cls, text: str) -> GatewayIdentification:
        try:
            fields = next(csv.reader([text], strict=True))
        except (csv.Error, StopIteration) as exc:
            raise ProtocolError("Malformed gateway identification") from exc
        if len(fields) != 4 or any(
            ord(c) < 32 or ord(c) > 126 for field in fields for c in field
        ):
            raise ProtocolError(
                "Expected four printable ASCII gateway identification fields"
            )
        return cls(*fields)


class DriverOptions(TypedDict, total=False):
    """Constructor switches; omitted values default to false."""

    simulate: bool
    query_instrument_status: bool


def _options(
    options: DriverOptions | dict[str, bool] | str | None,
) -> dict[str, bool]:
    if options is None:
        return {}
    if isinstance(options, str):
        parsed: dict[str, bool] = {}
        for item in options.split(","):
            if not item.strip():
                continue
            key, sep, value = item.strip().partition("=")
            if not sep or value.strip().lower() not in (
                "true",
                "false",
                "1",
                "0",
            ):
                raise ValueError(
                    "Options use simulate=true,query_instrument_status=false"
                )
            if key.strip().lower() in parsed:
                raise ValueError("Duplicate option")
            parsed[key.strip().lower()] = value.strip().lower() in (
                "true",
                "1",
            )
    elif isinstance(options, dict):
        # TypedDict and ordinary dicts share this validated runtime
        # path.
        parsed = cast(dict[str, bool], dict(options))
    else:
        raise TypeError("options must be a dictionary, string or None")
    if any(k not in ("simulate", "query_instrument_status") for k in parsed):
        raise ValueError("Unknown driver option")
    if any(type(v) is not bool for v in parsed.values()):
        raise TypeError("Driver options must be booleans")
    return parsed


class CiviIc7300:
    """A serialized TCP session to the CIVI gateway, or an in-process
    simulation.

    resource_name: TCPIP[0]::<host>::<port>::SOCKET. id_query verifies
    CIVI's identity. reset selects the documented CIVI receive baseline.
    options accepts simulate and query_instrument_status booleans.
    timeout_ms is a positive integer.
    """

    def __init__(
        self,
        resource_name: str,
        id_query: bool = True,
        reset: bool = False,
        options: DriverOptions | dict[str, bool] | str | None = None,
        *,
        timeout_ms: int = 5000,
    ) -> None:
        host, port = _address(resource_name)
        settings = _options(options)
        if type(id_query) is not bool or type(reset) is not bool:
            raise TypeError("id_query and reset must be booleans")
        if type(timeout_ms) is not int or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive integer")
        self._lock = threading.RLock()
        self._simulate = settings.get("simulate", False)
        self._check_status = settings.get("query_instrument_status", False)
        self._timeout_ms = timeout_ms
        self._socket: socket.socket | None = None
        self._closed = False
        self._buffer = bytearray()
        self._replies: list[bytes] = []
        self._simulation = Simulation() if self._simulate else None
        self._ivi_utility = Utility(self)
        self._ivi_direct_io = DirectIo(self)
        self._radio = Radio(self)
        self._vfos = VfoCollection(self)
        self._gains = Gains(self)
        self._meters = Meters(self)
        self._scope = Scope(self)
        self._menus = MenuCollection(self)
        self._memories = MemoryCollection(self)
        self._band_stacks = BandStackCollection(self)
        self._keyers = KeyerCollection(self)
        self._scan = ScanControl(self)
        self._bands = Bands(self)
        self._operations = RadioOperations(self)
        if not self._simulate:
            self._socket = socket.create_connection(
                (host, port), timeout_ms / 1000
            )
        try:
            if id_query:
                identity = GatewayIdentification._decode(
                    self._operation("*IDN?", True)
                )
                if (identity.manufacturer, identity.model) != (
                    "CIVI Project",
                    "CIVI/IC-7300",
                ):
                    raise ProtocolError(
                        "Expected CIVI Project,CIVI/IC-7300 identity"
                    )
            if reset:
                self.ivi_utility.reset()
            elif not id_query and self._check_status:
                self.ivi_utility.raise_on_device_error()
        except BaseException:
            self.close()
            raise

    @property
    def ivi_utility(self) -> Utility:
        return self._ivi_utility

    @property
    def ivi_direct_io(self) -> DirectIo:
        return self._ivi_direct_io

    @property
    def radio(self) -> Radio:
        return self._radio

    @property
    def vfos(self) -> VfoCollection:
        return self._vfos

    @property
    def gains(self) -> Gains:
        return self._gains

    @property
    def meters(self) -> Meters:
        return self._meters

    @property
    def scope(self) -> Scope:
        return self._scope

    @property
    def menus(self) -> MenuCollection:
        return self._menus

    @property
    def memories(self) -> MemoryCollection:
        return self._memories

    @property
    def band_stacks(self) -> BandStackCollection:
        return self._band_stacks

    @property
    def keyers(self) -> KeyerCollection:
        return self._keyers

    @property
    def scan(self) -> ScanControl:
        return self._scan

    @property
    def bands(self) -> Bands:
        return self._bands

    @property
    def operations(self) -> RadioOperations:
        return self._operations

    def __enter__(self) -> Self:
        with self._lock:
            self._ensure_open()
            return self

    @contextmanager
    def checked(self) -> Iterator[Self]:
        """Temporarily enable typed status checks; serialize the entire
        block.

        No I/O occurs on entry/exit. Nested blocks and exceptions
        restore the previous setting. Raw I/O stays caller-managed.
        """
        with self._lock:
            self._ensure_open()
            previous = self._check_status
            self._check_status = True
            try:
                yield self
            finally:
                self._check_status = previous

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Close this session. A failed I/O session must be reopened
        explicitly.
        """
        with self._lock:
            self._closed = True
            if self._simulation is not None:
                self._simulation.operations.stop(self._simulation.values)
            if self._socket is not None:
                self._socket.close()
                self._socket = None
            self._buffer.clear()
            self._replies.clear()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError(
                "Session is closed; create a new driver instance"
            )

    def _send(self, data: bytes) -> None:
        self._ensure_open()
        if self._simulate:
            self._simulate_message(data)
        else:
            assert self._socket is not None
            self._socket.sendall(data)

    def _read(self) -> bytes:
        self._ensure_open()
        if self._simulate:
            if not self._replies:
                raise ProtocolError("No pending simulated response")
            return self._replies.pop(0)
        assert self._socket is not None
        while b"\n" not in self._buffer:
            chunk = self._socket.recv(4096)
            if not chunk:
                raise ConnectionError("Gateway closed the SCPI connection")
            self._buffer.extend(chunk)
            if len(self._buffer) > 1_048_576:
                raise ProtocolError("Response exceeds one MiB")
        end = self._buffer.index(b"\n") + 1
        reply = bytes(self._buffer[:end])
        del self._buffer[:end]
        return reply

    def query(self, command: str) -> str:
        """Atomically send one LF-terminated program and read one
        response line.

        Raw I/O does not run automatic status checks; callers own
        query framing.
        """
        data = _message(command.encode("ascii"))
        with self._lock:
            try:
                self._send(data)
                result = self._read().decode("ascii").rstrip("\r\n")
                if result == "ERROR":
                    if command.strip().upper() == "SYST:ERR?":
                        raise ProtocolError(
                            "Gateway could not read its error queue"
                        )
                    raise QueryError(
                        "Gateway returned ERROR; inspect "
                        "ivi_utility.error_query() for details"
                    )
                return result
            except (OSError, UnicodeError, ProtocolError):
                self.close()
                raise

    def _operation(self, command: str, query: bool) -> str:
        with self._lock:
            try:
                result = self.query(command if query else command + ";*OPC?")
            except QueryError:
                if self._check_status:
                    self.ivi_utility.raise_on_device_error()
                raise
            if self._check_status:
                self.ivi_utility.raise_on_device_error()
            if not query and result != "1":
                self.close()
                raise ProtocolError("Expected operation-complete response 1")
            return result

    def _write_operation(
        self, command: str, *, stopping: bool = False
    ) -> None:
        """Policy-aware protected write; STOP still attempts before
        reporting prior errors.
        """
        with self._lock:
            if not self._check_status:
                self._operation(command, False)
                return
            previous = self.ivi_utility.error_query_all()
            if previous and not stopping:
                raise DeviceError(previous)
            try:
                self._operation(command, False)
            except DeviceError as exc:
                raise DeviceError(previous + exc.errors) from exc
            if previous:
                raise DeviceError(previous)

    def _simulate_message(self, data: bytes) -> None:
        assert self._simulation is not None
        reply = self._simulation.process(data)
        if reply is not None:
            self._replies.append(reply)


def _message(data: bytes) -> bytes:
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    body = data[:-1] if data.endswith(b"\n") else data
    body = body[:-1] if body.endswith(b"\r") else body
    body.decode("ascii")
    if not body or any(c in body for c in (b"\r", b"\n", b"\x00")):
        raise ValueError("Send exactly one nonempty ASCII SCPI program")
    return body + b"\n"


def _frequency(value: float) -> int:
    return frequency(value)


def _mode(value: str) -> str:
    return mode_name(value)


class Radio(ReceiverSettings):
    """Selected-VFO radio controls. Meter levels are uncalibrated raw
    codes.
    """

    def __init__(self, driver: CiviIc7300) -> None:
        super().__init__(driver)

    @property
    def frequency_hz(self) -> int:
        """Read/write whole Hz, 30000..60000000; SENS:FREQ[?]."""
        return int(self._driver._operation("SENS:FREQ?", True))

    @frequency_hz.setter
    def frequency_hz(self, value: float) -> None:
        self._driver._operation(f"SENS:FREQ {_frequency(value)}", False)

    @property
    def mode(self) -> str:
        """Read/write LSB/USB/AM/CW/RTTY/FM/CW-R/RTTY-R; RAD:MODE[?]."""
        return self._driver._operation("RAD:MODE?", True)

    @mode.setter
    def mode(self, value: str) -> None:
        self._driver._operation(f"RAD:MODE {_mode(value)}", False)

    @property
    def smeter_raw(self) -> int:
        """Read-only raw 0..255, without dBm conversion; READ:SMET?."""
        return int(self._driver._operation("READ:SMET?", True))

    @property
    def firmware_revision(self) -> str:
        """Manual radio firmware metadata or Unknown; RAD:FIRM?, not
        CI-V auto-read.
        """
        return self._driver._operation("RAD:FIRM?", True)


class Utility(IviUtility):
    """Driver metadata, SCPI error queue and configuration."""

    def __init__(self, driver: CiviIc7300) -> None:
        self._driver = driver

    @property
    def driver_version(self) -> str:
        return "0.13.1"

    @property
    def driver_vendor(self) -> str:
        return "7M4MON"

    @property
    def instrument_manufacturer(self) -> str:
        return self.identification.manufacturer

    @property
    def instrument_model(self) -> str:
        return self.identification.model

    @property
    def identification(self) -> GatewayIdentification:
        return GatewayIdentification._decode(
            self._driver._operation("*IDN?", True)
        )

    def clear_status(self) -> None:
        """Clear this client's error queue with *CLS; does not recover
        CI-V quarantine.
        """
        self._driver._operation("*CLS", False)

    def wait_for_complete(self) -> None:
        """Await *OPC? = 1; result errors follow the status option."""
        if self._driver._operation("*OPC?", True) != "1":
            raise ProtocolError("Expected operation-complete response 1")

    @property
    def supported_instrument_models(self) -> tuple[str, ...]:
        return ("CIVI/IC-7300",)

    @property
    def simulation_enabled(self) -> bool:
        return self._driver._simulate

    @property
    def simulate(self) -> bool:
        return self.simulation_enabled

    @property
    def query_instrument_status_enabled(self) -> bool:
        with self._driver._lock:
            return self._driver._check_status

    @query_instrument_status_enabled.setter
    def query_instrument_status_enabled(self, enabled: bool) -> None:
        if type(enabled) is not bool:
            raise TypeError("enabled must be boolean")
        with self._driver._lock:
            self._driver._check_status = enabled

    query_instrument_status = query_instrument_status_enabled

    def error_query(self) -> ErrorQueryResult | None:
        """Pop SYST:ERR? once; return None for code zero, else
        code/message.
        """
        with self._driver._lock:
            try:
                fields = next(
                    csv.reader(
                        [self._driver.query("SYST:ERR?")],
                        skipinitialspace=True,
                        strict=True,
                    )
                )
                if (
                    len(fields) != 2
                    or re.fullmatch(r"[+-]?[0-9]+", fields[0].strip()) is None
                ):
                    raise ValueError("Expected signed code and message")
                code = int(fields[0])
            except (csv.Error, StopIteration, ValueError) as exc:
                raise ProtocolError("Malformed SCPI error response") from exc
            return ErrorQueryResult(code, fields[1]) if code else None

    def error_query_all(self) -> tuple[ErrorQueryResult, ...]:
        """Drain at most 256 errors; fail if the queue never reaches
        code zero.
        """
        with self._driver._lock:
            errors: list[ErrorQueryResult] = []
            for _ in range(256):
                error = self.error_query()
                if error is None:
                    return tuple(errors)
                errors.append(error)
            raise ProtocolError("SCPI error queue did not terminate")

    def raise_on_device_error(self) -> None:
        """Drain this session's queue and raise DeviceError when
        nonempty.
        """
        errors = self.error_query_all()
        if errors:
            raise DeviceError(errors)

    def reset(self, *, timeout_ms: int = 30000) -> None:
        """Select CIVI's verified receive baseline; requires updated
        gateway.

        No Partial/All Reset, LAN RESET or *CLS is sent. Completion
        is awaited; error checks follow
        query_instrument_status_enabled. Use checked() for explicit
        preflight/result checks. See the bundled reset documentation.
        """
        with self._driver._lock:
            previous_timeout = self._driver._timeout_ms
            self._driver.ivi_direct_io.io_timeout_ms = timeout_ms
            try:
                self._driver._write_operation("RAD:RESET")
            finally:
                self._driver._timeout_ms = previous_timeout
                if self._driver._socket is not None:
                    self._driver._socket.settimeout(previous_timeout / 1000)


class DirectIo(IviDirectIo):
    """ASCII LF-framed raw I/O; no automatic instrument-status checking.

    Use driver.query for atomic write/read. Separate write/read calls
    require caller synchronization when shared between threads.
    Binary blocks and arbitrary VISA transports are not implemented.
    """

    def __init__(self, driver: CiviIc7300) -> None:
        self._driver = driver

    @property
    def io_timeout_ms(self) -> int:
        with self._driver._lock:
            return self._driver._timeout_ms

    @io_timeout_ms.setter
    def io_timeout_ms(self, timeout_ms: int) -> None:
        if type(timeout_ms) is not int or timeout_ms <= 0:
            raise ValueError("timeout_ms must be a positive integer")
        with self._driver._lock:
            self._driver._ensure_open()
            self._driver._timeout_ms = timeout_ms
            if self._driver._socket is not None:
                self._driver._socket.settimeout(timeout_ms / 1000)

    def write_bytes(self, data: bytes) -> None:
        """Send one ASCII SCPI program, adding LF if absent."""
        payload = _message(data)
        with self._driver._lock:
            try:
                self._driver._send(payload)
            except OSError:
                self._driver.close()
                raise

    def write_string(self, data: str) -> None:
        """Encode ASCII and send; equivalent to write_bytes."""
        self.write_bytes(data.encode("ascii"))

    def read_bytes(self) -> bytes:
        """Read one complete LF-terminated response, preserving LF."""
        with self._driver._lock:
            try:
                return self._driver._read()
            except (OSError, ProtocolError):
                self._driver.close()
                raise

    def read_string(self) -> str:
        """Read one ASCII response, removing its CR/LF terminator."""
        return self.read_bytes().decode("ascii").rstrip("\r\n")
