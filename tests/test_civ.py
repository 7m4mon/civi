import time
import pytest
from civi.backend import FrameParser, CivBackend, bcd_encode, bcd_decode, load_profile
from civi.errors import CiviError


def frame(payload, dest=0xe0, source=0x94):
    return b"\xfe\xfe" + bytes([dest, source]) + payload + b"\xfd"


class FakeSerial:
    def __init__(self, replies):
        self.replies = list(replies)
        self.chunks = []
        self.writes = []
        self.closed = False

    def reset_input_buffer(self): self.chunks = []
    def write(self, data):
        self.writes.append(data)
        self.chunks = self.replies.pop(0) if self.replies else []
        return len(data)
    def read(self, count):
        if self.chunks: return self.chunks.pop(0)
        time.sleep(0.001)
        return b""
    def close(self): self.closed = True


def backend(config, replies):
    port = FakeSerial(replies)
    config["serial"]["timeout"] = 0.02
    return CivBackend(load_profile(), config["serial"], lambda: port), port


def test_parser_split_concatenated_noise_and_preamble():
    p = FrameParser()
    a = frame(b"\x03" + bcd_encode(7100000,5))
    assert p.feed(b"noise\xfe") == []
    assert p.feed(b"\xfe" + a) == [a]
    assert p.feed(a[:4]) == []
    assert p.feed(a[4:] + frame(b"\xfb")) == [a, frame(b"\xfb")]


def test_frequency_echo_notifications_and_address_match(config):
    request = frame(b"\x03", 0x94, 0xe0)
    valid = frame(b"\x03" + bcd_encode(7100000, 5))
    wrong = frame(b"\x03" + bcd_encode(7200000, 5), source=0x95)
    notify = frame(b"\x00" + bcd_encode(7000000, 5), dest=0)
    b, p = backend(config, [[request+wrong+notify+frame(b"\x04\x01\x01")+valid[:5], valid[5:]]])
    assert b.call("frequency_get") == 7100000
    assert b.notifications
    assert b.state == "connected"


@pytest.mark.parametrize("op,payload,expected", [("mode_get",b"\x04\x01\x02","USB"),("smeter_get",b"\x15\x02\x02\x55",255),("ptt_get",b"\x1c\x00\x00",False)])
def test_radio_queries(config, op, payload, expected):
    b, _ = backend(config, [[frame(payload)]])
    assert b.call(op) == expected


def test_settings_ack_nak(config):
    b, p = backend(config, [[frame(b"\xfb")], [frame(b"\xfa")]])
    b.call("frequency_set", 7100000)
    assert p.writes[0] == frame(b"\x05\x00\x00\x10\x07\x00", 0x94, 0xe0)
    with pytest.raises(CiviError, match="NAK"): b.call("mode_set", "USB")
    assert b.state == "connected"


def test_timeout_quarantines_late_response(config):
    b, p = backend(config, [[], [frame(b"\x03"+bcd_encode(7100000,5))]])
    with pytest.raises(CiviError, match="timeout"): b.call("frequency_get")
    p.chunks = [frame(b"\x03"+bcd_encode(7100000,5))]
    with pytest.raises(CiviError, match="quarantined"): b.call("frequency_get")
    assert len(p.writes) == 1
    assert b.state == "quarantined"


@pytest.mark.parametrize("payload", [b"\x03\xff\x00\x00\x00\x00",b"\x03\x00",b"\x15\x02\x09\x99",b"\x1c\x00\x02"])
def test_malformed(config, payload):
    op = "frequency_get" if payload[0] == 3 else "smeter_get" if payload[0] == 0x15 else "ptt_get"
    b, _ = backend(config, [[frame(payload)]])
    with pytest.raises(CiviError): b.call(op)
    assert b.state == "quarantined"


def test_quarantine_emergency_ack_is_not_confirmation(config):
    b, _ = backend(config, [[frame(b"\xfb")]])
    b.state = "quarantined"
    with pytest.raises(CiviError, match="cannot confirm"): b.call("ptt_set", False)
    assert b.state == "quarantined"


def test_bcd_roundtrip():
    assert bcd_encode(7100000,5) == b"\x00\x00\x10\x07\x00"
    assert bcd_decode(bcd_encode(7100000,5)) == 7100000
    assert bcd_decode(b"\x02\x55",False) == 255


def test_model_id_is_independent_of_configured_address(config):
    config['serial']['radio_address'] = 0xa4
    b,p = backend(config, [[frame(b'\x19\x00\x94', source=0xa4)]])
    assert b.call('model_id_get') == 0x94
    assert p.writes == [frame(b'\x19\x00', dest=0xa4, source=0xe0)]


def test_usb_io_failure_requires_explicit_recovery(config):
    b,p=backend(config,[])
    def broken_write(data): raise OSError("USB unplugged")
    p.write=broken_write
    with pytest.raises(CiviError,match="USB I/O failed"): b.call("frequency_get")
    assert p.closed
    assert b.state=="quarantined"
    replacement=FakeSerial([[frame(b"\x03"+bcd_encode(7100000,5))]])
    b.factory=lambda:replacement
    with pytest.raises(CiviError): b.call("frequency_get")
    assert not replacement.writes
    b.recover()
    assert b.state=="connected"
