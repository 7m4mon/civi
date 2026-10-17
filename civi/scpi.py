import re
from decimal import Decimal, DecimalException
from .errors import CiviError
from .commands import CATALOG
from . import menus # Registers IC-7300 menu commands.


HEADERS = {
    "SYSTEM:ERROR": "error", "SYST:ERR": "error",
    "SENSE:FREQUENCY": "frequency", "SENS:FREQ": "frequency",
    "RADIO:MODE": "mode", "RAD:MODE": "mode",
    "READ:SMETER": "smeter", "READ:SMET": "smeter",
    "RADIO:PTT": "ptt", "RAD:PTT": "ptt",
    "RAD:FIRM": "firmware",
}


def parse(part, parent=""):
    words = part.strip().split(None, 1)
    if not words: raise CiviError(-102, "Empty command")
    raw = words[0].upper()
    absolute = raw.startswith(":")
    raw = raw.lstrip(":")
    query = raw.endswith("?")
    header = raw[:-1] if query else raw
    arg = words[1].strip() if len(words) == 2 else None
    if not absolute and not header.startswith("*") and ":" not in header and parent:
        header = parent + ":" + header
    next_parent = header.rsplit(":", 1)[0] if ":" in header else parent
    if header.startswith("*"):
        if header in ("*IDN", "*OPC") and query and arg is None: return header, True, None, next_parent
        if header == "*CLS" and not query and arg is None: return header, False, None, next_parent
        raise CiviError(-113, "Undefined header")
    # Independently accept each documented short or long mnemonic.
    normalized = header.replace("SYSTEM", "SYST").replace("ERROR", "ERR").replace("SENSE", "SENS").replace("FREQUENCY", "FREQ").replace("RADIO", "RAD").replace("SMETER", "SMET").replace("FIRMWARE", "FIRM")
    key = HEADERS.get(normalized)
    if normalized == 'RAD:SCOPE:WAVE':
        if not query or arg is not None: raise CiviError(-113,'Scope waveform is query only')
        return 'scope_wave',True,None,next_parent
    if normalized in CATALOG:
        spec = CATALOG[normalized]
        # The descriptor validates selectors/parameters before touching serial.
        try: spec.prepare(query,arg)
        except CiviError: raise
        except (ValueError,UnicodeError,DecimalException) as e:
            raise CiviError(-222,'Invalid extended command parameter') from e
        return 'catalog:'+normalized,query,arg,next_parent
    if not key: raise CiviError(-113, "Undefined header")
    if query:
        if arg is not None: raise CiviError(-108, "Parameter not allowed")
    elif key in ("error", "smeter", "firmware"):
        raise CiviError(-113, "Query only command")
    elif arg is None:
        raise CiviError(-109, "Missing parameter")
    return key, query, arg, next_parent


def frequency(text):
    m = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(Hz|kHz|MHz)?", text, re.I)
    if not m: raise CiviError(-104, "Invalid frequency")
    try:
        value = Decimal(m[1]) * {"hz": 1, "khz": 1000, "mhz": 1000000}[ (m[2] or "Hz").lower() ]
        if not value.is_finite() or value != value.to_integral_value() or not 0 <= value <= 9999999999:
            raise CiviError(-222, "Frequency must be whole Hz within profile range")
        return int(value)
    except DecimalException as e:
        raise CiviError(-222, "Frequency out of range") from e


def split_program(line):
    """SCPI separators inside quoted strings are data, including doubled quotes."""
    parts, start, quoted, i = [],0,False,0
    while i < len(line):
        if line[i] == '"':
            if quoted and i+1 < len(line) and line[i+1] == '"': i += 2; continue
            quoted = not quoted
        elif line[i] == ';' and not quoted:
            parts.append(line[start:i]); start = i+1
        i += 1
    if quoted: raise CiviError(-102,'Unterminated SCPI string')
    parts.append(line[start:])
    return parts
