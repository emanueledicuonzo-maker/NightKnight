#!/bin/sh
# Versione per il browser di NightKnight (pygbag). Il gioco per computer non cambia:
# qui si copia il codice, si aggiunge web/main.py e le immagini passano a 256 colori
# (stesse dimensioni, da 117 a ~17 MB). Risultato in web/nightknight/build/web/.
set -e
cd "$(dirname "$0")/.."
OUT=web/nightknight
rm -rf "$OUT"; mkdir -p "$OUT/assets"
cp assets.py athletics.py fonts.py goblin.py knights.py levels.py music.py nix.py progress.py titan.py waves.py "$OUT/"
cp web/main.py "$OUT/"
cp -r assets/fonts "$OUT/assets/"
python3 - "$OUT/assets" <<'PY'
import glob, os, sys
from PIL import Image
for f in glob.glob("assets/*.png"):
    im = Image.open(f).convert("RGBA")
    im.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(
        os.path.join(sys.argv[1], os.path.basename(f)), optimize=True)
PY
.venv-web/bin/pygbag --build --title NightKnight "$OUT"
