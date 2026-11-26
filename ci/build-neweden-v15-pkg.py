#!/usr/bin/env python3
"""Experimental 04.89 GP4 -> PS4 PKG builder. NEVER a V15 UI completion claim."""
import argparse, hashlib, importlib.util, json, shutil, subprocess, tempfile
from pathlib import Path

CONTENT_ID='IV0000-EDNP00001_00-EDENPS4000000000'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def run(args):
    if not args.allow_experimental: raise ValueError('V15 runtime UI not integrated; explicit --allow-experimental needed')
    image=args.image0.absolute()
    if not image.is_dir(): raise ValueError('Image0 missing')
    if args.out.exists(): raise ValueError('Refusing to overwrite PKG output')
    for tool in [args.create_gp4,args.pkgtool]:
        if not Path(tool).is_file(): raise ValueError('OpenOrbis executable missing: '+tool)
    spec=importlib.util.spec_from_file_location('preflight',Path(__file__).with_name('v15-preflight-gp4-from-exact-app0.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory(prefix='v15-experimental-') as temp:
        tmp=Path(temp)
        report=mod.make(image,tmp/'gp4-audit')
        assert report['file_count']==15
        stage=tmp/'Image0';shutil.copytree(image,stage)
        # Preserve the exact R13 external PS4 cover; NOT an internal UI asset.
        # A R13 external PS4 icon is mandatory for this experiment; the menu art is separate.
        from PIL import Image, ImageOps
        icon_src=Path(args.r13_icon).resolve(strict=True)
        approved_sha='ec00188208f4a949d492b2ce665a4a52626206ea9c728d771f1dc3510b27a778'
        if sha(icon_src)!=approved_sha: raise ValueError('R13 external icon source hash mismatch')
        with Image.open(icon_src) as src:
            icon_image=ImageOps.fit(src.convert('RGB'),(512,512),Image.Resampling.LANCZOS)
            icon_image.save(stage/'sce_sys'/'icon0.png',format='PNG',optimize=True)
        r13_icon_hash=sha(stage/'sce_sys'/'icon0.png')
        gp4=tmp/'experimental.gp4'
        files=' '.join(record['path'] for record in report['files'])
        subprocess.run([str(Path(args.create_gp4).resolve()),'-out',str(gp4),'--content-id='+CONTENT_ID,'--files',files],cwd=stage,timeout=180,check=True)
        if not gp4.is_file() or gp4.stat().st_size<100: raise ValueError('GP4 output missing/invalid')
        generated=tmp/'packages';generated.mkdir()
        subprocess.run([str(Path(args.pkgtool).resolve()),'pkg_build',str(gp4),str(generated)],cwd=stage,timeout=1800,check=True)
        candidates=list(generated.glob('*.pkg'))
        if len(candidates)!=1 or candidates[0].stat().st_size<5_000_000: raise ValueError('No PS4 PKG produced')
        with candidates[0].open('rb') as f:
            if f.read(4)!=bytes((0x7f,))+b'CNT': raise ValueError('Not a PS4 PKG header')
        # Parse and validate internal PKG digests with the real LibOrbisPkg tool.
        subprocess.run([str(Path(args.pkgtool).resolve()),'pkg_validate',str(candidates[0])],cwd=stage,timeout=600,check=True)
        args.out.mkdir(parents=True)
        dest=args.out/'HIMURA-V15-EXPERIMENTAL-NAO-INSTALAR.pkg'
        shutil.copyfile(candidates[0],dest)
        manifest={'status':'EXPERIMENTAL PKG STRUCTURE ONLY, NOT PLAYSTATION-TESTED','sha256':sha(dest),
                  'content_id':CONTENT_ID,'size':dest.stat().st_size,
                  'r13_external_icon_sha256':r13_icon_hash,
                  'known_missing':['runtime R13 wallpaper','V15 functional menu','PT-BR complete','PS4 boot test']}
        (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+chr(10))
        return manifest
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--image0',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--create-gp4',required=True);p.add_argument('--pkgtool',required=True)
    p.add_argument('--allow-experimental',action='store_true')
    p.add_argument('--r13-icon',required=True,help='REQUIRED: verified R13 WebP external icon; never used as an internal menu background')
    a=p.parse_args()
    try: print(json.dumps(run(a),indent=2))
    except (ValueError,FileNotFoundError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
        p.exit(2,'FAIL CLOSED: '+str(e)+'\\n')
if __name__=='__main__':main()
