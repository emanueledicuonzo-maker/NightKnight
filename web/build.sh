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
# Il canvas sempre 16:9 a tutta finestra: pygbag ne calcola le proporzioni prima che il
# gioco apra la sua finestra 1920x1080 e, per esempio a 1366x768, lo lascia quadrato.
python3 - "$OUT/build/web/index.html" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
css = "#canvas{width:min(100vw,177.78vh)!important;height:min(56.25vw,100vh)!important}\n    </style>"
s = s.replace("</style>", css, 1)
open(p, "w").write(s)
PY
rm -f "$OUT/build/web/nightknight.apk"   # pygbag carica il .tar.gz; il doppione supera il limite dei 25 MB per Worker
