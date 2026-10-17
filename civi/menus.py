"""Menu 1A 05 catalog (IC-7300 supplement printed pages 4-7)."""
from .commands import add, Codec, BOOL, RAW, pack_bcd


def build():
    # Reserved 0028 is deliberately absent. IDs are BCD digits in the protocol.
    codecs = {n: BOOL for n in range(1,218) if n != 28}
    for n in (2,3,5,6,8,9,12,13,17,18,19,20): codecs[n] = Codec(maximum=10)
    for n in (21,43,58,60,63,64,65,81,158,190,195): codecs[n] = RAW
    for n, maximum in {24:3,25:2,26:5,27:5,29:5,36:2,37:2,47:2,50:2,51:2,66:4,67:4,77:3,78:2,79:2,80:2,
                       89:3,98:2,99:2,102:3,108:2,109:2,110:7,155:4,162:3,164:2,166:3,187:3,188:3,
                       189:9,191:20,192:3,194:2,198:5,199:5,200:5,201:5,202:19,203:19}.items():
        codecs[n] = Codec(maximum=maximum)
    codecs[72] = Codec(size=2,maximum=223)
    codecs[156] = Codec(minimum=1,maximum=8)
    codecs[157] = Codec(size=2,minimum=1,maximum=9999)
    codecs[160] = Codec(minimum=1,maximum=60)
    codecs[161] = Codec(minimum=28,maximum=45)
    codecs[181] = Codec(minimum=1,maximum=15)
    for n in (1,4,7,10,11): codecs[n] = Codec('hpf',minimum=2,maximum=2)
    for n in (14,15,16,196): codecs[n] = Codec('bandwidth',minimum=1,maximum=1)
    for n in (104,105,106,152,154,167,171,172): codecs[n] = Codec('color',minimum=6,maximum=6)
    bands = [(30000,1600000),(1600000,2000000),(2000000,6000000),(6000000,8000000),
             (8000000,11000000),(11000000,15000000),(15000000,20000000),(20000000,22000000),
             (22000000,26000000),(26000000,30000000),(30000000,45000000),(45000000,60000000),(60000000,74800000)]
    for n in (*range(112,151), *range(204,217)):
        band = (n-112)//3 if n < 204 else n-204
        low,high = bands[band]
        example = (pack_bcd(low//100,3,True)+pack_bcd(high//100,3,True)).hex().upper()
        codecs[n] = Codec('menu_edge',minimum=6,maximum=6,example=example)
    # Signed repeater offsets use a different format from RIT; added below after
    # their dedicated encoder has been selected.
    for n in (31,32): codecs[n] = Codec('repeater_offset',size=3,minimum=-9999000,maximum=9999000)
    codecs[91] = Codec('opening')
    codecs[94] = Codec('date',size=4)
    codecs[95] = Codec('time',size=2)
    codecs[96] = Codec('timezone',size=2)
    labels = {}
    groups = {
      (1,11):'Receive audio filter/EQ', (12,20):'Transmit audio EQ/bandwidth', (21,23):'Beep',
      (24,24):'Band edge beep/limit', (25,25):'RF/SQL control', (26,27):'Transmit delay', (29,29):'CI-V TX timeout',
      (30,35):'Split/tuner setup', (36,38):'RTTY signal', (39,45):'Speech/lock setup', (46,49):'Memo/dial/key behavior',
      (50,53):'Notch/CW behavior', (54,56):'Screenshot/keyboard', (57,58):'Reference calibration',
      (59,65):'ACC/USB audio routing/levels', (66,67):'Modulation source', (68,70):'External memory keypad',
      (71,77):'CI-V/USB communication', (78,80):'USB SEND/keying pins', (81,93):'Display/UI',
      (94,96):'Clock', (97,111):'Scope display', (112,150):'Stored scope band edges', (151,154):'Audio scope display',
      (155,157):'CW contest counter', (158,165):'CW sidetone/keyer', (166,177):'RTTY decoder/log',
      (178,179):'Scan behavior', (180,181):'Voice memory playback', (182,188):'QSO recording', (189,190):'Noise blanker shape',
      (191,192):'VOX timing', (193,193):'Medium-wave attenuator', (194,194):'Keyboard layout', (195,195):'Voice TX level',
      (196,196):'SSB DATA transmit bandwidth', (197,197):'USB input inhibit', (198,203):'Front/microphone key assignment',
      (204,216):'Stored scope band edge 4', (217,217):'PTT terminal behavior',
    }
    for (lo,hi), label in groups.items():
        for n in range(lo,hi+1): labels[n] = label
    labels.update({1:'SSB RX HPF/LPF',2:'SSB RX bass',3:'SSB RX treble',4:'AM RX HPF/LPF',5:'AM RX bass',6:'AM RX treble',
        7:'FM RX HPF/LPF',8:'FM RX bass',9:'FM RX treble',10:'CW RX HPF/LPF',11:'RTTY RX HPF/LPF',
        31:'HF repeater split offset',32:'50 MHz repeater split offset',58:'Reference frequency adjustment',
        71:'CI-V transceive',72:'USB-to-REMOTE transceive address',73:'Antenna CI-V output',74:'CI-V USB port mode (read only)',
        75:'USB CI-V echo',76:'USB serial function',77:'RTTY serial baud code',78:'USB SEND pin',79:'USB CW keying pin',80:'USB FSK pin',
        91:'Opening screen text',94:'Date',95:'Time',96:'UTC offset',156:'Counter trigger memory',157:'Contest counter',
        160:'Keyer repeat seconds',161:'Keyer dot/dash weight',181:'Voice repeat seconds',217:'PTT terminal function'})
    for n,codec in codecs.items():
        guard = 'menu'
        if n in (57,58): guard = 'calibration'
        if 71 <= n <= 80 or n == 197: guard = 'link'
        label = labels[n]
        if codec.kind == 'menu_edge':
            band = (n-112)//3 if n < 204 else n-204
            edge = (n-112)%3+1 if n < 204 else 4
            lo,hi = bands[band]
            label = f'Scope band {band+1} edge {edge} ({lo/1e6:g}-{hi/1e6:g} MHz)'
        add(f'RAD:MENU:{n:04}',f'1a05{n:04}',f'{label} [{n:04}]',codec,
            access='r' if n == 74 else 'rw',guard=guard,page='4-7')


build()
