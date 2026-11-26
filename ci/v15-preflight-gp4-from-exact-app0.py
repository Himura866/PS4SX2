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

# Baseline bytes for *every* app0 member from the user's verified export.
# Prevent mixing DLL/PRX, NRO or symbols from different versions.
BASELINE_HASHES = {
 'blocks.nro': '26d16ab4859293142ee2f50857e9b047097d210eb42d16a87a336ba295c79ea1',
 'breakout.nro': '97b4706f170950591a1f622d49ed916b2078ff91d3926631bf88829d09843bf8',
 'eboot.bin': SOURCE_EBOOT_SHA,
 'gputest.nro': 'd692a092b41174b2b9fa327a5180d081e6a0f5087eb01c3f3950f93a206d92a8',
 'hello.nro': '6459e564187297422095d77198f90492a29584236fd330439f00db0c423f7ecb',
 'nativetest.nro': '3fc94c16b8595ab33ac9acb2c9d0e71d1114e87be06dcd991fda8f782dc0bd80',
 'nativetest_gnu.nro': '653c0bd752cbab1860671ee28f578df667c572fa1a5501cbaa9155ca516d3d31',
 'padtest.nro': '815364529fc7f0b305114df08db9f396d862424b9d8007c479876997f7db910c',
 'sce_module/libSceFios2.prx': 'e703abbabb85468f3e127541825fda500ab3b4f22208a9296b5685ca35df6d3d',
 'sce_module/libc.prx': '3f953833539ec5f1e34f56900389203c3448f2c2bc6af242855760af54c7c8a3',
 'sce_sys/icon0.png': SOURCE_ICON_SHA,
 'sce_sys/keystone': 'd09eb8ab5f3b700164fc8ad85c54c2acbad71244e942aeedf7e3e7eb56408aac',
 'sce_sys/param.sfo': SOURCE_SFO_SHA,
 'stacktest.nro': '67aad1b2b4164f89c4ecc511e10279cf066ffbbdafa63345432b310fba83bead',
 'symbols.zst': '792375292f844ec4afb87a76217e38e672eda4f14541bcdbae29900ee58e22a7',
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
 if set(BASELINE_HASHES)!=EXPECTED:raise ValueError('STOP: internal baseline manifest missing entries')
 for name, expected_sha in BASELINE_HASHES.items():
  if sha(stage/name)!=expected_sha:raise ValueError('STOP: baseline SHA-256 mismatch: '+name)
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
