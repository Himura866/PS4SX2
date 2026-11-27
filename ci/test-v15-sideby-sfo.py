#!/usr/bin/env python3
"""SFO identity cloning test with no owner files, games, keys or firmware."""
import hashlib,importlib.util,struct
from pathlib import Path

spec=importlib.util.spec_from_file_location('v15sfo',Path(__file__).with_name('v15-sideby-sfo.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

fields=[('TITLE_ID','EDNP00001',12),('CONTENT_ID','IV0000-EDNP00001_00-EDENPS4000000000',48),
        ('TITLE','New Eden',128),('APP_VER','04.89',8),('VERSION','04.89',8),
        ('CATEGORY','gd',4)]
keys=bytearray();values=bytearray();entries=bytearray()
for k,v,maxlen in fields:
    koff=len(keys);voff=len(values)
    keys+=k.encode()+b'\0';encoded=v.encode()+b'\0'
    values+=encoded.ljust(maxlen,b'\0')
    entries+=struct.pack('<HHIII',koff,0x204,len(encoded),maxlen,voff)
ka=20+len(entries);da=ka+len(keys)
raw=struct.pack('<4sIIII',b'\x00PSF',0x101,ka,da,len(fields))+entries+keys+values
m.ORIGINAL_SFO_SHA=hashlib.sha256(raw).hexdigest()
output=m.patch(raw)
assert len(output)==len(raw)
assert output!=raw
assert m.TITLE_ID.encode()+b'\0' in output
assert m.CONTENT_ID.encode()+b'\0' in output
assert m.TITLE.encode()+b'\0' in output
assert b'gd\0' in output
assert raw.find(b'New Eden\0')>=0 and raw.find(b'EDNP00001\0')>=0
try:
    m.patch(raw+b'corrupt')
except ValueError:
    pass
else:
    raise AssertionError('tampered original SFO accepted')
print('PASS: parallel V15 metadata copied into SFO slots; original unchanged; negative check')
