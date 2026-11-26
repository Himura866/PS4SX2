#!/usr/bin/env python3
"""Negative regressions: invalid input must fail before stage creation."""
import importlib.util
from pathlib import Path
import shutil
import tempfile

D=Path(__file__).resolve().parent
modspec=importlib.util.spec_from_file_location('stage',D/'prepare-neweden-v15-image0.py')
mod=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(mod)
class Opt: pass
root=Path('/mnt/data')
args=Opt()
args.original_eboot=root/'neweden_0489_inspect'/'eboot.bin'
args.experimental_eboot=root/'HIMURA_NEWEDEN_V15_ETAPA02'/'output'/'eboot-V15-PTBR-EXPERIMENTAL-NAO-INSTALAR.bin'
args.pkg=root/'NewEden-04.89.pkg'
args.app0_zip=root/'EDNP00001-app0.zip'
args.param_sfo=root/'neweden_pkg_analysis'/'param.sfo'
args.icon=root/'neweden_pkg_analysis'/'icon0.png'
args.safety_script=root/'HIMURA_NEWEDEN_V15_ETAPA03'/'ci'/'v15_safety_gate.py'
args.patch_script=root/'HIMURA_NEWEDEN_V15_ETAPA03'/'ci'/'patch_v15_ptbr_labels.py'
with tempfile.TemporaryDirectory() as tm:
    td=Path(tm)
    cases=[('PKG com hash errado','pkg'),('eboot com hash errado','original_eboot'),
           ('icone diferente do original','icon'),('SFO divergente','param_sfo'),
           ('patch com bytes inesperados','experimental_eboot')]
    for i,(title,attr) in enumerate(cases):
        saved=getattr(args,attr)
        p=td/(attr+str(i)+'.bin')
        with p.open('wb') as target, saved.open('rb') as source:
            shutil.copyfileobj(source,target)
        with p.open('r+b') as target:
            target.seek(10);old=target.read(1);target.seek(10);target.write(bytes([old[0]^1]))
        setattr(args,attr,p)
        args.stage=td/('should_not_exist'+str(i))
        try:
            mod.prepare(args)
        except (ValueError,FileNotFoundError) as exc:
            assert not args.stage.exists(), title
            print('PASS negative:',title, '->',str(exc)[:100])
        else: raise AssertionError('Gate accepted corrupt input: '+title)
        finally: setattr(args,attr,saved)
print('PASS: 5 negative gates; no staging from corrupted inputs')
