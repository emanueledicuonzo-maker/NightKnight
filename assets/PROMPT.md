# Immagini per Goblin — cartella assets/, nomi esatti, PNG

## Prefisso per personaggi e oggetti
Usa come riferimento di stile l'immagine gia presente in questa cartella:
`ChatGPT Image 15 set 2026, 20_12_25.png`.

Stile: render/illustrazione 3D iperrealistica dark fantasy, qualita da poster premium,
armature metalliche consumate e sporche, dettagli realistici di graffi, sangue secco, pelle,
barba/capelli e cuoio, luce lunare fredda con rim light blu, contrasto alto, silhouette leggibile
per un gioco a scorrimento laterale. Non pixel art, non cartoon, non anime, non low-poly.

Per personaggi, nemici e oggetti: sfondo TRASPARENTE reale (PNG alpha), nessun terreno, nessuna
ombra sul pavimento, soggetto intero visto di lato, RIVOLTO A DESTRA, centrato, 1024x1024 salvo
dimensioni diverse specificate sotto. Mantieni la stessa identita visiva di Arthur del riferimento:
cavaliere massiccio in armatura d'argento usurata, barba rossa/castana, panno cremisi, luce blu
sui bordi.

## Arthur (cavaliere con armatura d'argento, barba rossa, elmo)
arthur_idle.png       in piedi in guardia
arthur_run1.png       corsa, gamba destra avanti
arthur_run2.png       corsa, gamba sinistra avanti
arthur_jump.png       salto, ginocchia piegate
arthur_throw.png      lancia la lancia, braccio teso in avanti
arthur_punch.png      pugno teso in avanti stile Street Fighter
arthur_kick.png       calcio alto in avanti
arthur_hurt.png       colpito, piegato all'indietro
arthur_special.png    braccia aperte, aura di energia dorata (Cosmo)
arthur_climb.png      si arrampica su una scala, mani in alto
arthur_nude_idle.png / _run1 / _run2 / _jump / _throw : stesse pose SENZA armatura,
                      in mutande bianche a cuori rossi, elmo perso

## Nemici
zombie_walk1.png, zombie_walk2.png      zombie putrefatto braccia tese, due fasi del passo
skeleton_walk1.png, skeleton_walk2.png  scheletro con spada arrugginita
crow_1.png, crow_2.png                  corvo nero occhi rossi, ali in alto / ali in basso

## Boss cimitero 1 — Cavaliere della Nebbia
armatura grigio-argento corrosa, mantello fatto di nebbia, elmo con corna, occhi azzurri luminosi
boss01_idle.png, boss01_walk.png, boss01_attack.png (artiglio/spada in avanti),
boss01_special.png (lancia energia), boss01_hurt.png, boss01_ko.png (a terra)
(Per i cimiteri 2..12: boss02_*.png ... boss12_*.png, vedi nomi in levels.py)

## Oggetti (trasparenti)
lance.png    lancia medievale orizzontale, punta a destra, 1024x256
pot.png      anfora di terracotta antica, 512x512
chest.png    forziere di legno e ferro chiuso, 512x512
door.png     portale di pietra di una cripta, socchiuso, luce verde dentro, 512x1024
tomb1.png, tomb2.png   lapidi antiche muschiose, 512x512
cross.png    croce di pietra storta, 512x512
tree.png     albero morto contorto, 1024x2048

## Tile del terreno (512x512, SENZA trasparenza, bordi che si ripetono)
ground_grass.png   erba scura e terra in sezione, cimitero notturno
ground_dirt.png    solo terra scura con radici e ossa
slab.png           lastra di pietra tombale grigia vista di lato (piattaforma)
stone_wall.png     muro di pietra di cripta, muschio
ladder.png         scala a pioli di legno vecchio, trasparente ai lati
spikes.png         punte di ferro dal basso, trasparente sopra

## Fondali 1920x1080
sky_01.png       cielo notturno, luna piena enorme, castello gotico su rupe, pipistrelli
hills_01.png     colline nebbiose con lapidi e alberi morti in silhouette, cielo TRASPARENTE
crypt_bg_01.png  interno di cripta: colonne, teschi, torce verdi
arena_bg_01.png  radura del cimitero con lapidi e nebbia, luna: il duello
(Per i cimiteri successivi: sky_02.png ... ecc. Se mancano si riusa il precedente.)
