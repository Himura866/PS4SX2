#!/usr/bin/env bash
# R07: testar a base Eden4 sem reconstruir a toolchain PS4 inteira.
# Compila somente o menu HOME nativo de host (Linux), nao gera PKG/ELF PS4.
set -Eeuo pipefail
BASE="$(pwd)"
OUT="$BASE/switch-r07-ui-preview"
REPORT="$BASE/switch-r07-reports"
ROOT="$BASE/.himura-bases/eden4"
STAGE="inicio"
mkdir -p "$OUT" "$REPORT"
on_exit() {
  local rc=$?
  set +e
  printf 'stage=%s\nexit_code=%s\n' "$STAGE" "$rc" > "$REPORT/result.txt"
  if [ "$rc" -ne 0 ]; then
    echo "R07 FALHOU: stage=$STAGE code=$rc"
    find "$REPORT" -maxdepth 1 -type f -print
  else
    echo "R07: preview do Eden4 compilado e conferido (NAO E PKG PS4)"
  fi
}
trap on_exit EXIT

STAGE="obter-eden4"
bash ci/prepare-eden4-base.sh "$ROOT" 2>&1 | tee "$REPORT/source.log"
git -C "$ROOT" rev-parse HEAD > "$REPORT/source-commit.txt"
printf 'Base verificada: %s\n' "$(cat "$REPORT/source-commit.txt")"

STAGE="validar-materiais"
for f in "$ROOT/eden/ps4/ui-preview/build.sh" "$ROOT/eden/ps4/generate-ui-assets.py" "$ROOT/runtime/fonts/Nunito-Regular.ttf" "$ROOT/eden/src/yuzu_ps4/ui_launcher.cpp"; do
  test -s "$f" || { echo "Arquivo necessario nao encontrado: $f"; exit 4; }
done
command -v c++ >/dev/null
python3 -c 'from PIL import Image; print("Pillow disponivel")'

STAGE="compilar-menu-home"
bash "$ROOT/eden/ps4/ui-preview/build.sh" "$OUT" 2>&1 | tee "$REPORT/ui-preview-build.log"
test -s "$OUT/preview" || { echo "Binario nativo preview nao foi gerado"; exit 5; }

STAGE="conferir-imagens"
COUNT="$(find "$OUT" -maxdepth 1 -name '*.png' -type f | wc -l)"
printf 'generated_pngs=%s\n' "$COUNT" > "$REPORT/preview-summary.txt"
if [ "$COUNT" -lt 1 ]; then
  echo "Menu compilou, mas nao gerou capturas PNG"; exit 6
fi
find "$OUT" -maxdepth 1 -name '*.png' -printf '%f\n' | sort >> "$REPORT/preview-summary.txt"
echo "Menu HOME preview: $COUNT imagens PNG geradas"
STAGE="preview-concluido"
