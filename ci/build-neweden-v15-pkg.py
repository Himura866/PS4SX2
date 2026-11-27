#!/usr/bin/env python3
"""Experimental 04.89 GP4 -> PS4 PKG builder. NEVER a V15 UI completion claim."""
import argparse, hashlib, importlib.util, json, shutil, subprocess, tempfile
from pathlib import Path
from xml.etree import ElementTree

CONTENT_ID='IV0000-EDNP00001_00-EDENPS4000000000'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def validate_gp4_sources(gp4, stage, expected_paths, content_id=CONTENT_ID):
    """Confirm LibOrbisPkg will find every file relative to the GP4's folder.

    PfsProperties.BuildFSTree combines GP4's directory with each orig_path;
    passing a different cwd to PkgTool does NOT fix a misplaced GP4.
    """
    document=ElementTree.parse(gp4)
    root=document.getroot()
    package=root.find("./volume/package")
    if package is None or package.get("content_id")!=content_id:
        raise ValueError("GP4 content ID does not match app0")
    entries=root.findall("./files/file")
    if len(entries)!=len(expected_paths):
        raise ValueError("GP4 file count mismatch")
    if {e.get("targ_path") for e in entries}!=set(expected_paths):
        raise ValueError("GP4 files do not match the verified Image0")
    if gp4.resolve().parent != stage.resolve():
        raise ValueError("GP4 must reside in the stage folder")
    for entry in entries:
        relative=entry.get("orig_path")
        target=entry.get("targ_path")
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ValueError("Unsafe GP4 source path")
        file=(gp4.parent/relative).resolve(strict=True)
        expected=(stage/target).resolve(strict=True)
        if file!=expected or not file.is_file():
            raise ValueError("GP4 orig_path does not resolve to verified image file: "+target)
    return len(entries)

def assert_staged_baseline(report, stage, allow_generated_gp4=False):
    expected={entry['path']:entry['sha256'] for entry in report['files']}
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    if allow_generated_gp4:
        actual.discard('experimental.gp4')  # expected build recipe, not an app0 file
    if set(expected)!=actual:
        raise ValueError('Baseline staging file list changed')
    for name,digest in expected.items():
        if sha(stage/name)!=digest:
            raise ValueError('Baseline staging hash mismatch: '+name)
    return len(expected)

def run(args):
    if not args.allow_experimental: raise ValueError('V15 runtime UI not integrated; explicit --allow-experimental needed')
    if getattr(args, 'boot_fself_experiment', False) and (not args.baseline_original or args.ptbr_labels_experimental):
        raise ValueError('Orbis fSELF probe can wrap ONLY the exact 04.89 original in --baseline-original mode')
    if getattr(args, 'parallel_title_experiment', False) and not (args.baseline_original and args.boot_fself_experiment):
        raise ValueError('Parallel V15 test requires exact 04.89 baseline plus fSELF wrapper')
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
        # PS4 CE failure: the experimental Image0 executable is NOT the exact
        # working New Eden 04.89 eboot that was exported from the user's PS4.
        # Do not make another package from an unverified replacement ELF.
        known_good_eboot='5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381'
        actual_eboot=sha(image/'eboot.bin')
        if actual_eboot != known_good_eboot:
            raise ValueError('BOOT SAFETY STOP: staged eboot differs from proven working New Eden 04.89. '
                             'Rebuild Image0 with exact original app0; refusing another potentially non-booting PKG. '
                             'staged='+actual_eboot+' expected='+known_good_eboot)
        stage=tmp/'Image0';shutil.copytree(image,stage)
        # This is an OPTIONALLY enabled, byte-verified PARTIAL translation.
        # The original 04.89 image was verified by preflight and remains untouched.
        if getattr(args, 'ptbr_labels_experimental', False):
            patch_path = Path(__file__).with_name('v15-ptbr-verified-label-patch.py')
            label_spec = importlib.util.spec_from_file_location('v15_ptbr_labels',patch_path)
            label_mod = importlib.util.module_from_spec(label_spec)
            label_spec.loader.exec_module(label_mod)
            translated = label_mod.patch_bytes((stage/'eboot.bin').read_bytes())
            (stage/'eboot.bin').write_bytes(translated)
            if sha(stage/'eboot.bin') != label_mod.PATCHED_SHA256:
                raise ValueError('PT-BR label patch final hash mismatch')

        # Unmodified 04.89 baseline: keep original executable, SFO and icon.
        if args.baseline_original:
            if args.ptbr_labels_experimental:
                raise ValueError('Baseline cannot apply an eboot text patch')
            assert_staged_baseline(report,stage)
            branded={'title':report['sfo']['TITLE'], 'app_ver':report['sfo']['APP_VER'],
                     'branded_sfo_sha256':sha(stage/'sce_sys'/'param.sfo')}
            r13_icon_hash=None
        else:
            # Rebrand visible title/version ONLY after verifying the original SFO,
            # never the installed app, PS4 title ID, data directory or eboot.
            branded_spec=importlib.util.spec_from_file_location('sfo_brand',Path(__file__).with_name('v15-brand-sfo.py'))
            branded_mod=importlib.util.module_from_spec(branded_spec)
            branded_spec.loader.exec_module(branded_mod)
            branded=branded_mod.patch(stage/'sce_sys'/'param.sfo')
            # Preserve the exact R13 external PS4 cover; NOT an internal UI asset.
            # A R13 external PS4 icon is mandatory for this experiment; the menu art is separate.
            from PIL import Image, ImageOps
            icon_src=Path(args.r13_icon).resolve(strict=True)
            approved_sha='ec00188208f4a949d492b2ce665a4a52626206ea9c728d771f1dc3510b27a778'
            if sha(icon_src)!=approved_sha: raise ValueError('R13 external icon source hash mismatch')
            with Image.open(icon_src) as src:
                icon_image=ImageOps.fit(src.convert('RGB'),(512,512),getattr(Image, 'Resampling', Image).LANCZOS)
                icon_image.save(stage/'sce_sys'/'icon0.png',format='PNG',optimize=True)
            r13_icon_hash=sha(stage/'sce_sys'/'icon0.png')
        # Isolated test identity (HIMU00015) to avoid replacing installed EDNP00001.
        # Runtime files under /data/eden-ps4 may still be shared: NO claim of save
        # isolation, and no user install recommendation without console safeguards.
        parallel_meta = None
        if getattr(args, 'parallel_title_experiment', False):
            clone_spec = importlib.util.spec_from_file_location(
                'v15_sideby', Path(__file__).with_name('v15-sideby-sfo.py'))
            clone_mod = importlib.util.module_from_spec(clone_spec)
            clone_spec.loader.exec_module(clone_mod)
            original_sfo = (stage/'sce_sys'/'param.sfo').read_bytes()
            cloned_sfo = clone_mod.patch(original_sfo)
            (stage/'sce_sys'/'param.sfo').write_bytes(cloned_sfo)
            parallel_meta = {'title':clone_mod.TITLE, 'title_id':clone_mod.TITLE_ID,
                             'content_id':clone_mod.CONTENT_ID, 'app_ver':clone_mod.APP_VER,
                             'sfo_sha256':hashlib.sha256(cloned_sfo).hexdigest(),
                             'runtime_data_isolated':False}
            branded = {'title':clone_mod.TITLE, 'app_ver':clone_mod.APP_VER,
                       'branded_sfo_sha256':parallel_meta['sfo_sha256']}
        active_content_id = parallel_meta['content_id'] if parallel_meta else CONTENT_ID
        # This is an ISOLATED boot-format experiment: OpenOrbis expects a fSELF,
        # but the owner's PS4 FTP app0 export contains a raw ET_SCE_EXEC_ASLR ELF.
        # Wrap only the original ELF, preserving all its loadable segment bytes.
        # Never equate structural fSELF verification to a successful PS4 boot.
        wrapped_info = None
        if getattr(args, 'boot_fself_experiment', False):
            selfspec = importlib.util.spec_from_file_location(
                'v15_fself_wrapper', Path(__file__).with_name('v15-wrap-orbis-fself.py'))
            selfmod = importlib.util.module_from_spec(selfspec)
            selfspec.loader.exec_module(selfmod)
            original_bytes = (stage/'eboot.bin').read_bytes()
            wrapped_bytes, wrapped_info = selfmod.wrap(original_bytes, require_original=True)
            selfmod.validate_wrapper(original_bytes, wrapped_bytes)
            if wrapped_bytes[:4] != selfmod.SELF_MAGIC or wrapped_info['original_elf_sha256'] != known_good_eboot:
                raise ValueError('BOOT PROBE STOP: invalid fSELF or original ELF SHA')
            (stage/'eboot.bin').write_bytes(wrapped_bytes)
            # Independently verify that the OTHER fourteen app0 files were not altered.
            allowed = {entry['path'] for entry in report['files']}
            existing = {p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
            if existing != allowed:
                raise ValueError('BOOT PROBE STOP: extra/missing app0 files')
            for record in report['files']:
                if record['path'] not in ({'eboot.bin', 'sce_sys/param.sfo'} if parallel_meta else {'eboot.bin'}) and sha(stage/record['path']) != record['sha256']:
                    raise ValueError('BOOT PROBE STOP: non-eboot app0 changed: '+record['path'])
            print('BOOT-FSELF-PROBE ' + json.dumps(wrapped_info, sort_keys=True), flush=True)
        # LibOrbisPkg resolves orig_path RELATIVE TO the GP4 location, not cwd.
        # Keep GP4 beside the staged app0 files; exclude it from the explicit file list.
        gp4=stage/'experimental.gp4'
        verified_paths=[record['path'] for record in report['files']]
        files=' '.join(verified_paths)
        subprocess.run([str(Path(args.create_gp4).resolve()),'-out',str(gp4),'--content-id='+active_content_id,'--files',files],cwd=stage,timeout=180,check=True)
        if not gp4.is_file() or gp4.stat().st_size<100: raise ValueError('GP4 output missing/invalid')
        validate_gp4_sources(gp4,stage,verified_paths,active_content_id)
        generated=tmp/'packages';generated.mkdir()
        subprocess.run([str(Path(args.pkgtool).resolve()),'pkg_build',str(gp4),str(generated)],cwd=stage,timeout=1800,check=True)
        if args.baseline_original and not getattr(args, 'boot_fself_experiment', False):
            assert_staged_baseline(report,stage,allow_generated_gp4=True)
        candidates=list(generated.glob('*.pkg'))
        if len(candidates)!=1 or candidates[0].stat().st_size<5_000_000: raise ValueError('No PS4 PKG produced')
        with candidates[0].open('rb') as f:
            if f.read(4)!=bytes((0x7f,))+b'CNT': raise ValueError('Not a PS4 PKG header')
        # Parse and validate internal PKG digests with the real LibOrbisPkg tool.
        subprocess.run([str(Path(args.pkgtool).resolve()),'pkg_validate',str(candidates[0])],cwd=stage,timeout=600,check=True)
        # Inspect real PS4 CNT header and embedded param.sfo in the GENERATED
        # package, not just the trusted Image0. A valid pkg_validate result does
        # not prove that Orbis loader attributes/DRM/PFS are compatible.
        loader_spec = importlib.util.spec_from_file_location(
            'v15_pkg_header_audit', Path(__file__).with_name('v15-ps4-pkg-metadata-diff.py'))
        loader_mod = importlib.util.module_from_spec(loader_spec)
        loader_spec.loader.exec_module(loader_mod)
        loader_meta = loader_mod.read_package(candidates[0])
        loader_expected = {
            'pkg.drm_type': 15,
            'pkg.content_type': 0x1A,
            'pkg.content_flags': 0x0A000000,
            'pkg.content_id': active_content_id,
            'sfo.APP_TYPE': 1,
            'sfo.ATTRIBUTE': 0x00010002,
            'sfo.CATEGORY': 'gd',
            'sfo.TITLE_ID': parallel_meta['title_id'] if parallel_meta else 'EDNP00001',
            'sfo.CONTENT_ID': active_content_id,
        }
        if args.baseline_original:
            loader_expected.update({
                'sfo.APP_VER': parallel_meta['app_ver'] if parallel_meta else '04.89',
                'sfo.VERSION': parallel_meta['app_ver'] if parallel_meta else '04.89',
                'sfo.TITLE': parallel_meta['title'] if parallel_meta else 'New Eden',
            })
        loader_actual = {}
        for key in loader_expected:
            source, field = key.split('.', 1)
            loader_actual[key] = loader_meta['header' if source == 'pkg' else 'sfo'].get(field)
        loader_differences = {
            key: {'original': expected, 'rebuilt': loader_actual[key]}
            for key, expected in loader_expected.items()
            if loader_actual[key] != expected
        }
        print('ORIGINAL-0489-LOADER-METADATA ' +
              json.dumps({'matches_reference': not loader_differences,
                          'differences': loader_differences}, sort_keys=True), flush=True)
        args.out.mkdir(parents=True)
        dest=args.out/'HIMURA-V15-EXPERIMENTAL-NAO-INSTALAR.pkg'
        shutil.copyfile(candidates[0],dest)
        manifest={'status':'EXPERIMENTAL PKG STRUCTURE ONLY, NOT PLAYSTATION-TESTED','sha256':sha(dest),
                  'content_id':active_content_id,'size':dest.stat().st_size,
                  'r13_external_icon_sha256':r13_icon_hash,
                  'packaging_mode':'FSELF_PARALLEL_V15_TITLE_EXPERIMENT' if parallel_meta else ('ORIGINAL_ORBIS_ELF_FSELF_WRAPPED_BOOT_PROBE' if wrapped_info else ('EXACT_ORIGINAL_IMAGE0' if args.baseline_original else 'V15_EXPERIMENT')),
                  'original_image0_unchanged':bool(args.baseline_original and not wrapped_info),
                  'only_original_eboot_container_changed':bool(wrapped_info and not parallel_meta),
                  'fself_wrapper_report':wrapped_info,
                  'parallel_title_metadata':parallel_meta,
                  'display_title':branded['title'],'ps4_app_ver':branded['app_ver'],
                  'sfo_sha256':branded['branded_sfo_sha256'],
                  'working_base_eboot_sha256':known_good_eboot,
                  'experimental_ptbr_label_bytes':131 if getattr(args,'ptbr_labels_experimental',False) else 0,
                  'experimental_eboot_sha256':sha(stage/'eboot.bin'),
                  'original_title_id_preserved':parallel_meta is None,
                  'known_missing':['runtime R13 wallpaper','V15 functional menu','PT-BR complete','PS4 boot test'],
                  'candidate_pkg_loader_header':loader_meta['header'],
                  'candidate_pkg_sfo_fields':loader_meta['sfo'],
                  'candidate_pkg_embedded_sfo_sha256':loader_meta['sfo_sha256'],
                  'candidate_pkg_embedded_icon_sha256':loader_meta['icon_sha256'],
                  'loader_metadata_matches_original_0489':not bool(loader_differences),
                  'loader_metadata_differences':loader_differences}
        (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+chr(10))
        return manifest
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--image0',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--create-gp4',required=True);p.add_argument('--pkgtool',required=True)
    p.add_argument('--allow-experimental',action='store_true')
    p.add_argument('--baseline-original',action='store_true',help='Original 04.89 SFO, icon and source ELF preserved; defaults to byte-identical Image0')
    p.add_argument('--boot-fself-experiment',action='store_true',help='Isolated non-installable test: wrap original ET_SCE_EXEC_ASLR as PS4 fSELF before PKG')
    p.add_argument('--parallel-title-experiment',action='store_true',help='Isolated HIMU00015 PS4 test identity, no verified save/data isolation')
    p.add_argument('--ptbr-labels-experimental',action='store_true',help='Only 131 experimental label bytes; NOT full PT-BR or approved install')
    p.add_argument('--r13-icon',required=True,help='REQUIRED: verified R13 WebP external icon; never used as an internal menu background')
    a=p.parse_args()
    try: print(json.dumps(run(a),indent=2))
    except (ValueError,FileNotFoundError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as e:
        p.exit(2,'FAIL CLOSED: '+str(e)+'\\n')
if __name__=='__main__':main()
