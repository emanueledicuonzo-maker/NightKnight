#!/bin/bash
# oggetto su trasparente: $1 nome, $2 soggetto, $3 formato (es. 1536x1024)
cd ~/Documenti/goblin
cat > assets/_codex/prompt_$1.txt <<P
Con lo strumento di generazione immagini crea UNA immagine e salvala come assets/_codex/$1.png ($3, PNG con trasparenza vera: canale alpha). Allegata c'è assets/knight_idle.png: NON disegnarla, usala solo per lo stile e per la scala (cartoon 2D cupo: contorni neri marcati, colori piatti con una o due tonalità d'ombra, forme semplificate, superfici sporche).

Soggetto, in inglese per il modello:
"$2 Dark 2D cartoon style with bold black outlines and flat cel shading. Transparent PNG background with real alpha: everything outside the drawn object is fully transparent, not black, not a drawn sky, no checkerboard, no ground plane, no shadow on the ground, no text, no frame."

Dopo averla generata controlla con Python/Pillow: deve essere $3, modalità RGBA, e gli angoli dell'immagine devono avere alpha 0. Se lo sfondo non è trasparente, rigenerala chiedendo esplicitamente lo sfondo trasparente. Alla fine stampa percorso, dimensioni e modalità.
P
codex exec --skip-git-repo-check --sandbox workspace-write -C ~/Documenti/goblin --image assets/knight_idle.png - < assets/_codex/prompt_$1.txt > assets/_codex/codex_$1.log 2>&1
