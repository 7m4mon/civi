import json
import time
from pathlib import Path
from .errors import CiviError


def load_profile(name="ic7300"):
    if not name.replace("_", "").isalnum():
        raise ValueError("Invalid profile name")
    return json.loads((Path(__file__).parent / "profiles" / f"{name}.json").read_text())


def bcd_encode(value, count):
    if not 0 <= value < 10 ** (count * 2):
        raise ValueError("BCD out of range")
    return bytes(int(f"{value:0{count * 2}d}"[i:i+2], 16) for i in range(0, count * 2, 2))[::-1]


def bcd_decode(data, little=True):
    if any((b & 15) > 9 or (b >> 4) > 9 for b in data):
        raise CiviError(-310, "Invalid BCD response")
    return int("".join(f"{b:02x}" for b in (data[::-1] if little else data)))


class FrameParser:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, chunk):
        self.buffer.extend(chunk)
        frames = []
        while True:
            start = self.buffer.find(b"\xfe\xfe")
            if start < 0:
                self.buffer[:] = self.buffer[-1:] if self.buffer[-1:] == b"\xfe" else b""
                break
            del self.buffer[:start]
            # Additional FE preamble bytes are allowed.
            while self.buffer[:3] == b"\xfe\xfe\xfe":
                del self.buffer[0]
            end = self.buffer.find(b"\xfd", 2)
            if end < 0:
                if len(self.buffer) > 1024:
                    self.buffer.clear()
                break
            frame = bytes(self.buffer[:end + 1])
            del self.buffer[:end + 1]
            if len(frame) >= 6:
                frames.append(frame)
        return frames


class MockBackend:
    def __init__(self, profile):
        self.profile = profile
        self.state = "connected"
        self.frequency, self.mode, self.ptt = 7100000, "LSB", False
        self.failure = None

    def call(self, op, value=None):
        if self.failure:
            self.state = "disconnected"
            raise CiviError(-365, self.failure)
        self.state = "connected"
        if op == "model_id_get": return self.profile["model_id"]
        if op == "frequency_get": return self.frequency
        if op == "mode_get": return self.mode
        if op == "smeter_get": return 96
        if op == "ptt_get": return self.ptt
        if op == "frequency_set": self.frequency = value
        elif op == "mode_set": self.mode = value
        elif op == "ptt_set": self.ptt = value

    def recover(self):
        self.failure = None
        self.state = "connected"

    def close(self):
        self.state = "disconnected"


class CivBackend:
    """Only the service worker calls this synchronous serial owner.

    CI-V has no transaction IDs. After uncertain I/O, all operations except
    best-effort PTT OFF are quarantined until an operator resets the radio/link.
    """
    def __init__(self, profile, settings, factory=None):
        self.profile, self.settings = profile, settings.copy()
        self.factory, self.port = factory, None
        self.parser = FrameParser()
        self.state = "disconnected"
        self.notifications = []

    def _open(self):
        if self.port is None:
            try:
                if self.factory is None:
                    import serial
                    s = serial.Serial()
                    s.port = self.settings["port"]
                    s.baudrate = self.settings["baud"]
                    s.timeout = 0.05
                    s.write_timeout = self.settings["timeout"]
                    # Do not key USB SEND/RTS/DTR on opening the serial port.
                    s.dtr = s.rts = False
                    s.open()
                    self.port = s
                else:
                    self.port = self.factory()
                self.parser = FrameParser()
            except Exception as e:
                self.state = "disconnected"
                raise CiviError(-365, "USB serial unavailable") from e

    def _exchange(self, command, ack=False, emergency=False):
        if self.state == "quarantined" and not emergency:
            raise CiviError(-365, "Link quarantined; reset radio/link and recover explicitly")
        self._open()
        radio = self.settings["radio_address"]
        controller = self.settings["controller_address"]
        request = b"\xfe\xfe" + bytes([radio, controller]) + command + b"\xfd"
        try:
            # Flush frames received before this operation, never treat them as replies.
            self.port.reset_input_buffer()
            self.parser = FrameParser()
            if self.port.write(request) != len(request):
                raise OSError("Short serial write")
            deadline = time.monotonic() + self.settings["timeout"]
            while time.monotonic() < deadline:
                for frame in self.parser.feed(self.port.read(256)):
                    if frame == request: continue
                    dest, source, payload = frame[2], frame[3], frame[4:-1]
                    if source == radio and dest == 0 and payload[:1] in (b"\x00", b"\x01"):
                        self.notifications.append(payload.hex())
                        self.notifications[:] = self.notifications[-32:]
                        continue
                    if source != radio or dest != controller: continue
                    if payload == b"\xfa":
                        self.state = "connected" if not emergency else self.state
                        raise CiviError(-200, "Radio rejected command (NAK)")
                    if ack and payload == b"\xfb":
                        if not emergency: self.state = "connected"
                        return b""
                    if not ack and payload.startswith(command) and len(payload) > len(command):
                        if not emergency: self.state = "connected"
                        return payload[len(command):]
            raise CiviError(-365, "CI-V response timeout; link quarantined")
        except CiviError as e:
            if e.code == -365: self.state = "quarantined"
            raise
        except Exception as e:
            self.state = "quarantined"
            self._close_port()
            raise CiviError(-365, "USB I/O failed; link quarantined") from e

    def call(self, op, value=None):
        if op not in self.profile["commands"]:
            raise CiviError(-241, "Unsupported radio feature")
        cmd = bytes.fromhex(self.profile["commands"][op])
        if op == "frequency_set": cmd += bcd_encode(value, 5)
        if op == "mode_set": cmd += bytes([self.profile["modes"][value]])
        if op == "ptt_set": cmd += bytes([int(value)])
        uncertain_stop = self.state == "quarantined" and op == "ptt_set" and value is False
        data = self._exchange(cmd, ack=op.endswith("set"), emergency=op == "ptt_set" and value is False)
        if uncertain_stop:
            raise CiviError(-365, "PTT OFF attempted; quarantined ACK cannot confirm stop")
        try:
            if op == "model_id_get":
                if len(data) != 1: raise ValueError()
                return data[0]
            if op == "frequency_get":
                if len(data) != 5: raise ValueError()
                result = bcd_decode(data)
                if not any(lo <= result <= hi for lo, hi in self.profile["frequency_ranges"]): raise ValueError()
                return result
            if op == "mode_get":
                if len(data) != 2 or data[1] not in (1, 2, 3): raise ValueError()
                return next(k for k, v in self.profile["modes"].items() if v == data[0])
            if op == "smeter_get":
                if len(data) != 2: raise ValueError()
                value = bcd_decode(data, little=False)
                if not 0 <= value <= 255: raise ValueError()
                return value
            if op == "ptt_get":
                if len(data) != 1 or data[0] not in (0, 1): raise ValueError()
                return bool(data[0])
        except (ValueError, StopIteration, CiviError) as e:
            self.state = "quarantined"
            raise CiviError(-310, "Malformed or unsupported CI-V response") from e

    def _close_port(self):
        if self.port:
            try: self.port.close()
            finally: self.port = None

    def recover(self):
        self._close_port()
        self.state = "disconnected"
        self._open()
        self.call("frequency_get")

    def close(self):
        self._close_port()
        self.state = "disconnected"
