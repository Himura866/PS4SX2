#!/usr/bin/env python3
"""HIMURA SWITCH PS4 R11 original PS4 XMB branding.
Creates artwork for the build checkout only; no Nintendo copyrighted assets.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import sys

def font(px, bold=True):
    names = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf")
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, px)
    return ImageFont.load_default()

def blend(rgb, a, b, f):
    return tuple(int(a[i] * (1-f) + b[i]*f) for i in range(3))

def scene(w, h, icon=False):
    image = Image.new("RGB", (w,h))
    p = image.load()
    for y in range(h):
        t=y/max(1,h-1)
        color=blend(None,(6,10,22),(57,8,22),t)
        for x in range(w): p[x,y]=color
    d=ImageDraw.Draw(image, "RGBA")
    scale = w / (512 if icon else 1920)
    def xy(a): return round(a*scale)
    def rect(b, fill, radius=0, outline=None, width=1):
        box=tuple(xy(v) for v in b)
        d.rounded_rectangle(box,radius=xy(radius),fill=fill,outline=outline,width=max(1,xy(width)))
    def ellipse(b, fill, outline=None, width=1):
        d.ellipse(tuple(xy(v) for v in b), fill=fill, outline=outline,width=max(1,xy(width)))
    def poly(points, fill): d.polygon([(xy(x),xy(y)) for x,y in points],fill=fill)
    def line(points, fill, width):
        d.line([(xy(x),xy(y)) for x,y in points],fill=fill,width=max(1,xy(width)),joint="curve")
    if icon:
        ellipse((270,25,530,285),(208,17,39,95))
        ellipse((300,55,500,255),(221,27,52,100))
        # original samurai silhouette
        poly([(295,95),(330,65),(382,82),(410,124),(395,240),(305,250)],(8,11,21,235))
        poly([(285,160),(415,160),(458,353),(245,353)],(13,17,31,255))
        poly([(305,107),(378,104),(411,147),(290,151)],(5,8,19,255))
        line([(300,170),(386,170)],(231,34,51,200),5)
        # left red and right blue controllers
        rect((28,232,125,432),(233,49,66,245),36)
        rect((386,232,484,432),(30,133,220,245),36)
        ellipse((63,265,91,293),(14,22,36,255))
        ellipse((421,265,449,293),(12,28,48,255))
        for px,py in [(66,340),(89,340),(425,340),(447,340)]:
            ellipse((px-8,py-8,px+8,py+8),(12,19,28,255))
        rect((30,435,483,501),(6,10,24,237),16,outline=(197,33,51,255),width=2)
        d.text((xy(256),xy(444)),"HIMURA",font=font(xy(26)),anchor="mt",fill=(255,255,255,255),stroke_width=max(1,xy(1)),stroke_fill=(60,7,20))
        d.text((xy(256),xy(477)),"SWITCH PS4",font=font(xy(16)),anchor="mt",fill=(255,90,100,255))
    else:
        ellipse((1270,85,1840,655),(189,17,44,80))
        ellipse((1350,160,1770,580),(220,27,48,115))
        # samurai on the right does not cover the HIMURA text
        poly([(1380,230),(1520,120),(1620,175),(1700,260),(1670,495),(1340,500)],(8,11,22,245))
        poly([(1250,485),(1710,485),(1840,1020),(1130,1020)],(9,13,26,255))
        poly([(1320,250),(1710,250),(1690,295),(1300,295)],(5,8,18,255))
        line([(1360,355),(1640,355)],(241,47,66,230),12)
        line([(1330,650),(1750,295)],(246,239,229,190),10)
        line([(1320,660),(1760,300)],(255,38,62,170),19)
        # Torii ornamental motif in lower right
        rect((1560,828,1580,1020),(7,11,20,255))
        rect((1740,828,1760,1020),(7,11,20,255))
        rect((1515,790,1810,816),(189,21,43,255),5)
        # original graphic controllers around wordmark
        rect((120,430,238,720),(233,49,66,247),45)
        rect((585,430,703,720),(34,145,220,247),45)
        ellipse((160,490,204,534),(13,22,40,255))
        ellipse((625,490,669,534),(13,22,40,255))
        for px,py in [(165,590),(196,590),(630,590),(661,590)]:
            ellipse((px-10,py-10,px+10,py+10),(7,13,22,255))
        rect((245,495,578,655),(7,12,26,245),28,outline=(128,37,59,220),width=3)
        d.text((xy(415),xy(495)),"HIMURA",font=font(xy(55)),anchor="mt",fill=(255,255,255,255))
        d.text((xy(415),xy(573)),"SWITCH PS4",font=font(xy(34)),anchor="mt",fill=(255,68,86,255))
        line([(80,875),(900,875)],(237,47,67,225),5)
        d.text((xy(92),xy(898)),"R11  |  SAMURAI EDITION",font=font(xy(33)),fill=(238,238,242,255))
    return image

def main():
    if len(sys.argv)!=2: raise SystemExit("Usage: generate-r11-branding.py <Eden4 checkout>")
    out=Path(sys.argv[1]).resolve()/"branding"
    out.mkdir(parents=True,exist_ok=True)
    icon=scene(512,512,True)
    backdrop=scene(1920,1080,False)
    icon.save(out/"icon0.png",optimize=True)
    backdrop.save(out/"pic1.png",optimize=True)
    print("R11: generated independent PS4 XMB icon and 1080p background:",out)

if __name__=="__main__":
    main()
