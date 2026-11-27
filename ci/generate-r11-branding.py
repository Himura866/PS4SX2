#!/usr/bin/env python3
"""R11 artwork: package the actual samurai icon and library picture approved by the owner.

Never redraw surrogate Joy-Cons or placeholder soldiers; fail early when art is
missing. The source WebPs are near-lossless uploads from the two approved images.
The runtime menu picture is distinct from sce_sys/pic1.png (PS4 XMB wallpaper).
"""
from pathlib import Path
import hashlib
import sys
from PIL import Image, ImageOps, ImageFilter, ImageEnhance, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
ASSETS=ROOT/"assets"
ICON_SHA="ec00188208f4a949d492b2ce665a4a52626206ea9c728d771f1dc3510b27a778"
MENU_SHA="b36c6a9eb5af0ee280c52845c91ca2f3a04b68e79d4f85b620bba9c25705b058"

def verified(path, sha):
    if not path.is_file():
        raise RuntimeError(f"R11 approved artwork MISSING: {path}")
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != sha:
        raise RuntimeError(f"R11 approved artwork checksum mismatch: {path}")
    with Image.open(path) as image:
        return image.convert("RGB")

def main():
    if len(sys.argv)!=2:
        raise SystemExit("Usage: generate-r11-branding.py <pinned Eden4 checkout>")
    out=Path(sys.argv[1]).resolve()/"branding"
    out.mkdir(parents=True,exist_ok=True)
    icon=verified(ASSETS/"r11-approved-icon.webp", ICON_SHA)
    menu=verified(ASSETS/"r11-approved-menu.webp", MENU_SHA)
    icon=ImageOps.fit(icon,(512,512),Image.Resampling.LANCZOS)
    menu=ImageOps.fit(menu,(1920,1080),Image.Resampling.LANCZOS)
    # Derived artwork ONLY. Preserve the SHA-verified source WebP; clean the
    # baked screenshot controls/covers/version from the generated PNG. Use
    # edge-colour interpolation to avoid opaque black masking in the launcher.
    def remove_mock(box, feather=10):
        nonlocal menu
        x0,y0,x1,y1=box
        w,h=x1-x0,y1-y0
        top=menu.crop((x0,y0-1,x1,y0))
        bottom=menu.crop((x0,y1,x1,y1+1))
        fill=Image.new("RGB",(w,h))
        for y in range(h):
            row=Image.blend(top,bottom,(y+1)/(h+1))
            fill.paste(row,(0,y))
        proposal=menu.copy()
        proposal.paste(fill,(x0,y0))
        mask=Image.new("L",menu.size)
        ImageDraw.Draw(mask).rectangle((x0,y0,x1,y1),fill=255)
        mask=mask.filter(ImageFilter.GaussianBlur(feather))
        menu=Image.composite(proposal,menu,mask)
    for box in ((126,427,495,808),(482,439,817,798),
                (807,440,1143,801),(1136,440,1476,798),
                (1467,439,1810,799),(54,571,123,679),
                (1806,570,1885,681),(788,793,1135,859),
                (696,117,838,197),(956,23,1906,190)):
        remove_mock(box)
    # Continue the actual lower landscape to 1080p with a mirror extension;
    # this starts at the last scenery row and avoids a solid black footer.
    footer=ImageOps.flip(menu.crop((0,860,1920,970)))
    menu.paste(footer,(0,970))
    icon.save(out/"icon0.png",optimize=True)
    menu.save(out/"himura-r11-menu.png",optimize=True)

    # Authentic approved icon on the PS4 XMB background, not mock game tiles
    # and not the old pair of isolated controller shapes.
    blurred=ImageOps.fit(icon,(1920,1080),Image.Resampling.BICUBIC)
    blurred=ImageEnhance.Brightness(blurred.filter(ImageFilter.GaussianBlur(65))).enhance(0.28)
    blurred.paste(icon.resize((980,980),Image.Resampling.LANCZOS),((1920-980)//2,50))
    blurred.save(out/"pic1.png",optimize=True)
    print("R11 approved artwork staged:",out)
    print("  PS4 XMB original samurai icon:",out/"icon0.png")
    print("  Interactive menu backdrop:",out/"himura-r11-menu.png")
    print("  PS4 XMB highlight background:",out/"pic1.png")

if __name__=="__main__":
    main()
