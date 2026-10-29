"""Build one complete 32x32 PNG per CIVI VI, with no outer whitespace."""
from pathlib import Path
import csv
import io
import struct
import textwrap
import zipfile

from make_radio_icons import FONT, png, rect, scale, text

OUT = Path(__file__).resolve().parent / 'complete'
FONT.update({
    'A':['010','101','111','101','101'],
    'B':['110','101','110','101','110'],
    'D':['110','101','101','101','110'],
    'E':['111','100','110','100','111'],
    'F':['111','100','110','100','100'],
    'G':['111','100','101','101','111'],
    'H':['101','101','111','101','101'],
    'L':['100','100','100','100','111'],
    'M':['101','111','111','101','101'],
    'O':['111','101','101','101','111'],
    'P':['110','101','110','100','100'],
    'Q':['111','101','101','111','001'],
    'R':['110','101','110','101','101'],
    'S':['111','100','111','001','111'],
    'U':['101','101','101','101','111'],
    'W':['101','101','111','111','101'],
    'X':['101','101','010','101','101'],
    'Y':['101','101','010','010','010'],
    'Z':['111','001','010','100','111'],
    '-':['000','000','111','000','000'],
    ' ':['000']*5,
})

# Middle and bottom display lines; CIVI is always the first line.
LABELS = {
    'CIVI Initialize.vi': ('INIT',),
    'CIVI Close.vi': ('CLOSE',),
    'CIVI Ensure LF.vi': ('LF',),
    'CIVI Query.vi': ('QUERY',),
    'CIVI Write.vi': ('WRITE',),
    'CIVI Error Query.vi': ('ERR','QUERY'),
    'CIVI Set Frequency.vi': ('SET','FREQ'),
    'CIVI Set Mode.vi': ('SET','MODE'),
    'CIVI Read Frequency Session.vi': ('READ','FREQ'),
    'CIVI Read Mode Session.vi': ('READ','MODE'),
    'CIVI Read S Meter Session.vi': ('READ','SMET'),
    'CIVI Basic Control Example.vi': ('EX','CTRL'),
    'CIVI Frequency Sweep Example.vi': ('EX','SWEEP'),
    'CIVI Initialize Close Example.vi': ('EX','INIT'),
    'CIVI Read Session Example.vi': ('EX','READ'),
    'CIVI Set Frequency Example.vi': ('EX-SET','FREQ'),
    'CIVI Set Mode Example.vi': ('EX-SET','MODE'),
    'CIVI IDN Test.vi': ('TEST','IDN'),
    'CIVI Query Once.vi': ('QUERY','ONCE'),
    'CIVI Read Frequency.vi': ('OLD','FREQ'),
    'CIVI Read Mode.vi': ('OLD','MODE'),
    'CIVI Read S Meter.vi': ('OLD','SMET'),
    'CIVI Read Frequency Example.vi': ('EX-OLD','FREQ'),
}

def draw(lines):
    # Entire canvas is the radio housing: no white or transparent margin.
    p = [[(27,29,32)]*32 for _ in range(32)]
    rect(p,1,1,30,30,(49,52,57))
    rect(p,1,1,30,1,(91,96,103))
    rect(p,1,2,30,25,(14,16,19))
    rect(p,2,3,29,24,(33,37,42))
    rect(p,2,3,29,3,(62,67,74))
    for x in (3,8,13,18):
        rect(p,x,27,x+2,29,(15,17,20))
        rect(p,x,27,x+2,27,(127,133,141))
    # Bottom-right tuning knob remains below the text display.
    for y in range(25,32):
        for x in range(24,31):
            d=(x-27)**2+(y-28)**2
            if d<=10:
                p[y][x]=(10,12,14) if d>5 else (119,126,135)
    rect(p,27,25,27,27,(242,244,246))
    words=('CIVI',)+lines
    ys=(6,16) if len(words)==2 else (5,12,19)
    for word,y in zip(words,ys):
        width=len(word)*4-1
        assert width<=26,word
        text(p,word,(32-width)//2,y,(245,247,250))
    return p

def main(output_dir=None, renderer=None, archive_name='CIVI-radio-icons-32.zip',
         design='Dark radio body, white text, large display, bottom-right tuning knob.',
         generator='make_complete_set.py'):
    OUT = output_dir or globals()['OUT']
    renderer = renderer or draw
    OUT.mkdir(exist_ok=True)
    actual={p.name for p in (OUT.parent.parent/'VIs').glob('*.vi')}
    assert actual==set(LABELS), (actual-set(LABELS),set(LABELS)-actual)
    rows=[]
    drawings=[]
    for name, lines in LABELS.items():
        filename=name[:-3]+'.png'
        p=renderer(lines)
        png(OUT/filename,p)
        assert struct.unpack('>II',(OUT/filename).read_bytes()[16:24])==(32,32)
        rows.append((name,filename,' / '.join(('CIVI',)+lines)))
        drawings.append((name,p))
    # Enlarged nearest-neighbor contact sheet with filename captions.
    cw,ch,cols=210,166,5
    height=((len(drawings)+cols-1)//cols)*ch
    sheet=[[(236,239,242)]*(cols*cw) for _ in range(height)]
    for i,(name,p) in enumerate(drawings):
        x=(i%cols)*cw
        y=(i//cols)*ch
        enlarged=scale(p,4)
        for j,row in enumerate(enlarged):
            sheet[y+5+j][x+41:x+169]=row
        caption=name.removeprefix('CIVI ').removesuffix('.vi').upper()
        for j,line in enumerate(textwrap.wrap(caption,32)):
            text(sheet,line,x+(cw-(4*len(line)-1))//2,y+140+8*j,(35,40,47))
    png(OUT/'preview.png',sheet)
    with (OUT/'manifest.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(('VI','PNG','Icon text'))
        writer.writerows(rows)
    (OUT/'README.md').write_text(
        '# CIVI radio icons\n\n'
        '23 complete 32x32 RGB PNG icons, one per VI, without outer whitespace. '
        + design + '\n\n'
        'READ and SET distinguish the APIs. EX marks examples, OLD marks legacy '
        'read VIs, and EX-OLD marks the legacy read example. See manifest.csv.\n\n'
        'These PNGs include all text. Clear existing icon text, templates and '
        'user artwork before importing to avoid overlapping the new icon. '
        'This package does not modify the VI files. preview.png is an enlarged '
        'contact sheet, not an importable VI icon.\n\n'
        f'Regenerate using ../{generator} (Python standard library only).\n',
        encoding='utf-8')
    archive=OUT.parent/archive_name
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()):
            if p.is_file():
                z.write(p,p.name)
    assert len({(OUT/(name[:-3]+'.png')).read_bytes() for name in LABELS})==23
    print(f'Validated {len(rows)} unique icons, 32x32 each; all VI files covered.')
    print(archive)

if __name__=='__main__':
    main()
