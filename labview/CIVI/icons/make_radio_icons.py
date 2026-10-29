"""Draw exact-size LabVIEW radio icons using only the Python standard library."""
from pathlib import Path
import struct
import zlib

OUT = Path(__file__).resolve().parent
FONT = {
    'C': ['111','100','100','100','111'],
    'I': ['111','010','010','010','111'],
    'V': ['101','101','101','101','010'],
    'N': ['101','111','111','111','101'],
    'T': ['111','010','010','010','010'],
}

def png(path, pixels):
    h, w = len(pixels), len(pixels[0])
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    raw = b''.join(b'\0' + bytes(c for p in row for c in p) for row in pixels)
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))

def rect(p, x0, y0, x1, y1, color):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            p[y][x] = color

def text(p, word, x, y, color=(18,49,57)):
    for i, ch in enumerate(word):
        for dy, row in enumerate(FONT[ch]):
            for dx, on in enumerate(row):
                if on == '1':
                    p[y + dy][x + i * 4 + dx] = color

def radio_v3(label=False):
    p = [[(31,33,36)] * 30 for _ in range(30)]
    rect(p,1,1,28,28,(51,54,58))
    rect(p,1,1,28,1,(96,100,106))
    # Large 26 x 20 pixel display; the lower strip carries the controls.
    rect(p,1,2,28,23,(17,19,22))
    rect(p,2,3,27,22,(35,39,44))
    rect(p,2,3,27,3,(63,68,74))
    for x in (3,8,13,18):
        rect(p,x,25,x+2,26,(19,21,24))
        rect(p,x,25,x+2,25,(124,129,136))
    for y in range(23,30):
        for x in range(22,29):
            d = (x-25)**2 + (y-26)**2
            if d <= 10:
                p[y][x] = (13,15,17) if d > 5 else (119,125,133)
    rect(p,25,23,25,25,(235,238,241))
    if label:
        text(p,'CIVI',7,6,(242,244,247))
        text(p,'INIT',7,15,(255,255,255))
    return p

def radio(label=False):
    p = [[(255,255,255)] * 30 for _ in range(30)]
    rect(p, 0,0,29,29,(28,35,42))
    rect(p, 1,1,28,28,(166,176,184))
    rect(p, 1,1,28,2,(224,231,235))
    rect(p, 1,28,28,28,(87,100,113))
    rect(p, 2,4,21,23,(44,57,68))
    rect(p, 3,5,20,22,(178,225,231))
    rect(p, 3,5,20,5,(218,246,246))
    # Seven-pixel tuning knob, with a bright position mark.
    for y in range(11,18):
        for x in range(22,29):
            d = (x-25)**2 + (y-14)**2
            if d <= 10:
                p[y][x] = (28,35,42) if d > 5 else (73,86,98)
    rect(p,25,11,25,13,(236,242,245))
    rect(p,24,5,26,6,(44,57,68))
    rect(p,25,5,26,5,(93,213,136))
    for x in (3,9,15):
        rect(p,x,25,x+3,27,(44,57,68))
        rect(p,x,25,x+2,25,(230,235,239))
    rect(p,24,22,27,25,(44,57,68))
    rect(p,25,23,26,24,(113,128,140))
    if label:
        text(p,'CIVI',4,7)
        text(p,'INIT',4,15)
    return p

def border(p):
    q = [[(0,0,0)] * 32 for _ in range(32)]
    for y in range(30):
        q[y+1][1:31] = p[y][:]
    return q

def canvas(p):
    q = [[(255,255,255)] * 32 for _ in range(32)]
    for y in range(30):
        q[y+1][1:31] = p[y][:]
    return q

def scale(p, n):
    return [[v for c in row for v in [c]*n] for row in p for _ in range(n)]

def main():
    blank, init = radio(), radio(True)
    png(OUT/'radio-background-30.png', blank)
    png(OUT/'radio-template-32.png', border(blank))
    png(OUT/'radio-init-32.png', border(init))
    png(OUT/'radio-template-32-v2.png', canvas(blank))
    png(OUT/'radio-init-32-v2.png', canvas(init))
    # Nearest-neighbor enlargement for inspecting the actual pixels.
    left, right = scale(canvas(blank),10), scale(canvas(init),10)
    preview = [[(245,245,245)]*680 for _ in range(340)]
    for y in range(320):
        preview[y+10][10:330] = left[y]
        preview[y+10][350:670] = right[y]
    png(OUT/'radio-preview-v2.png', preview)
    png(OUT/'radio-template-32-v3.png', canvas(radio_v3()))
    png(OUT/'radio-init-32-v3.png', canvas(radio_v3(True)))
    left, right = scale(canvas(radio_v3()),10), scale(canvas(radio_v3(True)),10)
    preview = [[(245,245,245)]*680 for _ in range(340)]
    for y in range(320):
        preview[y+10][10:330] = left[y]
        preview[y+10][350:670] = right[y]
    png(OUT/'radio-preview-v3.png', preview)

if __name__ == '__main__':
    main()
