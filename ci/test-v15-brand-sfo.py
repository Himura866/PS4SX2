#!/usr/bin/env python3
"""Unit tests for byte-safe V15 SFO rebrand (synthetic SFO, no private keys)."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import tempfile

source=Path(__file__).with_name("v15-brand-sfo.py")
spec=importlib.util.spec_from_file_location("v15_brand_sfo",source)
b=importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

def make_sfo(title_capacity=128):
    items=[
        ("TITLE_ID", b.EXPECTED_TITLE_ID,16),
        ("CONTENT_ID",b.EXPECTED_CONTENT_ID,48),
        ("APP_VER",b.SOURCE_APP_VER,8),
        ("TITLE","New Eden",title_capacity),
        ("VERSION","01.00",8),
    ]
    keybase=20+16*len(items)
    keydata=bytearray()
    entries=[]
    values=bytearray()
    for key,value,cap in items:
        keyoff=len(keydata)
        keydata+=key.encode()+b"\0"
        while len(values)%4:
            values+=b"\0"
        valueoff=len(values)
        v=value.encode()+b"\0"
        if len(v)>cap:
            raise ValueError("synthetic test SFO cap too small")
        values+=v+bytes(cap-len(v))
        entries.append((keyoff,0x0204,len(v),cap,valueoff))
    database=keybase+len(keydata)
    database=(database+3)&~3
    out=bytearray(struct.pack("<4sIIII",b"\x00PSF",0x101,keybase,database,len(items)))
    for e in entries:
        out+=struct.pack("<HHIII",*e)
    out+=keydata
    out+=bytes(database-len(out))
    out+=values
    return bytes(out)

with tempfile.TemporaryDirectory(prefix="v15-brand-test-") as tmp:
    path=Path(tmp)/"param.sfo"
    original=make_sfo()
    path.write_bytes(original)
    report=b.patch(path,hashlib.sha256(original).hexdigest())
    assert report["app_ver"]=="15.00"
    assert report["title"]=="HIMURA SWITCH PS4 V15"
    assert report["title_id"]==b.EXPECTED_TITLE_ID
    assert report["eboot_modified"] is False
    updated=path.read_bytes()
    assert len(updated)==len(original)
    index=b.fields(updated)
    assert b.text_value(updated,index["APP_VER"])=="15.00"
    assert b.text_value(updated,index["TITLE"])=="HIMURA SWITCH PS4 V15"
    assert b.text_value(updated,index["TITLE_ID"])==b.EXPECTED_TITLE_ID
    assert b.text_value(updated,index["CONTENT_ID"])==b.EXPECTED_CONTENT_ID
    assert b.text_value(updated,index["VERSION"])=="01.00"
    print("PASS: V15 title and app version updated without changing IDs or VERSION")

    # Verify only the two permitted value regions and their lengths may differ.
    allowed=set()
    original_fields=b.fields(original)
    for key in ("APP_VER","TITLE"):
        pos,_,_,cap,start=original_fields[key]
        allowed.update(range(pos+4,pos+8))
        allowed.update(range(start,start+cap))
    assert all(i in allowed for i,(a,bv) in enumerate(zip(original,updated)) if a!=bv)
    print("PASS: every altered SFO byte is within the approved fields")

    path.write_bytes(original)
    try:
        b.patch(path,"0"*64)
    except ValueError as exc:
        assert "Unexpected SFO hash" in str(exc)
    else:
        raise AssertionError("wrong SFO hash was accepted")
    assert path.read_bytes()==original
    print("PASS: wrong source hash cannot mutate file")

    limited=make_sfo(title_capacity=10)
    path.write_bytes(limited)
    try:
        b.patch(path,hashlib.sha256(limited).hexdigest())
    except ValueError as exc:
        assert "Not enough SFO field capacity" in str(exc)
    else:
        raise AssertionError("insufficient title capacity accepted")
    assert path.read_bytes()==limited
    print("PASS: insufficient TITLE capacity does not mutate file")

    path.write_bytes(original)
    try:
        b.patch(path, hashlib.sha256(updated).hexdigest())
    except ValueError:
        pass
    else:
        raise AssertionError("different SFO revision was accepted")

print("PASS: staged SFO branding tests completed, no PS4 PKG generated")
