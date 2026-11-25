#!/usr/bin/env bash
# HIMURA Switch PS4 - R07: checkout auditavel da base Eden4.
# Nao compila, nao instala jogos/firmware/keys e nao altera o PS2.
set -Eeuo pipefail

SOURCE_URL="https://github.com/xatyy/Eden4.git"
SOURCE_SHA="fab246cbac93c7995aaf451dca83ae93ba0bd234"
DEST="${1:-$PWD/.himura-bases/eden4}"

if [ -e "$DEST" ]; then
  echo "ERRO: destino ja existe, para evitar sobrescrever: $DEST" >&2
  exit 2
fi
mkdir -p "$(dirname "$DEST")"
git clone --filter=blob:none --no-checkout "$SOURCE_URL" "$DEST"
git -C "$DEST" checkout --detach "$SOURCE_SHA"
ACTUAL="$(git -C "$DEST" rev-parse HEAD)"
if [ "$ACTUAL" != "$SOURCE_SHA" ]; then
  echo "ERRO: o commit da base mudou inesperadamente" >&2
  exit 3
fi
for f in LICENSE README.md docs/BUILDING.md docs/KNOWN_ISSUES.md eden/ps4/build.sh; do
  if [ ! -s "$DEST/$f" ]; then
    echo "ERRO: falta arquivo necessario: $f" >&2
    exit 4
  fi
done
echo "Eden4 obtido e verificado, commit $ACTUAL"
echo "Fonte: $SOURCE_URL"
echo "Destino: $DEST"
echo "PROXIMO: revisar dependencias LLVM21/PacBrew/Mesa antes de compilar."
echo "Nao foi gerado PKG por este script."
