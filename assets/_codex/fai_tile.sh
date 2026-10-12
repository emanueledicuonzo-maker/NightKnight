#!/bin/bash
# tessera quadrata opaca: $1 nome, $2 soggetto
cd ~/Documenti/goblin
cat > assets/_codex/prompt_$1.txt <<P
Con lo strumento di generazione immagini crea UNA immagine e salvala come assets/_codex/$1.png (quadrata, 1024x1024, PNG opaco). Allegata c'è assets/knight_idle.png: NON disegnarla, usala solo per lo stile (cartoon 2D cupo: contorni neri marcati, colori piatti con una o due tonalità d'ombra, forme semplificate, superfici sporche).

Soggetto, in inglese per il modello:
"$2 Dark 2D cartoon style with bold black outlines and flat cel shading, no gradients, no glow. The texture must fill the whole square edge to edge and tile seamlessly left to right (the left edge continues the right edge). No sky, no characters, no text, no frame."

Dopo averla generata controlla con Python/Pillow che sia 1024x1024. Alla fine stampa percorso e dimensioni.
P
codex exec --skip-git-repo-check --sandbox workspace-write -C ~/Documenti/goblin --image assets/knight_idle.png - < assets/_codex/prompt_$1.txt > assets/_codex/codex_$1.log 2>&1
