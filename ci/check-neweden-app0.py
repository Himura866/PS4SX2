#!/usr/bin/env python3
"""Read-only gate for a decrypted, installed New Eden 04.89 PS4 app directory.

Never replaces eboot.bin or repackages the user PKG. Use a mounted app0
exported from the owner's PS4; reject mismatching editions early.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

EXPECTED = {
    "TITLE_ID": "EDNP00001",
    "CONTENT_ID": "IV0000-EDNP00001_00-EDENPS4000000000",
    "APP_VER": "04.89",
}
PKG_SHA256 = "06e4bc0538b5217ed5c539c12403bd808131e5d50c96315b2840911170939ccd"
EBOOT_SHA256 = "5defaadbc08c5ba58b62dbe2a006c892dfab9d941f99900b696feff3fe812381"
EBOOT_SIZE = 78376440

def sfo_values(path):
    raw = path.read_bytes()
    if len(raw) < 20 or raw[:4] != b"\x00PSF":
        raise ValueError("param.sfo ausente ou invalido")
    _, _, key_off, data_off, count = struct.unpack_from("<4sIIII", raw)
    if count > 512:
        raise ValueError("sfo: tabela excessiva")
    result = {}
    for i in range(count):
        pos = 20 + i*16
        if pos + 16 > len(raw):
            raise ValueError("sfo: indice incompleto")
        name_at, typ, length, _, data_at = struct.unpack_from("<HHIII", raw, pos)
        name_pos = key_off + name_at
        val_pos = data_off + data_at
        if name_pos < 0 or name_pos >= len(raw) or val_pos > len(raw) or length > len(raw)-val_pos:
            raise ValueError("sfo: deslocamento fora do arquivo")
        name_end = raw.find(b"\x00", name_pos)
        if name_end < 0:
            raise ValueError("sfo: chave nao terminada")
        key = raw[name_pos:name_end].decode("utf-8")
        if typ == 0x0204:
            result[key] = raw[val_pos:val_pos+length].rstrip(b"\x00").decode("utf-8", "replace")
        elif typ == 0x0404 and length == 4:
            result[key] = struct.unpack_from("<I", raw, val_pos)[0]
    return result

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()

def inspect(root, original_pkg):
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("Pasta app0 nao encontrada; nada foi extraido")
    sfo = root / "sce_sys" / "param.sfo"
    eboot = root / "eboot.bin"
    if not eboot.is_file():
        raise ValueError("Exportacao incompleta: faltou eboot.bin")
    if eboot.stat().st_size != EBOOT_SIZE:
        raise ValueError("eboot.bin nao tem o tamanho da revisao 04.89 recebida")
    actual_eboot_sha256 = sha256(eboot)
    if actual_eboot_sha256 != EBOOT_SHA256:
        raise ValueError("O executavel NAO corresponde ao New Eden 04.89 exportado pelo usuario")
    # A montagem pfsmnt do usuario nao inclui param.sfo nem icon0.png.
    # O PKG original os contem, e a equivalencia do ELF foi verificada pelo hash.
    metadata = sfo_values(sfo) if sfo.is_file() else {}
    if sfo.is_file():
        errors = [f"{k}: esperado {v!r}, encontrado {metadata.get(k)!r}"
                  for k,v in EXPECTED.items() if metadata.get(k) != v]
        if errors:
            raise ValueError("PKG nao corresponde ao New Eden 04.89: " + "; ".join(errors))
    if original_pkg:
        if sha256(original_pkg) != PKG_SHA256:
            raise ValueError("O PKG de origem difere do arquivo enviado pelo usuario")
    file_list = [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]
    manifest = {
        "source": "New Eden 04.89 - decrypted installed app0, not Orbis-EDEN",
        "matched": True,
        "sfo": metadata,
        "sfo_included_in_app0": sfo.is_file(),
        "identity_verified_by": "sha256 of exact uploaded eboot.bin",
        "eboot_size": eboot.stat().st_size,
        "eboot_sha256": actual_eboot_sha256,
        "files": len(file_list),
        "paths": [str(p.relative_to(root)) for p in sorted(file_list)],
        "not_verified": ["PS4 game boot", "editing support", "source code provenance"],
    }
    return manifest

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("app0", type=Path, help="Pasta app0 extraida da instalacao EDNP00001")
    ap.add_argument("--pkg", type=Path, default=None, help="PKG 04.89 original, opcional")
    ap.add_argument("--report", type=Path, default=Path("NEWEDEN-0489-APP0-MANIFEST.json"))
    args = ap.parse_args()
    result = inspect(args.app0, args.pkg)
    args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(f"OK: EDNP00001 v04.89; {result['files']} arquivos; eboot SHA256 {result['eboot_sha256']}")
    print(f"Inventario: {args.report}")
    print("Nao modifica jogos, executavel, saves ou PKG.")
