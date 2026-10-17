"""Typed IC-7300 command catalog. No unrestricted raw CI-V passthrough.

Numeric gain/meter/menu values are protocol codes, not calibrated units.
Complex records use bounded, validated hex where a useful textual API would
otherwise lose information. All execution still belongs to ControlService.
"""
import csv
import datetime
import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from .errors import CiviError


def invalid(message="Invalid command parameter"):
    return CiviError(-222, message)


def pack_bcd(value, size, little=False):
    if not isinstance(value, int) or not 0 <= value < 100 ** size:
        raise invalid("BCD value out of range")
    data = bytes.fromhex(f"{value:0{size*2}d}")
    return data[::-1] if little else data


def unpack_bcd(data, little=False):
    if not data or any(b >> 4 > 9 or b & 15 > 9 for b in data):
        raise invalid("Invalid BCD")
    return int((data[::-1] if little else data).hex())


def fields(text):
    if text is None or not text.strip(): return []
    try: return next(csv.reader([text], skipinitialspace=True, strict=True))
    except csv.Error as e: raise invalid("Invalid comma-separated parameters") from e


@dataclass(frozen=True)
class Codec:
    kind: str = "number"
    size: int = 1
    minimum: int = 0
    maximum: int = 1
    choices: tuple = ()
    names: tuple = ()
    example: str | None = None

    def encode(self, text):
        text = str(text) if self.kind in ('text','opening','keyer') else str(text).strip()
        if self.kind == "text":
            # Firmware supports half-width kana in memory records, not in CW.
            value = text.encode("ascii", errors="strict")
            allowed = b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz/?.-,:'()=+\"@ ^"
            if not self.minimum <= len(value) <= self.maximum or any(b not in allowed for b in value):
                raise invalid("Invalid CW text or length")
            return value
        if self.kind == "opening":
            if not re.fullmatch(r"[A-Z0-9 ./@-]{0,10}", text): raise invalid("Opening text: max 10 uppercase letters, digits, space, -./@")
            return text.ljust(10).encode('ascii')
        if self.kind == "keyer":
            if not re.fullmatch(r"[0-9A-Za-z /?.,@^*]{0,70}", text): raise invalid("Keyer text: max 70 supported characters")
            return text.ljust(70).encode('ascii')
        if self.kind == "frequency":
            from .scpi import frequency
            value = frequency(text)
            if not self.minimum <= value <= self.maximum: raise invalid("Frequency outside command range")
            return pack_bcd(value, 5, True)
        if self.kind in ("hex", "memory", "stack", "edge", "menu_edge", "bandedge", "color", "hpf", "bandwidth", "mode", "data", "scope_ref", "scope_span", "scope_edge"):
            try: value = bytes.fromhex(text)
            except ValueError as e: raise invalid("Expected hexadecimal payload") from e
            self.validate_bytes(value)
            return value
        if self.kind == "signed":
            value = int(text)
            if not self.minimum <= value <= self.maximum: raise invalid()
            return pack_bcd(abs(value), self.size, True) + bytes([int(value < 0)])
        if self.kind == 'repeater_offset':
            value = int(text)
            if abs(value) > 9999000 or value % 1000: raise invalid('Repeater offset: whole kHz, magnitude <= 9999 kHz')
            return pack_bcd(abs(value)//100,3,True) + bytes([int(value < 0)])
        if self.kind == "timezone":
            if not re.fullmatch(r"[+-]?\d{2}:\d{2}", text): raise invalid("Use +/-HH:MM")
            hour, minute = map(int, text.lstrip('+-').split(':'))
            if hour > 14 or minute > 59 or hour == 14 and minute: raise invalid("UTC offset out of range")
            return pack_bcd(hour * 100 + minute, 2) + bytes([int(text.startswith('-'))])
        if self.kind == "date":
            date = datetime.date.fromisoformat(text)
            if not 2000 <= date.year <= 2099: raise invalid("Date outside 2000-2099")
            return pack_bcd(int(date.strftime('%Y%m%d')), 4)
        if self.kind == "time":
            if not re.fullmatch(r"\d{2}:\d{2}", text): raise invalid("Use HH:MM")
            hour, minute = map(int, text.split(':'))
            datetime.time(hour, minute)
            return pack_bcd(hour * 100 + minute, 2)
        if self.kind == "tone":
            value = Decimal(text) * 10
            if value != value.to_integral_value() or not 670 <= value <= 2541: raise invalid("Tone must be 67.0-254.1 Hz in 0.1 Hz increments")
            return pack_bcd(int(value), 2)
        if self.kind == 'band_selector':
            value = int(text)
            if not 1 <= value // 100 <= 11 or not 1 <= value % 100 <= 3: raise invalid('Use band*100+slot; band 1-11, slot 1-3')
            return pack_bcd(value,2)
        if self.kind == 'scope_edge_selector':
            value = int(text)
            if not 1 <= value // 100 <= 13 or not 1 <= value % 100 <= 4: raise invalid('Use scope_band*100+edge; band 1-13, edge 1-4')
            return pack_bcd(value,2)
        if self.names and text.upper() in self.names:
            value = self.choices[self.names.index(text.upper())]
        elif text.upper() in ("ON", "OFF") and self.maximum == 1:
            value = int(text.upper() == 'ON')
        else:
            if not re.fullmatch(r"[+-]?\d+", text): raise invalid("Expected integer protocol code")
            value = int(text)
        if not self.minimum <= value <= self.maximum or self.choices and value not in self.choices:
            raise invalid("Value outside supported range")
        return pack_bcd(value, self.size)

    def validate_bytes(self, data):
        if self.kind == 'memory' and data == b'\xff': return
        if not self.minimum <= len(data) <= self.maximum: raise invalid("Payload length out of range")
        if self.kind == "color":
            if any(unpack_bcd(data[i:i+2]) > 255 for i in (0,2,4)): raise invalid("RGB components must be 0-255")
        elif self.kind == "hpf":
            low,high=unpack_bcd(data[:1]),unpack_bcd(data[1:])
            if not 0 <= low <= 20 or not 5 <= high <= 25 or low and high != 25 and low >= high:
                raise invalid("HPF/LPF index out of range or HPF not below LPF")
        elif self.kind == "bandwidth":
            if data[0] >> 4 > 3 or data[0] & 15 > 3: raise invalid("SSB bandwidth index out of range")
        elif self.kind == "mode":
            if data[0] not in (0,1,2,3,4,5,7,8) or data[1] not in (0,1) or data[2] not in (1,2,3): raise invalid("Invalid mode/data/filter")
        elif self.kind == "data":
            if data[0] not in (0,1) or data[1] not in ((0,) if data[0] == 0 else (1,2,3)): raise invalid("Invalid data/filter")
        elif self.kind == "edge":
            low, high = unpack_bcd(data[:5], True), unpack_bcd(data[5:], True)
            if low > high or high > 74800000 or low % 1000 or high % 1000: raise invalid("Invalid scope edge frequencies (whole kHz)")
        elif self.kind == 'menu_edge':
            low,high=unpack_bcd(data[:3],True),unpack_bcd(data[3:],True)
            if low > high or high > 748000 or low % 10 or high % 10: raise invalid('Stored scope edge: 100 Hz BCD units, whole kHz')
        elif self.kind == 'bandedge':
            if data[5] != 0x2d: raise invalid('Band edge separator must be 2D')
            low,high=unpack_bcd(data[:5],True),unpack_bcd(data[6:],True)
            if low > high or high > 74800000: raise invalid('Invalid transmit band edges')
        elif self.kind == "scope_span":
            if unpack_bcd(data, True) not in (2500,5000,10000,25000,50000,100000,250000,500000): raise invalid("Unsupported scope span")
        elif self.kind == "scope_ref":
            whole=unpack_bcd(data[:1])
            if data[2] not in (0,1) or data[1] not in (0,0x50) or whole > 20 or whole == 20 and data[1]:
                raise invalid("Reference: whole-dB BCD byte, fractional byte 00/50, sign byte 00/01; magnitude <=20 dB")
        elif self.kind == "scope_edge":
            if not 1 <= unpack_bcd(data[:1]) <= 13 or not 1 <= unpack_bcd(data[1:2]) <= 4: raise invalid("Invalid scope band/edge")
            Codec('edge', minimum=10, maximum=10).validate_bytes(data[2:])
        elif self.kind == 'stack':
            Codec('memory',minimum=39,maximum=39).validate_bytes(b'\x00'+data*2+b' '*10)
        elif self.kind == "memory":
            if data[0] >> 4 not in (0,1) or data[0] & 15 not in (0,1,2,3): raise invalid("Invalid memory split/select flags")
            # Two 14-byte frequency/mode/tone records and ten name bytes.
            for off in (1,15):
                freq = unpack_bcd(data[off:off+5], True)
                if not 30000 <= freq <= 74800000: raise invalid("Memory frequency out of range")
                if data[off+5] not in (0,1,2,3,4,5,7,8) or data[off+6] not in (1,2,3): raise invalid("Invalid memory mode/filter")
                flag = data[off+7]
                if flag >> 4 not in (0,1) or flag & 15 not in (0,1,2): raise invalid("Invalid memory DATA/tone flags")
                for pos in (off+8,off+11):
                    tone = unpack_bcd(data[pos:pos+3])
                    if not 670 <= tone <= 2541: raise invalid("Invalid memory tone")
            if any(b < 32 or b > 126 and not 0xa1 <= b <= 0xdf for b in data[29:]): raise invalid("Invalid memory name characters")

    def decode(self, data):
        if self.kind == 'data':
            # The manual's OFF/00 restriction is a write requirement. A read
            # can still report the selected FIL1-FIL3 while DATA is OFF.
            if len(data) != 2 or data[0] not in (0,1) or data[1] not in (1,2,3) and data != b'\x00\x00':
                raise invalid('Invalid DATA/filter response')
            return data.hex().upper()
        if self.kind in ("hex", "memory", "stack", "edge", "menu_edge", "bandedge", "color", "hpf", "bandwidth", "mode", "data", "scope_ref", "scope_span", "scope_edge"):
            self.validate_bytes(data)
            return data.hex().upper()
        if self.kind in ('text','opening','keyer'):
            result = data.decode('ascii').rstrip()
            self.encode(result)
            return '"' + result.replace('"','""') + '"'
        if self.kind == 'frequency':
            if len(data) != 5: raise invalid("Invalid frequency response length")
            value = unpack_bcd(data, True)
            self.encode(str(value)); return str(value)
        if self.kind in ('signed', 'timezone','repeater_offset'):
            if len(data) != self.size + 1 or data[-1] not in (0,1): raise invalid("Invalid signed response")
            value = unpack_bcd(data[:-1], self.kind != 'timezone')
            if self.kind == 'repeater_offset': value *= 100
            if self.kind == 'timezone':
                result = ('-' if data[-1] else '+') + f'{value//100:02}:{value%100:02}'
            else: result = str(-value if data[-1] else value)
            self.encode(result); return result
        if self.kind == 'tone':
            if len(data) != 3 or data[0] != 0: raise invalid("Invalid tone response")
            value = unpack_bcd(data) / 10
            self.encode(str(value)); return f'{value:.1f}'
        if len(data) != self.size: raise invalid("Invalid response length")
        value = unpack_bcd(data)
        if self.kind == 'date':
            digits = f'{value:08}'
            result = f'{digits[:4]}-{digits[4:6]}-{digits[6:]}'
        elif self.kind == 'time': result = f'{value//100:02}:{value%100:02}'
        else: result = str(value)
        self.encode(result)
        if self.names:
            return self.names[self.choices.index(value)]
        return result

    def sample(self):
        if self.example is not None: return self.example
        samples = {'frequency':'7100000', 'signed':'0','repeater_offset':'0','timezone':'+00:00','date':'2026-01-01','time':'00:00',
                   'tone':'88.5','text':'TEST','opening':'CIVI','keyer':'CQ', 'color':'012801280128',
                   'hpf':'0005','bandwidth':'00','mode':'010001','data':'0000','edge':'00000000000000000100',
                   'scope_span':'0000250000','scope_ref':'000000','scope_edge':'010100000000000000000100',
                   'memory':'00'+'0000100700010100000885000885'*2+'20'*10}
        if self.kind == 'menu_edge': return '001007002007'
        if self.kind == 'bandedge': return '00001007002D0000200700'
        if self.kind == 'stack': return '0000100700010100000885000885'
        if self.kind == 'band_selector': return '101'
        if self.kind == 'scope_edge_selector': return '101'
        if self.kind == 'hex': return '00'*self.minimum
        return samples.get(self.kind, self.names[0] if self.names else str(self.choices[0] if self.choices else self.minimum))


BOOL = Codec(choices=(0,1), names=('OFF','ON'))
RAW = Codec(size=2, maximum=255)
FREQ = Codec('frequency', minimum=30000, maximum=74800000)


@dataclass(frozen=True)
class Command:
    header: str
    wire: str
    description: str
    codec: Codec = BOOL
    access: str = 'rw'
    selector: Codec | None = None
    guard: str = ''
    page: str = '3-8'
    fixed: str = ''
    selector_on_wire: bool = True

    def prepare(self, query, text):
        if ('r' if query else 'w') not in self.access: raise CiviError(-113, 'Read/write direction not supported')
        parts = fields(text)
        prefix = bytes.fromhex(self.wire)
        if self.selector:
            if not parts: raise CiviError(-109, 'Missing selector')
            selector = self.selector.encode(parts.pop(0))
            if self.selector_on_wire: prefix += selector
        expected = 0 if query or self.access == 'w' and (self.fixed or self.header in NO_DATA_ACTIONS) else 1
        if len(parts) != expected: raise CiviError(-109 if len(parts) < expected else -108, 'Wrong number of parameters')
        data = b'' if query or self.header in NO_DATA_ACTIONS else bytes.fromhex(self.fixed) if self.fixed else self.codec.encode(parts[0])
        if self.header == 'RAD:MEM:CONTENT' and unpack_bcd(prefix[-2:]) >= 100 and (data == b'\xff' or data and data[0] != 0):
            raise invalid('P1/P2 cannot be cleared and require split/select flags zero')
        return prefix, data

    def public(self):
        selector = (self.selector.sample()+',') if self.selector else ''
        return {'header':self.header,'civ':self.wire,'description':self.description,'access':self.access,
                'format':self.codec.kind,'minimum':self.codec.minimum,'maximum':self.codec.maximum,
                'choices':list(self.codec.names or self.codec.choices),'guard':self.guard,'page':self.page,
                'set_example':selector + ('' if self.fixed or self.header in NO_DATA_ACTIONS else self.codec.sample()) if 'w' in self.access else None,
                'query_example':(self.selector.sample() if self.selector else '') if 'r' in self.access else None,
                'hardware_verified':False}


CATALOG = {}


def add(header, wire, description, codec=BOOL, access='rw', selector=None, guard='', page='3-8', fixed='', selector_on_wire=True):
    c = Command(header,wire,description,codec,access,selector,guard,page,fixed,selector_on_wire)
    if header in CATALOG: raise ValueError(f'Duplicate command {header}')
    CATALOG[header] = c
    return c


def enum(*names):
    return Codec(maximum=len(names)-1, choices=tuple(range(len(names))), names=names)


def build_catalog():
    for name, sub, desc in [('AFGAIN','01','AF gain'),('RFGAIN','02','RF gain'),('SQL','03','Squelch level'),
          ('NR:LEVEL','06','Noise reduction level'),('PBT:INNER','07','Inner PBT'),('PBT:OUTER','08','Outer PBT'),
          ('CW:PITCH','09','CW pitch code'),('POWER','0a','RF power code'),('MICGAIN','0b','Microphone gain'),
          ('CW:SPEED','0c','Key speed code'),('NOTCH:LEVEL','0d','Notch position'),('COMP:LEVEL','0e','Compression level'),
          ('CW:DELAY','0f','Break-in delay code'),('NB:LEVEL','12','Noise blanker level'),('MONITOR:LEVEL','15','Monitor gain'),
          ('VOX:GAIN','16','VOX gain'),('VOX:ANTIGAIN','17','Anti-VOX gain'),('BACKLIGHT','19','LCD brightness')]:
        add('RAD:'+name,'14'+sub,desc,RAW)
    for name, sub in [('SQL','01'),('SQL:ALL','05'),('OVF','07')]:
        add('READ:'+name,'15'+sub,name+' status',BOOL,'r')
    for name, sub in [('POWER','11'),('SWR','12'),('ALC','13'),('COMP','14'),('VOLTAGE','15'),('CURRENT','16')]:
        add('READ:'+name,'15'+sub,name+' meter (raw, uncalibrated)',RAW,'r')
    for name, sub in [('NB','22'),('NR','40'),('ANOTCH','41'),('TONE','42'),('TSQL','43'),('COMP','44'),('MONITOR','45'),
                      ('VOX','46'),('NOTCH','48'),('TPF','4f'),('LOCK','50'),('IPPLUS','65'),('TXINHIBIT','66')]:
        add('RAD:'+name,'16'+sub,name+' enable',BOOL,guard='autotx' if name == 'VOX' else '')
    add('RAD:PREAMP','1602','Preamplifier',enum('OFF','PRE1','PRE2'))
    add('RAD:AGC','1612','AGC speed',Codec(minimum=1,maximum=3,choices=(1,2,3),names=('FAST','MID','SLOW')))
    add('RAD:BKIN','1647','CW break-in',enum('OFF','SEMI','FULL'),guard='autotx')
    add('RAD:FILTER:SHAPE','1656','DSP filter shape',enum('SHARP','SOFT'))
    add('RAD:NOTCH:WIDTH','1657','Notch width',enum('WIDE','MID','NARROW'))
    add('RAD:TXBANDWIDTH','1658','SSB TX bandwidth',enum('WIDE','MID','NARROW'))
    add('RAD:ATT','11','Attenuator code',Codec(maximum=20,choices=(0,20)))
    add('RAD:STEP','10','Tuning step code',Codec(maximum=8))
    add('RAD:SPLIT','0f','Split enable')
    add('RAD:RIT:FREQ','2100','RIT offset (Hz)',Codec('signed',size=2,minimum=-9999,maximum=9999))
    add('RAD:RIT','2101','RIT enable')
    add('RAD:XIT','2102','Delta TX enable')
    add('RAD:TXFREQ','1c03','Transmit frequency',FREQ,'r')
    add('RAD:XFC','1c02','Transmit frequency check')
    add('RAD:ANTOUTPUT','1c04','Antenna controller output',guard='link')
    add('RAD:TUNER','1c01','Antenna tuner (TUNE transmits)',enum('OFF','ON','TUNE'),guard='autotx')
    add('RAD:DATA','1a06','DATA/filter bytes',Codec('data',minimum=2,maximum=2))
    add('RAD:IPPLUS:ALT','1a07','IP+ alternate CI-V command')
    add('RAD:FILTER:WIDTH','1a03','Filter width index (mode dependent)',Codec(maximum=49))
    add('RAD:AGC:TIME','1a04','AGC time index (mode dependent)',Codec(maximum=13))
    add('RAD:VFO:SELECT','07','Select VFO A/B',enum('A','B'),'w')
    add('RAD:VFO:ENABLE','07','Enter VFO mode',access='w',fixed='') # special no-payload action below
    add('RAD:VFO:COPY','07','Copy selected VFO to the other VFO',access='w',fixed='a0')
    add('RAD:VFO:SWAP','07','Swap VFO contents',access='w',fixed='b0')
    selected = enum('SELECTED','OTHER')
    add('RAD:VFO:FREQ','25','Selected/other VFO frequency (Hz)',FREQ,selector=selected)
    add('RAD:VFO:MODE','26','Selected/other VFO mode/DATA/filter bytes',Codec('mode',minimum=3,maximum=3),selector=selected)
    add('RAD:TONE:FREQ','1b00','Repeater tone frequency (Hz)',Codec('tone'))
    add('RAD:TSQL:FREQ','1b01','Tone squelch frequency (Hz)',Codec('tone'))
    scan = {'STOP':'00','PROGRAM':'02','MEMORY':'22','AUTO':'01','DELTA':'03','FINEPROGRAM':'12','FINEDELTA':'13','SELECTMEM':'23',
            'SPAN5K':'a1','SPAN10K':'a2','SPAN20K':'a3','SPAN50K':'a4','SPAN100K':'a5','SPAN500K':'a6','SPAN1M':'a7',
            'SELECTOFF':'b0','SELECTON':'b1','RESUMEOFF':'d0','RESUMEON':'d3'}
    for name, payload in scan.items(): add('RAD:SCAN:'+name,'0e','Scan '+name,access='w',fixed=payload)
    add('RAD:SCAN:SELECT','0eb1','Assign memory select group',Codec(minimum=1,maximum=3),'w')
    add('RAD:SCAN:GROUP','0eb2','Select memory scan group',Codec(maximum=3),'w')
    add('RAD:MEM:SELECT','08','Select memory channel (100=P1,101=P2)',Codec(size=2,minimum=1,maximum=101),'w')
    for name,wire,desc in [('ENABLE','08','Enter memory mode'),('WRITE','09','Write selected memory'),('TOVFO','0a','Copy memory to VFO'),('CLEAR','0b','Clear selected memory')]:
        add('RAD:MEM:'+name,wire,desc,access='w',fixed='',guard='memory' if name in ('WRITE','CLEAR') else '')
    add('RAD:MEM:CONTENT','1a00','Memory record hex (channel selector omitted from payload)',Codec('memory',minimum=39,maximum=39),
        selector=Codec(size=2,minimum=1,maximum=101),guard='memory')
    add('RAD:BAND:STACK','1a01','Band stack record (band*100+slot selector)',Codec('stack',minimum=14,maximum=14),
        selector=Codec('band_selector',size=2,minimum=101,maximum=1103),guard='memory')
    add('RAD:KEYER:TEXT','1a02','Keyer memory text',Codec('keyer'),selector=Codec(minimum=1,maximum=8),guard='memory')
    add('RAD:CW:SEND','17','Send CW text (up to 30 characters)',Codec('text',minimum=1,maximum=30),'w',guard='tx')
    add('RAD:CW:STOP','17','Stop CI-V CW output',access='w',fixed='ff')
    add('RAD:VOICE','2800','Play voice memory; STOP or 1-8',Codec(maximum=8,choices=tuple(range(9)),names=('STOP','T1','T2','T3','T4','T5','T6','T7','T8')),'w',guard='tx')
    add('RAD:SPEECH','13','Announce S/frequency/mode',Codec(maximum=2),'w')
    add('RAD:POWER:OFF','18','Power off radio',access='w',fixed='00',guard='power')
    add('RAD:POWER:ON','18','Power on radio (wake preamble)',access='w',fixed='01',guard='power')
    add('RAD:BAND:EDGES','02','Read default band edges (validated BCD pair)',Codec('bandedge',minimum=11,maximum=11),'r')
    add('RAD:TXBAND:COUNT','1e00','Number of factory transmit bands',Codec(maximum=30),'r')
    add('RAD:TXBAND:READ','1e01','Read transmit band edge',Codec('bandedge',minimum=11,maximum=11),'r',selector=Codec(minimum=1,maximum=30))
    add('RAD:TXBAND:USERCOUNT','1e02','Number of user transmit bands',Codec(maximum=30),'r')
    add('RAD:TXBAND:USER','1e03','User transmit band edge',Codec('bandedge',minimum=11,maximum=11),selector=Codec(minimum=1,maximum=30),guard='calibration')
    for name,sub,codec in [('ENABLE','10',BOOL),('STREAM','11',BOOL),('DISPLAY','12',Codec(maximum=0)),('DUAL','13',Codec(maximum=0)),
        ('MODE','14',Codec(maximum=3)),('SPAN','15',Codec('scope_span',minimum=5,maximum=5)),('EDGE','16',Codec(minimum=1,maximum=4)),
        ('HOLD','17',BOOL),('REFERENCE','19',Codec('scope_ref',minimum=3,maximum=3)),('SPEED','1a',Codec(maximum=2)),
        ('TXDISPLAY','1b',BOOL),('CENTER','1c',Codec(maximum=2)),('VBW','1d',BOOL),
        ('FIXEDGE','1e',Codec('scope_edge',minimum=12,maximum=12)),('MARKER','20',BOOL)]:
        # Some scope commands have only a value, unlike MODE/SPAN/HOLD etc.
        # Retain CIVI's logical main-scope selector 0 without adding a CI-V byte.
        add('RAD:SCOPE:'+name,'27'+sub,'Scope '+name,codec,selector=Codec(maximum=0),guard='stream' if name=='STREAM' else '',
            selector_on_wire=sub not in ('10','11','12','13','1b','1c','20'))
    # FIX edge reads need a band/edge selector as well as the main-scope byte.
    CATALOG.pop('RAD:SCOPE:FIXEDGE')
    add('RAD:SCOPE:FIXEDGE','271e','Scope FIX edge (band*100+edge selector)',Codec('edge',minimum=10,maximum=10),
        selector=Codec('scope_edge_selector',size=2,minimum=101,maximum=1304))


build_catalog()
# Actions with no payload use a sentinel distinct from an unset fixed value.
NO_DATA_ACTIONS = {'RAD:VFO:ENABLE','RAD:MEM:ENABLE','RAD:MEM:WRITE','RAD:MEM:TOVFO','RAD:MEM:CLEAR'}
