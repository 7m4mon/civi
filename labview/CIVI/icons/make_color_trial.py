"""One colorful INIT prototype; leaves the complete monochrome set intact."""
from pathlib import Path

from make_complete_set import draw
from make_radio_icons import png, rect, scale, text

OUT = Path(__file__).resolve().parent

def draw_color(lines):
    p = draw(lines)
    # Edit the native pixel drawing, not a previously exported raster.
    rect(p,1,1,30,1,(49,52,57))
    # MON: dash=3 pixels, dot=1, symbol gap=1, letter gap=3.
    x=1
    for i,letter in enumerate(('--','---','-.')):
        if i:
            x+=3
        for j,symbol in enumerate(letter):
            if j:
                x+=1
            width=3 if symbol=='-' else 1
            rect(p,x,1,x+width-1,1,(219,226,234))
            x+=width
    assert x==30
    rect(p,2,3,29,24,(16,36,59))
    rect(p,2,24,29,24,(236,30,72))
    words=('CIVI',)+lines
    ys=(6,16) if len(words)==2 else (5,12,19)
    for word,y in zip(words,ys):
        text(p,word,(32-(len(word)*4-1))//2,y,(245,247,250))
    rect(p,1,26,22,30,(49,52,57))
    for x in (3,10,17):
        rect(p,x,27,x+3,29,(10,12,15))
        rect(p,x,27,x+3,27,(64,68,74))
    for y in range(25,32):
        for x in range(24,31):
            d=(x-27)**2+(y-28)**2
            if d<=10:
                p[y][x]=(183,192,202) if d>5 else (59,64,71)
    # Off-center finger recess; no pointer or direction mark.
    p[29][26]=(0,0,0)
    return p

def main():
    p=draw_color(('INIT',))
    png(OUT/'radio-init-color-trial-32-v5.png',p)
    png(OUT/'radio-init-color-trial-preview-v5.png',scale(p,12))
    print('Created one 32x32 color prototype and a nearest-neighbor preview.')

if __name__=='__main__':
    main()
