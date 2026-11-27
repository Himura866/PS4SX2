#!/usr/bin/env python3
"""Rebrand the PS4-visible SFO title/version in a STAGED COPY only.

Never change TITLE_ID, CONTENT_ID, keystone, original PKG, saves or eboot.
The PS4 APP_VER field is numeric XX.YY; the HIMURA user-facing brand is V15.
Refuses SFOs with unexpected hash, layout or insufficient TITLE capacity.
"""
import hashlib
import struct
from pathlib import Path

ORIGINAL_SFO_SHA256 = "9bfff1385d1cd7593825090616e4a0c198b7f0fb69a9ceaedb3e3eaf732f9c54"
EXPECTED_TITLE_ID = "EDNP00001"
EXPECTED_CONTENT_ID = "IV0000-EDNP00001_00-EDENPS4000000000"
SOURCE_APP_VER = "04.89"
TARGET_APP_VER = "15.00"
TARGET_TITLE = "HIMURA SWITCH"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def fields(raw):
    if len(raw) < 20 or raw[:4] != b"\x00PSF":
        raise ValueError("Invalid PS4 PARAM.SFO magic")
    _, _, keybase, database, count = struct.unpack_from("<4sIIII", raw)
    if count > 128 or keybase < 20 + 16 * count or database < keybase or database > len(raw):
        raise ValueError("Unsafe PARAM.SFO table layout")
    result = {}
    ranges = []
    for i in range(count):
        pos = 20 + 16 * i
        off, typ, nbytes, cap, valoff = struct.unpack_from("<HHIII", raw, pos)
        keypos = keybase + off
        if keypos >= database:
            raise ValueError("Invalid SFO key offset")
        keyend = raw.find(b"\x00", keypos, database)
        if keyend < 0:
            raise ValueError("Unterminated SFO key")
        name = raw[keypos:keyend].decode("utf-8")
        start = database + valoff
        if cap < nbytes or start < database or start + cap > len(raw):
            raise ValueError("Invalid SFO field allocation: " + name)
        if name in result:
            raise ValueError("Duplicate SFO field: " + name)
        result[name] = (pos, typ, nbytes, cap, start)
        ranges.append((start, start + cap))
    ranges.sort()
    if any(a[1] > b[0] for a,b in zip(ranges, ranges[1:])):
        raise ValueError("Overlapping SFO field allocations")
    return result

def text_value(raw, info):
    _, typ, nbytes, _, start = info
    if typ != 0x0204 or nbytes < 1:
        raise ValueError("Expected UTF-8 PS4 SFO string")
    value = raw[start:start+nbytes]
    if b"\x00" not in value:
        raise ValueError("Unterminated PS4 SFO string")
    return value.split(b"\x00", 1)[0].decode("utf-8")

def patch(staged_sfo: Path, original_sha256=ORIGINAL_SFO_SHA256):
    """In-place update of an ALREADY-STAGED SFO; abort before modifying on error."""
    source = staged_sfo.read_bytes()
    if digest(source) != original_sha256:
        raise ValueError("Unexpected SFO hash: refusing to change another release")
    index = fields(source)
    for key in ("APP_VER", "VERSION", "TITLE", "TITLE_ID", "CONTENT_ID"):
        if key not in index:
            raise ValueError("Missing required PS4 SFO field: " + key)
    for key in ("APP_VER", "VERSION"):
        if text_value(source,index[key]) != SOURCE_APP_VER:
            raise ValueError("Source "+key+" does not match original 04.89")
    if text_value(source,index["TITLE_ID"]) != EXPECTED_TITLE_ID:
        raise ValueError("TITLE_ID must stay EDNP00001")
    if text_value(source,index["CONTENT_ID"]) != EXPECTED_CONTENT_ID:
        raise ValueError("CONTENT_ID does not match original")
    if "New Eden" not in text_value(source,index["TITLE"]):
        raise ValueError("Unexpected source app title; refused to replace")
    output = bytearray(source)
    for key, value in (("APP_VER", TARGET_APP_VER),("VERSION", TARGET_APP_VER),("TITLE", TARGET_TITLE)):
        pos, typ, _, cap, start = index[key]
        if typ != 0x0204:
            raise ValueError("Unsafe SFO string type for " + key)
        encoded=value.encode("utf-8")+b"\x00"
        if len(encoded)>cap:
            raise ValueError("Not enough SFO field capacity to set " + key)
        # Fill only this field's allocated bytes, preserving every other entry.
        output[start:start+cap] = encoded + bytes(cap-len(encoded))
        struct.pack_into("<I", output, pos+4, len(encoded))
    updated=bytes(output)
    final=fields(updated)
    for key,expected in (("APP_VER",TARGET_APP_VER),("VERSION",TARGET_APP_VER),("TITLE",TARGET_TITLE),
                         ("TITLE_ID",EXPECTED_TITLE_ID),("CONTENT_ID",EXPECTED_CONTENT_ID)):
        if text_value(updated,final[key]) != expected:
            raise ValueError("SFO rebrand verification failed: "+key)
    if len(updated)!=len(source):
        raise ValueError("SFO allocation changed unexpectedly")
    staged_sfo.write_bytes(updated)
    return {"app_ver": TARGET_APP_VER, "version": TARGET_APP_VER, "title": TARGET_TITLE,
            "title_id": EXPECTED_TITLE_ID, "content_id": EXPECTED_CONTENT_ID,
            "source_sfo_sha256": digest(source), "branded_sfo_sha256": digest(updated),
            "eboot_modified": False, "original_sfo_modified": False}
