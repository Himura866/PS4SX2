#!/usr/bin/env python3
"""HIMURA V15: stage a *non-installable* PS4 Image0 candidate from exact owner files.

Fails closed: never edits the original PKG/app0/eboot, never signs/creates a PKG.
Do not distribute output as a working app. To ship a test PKG, a verified PS4
packaging toolchain AND functional UI changes and on-console tests are needed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import tempfile
import zipfile

BASE = 'EDNP00001-app0/'
SOURCE_ZIP_SHA = '66e8154774498ce8bd30bde0af36b561cebd6f24ef2d3cdaabafa7ff9a16ec02'
ORIGINAL_PKG_SHA = '06e4bc0538b5217ed5c539c12403bd808131e5d50c96315b2840911170939ccd'
ORIGINAL_EBOOT_SHA = '5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381'
EXPERIMENTAL_EBOOT_SHA = 'bab383c0271c2a7a3efa119c5e25b73459ad06d79c848f7d1c147e288e45bb6b'
ORIGINAL_SFO_SHA = '9bfff1385d1cd7593825090616e4a0c198b7f0fb69a9ceaedb3e3eaf732f9c54'
ORIGINAL_ICON_SHA = 'a91ec10529ee9f371d7657dd6bb09ef5c0cc4d21ef72fdd114f44d9528ccb9f8'
EXPECTED_FILES = {
    'blocks.nro', 'breakout.nro', 'eboot.bin', 'gputest.nro', 'hello.nro',
    'nativetest.nro', 'nativetest_gnu.nro', 'padtest.nro',
    'sce_module/libSceFios2.prx', 'sce_module/libc.prx',
    'sce_sys/keystone', 'stacktest.nro', 'symbols.zst',
}
META_OFFSETS = {'param.sfo': (0x47f0, 1076), 'icon0.png': (0x6c30, 59196)}

def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def require_hash(path, expected, label):
    p=Path(path)
    if not p.is_file() or sha(p)!=expected:
        raise ValueError(f'STOP: {label} faltando ou nao corresponde ao original verificado')
    return p

def load_safety(path):
    spec=importlib.util.spec_from_file_location('v15_safety_for_stage', str(path))
    if spec is None or spec.loader is None:
        raise ValueError('STOP: validador ausente')
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def verify_pkg_assets(pkg, sfo, icon):
    # Metadata table offsets verified from the user's exact New Eden-04.89.pkg.
    with pkg.open('rb') as fd:
        for name, fpath in [('param.sfo', sfo), ('icon0.png', icon)]:
            offset, size = META_OFFSETS[name]
            if fpath.stat().st_size != size:
                raise ValueError('STOP: metadata PS4 com tamanho incorreto: '+name)
            fd.seek(offset)
            if fd.read(size) != fpath.read_bytes():
                raise ValueError('STOP: '+name+' nao corresponde ao PKG original')
    raw=sfo.read_bytes()
    if raw[:4] != b'\x00PSF':
        raise ValueError('STOP: param.sfo com assinatura incorreta')
    _, _, keybase, datbase, n=struct.unpack_from('<4sIIII',raw)
    fields={}
    if n>256: raise ValueError('STOP: SFO com indice invalido')
    for i in range(n):
        off=20+16*i
        if off+16>len(raw): raise ValueError('STOP: SFO incompleto')
        keyoff, t, sz, maxsize, valoff=struct.unpack_from('<HHIII',raw,off)
        key_start=keybase+keyoff
        if key_start>=len(raw) or datbase+valoff+sz>len(raw): raise ValueError('STOP: offset SFO invalido')
        end=raw.find(b'\0',key_start)
        if end<0: raise ValueError('STOP: entrada SFO sem terminador')
        key=raw[key_start:end].decode('utf-8')
        if t==0x0204:
            fields[key]=raw[datbase+valoff:datbase+valoff+sz].rstrip(b'\0').decode('utf-8')
    for k,v in [('TITLE_ID','EDNP00001'),('APP_VER','04.89'),
                ('CONTENT_ID','IV0000-EDNP00001_00-EDENPS4000000000')]:
        if fields.get(k)!=v: raise ValueError(f'STOP: metadado {k} divergente')
    return fields

def zip_entries_checked(archive):
    files={}
    total=0
    for info in archive.infolist():
        path=PurePosixPath(info.filename)
        if not info.filename.startswith(BASE) or path.is_absolute() or '..' in path.parts or '\\' in info.filename:
            raise ValueError('STOP: caminho ZIP suspeito: '+info.filename)
        sub=info.filename[len(BASE):]
        if not sub or info.is_dir(): continue
        if sub in files: raise ValueError('STOP: membro duplicado no ZIP: '+sub)
        if (info.external_attr>>16)&0o170000 == 0o120000:
            raise ValueError('STOP: link simbolico inesperado')
        total+=info.file_size
        if total>110_000_000 or info.file_size>85_000_000:
            raise ValueError('STOP: tamanho expandido fora do esperado')
        files[sub]=info
    if set(files)!=EXPECTED_FILES:
        raise ValueError('STOP: conteudo app0 difere da exportacao auditada '+repr(sorted(set(files)^EXPECTED_FILES)))
    if files['eboot.bin'].file_size != 78_376_440:
        raise ValueError('STOP: eboot incorreto dentro do ZIP')
    return files

def prepare(args):
    original=require_hash(args.original_eboot, ORIGINAL_EBOOT_SHA, 'eboot original')
    edited=require_hash(args.experimental_eboot, EXPERIMENTAL_EBOOT_SHA, 'eboot PT-BR experimental')
    pkg=require_hash(args.pkg, ORIGINAL_PKG_SHA, 'PKG original')
    archive_path=require_hash(args.app0_zip, SOURCE_ZIP_SHA, 'ZIP app0')
    sfo=require_hash(args.param_sfo, ORIGINAL_SFO_SHA, 'param.sfo')
    icon=require_hash(args.icon, ORIGINAL_ICON_SHA, 'icone original')
    safety=load_safety(args.safety_script)
    safety.require_original(original,pkg)
    safety_report=safety.verify_experimental(original,edited,args.patch_script)
    sfo_fields=verify_pkg_assets(pkg,sfo,icon)
    dest=args.stage.resolve()
    if dest.exists(): raise FileExistsError('STOP: pasta de destino existente; sem sobrescrita')
    if dest.parent != dest and not dest.parent.exists(): dest.parent.mkdir(parents=True)
    with zipfile.ZipFile(archive_path) as z:
        if z.testzip() is not None:
            raise ValueError('STOP: CRC invalido no ZIP original')
        entries=zip_entries_checked(z)
        if hashlib.sha256(z.read(BASE+'eboot.bin')).hexdigest()!=ORIGINAL_EBOOT_SHA:
            raise ValueError('STOP: eboot da exportacao nao confere com original')
        with tempfile.TemporaryDirectory(prefix='.v15-stage-', dir=dest.parent) as tmp:
            root=Path(tmp)/'image0'
            root.mkdir()
            for name,entry in sorted(entries.items()):
                target=root.joinpath(*PurePosixPath(name).parts)
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(entry,'r') as src, target.open('wb') as out:
                    shutil.copyfileobj(src,out)
                if target.stat().st_size!=entry.file_size:
                    raise ValueError('STOP: extracao incompleta: '+name)
            shutil.copyfile(edited,root/'eboot.bin')
            shutil.copyfile(sfo,root/'sce_sys'/'param.sfo')
            shutil.copyfile(icon,root/'sce_sys'/'icon0.png')
            if sha(root/'eboot.bin')!=EXPERIMENTAL_EBOOT_SHA:
                raise ValueError('STOP: arquivo experimental alterado apos copia')
            files={p.relative_to(root).as_posix(): {'size':p.stat().st_size,'sha256':sha(p)}
                   for p in sorted(root.rglob('*')) if p.is_file()}
            if set(files) != EXPECTED_FILES|{'sce_sys/param.sfo','sce_sys/icon0.png'}:
                raise ValueError('STOP: faltam arquivos do Image0')
            report={
                'status':'IMAGE0 EXPERIMENTAL â NAO INSTALAR; NAO EH PKG',
                'original':'New Eden 04.89 / EDNP00001',
                'label':'HIMURA SWITCH PS4 V15 â apenas rotulos experimentais',
                'original_pkg_sha256':ORIGINAL_PKG_SHA,
                'experimental_eboot_sha256':EXPERIMENTAL_EBOOT_SHA,
                'metadata':sfo_fields,
                'original_icon_still_present':True,
                'text_patch':safety_report,
                'staged_files':files,
                'cannot_release_pkg_without':[
                    'arte externa aprovada integrada em icon0.png',
                    'integracao funcional do menu samurai/carrossel/botoes superiores',
                    'remocao real de News/Temas da navegacao e traducao integral',
                    'creditos V15 em Sobre',
                    'empacotamento e assinatura PS4 verificados para este ELF',
                    'testes de inicializacao, FPS, jogos e estabilidade no PS4 Pro',
                ],
                'unchanged_original':True,
            }
            out=Path(tmp)/'manifest-v15-stage.json'
            out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            tmpdest=Path(tmp)
            # TemporaryDirectory cleanup would delete staged data, so atomically move.
            os.replace(str(tmpdest),str(dest))
            return dest/'manifest-v15-stage.json'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('original_eboot','experimental_eboot','pkg','app0_zip','param_sfo','icon','safety_script','patch_script','stage'):
        ap.add_argument('--'+name.replace('_','-'), type=Path, required=True)
    a=ap.parse_args()
    result=prepare(a)
    print('PASS: imagem0 experimental montada: '+str(result))
    print('STOP: NAO EH PKG INSTALAVEL e NAO eh a V15 com menu integrado')
if __name__=='__main__': main()
