"""Public client errors and SCPI error records."""

from dataclasses import dataclass


class ProtocolError(RuntimeError):
    """The gateway returned an invalid or misframed response."""


class QueryError(RuntimeError):
    """Gateway returned ERROR; its error queue is preserved for explicit
    inspection.
    """


@dataclass(frozen=True)
class ErrorQueryResult:
    """One gateway SCPI error: a signed code and English message."""

    code: int
    message: str


class DeviceError(RuntimeError):
    """Errors extracted from this client's SCPI error queue."""

    def __init__(self, errors: tuple[ErrorQueryResult, ...]) -> None:
        self.errors = errors
        super().__init__("; ".join(f'{e.code},"{e.message}"' for e in errors))
