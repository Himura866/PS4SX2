#!/usr/bin/env bash
# HIMURA Switch PS4 - build experimental Linux / CircleCI.
# Builds Orbis Eden upstream unchanged except for in-workspace Linux path adaptation.
set -Eeuo pipefail

BASE="$(pwd)"
WORK="$BASE/.himura-work"
ROOT="$WORK/orbis-eden"
REPORT="$BASE/switch-build-reports"
PKG_ARTIFACTS="$BASE/switch-build-pkgs"
SOURCE_COMMIT="f004df1c7a812cc65703d8f937d0bd12a6d06a58"
SDK_SHA256="f4f079a4df334b46a76996f895283904283d6a006f97102aafaa53d4ecfc9622"
mkdir -p "$WORK" "$REPORT" "$PKG_ARTIFACTS"
: > "$REPORT/build.log"
exec > >(tee -a "$REPORT/build.log") 2>&1
STAGE="inicio"
on_exit() {
  result=$?
  set +e
  # Diagnostico resumido para telas pequenas: coletar a PRIMEIRA mensagem
  # real de erro do compilador, nao apenas o ultimo 'exit 1'.
  if [ "$result" -ne 0 ]; then
    # O tee global pode ainda estar finalizando ao disparar EXIT.
    # O log da etapa é fechado e sincronizado antes do diagnostico.
    error_source="$REPORT/$STAGE.log"
    if [ ! -s "$error_source" ]; then error_source="$REPORT/build.log"; fi
    {
      echo "HIMURA SWITCH PS4 - diagnostico de erro (R06)"
      printf 'log_analisado=%s\n' "$error_source"
      printf 'stage=%s exit_code=%s\n' "$STAGE" "$result"
      echo "PRIMEIRAS MENSAGENS DE ERRO:"
      grep -nEi '(^|[[:space:]])(fatal[[:space:]]+)?error:|FAILED:|CMake Error|ninja: build stopped|Assertion failed|undefined reference' "$error_source" | head -n 15 || true
      echo "ULTIMAS MENSAGENS DE ERRO:"
      grep -nEi '(^|[[:space:]])(fatal[[:space:]]+)?error:|FAILED:|CMake Error|ninja: build stopped|Assertion failed|undefined reference' "$error_source" | tail -n 15 || true
      echo "FINAL DO LOG:"
      tail -n 25 "$error_source" || true
    } > "$REPORT/ERRO-PRINCIPAL.txt"
    echo "========== HIMURA SWITCH: ERRO RESUMIDO =========="
    cat "$REPORT/ERRO-PRINCIPAL.txt"
    echo "==================================================="
  fi
  printf 'stage=%s\nexit_code=%s\nsource_commit=%s\nsdk_sha256=%s\n' "$STAGE" "$result" "$SOURCE_COMMIT" "$SDK_SHA256" > "$REPORT/result.txt"
  if [ -d "$ROOT/out-eden" ]; then
    find "$ROOT/out-eden" -maxdepth 1 -type f -exec cp -f {} "$PKG_ARTIFACTS/" \;
  fi
  if [ -d "$ROOT/elf" ]; then
    find "$ROOT/elf" -maxdepth 1 -type f -name '*.elf' -exec cp -f {} "$PKG_ARTIFACTS/" \;
  fi
  if [ -d "$ROOT/logs" ]; then cp -a "$ROOT/logs" "$REPORT/upstream-logs"; fi
  (cd "$PKG_ARTIFACTS" && sha256sum ./* > "$REPORT/artifact-sha256.txt" 2>/dev/null) || true
  echo "HIMURA SWITCH R14 build result: stage=$STAGE exit=$result"
}
trap on_exit EXIT

STAGE="baixar-fonte"
# Fixamos a revisao auditada: nao usar o HEAD movel de main (ele mudou em 25/11).
git init -q "$ROOT"
git -C "$ROOT" remote add origin https://github.com/MrKitsune9/Orbis-EDEN.git
git -C "$ROOT" fetch --depth 1 origin "$SOURCE_COMMIT"
git -C "$ROOT" checkout --detach -q FETCH_HEAD
actual="$(git -C "$ROOT" rev-parse HEAD)"
printf '%s\n' "$actual" > "$REPORT/source-commit.txt"
if [ "$actual" != "$SOURCE_COMMIT" ]; then
  echo "ERRO: origem mudou de commit; interrompido para nao usar codigo nao aprovado"
  exit 12
fi
# A base Orbis usa Eden 5f142c79 + 46 patches PS4. Abortar antes de instalar
# SDK/compilar caso a cadeia de compatibilidade tenha mudado inesperadamente.
for required in scripts/fetch-eden.sh \
 patches/eden/0003-PS4-64-MiB-JIT-caches-generic-dynarmic-exception-han.patch \
 patches/eden/0009-PS4-avoid-RADV-GFX7-GPU-hangs-from-indirect-count-dr.patch \
 patches/eden/0027-ORBIS-commit-lazy-guest-memory-from-the-top-2-GiB-of.patch \
 patches/eden/0031-PS4-built-in-Miis-when-database-is-empty.patch \
 frontend/libc_wide_fixes.cpp frontend/ps4_platform.cpp tools/analyze-boot.py; do
  test -s "$ROOT/$required" || { echo "ERRO: base Orbis incompleta: $required"; exit 16; }
done
patch_count="$(find "$ROOT/patches/eden" -maxdepth 1 -type f -name '*.patch' | wc -l | tr -d '[:space:]')"
[ "$patch_count" = 46 ] || { echo "ERRO: esperados 46 patches PS4, achados $patch_count"; exit 17; }
grep -Fq 'COMMIT=5f142c7926d0c7fcbbd0ce30794d72f638a43b2a' "$ROOT/scripts/fetch-eden.sh" || {
  echo "ERRO: Eden base mudou, auditar antes de compilar"; exit 18;
}
echo "Fonte Orbis auditada: $actual; Eden base 5f142c79; 46 patches PS4"

# Adapt ONLY this pinned upstream checkout; never mutate the source branch or R13.
STAGE="adaptar-r14-frontend"
python3 ci/r14-adapt-orbis.py "$ROOT"
python3 ci/r14-prepare-art.py "$ROOT"
python3 ci/r14-enable-update-manager.py "$ROOT"
bash -n "$ROOT/ci/70-package.sh"
echo "R14: artwork and standalone HIMURA packaging prepared"

STAGE="baixar-sdk"
curl --fail --location --retry 3 \
  --output "$WORK/orbis-sdk-v1.tar.gz" \
  "https://github.com/orbis-ports/orbis-porting-kit/releases/download/orbis-sdk-v1/orbis-sdk-v1.tar.gz"
echo "$SDK_SHA256  $WORK/orbis-sdk-v1.tar.gz" | sha256sum -c -
mkdir -p "$ROOT/sdk-dl"
tar -xzf "$WORK/orbis-sdk-v1.tar.gz" -C "$ROOT/sdk-dl"
SDK="$ROOT/sdk-dl/orbis-sdk-v1"
for f in "$SDK/toolchain/orbis-sdk.cmake" "$SDK/sdk/lib/crt1.o" "$SDK/orbis-compat/build/liborbis-compat.a" \
 "$SDK/sdk/bin/linux/create-fself" "$SDK/sdk/bin/linux/create-gp4" "$SDK/sdk/bin/linux/PkgTool.Core"; do
  test -s "$f" || { echo "SDK incompleto: $f"; exit 13; }
done
chmod +x "$SDK/sdk/bin/linux/create-fself" "$SDK/sdk/bin/linux/create-gp4" "$SDK/sdk/bin/linux/PkgTool.Core"

STAGE="openorbis-e-caminhos-linux"
mkdir -p "$ROOT/deps"
git clone --depth 1 --branch v0.5.4 https://github.com/OpenOrbis/OpenOrbis-PS4-Toolchain.git "$ROOT/deps/OpenOrbis"
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
r = Path(sys.argv[1]).resolve()
paths = [
    r/"configure-eden.sh",
    r/"toolchain/eden-ps4.cmake",
    r/"toolchain/runtimes-ps4.cmake",
    r/"tools/ps4-cc.sh",
]
for p in paths:
    s = p.read_text()
    s = s.replace("C:/nxorbis/repo", str(r)).replace("/c/nxorbis/repo", str(r))
    s = s.replace("C:/nxorbis/tools/llvm/bin", "/usr/lib/llvm-18/bin")
    s = s.replace("/c/nxorbis/tools/llvm/bin", "/usr/lib/llvm-18/bin")
    s = s.replace(".exe", "")
    p.write_text(s)
env = r/"tools/env-build.sh"
env.write_text(f'''#!/usr/bin/env bash
export PATH="/usr/lib/llvm-18/bin:$PATH"
export PS4_SDK="{r}/sdk-dl/orbis-sdk-v1/sdk"
export PS4_COMPAT="{r}/sdk-dl/orbis-sdk-v1/orbis-compat"
export PS4_OVERLAY="{r}/toolchain/include-overlay"
export PS4_PREFIX="{r}/prefix"
export PS4_CFLAGS="--target=x86_64-pc-freebsd12-elf -O2 -fPIC -funwind-tables -D__PS4__ -D__ORBIS__ -D_BSD_SOURCE=1 -U__FreeBSD__ -isysroot $PS4_SDK -isystem $PS4_OVERLAY -isystem $PS4_COMPAT/include -isystem $PS4_SDK/include -include orbis_prefix.h"
''')
assert str(r) in (r/"toolchain/eden-ps4.cmake").read_text()
print("Paths converted for CircleCI Linux workspace")
PY
test -f "$ROOT/deps/OpenOrbis/samples/piglet/sce_module/libc.prx"
test -x /usr/lib/llvm-18/bin/clang
printf '%s\n' "SDK, tools e caminhos prontos" > "$REPORT/preparation.txt"

# Registrar cada compilacao num arquivo proprio e aguardar o tee concluir.
# Garante que ERRO-PRINCIPAL.txt consulte o log INTEGRAL da etapa falha.
run_stage() {
  local stage_name="$1" script_path="$2" stage_log code
  STAGE="$stage_name"
  stage_log="$REPORT/$stage_name.log"
  : > "$stage_log"
  set +e
  (cd "$ROOT" && bash "$script_path") 2>&1 | tee "$stage_log"
  local -a pipeline_status=("${PIPESTATUS[@]}")
  set -e
  code="${pipeline_status[0]}"
  if [ "$code" -eq 0 ] && [ "${pipeline_status[1]}" -ne 0 ]; then
    code="${pipeline_status[1]}"
  fi
  printf 'HIMURA etapa: %s, codigo: %s, log: %s\n' "$stage_name" "$code" "$stage_log"
  return "$code"
}

STAGE="libcxx18"
# Copy target-specific patch into the pinned Orbis working tree before building libc++.
cp ci/r14-fix-libcxx-random.py "$ROOT/ci/r14-fix-libcxx-random.py"
# upstream Orbis Eden ci/30-libcxx.sh procura __linux__ nos 120 primeiros
# caracteres/linhas, mas LLVM 18.1.8 usa __has_include(<sys/sendfile.h>).
# No PS4 (__ORBIS__), sendfile segue a API FreeBSD, nao a API Linux:
# altere somente a condicao de selecao dentro da fonte baixada.
python3 - "$ROOT" <<'PYLIBCXX'
from pathlib import Path
import sys
script = Path(sys.argv[1]) / "ci/30-libcxx.sh"
src = script.read_text()
start = src.index("    # the Linux sendfile condition near the top of the file")
end = src.index('\nfi\nstep "configure + build"', start)
fixed = """    python3 - "$F" <<'PYFIX'
from pathlib import Path
import sys
file = Path(sys.argv[1])
src = file.read_text()
original = '#if __has_include(<sys/sendfile.h>)'
patched = '#if __has_include(<sys/sendfile.h>) && !defined(__ORBIS__)'
if original in src:
    file.write_text(src.replace(original, patched, 1))
elif patched not in src:
    raise SystemExit('HIMURA: sendfile condition mismatch in libcxx18')
print('HIMURA: sendfile guard adapted to PS4 libcxx18')
PYFIX"""
# O CMAKE_SYSTEM_NAME=Generic e -U__FreeBSD__ impedem o LLVM de
# selecionar pthreads automaticamente. libc++ 18 suporta a opcao oficial.
patched_script = src[:start] + fixed + src[end:]
# On Ubuntu, the host has linux/random.h, but the PS4 sysroot lacks the
# Linux asm/types.h transitively included by it. Apply only to __ORBIS__
# after sparse checkout and BEFORE compiling the random.cpp object.
configure_marker = 'step "configure + build"'
if patched_script.count(configure_marker) != 1:
    raise SystemExit('HIMURA R14: libcxx configure step moved unexpectedly')
random_fix = 'python3 "$ROOT/ci/r14-fix-libcxx-random.py" "$ROOT/deps/llvm-project/libcxx/src/random.cpp"'
patched_script = patched_script.replace(configure_marker, random_fix + '\n' + configure_marker, 1)
needle = '-DLIBCXX_HAS_MUSL_LIBC=ON '
if patched_script.count(needle) != 1:
    raise SystemExit('HIMURA: cannot find libcxx18 CMake threading option insertion')
patched_script = patched_script.replace(
    needle,
    '-DLIBCXX_HAS_MUSL_LIBC=ON -DLIBCXX_HAS_PTHREAD_API=ON ',
    1,
)
script.write_text(patched_script)
print('HIMURA R05: force PTHREAD thread API in libc++18 build')
PYLIBCXX
run_stage "libcxx18" "ci/30-libcxx.sh"
STAGE="openssl-ffmpeg"
run_stage "openssl-ffmpeg" "ci/40-openssl-ffmpeg.sh"
STAGE="compilar-eden"
# CI-only identity inherited by nested git am / git commit processes.
export GIT_COMMITTER_NAME="HIMURA CI"
export GIT_COMMITTER_EMAIL="himura-ci@users.noreply.github.com"
export GIT_AUTHOR_NAME="$GIT_COMMITTER_NAME"
export GIT_AUTHOR_EMAIL="$GIT_COMMITTER_EMAIL"
git -C "$ROOT" var GIT_COMMITTER_IDENT
# Upstream 60-eden.sh uses 'git log --oneline | head -5' under pipefail.
# Git can receive SIGPIPE (141) once head has its five lines, even after
# all Eden patches succeeded. Replace only this diagnostic display pipeline.
python3 - "$ROOT/ci/60-eden.sh" <<'PYSIGPIPE'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
old = 'git -C deps/eden log --oneline | head -5'
new = 'git -C deps/eden log -5 --oneline'
if s.count(old) != 1:
    raise SystemExit('HIMURA R14: unexpected upstream Eden log command; refusing blind patch')
p.write_text(s.replace(old, new, 1))
assert new in p.read_text() and old not in p.read_text()
print('HIMURA R14: Eden git log SIGPIPE/141 guard applied')
PYSIGPIPE
# The nested fetch-eden.sh has a second 'git log | head' under pipefail.
# Fix both diagnostic commands; neither change affects patch application.
python3 - "$ROOT/scripts/fetch-eden.sh" <<'PYFETCHSIGPIPE'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
old = 'git log --oneline | head -3'
new = 'git log -3 --oneline'
if s.count(old) != 1:
    raise SystemExit('HIMURA R14: nested Eden fetch log command changed unexpectedly')
p.write_text(s.replace(old, new, 1))
print('HIMURA R14: nested fetch-eden SIGPIPE/141 fixed')
PYFETCHSIGPIPE
bash -n "$ROOT/scripts/fetch-eden.sh"
bash -n "$ROOT/ci/60-eden.sh"
run_stage "compilar-eden" "ci/60-eden.sh"
test -s "$ROOT/build-eden/bin/eden-ps4" || { echo "ELF ausente"; exit 14; }
cp -f "$ROOT/build-eden/bin/eden-ps4" "$PKG_ARTIFACTS/eden-ps4.elf"
STAGE="empacotar-pkg"
# Keep the original Orbis-EDEN packaging procedure, but remove unsafe
# find|grep|head pipelines: with pipefail, head can make find fail with 141.
# Exact upstream anchors prevent accidentally changing an unknown revision.
python3 - "$ROOT/ci/70-package.sh" <<'PYPKGSIGPIPE'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text()
changes = [
    ("find build-eden -name 'eden-ps4' -type f | head -1",
     "find build-eden -name 'eden-ps4' -type f -print -quit"),
    ("find \"$SDK_ROOT\" \"$ROOT/deps/oo-release\" -type f -iname 'PkgTool.Core.dll' 2>/dev/null | head -1",
     "find \"$SDK_ROOT\" \"$ROOT/deps/oo-release\" -type f -iname 'PkgTool.Core.dll' -print -quit 2>/dev/null"),
]
for old, new in changes:
    if s.count(old) != 1:
        raise SystemExit(f'HIMURA R14 packaging upstream drift: {old}')
    s = s.replace(old, new, 1)
old = 'find_tool() { find "$SDK_ROOT" "$ROOT/deps/oo-release" "$OO" -type f -iname "$1" 2>/dev/null | grep -i -v \'\\.exe$\' | grep -i -E \'linux|/bin/\' | head -1; }'
new = """find_tool() {
  find "$SDK_ROOT" "$ROOT/deps/oo-release" "$OO" -type f -iname "$1" 2>/dev/null |
    awk 'tolower($0) !~ /\\.exe$/ && (tolower($0) ~ /linux|\\/bin\\//) { if (!found) { print; found=1 } }'
}"""
if s.count(old) != 1:
    raise SystemExit('HIMURA R14 packaging upstream drift: find_tool')
s = s.replace(old, new, 1)
p.write_text(s)
print('HIMURA R14: package tool discovery SIGPIPE/141 guarded')
PYPKGSIGPIPE
bash -n "$ROOT/ci/70-package.sh"
run_stage "empacotar-pkg" "ci/70-package.sh"
find "$ROOT/out-eden" -maxdepth 1 -type f -name '*.pkg' -size +1M -print -quit | grep -q . || {
  echo "Nenhum PKG valido gerado"
  exit 15
}
STAGE="compilacao-terminada"
echo "PKG gerado no CircleCI; inicializacao e compatibilidade no PS4 Pro ainda nao testadas"
