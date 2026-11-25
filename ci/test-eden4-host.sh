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

STAGE="integrar-creditos-himura"
python3 ci/patch-eden4-credits.py "$ROOT" 2>&1 | tee "$REPORT/credits-patch.log"
git -C "$ROOT" diff --check

STAGE="compilar-menu-home"
bash "$ROOT/eden/ps4/ui-preview/build.sh" "$OUT" 2>&1 | tee "$REPORT/ui-preview-build.log"
test -s "$OUT/preview" || { echo "Binario nativo preview nao foi gerado"; exit 5; }

STAGE="conferir-imagens"
COUNT="$(find "$OUT" -maxdepth 1 -name '*.png' -type f | wc -l)"
printf 'generated_pngs=%s\n' "$COUNT" > "$REPORT/preview-summary.txt"
if [ "$COUNT" -lt 1 ]; then
  echo "Menu compilou, mas nao gerou capturas PNG"; exit 6
fi
# O preview precisa visitar de verdade as telas de Sobre e Creditos.
for image in himura_about himura_credits; do
  test -s "$OUT/$image.png" || { echo "Captura obrigatoria ausente: $image.png"; exit 7; }
done
python3 - "$OUT" <<'PYVERIFY'
from pathlib import Path
from PIL import Image
import sys
root = Path(sys.argv[1])
for name in ("himura_about", "himura_credits"):
    with Image.open(root / (name + ".png")) as image:
        if image.size != (1920, 1080):
            raise SystemExit(f"{name}: imagem fora de 1920x1080: {image.size}")
        if not image.getbbox():
            raise SystemExit(f"{name}: imagem vazia")
        print(f"HIMURA R07: {name} preview validado {image.size}")
PYVERIFY
sha256sum "$OUT/himura_about.png" "$OUT/himura_credits.png" > "$REPORT/preview-checksums.txt"

# Galeria compacta feita com as capturas reais do preview Linux.
# NAO sao prints de um PKG instalado no PS4; identificacao gravada na imagem.
STAGE="montar-galeria"
python3 - "$OUT" <<'PYGALLERY'
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys
out = Path(sys.argv[1])
screens = [
    ("home", "Tela inicial"),
    ("library", "Biblioteca"),
    ("settings", "Configuracoes"),
    ("himura_about", "Sobre"),
    ("himura_credits", "Creditos e licencas"),
    ("controllers", "Controles"),
]
w, h, top, label_h = 640, 360, 56, 40
sheet = Image.new("RGB", (w * 2, (h + label_h) * 3 + top), (20, 24, 32))
draw = ImageDraw.Draw(sheet)
draw.text((16, 16), "HIMURA SWITCH PS4 - R07  |  PREVIA LINUX - NAO TESTADO NO PS4", fill="white")
for i, (filename, label) in enumerate(screens):
    path = out / (filename + ".png")
    if not path.is_file():
        raise SystemExit("Captura obrigatoria ausente na galeria: " + path.name)
    with Image.open(path) as src:
        if src.size != (1920, 1080):
            raise SystemExit("Captura inesperada: " + path.name)
        thumb = src.convert("RGB").resize((w, h), Image.Resampling.LANCZOS)
    x, y = (i % 2) * w, top + (i // 2) * (h + label_h)
    sheet.paste(thumb, (x, y))
    draw.rectangle([x, y + h, x + w - 1, y + h + label_h - 1], fill=(32, 38, 49))
    draw.text((x + 12, y + h + 12), label, fill="white")
sheet.save(out / "himura-r07-galeria.jpg", quality=88, optimize=True)
print("Galeria criada:", out / "himura-r07-galeria.jpg")
PYGALLERY
test -s "$OUT/himura-r07-galeria.jpg"

find "$OUT" -maxdepth 1 -name '*.png' -printf '%f\n' | sort >> "$REPORT/preview-summary.txt"
echo "Menu HOME preview: $COUNT imagens PNG geradas"
STAGE="preview-concluido"
