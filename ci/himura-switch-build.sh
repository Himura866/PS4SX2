#!/usr/bin/env bash
# HIMURA Switch PS4 - build experimental Linux / CircleCI.
# Builds Orbis Eden upstream unchanged except for in-workspace Linux path adaptation.
set -Eeuo pipefail

BASE="$(pwd)"
WORK="$BASE/.himura-work"
ROOT="$WORK/orbis-eden"
REPORT="$BASE/switch-build-reports"
PKG_ARTIFACTS="$BASE/switch-build-pkgs"
SOURCE_COMMIT="c9a26c80d3b7a8b47f68b5a247fcee6d6d17707d"
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
    {
      echo "HIMURA SWITCH PS4 - diagnostico de erro (R04)"
      printf 'stage=%s exit_code=%s\n' "$STAGE" "$result"
      echo "PRIMEIRAS MENSAGENS DE ERRO:"
      grep -nEi '(^|[[:space:]])(fatal[[:space:]]+)?error:|FAILED:|CMake Error|ninja: build stopped|Assertion failed|undefined reference' "$REPORT/build.log" | head -n 15 || true
      echo "ULTIMAS MENSAGENS DE ERRO:"
      grep -nEi '(^|[[:space:]])(fatal[[:space:]]+)?error:|FAILED:|CMake Error|ninja: build stopped|Assertion failed|undefined reference' "$REPORT/build.log" | tail -n 15 || true
      echo "FINAL DO LOG:"
      tail -n 15 "$REPORT/build.log" || true
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
  echo "HIMURA SWITCH build result: stage=$STAGE exit=$result"
}
trap on_exit EXIT

STAGE="baixar-fonte"
git clone --depth 1 --single-branch --branch main https://github.com/MrKitsune9/Orbis-EDEN.git "$ROOT"
actual="$(git -C "$ROOT" rev-parse HEAD)"
printf '%s\n' "$actual" > "$REPORT/source-commit.txt"
if [ "$actual" != "$SOURCE_COMMIT" ]; then
  echo "ERRO: origem mudou de commit; interrompido para nao usar codigo nao aprovado"
  exit 12
fi
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

STAGE="libcxx18"
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
(cd "$ROOT" && bash ci/30-libcxx.sh)
STAGE="openssl-ffmpeg"
(cd "$ROOT" && bash ci/40-openssl-ffmpeg.sh)
STAGE="compilar-eden"
(cd "$ROOT" && bash ci/60-eden.sh)
test -s "$ROOT/build-eden/bin/eden-ps4" || { echo "ELF ausente"; exit 14; }
cp -f "$ROOT/build-eden/bin/eden-ps4" "$PKG_ARTIFACTS/eden-ps4.elf"
STAGE="empacotar-pkg"
(cd "$ROOT" && bash ci/70-package.sh)
find "$ROOT/out-eden" -maxdepth 1 -type f -name '*.pkg' -size +1M -print -quit | grep -q . || {
  echo "Nenhum PKG valido gerado"
  exit 15
}
STAGE="compilacao-terminada"
echo "PKG gerado no CircleCI; inicializacao e compatibilidade no PS4 Pro ainda nao testadas"
