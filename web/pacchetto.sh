#!/bin/sh
# Zip da scaricare di NightKnight per Windows, Mac e Linux: codice, immagini a 256 colori
# (quelle di web/build.sh), avvia.bat / avvia.sh che installano le librerie la prima volta.
# Prima: web/build.sh. Risultato: web/nightknight.zip
set -e
cd "$(dirname "$0")/.."
T=web/pacchetto/NightKnight
rm -rf web/pacchetto web/nightknight.zip; mkdir -p "$T"
cp assets.py athletics.py fonts.py goblin.py knights.py levels.py music.py nix.py progress.py titan.py waves.py requirements.txt LICENSE "$T/"
cp -r web/nightknight/assets "$T/"
cp web/avvia.bat web/avvia.sh web/LEGGIMI.txt "$T/"
python3 - <<'PY'
import os, zipfile
base = "web/pacchetto"
with zipfile.ZipFile("web/nightknight.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for root, _, files in os.walk(base):
        for f in sorted(files):
            p = os.path.join(root, f); a = os.path.relpath(p, base)
            info = zipfile.ZipInfo.from_file(p, a)
            if f == "avvia.sh":
                info.external_attr = 0o755 << 16
            with open(p, "rb") as fh:
                z.writestr(info, fh.read(), zipfile.ZIP_DEFLATED)
PY
rm -rf web/pacchetto
ls -la web/nightknight.zip
