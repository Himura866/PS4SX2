#!/usr/bin/env bash
set -Eeuo pipefail
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cat > "$work/check.cpp" <<'CPP'
#include "r13_memory_failure_probe.h"
#include <cstdio>
int main(int argc, char** argv) {
  if(argc!=2)return 2;
  if(!HimuraMemoryProbe::Append(argv[1],"operator_new","GPU cutscene",0,0,6017,6017,310))return 3;
  if(!HimuraMemoryProbe::Append(argv[1],"guest_RAM_direct_alloc","sceKernelAllocateDirectMemory",
                                4294967296ull,0x8002000c,0,0,0))return 4;
  return 0;
}
CPP
g++ -std=c++20 -Wall -Wextra -Werror -O2 -Ici "$work/check.cpp" -o "$work/probe"
"$work/probe" "$work/HIMURA_R13_OOM.txt"
test "$(wc -l < "$work/HIMURA_R13_OOM.txt")" -eq 2
grep -Fq 'origin=operator_new phase=GPU cutscene bytes=0 code=0x00000000 composites=6017' "$work/HIMURA_R13_OOM.txt"
grep -Fq 'origin=guest_RAM_direct_alloc phase=sceKernelAllocateDirectMemory bytes=4294967296 code=0x8002000c' "$work/HIMURA_R13_OOM.txt"
echo "PASS: append-only OOM probe compiled and persisted diagnostics without dynamic std::string"
