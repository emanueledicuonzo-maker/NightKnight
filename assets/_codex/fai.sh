#!/bin/bash
# $1 nome file (senza .png), $2 descrizione in inglese del soggetto
cd ~/Documenti/goblin
cat > assets/_codex/prompt_$1.txt <<P
Con lo strumento di generazione immagini crea UNA immagine e salvala come assets/_codex/$1.png (orizzontale, 1536x1024, PNG con trasparenza vera: canale alpha). Allegata c'è assets/knight_idle.png: NON disegnarla, usala solo per lo stile (cartoon 2D cupo: contorni neri marcati, colori piatti con una o due tonalità d'ombra, forme semplificate, superfici sporche).

Soggetto, in inglese per il modello:
"$2 Dark 2D cartoon style with bold black outlines and flat cel shading, no gradients, no glow except where stated. The scene occupies only the LOWER part of the image; everything above the silhouettes is FULLY TRANSPARENT (real alpha), not black, not a drawn sky, no stars, no checkerboard. The left and right edges should end at similar heights so the strip can repeat. No ground plane in front, no text, no frame."

Dopo averla generata controlla con Python/Pillow: deve essere 1536x1024, modalità RGBA, e i pixel della riga più in alto devono avere alpha 0. Se lo sfondo non è trasparente, rigenerala chiedendo esplicitamente lo sfondo trasparente. Alla fine stampa percorso, dimensioni e modalità.
P
codex exec --skip-git-repo-check --sandbox workspace-write -C ~/Documenti/goblin --image assets/knight_idle.png - < assets/_codex/prompt_$1.txt > assets/_codex/codex_$1.log 2>&1
