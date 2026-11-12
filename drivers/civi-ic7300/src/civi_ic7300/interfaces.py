"""Abstract utility and direct-I/O contracts for the IVI-Python API
design.

These interfaces describe the client contract; they do not assert
conformance or registration. Optional compatibility aliases are
implemented by Utility.
"""

from abc import ABC, abstractmethod

from .errors import ErrorQueryResult


class IviUtility(ABC):
    @property
    @abstractmethod
    def driver_version(self) -> str: ...

    @property
    @abstractmethod
    def driver_vendor(self) -> str: ...

    @property
    @abstractmethod
    def instrument_manufacturer(self) -> str: ...

    @property
    @abstractmethod
    def instrument_model(self) -> str: ...

    @property
    @abstractmethod
    def query_instrument_status_enabled(self) -> bool: ...

    @query_instrument_status_enabled.setter
    @abstractmethod
    def query_instrument_status_enabled(self, enabled: bool) -> None: ...

    @property
    @abstractmethod
    def simulation_enabled(self) -> bool: ...

    @property
    @abstractmethod
    def supported_instrument_models(self) -> tuple[str, ...]: ...

    @abstractmethod
    def error_query(self) -> ErrorQueryResult | None: ...

    @abstractmethod
    def error_query_all(self) -> tuple[ErrorQueryResult, ...]: ...

    @abstractmethod
    def raise_on_device_error(self) -> None: ...

    @abstractmethod
    def reset(self) -> None: ...


class IviDirectIo(ABC):
    @property
    @abstractmethod
    def io_timeout_ms(self) -> int: ...

    @io_timeout_ms.setter
    @abstractmethod
    def io_timeout_ms(self, timeout_ms: int) -> None: ...

    @abstractmethod
    def read_bytes(self) -> bytes: ...

    @abstractmethod
    def read_string(self) -> str: ...

    @abstractmethod
    def write_bytes(self, data: bytes) -> None: ...

    @abstractmethod
    def write_string(self, data: str) -> None: ...
