#!/usr/bin/env python3
"""Fail-closed V15 OpenOrbis GP4 input manifest for EXACT New Eden 04.89.

Creates only a verified file-list/manifest for OpenOrbis create-gp4. Never creates a
PKG, signs an ELF, mutates the original installation or claims the UI is complete.
"""
import argparse
from pathlib import Path
import json
import hashlib
import struct

SOURCE_EBOOT_SHA = 'bab383c0271c2a7a3efa119c5e25b73459ad06d79c848f7d1c147e288e45bb6b'
SOURCE_SFO_SHA = '9bfff1385d1cd7593825090616e4a0c198b7f0fb69a9ceaedb3e3eaf732f9c54'
SOURCE_ICON_SHA = 'a91ec10529ee9f371d7657dd6bb09ef5c0cc4d21ef72fdd114f44d9528ccb9f8'
EXPECTED_CONTENT_ID = 'IV0000-EDNP00001_00-EDENPS4000000000'
EXPECTED = {
 'blocks.nro', 'breakout.nro', 'eboot.bin', 'gputest.nro', 'hello.nro',
 'nativetest.nro', 'nativetest_gnu.nro', 'padtest.nro',
 'sce_module/libSceFios2.prx', 'sce_module/libc.prx',
 'sce_sys/keystone', 'sce_sys/param.sfo', 'sce_sys/icon0.png',
 'stacktest.nro', 'symbols.zst',
}

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while chunk:=f.read(1024*1024): h.update(chunk)
 return h.hexdigest()

def sfo(path):
 raw=path.read_bytes()
 if raw[:4]!=b'\0PSF' or len(raw)<20: raise ValueError('Invalid param.sfo')
 _, _, keybase, database, n=struct.unpack_from('<4sIIII',raw)
 if n>128: raise ValueError('SFO entries limit')
 fields={}
 for i in range(n):
  index=20+16*i
  if index+16>len(raw): raise ValueError('Invalid SFO index')
  ko, typ, length, maximum, valoff=struct.unpack_from('<HHIII',raw,index)
  key_start=keybase+ko
  val_start=database+valoff
  if key_start>=len(raw) or length>len(raw)-val_start: raise ValueError('SFO offset invalid')
  key_end=raw.find(b'\0',key_start)
  if key_end<0: raise ValueError('SFO unterminated key')
  key=raw[key_start:key_end].decode('utf-8')
  if typ==0x0204:fields[key]=raw[val_start:val_start+length].rstrip(b'\0').decode('utf-8')
 return fields

def make(stage, dest):
 stage=stage.resolve()
 if dest.exists():raise ValueError('STOP: destination already exists; no overwrite')
 if not stage.is_dir():raise ValueError('STOP: app0 stage is missing')
 if stage.is_symlink():raise ValueError('STOP: stage cannot be a symlink')
 allpaths=[p for p in stage.rglob('*') if p.is_file()]
 if any(p.is_symlink() for p in stage.rglob('*')):raise ValueError('STOP: unexpected symbolic link')
 names={p.relative_to(stage).as_posix() for p in allpaths}
 if names!=EXPECTED:raise ValueError('STOP: image0 file list differs: '+repr(sorted(names^EXPECTED)))
 if sha(stage/'eboot.bin')!=SOURCE_EBOOT_SHA:raise ValueError('STOP: wrong experimental eboot')
 if sha(stage/'sce_sys/param.sfo')!=SOURCE_SFO_SHA:raise ValueError('STOP: wrong original SFO')
 if sha(stage/'sce_sys/icon0.png')!=SOURCE_ICON_SHA:raise ValueError('STOP: wrong original icon')
 f=sfo(stage/'sce_sys/param.sfo')
 for k,exp in [('APP_VER','04.89'),('TITLE_ID','EDNP00001'),('CONTENT_ID',EXPECTED_CONTENT_ID)]:
  if f.get(k)!=exp:raise ValueError('STOP: '+k+' mismatch')
 files=[dict(path=n,size=(stage/n).stat().st_size,sha256=sha(stage/n)) for n in sorted(names)]
 manifest={
  'status':'GP4 PREPARED - NO PKG BUILT - NOT FOR INSTALLATION',
  'base':'New Eden 04.89',
  'personalization':'HIMURA SWITCH PS4 V15 (INCOMPLETE EXPERIMENT)',
  'technical_content_id':EXPECTED_CONTENT_ID,
  'emulator_title_id':'EDNP00001',
  'sfo':f,
  'image0':str(stage),
  'file_count':len(files),
  'files':files,
  'must_not_publish_until':['R13 icon integrated','R13 wallpaper minimally cleaned','real toolbar/carousel','News & Themes actions removed','all UI in pt-BR','credits','OpenOrbis PS4 PKG build verified','PS4 hardware boot and Silksong regressions'],
  'gp4_build_command_example':'cd IMAGE0 && create-gp4 -out ../HIMURA-V15-EXPERIMENTAL.gp4 --content-id='+EXPECTED_CONTENT_ID+' --files "$(cat ../files-gp4.txt)"',
  'pkg_build_command_example':'cd IMAGE0 && PkgTool.Core pkg_build ../HIMURA-V15-EXPERIMENTAL.gp4 .',
 }
 dest.mkdir(parents=True)
 (dest/'manifest-v15-gp4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 (dest/'files-gp4.txt').write_text(' '.join(sorted(names))+'\n')
 (dest/'READ-ME-FIRST.txt').write_text('HIMURA V15: manifest only. No valid PKG generated. Do NOT install or replace EDNP00001.\n')
 return manifest

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--stage',required=True,type=Path);a.add_argument('--out',required=True,type=Path)
 o=a.parse_args();r=make(o.stage,o.out)
 print('PASS: GP4 preflight inputs match exact New Eden 04.89; '+str(r['file_count'])+' files')
 print('STOP: No GP4/PKG built. Existing New Eden installation must not be modified.')
