#!/usr/bin/env bash
# Native-logic test, NOT a PS4 emulator test. CI-only scratch root and fake NCAs.
set -Eeuo pipefail
root="$(mktemp -d /tmp/r13-firmware-check-XXXXXX)"
trap 'rm -rf "$root"' EXIT
mkdir -p "$root/data"
test -s .r11-smoke/eden4/eden/src/yuzu_ps4/r13_firmware_zip.cpp
g++ -std=c++20 -O2 -Wall -Wextra -Werror \
  -DR13_FIRMWARE_DATA_ROOT="\"$root/data\"" \
  -I.r11-smoke/eden4/eden/src \
  -x c++ - .r11-smoke/eden4/eden/src/yuzu_ps4/r13_firmware_zip.cpp \
  -lz -o "$root/test-import" <<'CPP'
#include "yuzu_ps4/r13_firmware_zip.h"
#include <cstdio>
#include <string>
int main(int argc,char** argv) {
    if(argc!=3)return 3;
    const std::string result=HimuraFirmware::InstallZip(argv[1],[](size_t n,size_t total){
        std::printf("verified %zu/%zu\n",n,total);
    });
    std::printf("%s\n",result.c_str());
    const bool success=result.rfind("Firmware ZIP instalado:",0)==0;
    return success==(std::string(argv[2])=="ok")?0:1;
}
CPP
python3 - "$root/data" <<'PY'
import sys,zipfile,pathlib,struct
root=pathlib.Path(sys.argv[1])
nca=b"HIMURA_TEST_DUMMY_NCA_"*512
with zipfile.ZipFile(root/"valid.zip","w",zipfile.ZIP_DEFLATED) as z:
    z.writestr("Firmware/",b"")
    z.writestr("Firmware/"+"a"*32+".nca",nca)
with zipfile.ZipFile(root/"slip.zip","w",zipfile.ZIP_STORED) as z:
    z.writestr("../escape.nca",nca)
# corrupt ONLY the verified CRC in the central directory
raw=bytearray((root/"valid.zip").read_bytes())
pos=raw.index(b"PK\x01\x02", raw.index(b"PK\x01\x02")+4)
raw[pos+16]^=0x80
(root/"crc-broken.zip").write_bytes(raw)
PY
"$root/test-import" "$root/data/slip.zip" fail
"$root/test-import" "$root/data/crc-broken.zip" fail
test ! -d "$root/data/nand/system/Contents/registered"
"$root/test-import" "$root/data/valid.zip" ok
test -s "$root/data/nand/system/Contents/registered/$(printf 'a%.0s' {1..32}).nca"
"$root/test-import" "$root/data/valid.zip" fail
test -s "$root/data/nand/system/Contents/registered/$(printf 'a%.0s' {1..32}).nca"
echo 'PASS: valid ZIP installed, unsafe paths and CRC rejected, existing NCA protected.'
