"""Write-only receiver scan commands; no invented status queries."""

from __future__ import annotations

from .controls import Control, boolean, choice, integer

SCAN_MODES = (
    "PROGRAM",
    "MEMORY",
    "AUTO",
    "DELTA",
    "FINEPROGRAM",
    "FINEDELTA",
    "SELECTMEM",
)
SCAN_SPANS = {
    5000: "SPAN5K",
    10000: "SPAN10K",
    20000: "SPAN20K",
    50000: "SPAN50K",
    100000: "SPAN100K",
    500000: "SPAN500K",
    1000000: "SPAN1M",
}


class ScanControl(Control):
    """Commands affect the radio's current VFO/memory context, shared by
    all clients.

    Completion means command acceptance, not that scanning has finished.
    There is no scan status query, span query or automatic restoration
    API.
    """

    def _run(self, suffix: str, argument: str = "") -> None:
        self._driver._write_operation(
            "RAD:SCAN:" + suffix + (" " + argument if argument else "")
        )

    def start(self, mode: str) -> None:
        """PROGRAM/MEMORY/AUTO/DELTA/FINEPROGRAM/FINEDELTA/SELECTMEM."""
        self._run(choice(mode, SCAN_MODES))

    def stop(self) -> None:
        self._run("STOP")

    def set_delta_span_hz(self, span_hz: int) -> None:
        """Set delta-scan half-span in Hz: center minus/plus span_hz.

        This controls scan range, not the receive filter bandwidth.
        """
        integer(span_hz, 5000, 1000000)
        if span_hz not in SCAN_SPANS:
            raise ValueError(
                "Scan span must be "
                "5000/10000/20000/50000/100000/500000/1000000 Hz"
            )
        self._run(SCAN_SPANS[span_hz])

    def set_select_enabled(self, enabled: bool) -> None:
        self._run("SELECT" + boolean(enabled))

    def set_resume_enabled(self, enabled: bool) -> None:
        self._run("RESUME" + boolean(enabled))

    def assign_selected_memory_group(self, group: int) -> None:
        """Assign select group 1..3 to the radio's current memory; no
        memory-write gate.
        """
        self._run("SELECT", str(integer(group, 1, 3)))

    def set_memory_group(self, group: int) -> None:
        """Select scan group 0..3; interpretation follows the
        gateway/CI-V codes.
        """
        self._run("GROUP", str(integer(group, 0, 3)))


class ScanSimulation:
    """Logical command state only: no sweep motion, clock, signal or RF
    model.
    """

    def __init__(self) -> None:
        self.mode: str | None = None
        self.span_hz = 5000
        self.select_enabled = False
        self.resume_enabled = False
        self.memory_group = 0
        self.last_assigned_group: int | None = None

    def command(self, suffix: str, argument: str) -> None:
        if suffix in ("SELECT", "GROUP"):
            integer(int(argument), 1 if suffix == "SELECT" else 0, 3)
            if suffix == "GROUP":
                self.memory_group = int(argument)
            else:
                self.last_assigned_group = int(argument)
            return
        if argument:
            raise ValueError("Scan action takes no arguments")
        if suffix == "STOP":
            self.mode = None
        elif suffix in SCAN_MODES:
            self.mode = suffix
        elif suffix in SCAN_SPANS.values():
            self.span_hz = next(
                k for k, v in SCAN_SPANS.items() if v == suffix
            )
        elif suffix in ("SELECTOFF", "SELECTON"):
            self.select_enabled = suffix.endswith("ON")
        elif suffix in ("RESUMEOFF", "RESUMEON"):
            self.resume_enabled = suffix.endswith("ON")
        else:
            raise NotImplementedError("Unknown scan action " + suffix)
