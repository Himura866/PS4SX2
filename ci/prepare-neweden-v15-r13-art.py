#!/usr/bin/env python3
"""Stage EXACT R13-approved external icon. The R13 menu screenshot contains FAKE buttons, and is REFERENCE-ONLY."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from PIL import Image, ImageOps

ICON_SHA='ec00188208f4a949d492b2ce665a4a52626206ea9c728d771f1dc3510b27a778'
MENU_SHA='b36c6a9eb5af0ee280c52845c91ca2f3a04b68e79d4f85b620bba9c25705b058'

def verified(path, digest):
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise ValueError('STOP: original R13 asset missing or changed: '+str(path))
    return path

def prepare(assets, out):
    icon=verified(assets/'r11-approved-icon.webp',ICON_SHA)
    menu=verified(assets/'r11-approved-menu.webp',MENU_SHA)
    if out.exists():
        raise ValueError('STOP: destination already exists; no overwrite')
    with Image.open(icon) as src:
        image=ImageOps.fit(src.convert('RGB'),(512,512),Image.Resampling.LANCZOS)
    with Image.open(menu) as src:
        if src.width<1280 or src.height<720:
            raise ValueError('STOP: R13 composite smaller than expected')
    (out/'external-ps4').mkdir(parents=True)
    (out/'reference-only').mkdir()
    external=out/'external-ps4'/'icon0.png'
    image.save(external,format='PNG',optimize=True)
    shutil.copyfile(menu,out/'reference-only'/'R13_ORIGINAL_COMPOSITE_NOT_WALLPAPER.webp')
    manifest={
      'name':'HIMURA SWITCH PS4 V15',
      'base':'New Eden 04.89 / EDNP00001',
      'art_source_branch':'himura-switch-r13-stability-staging',
      'external_icon_input_sha256':ICON_SHA,
      'r13_menu_composite_sha256':MENU_SHA,
      'icon0_png_sha256':hashlib.sha256(external.read_bytes()).hexdigest(),
      'icon0_usage':'PS4 application tile only - never use as emulator menu background',
      'menu_art_status':'REFERENCE ONLY - screenshot contains printed fake top buttons, sample game covers and footer hints',
      'runtime_wallpaper_ready':False,
      'ps4_pkg_ready':False
    }
    (out/'manifest-r13-v15.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--assets',type=Path,default=Path(__file__).resolve().parent.parent/'assets')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    print(prepare(args.assets,args.out))
    print('SAFE: icon staged; menu composite quarantined. NOT A PKG.')
