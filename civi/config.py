import tomllib
from pathlib import Path


def load(path):
    path = Path(path).resolve()
    with path.open("rb") as f:
        c = tomllib.load(f)
    if c.get("backend") not in ("mock", "civ"):
        raise ValueError("backend must be mock or civ")
    firmware = c.get("radio_firmware", "")
    if not isinstance(firmware, str) or len(firmware) > 64 or any(ord(ch) < 32 or ch in ',;"' for ch in firmware):
        raise ValueError("radio_firmware must be a single-line version string (up to 64 characters)")
    c["radio_firmware"] = firmware.strip()
    permissions = c.setdefault('permissions',{})
    for key in ('menu','memory','power','link','calibration'):
        value = permissions.setdefault(key,False)
        if type(value) is not bool: raise ValueError(f'permissions.{key} must be true or false')
    for key in ("scpi_port", "web_port"):
        if type(c.get(key)) is not int or not 1 <= c[key] <= 65535:
            raise ValueError(f"Invalid {key}")
    s = c["serial"]
    for key, default in (('trace_frames', True), ('trace_scope_frames', False)):
        value = s.setdefault(key, default)
        if type(value) is not bool: raise ValueError(f'Invalid serial.{key}: expected boolean')
    for key in ("radio_address", "controller_address"):
        if type(s[key]) is not int or not 1 <= s[key] <= 239:
            raise ValueError(f"Invalid {key}")
    if s["radio_address"] == s["controller_address"]:
        raise ValueError("CI-V addresses must differ")
    if not 0.05 <= s["timeout"] <= 30 or not 300 <= s["baud"] <= 115200:
        raise ValueError("Invalid serial timing")
    t = c["transmit"]
    if type(t["enabled"]) is not bool or not 0.1 <= t["max_seconds"] <= 600 or not 2 <= t["web_lease_seconds"] <= 60:
        raise ValueError("Invalid transmit configuration")
    for key in ("tls_cert", "tls_key"):
        c[key] = str((path.parent / c[key]).resolve())
    return c
