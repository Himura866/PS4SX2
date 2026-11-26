#!/usr/bin/env python3
"""Static negative cases: no GP4 inputs are emitted from corrupted or partial Image0."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import argparse

src=Path(__file__).with_name('v15-preflight-gp4-from-exact-app0.py')
sp=importlib.util.spec_from_file_location('gp4',src)
mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
parser=argparse.ArgumentParser()
parser.add_argument('--stage',required=True,type=Path,help='Verified Image0 stage from owner backup')
original=parser.parse_args().stage.resolve()
if not original.is_dir():raise SystemExit('Verified stage missing; no tests run')
with tempfile.TemporaryDirectory() as d:
 t=Path(d)
 valid=t/'valid'
 shutil.copytree(original,valid)
 manifest=mod.make(valid,t/'accepted')
 assert manifest['file_count']==15
 assert (t/'accepted'/'files-gp4.txt').is_file()
 try: mod.make(valid,t/'accepted')
 except ValueError: pass
 else: raise AssertionError('Output overwrite not blocked')
 cases=[('eboot.bin','corrupted executable'),('sce_sys/param.sfo','corrupted SFO'),('sce_sys/icon0.png','corrupted icon'),('stacktest.nro','missing file'),('sce_module/libc.prx','corrupted module'),('gputest.nro','corrupted NRO'),('sce_sys/keystone','changed keystone'),('symbols.zst','corrupted symbols')]
 for ix,(name,label) in enumerate(cases):
  bad=t/('bad'+str(ix));shutil.copytree(original,bad)
  p=bad/name
  if name=='stacktest.nro':p.unlink()
  else:
   with p.open('r+b') as f:
    f.seek(17);old=f.read(1);f.seek(17);f.write(bytes([old[0]^1]))
  dest=t/('should-not-exist'+str(ix))
  try:mod.make(bad,dest)
  except ValueError as exc:
   assert not dest.exists(),label
   print('PASS FAIL-CLOSED:',label)
  else:raise AssertionError('FAILED CASE '+label)
print('PASS: complete stage, output collision, four malformed inputs; no PKG emitted')
