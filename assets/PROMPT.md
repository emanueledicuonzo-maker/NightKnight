# Immagini per NightKnight — cartella assets/, nomi esatti, PNG

Storia, personaggi e meccaniche: vedi `../STORY.md`.

## Prefisso di stile (vale per ogni immagine)

Render/illustrazione 3D iperrealistica dark fantasy, qualita' da poster premium,
armature metalliche consumate e sporche, dettagli realistici di graffi, sangue secco,
pelle, barba/capelli e cuoio, luce lunare fredda con rim light blu, contrasto alto,
silhouette leggibile per un gioco a scorrimento laterale. Non pixel art, non cartoon,
non anime, non low-poly.

Per personaggi, nemici e oggetti: sfondo TRASPARENTE reale (PNG alpha), nessun
terreno, nessuna ombra sul pavimento, soggetto intero visto di lato, RIVOLTO A
DESTRA, centrato, 1024x1024 salvo dimensioni diverse specificate sotto.

**Scala dei personaggi**, da rispettare come proporzione relativa:
`NightKnight 1x · Guardiano 2x · Luna 3x`

## NightKnight (protagonista) — GIA' FATTO

Cavaliere massiccio in armatura d'argento usurata, barba rossa/castana, panno
cremisi, luce blu sui bordi. File `knight_*.png` e `knight_nude_*.png` (senza
armatura, in mutande bianche a cuori rossi, elmo perso). Completo, non rigenerare.

## Bianca (compagna) — DA FARE, 8 immagini

Corvo **sbiancato, non albino**: piumaggio grigio-perla con le punte delle ali e
della coda ancora nere, come se la trasformazione si fosse fermata a meta'. Occhi
scuri, vivi. Deve distinguersi dai corvi neri anche in controluce.

Quattro stadi di crescita, due fotogrammi di volo ciascuno (ali in alto / ali in
basso). Pulcino e giovane possono condividere la posa e cambiare solo proporzioni.

    bianca_chick_1.png   bianca_chick_2.png    pulcino, piume arruffate, becco corto, testa grande
    bianca_young_1.png   bianca_young_2.png    giovane, ali complete, corpo ancora magro
    bianca_adult_1.png   bianca_adult_2.png    adulta, apertura alare ampia, posa in picchiata
    bianca_great_1.png   bianca_great_2.png    grande, quasi alta quanto NightKnight, 1024x1024

## I 12 Guardiani (boss) — 1024x1024, rivolti a DESTRA

Armatura d'oro completa, mantello, elmo. **Alti il doppio di NightKnight**: la
proporzione si legge nell'immagine, non solo in gioco.

Nove pose per ognuno, `bossNN_<posa>.png` con NN = 01..12:

    idle      in guardia da combattimento
    walk      passo
    jump      calcio volante
    punch     pugno teso
    kick      calcio alto
    attack    colpo con la propria arma
    special   usa l'arma a distanza
    hurt      colpito, piegato all'indietro
    ko        a terra

Genera **prima l'idle** di ciascun Guardiano e usalo come riferimento visivo per le
sue otto pose successive: armatura, colori, arma e proporzioni devono restare
identici all'interno dello stesso boss.

    boss01  Guardiano di Titano     Nebbia    spada lunga, mantello di nebbia, occhi azzurri
    boss02  Guardiano di Nix        Corvi     ascia bipenne, piume nere sull'elmo
    boss03  Guardiano di Io         Fuoco     martello da guerra infuocato
    boss04  Guardiano di Europa     Gelo      lancia di ghiaccio, brina sull'armatura
    boss05  Guardiano di Rea        Radici    catene con uncini, edera sull'armatura
    boss06  Guardiano di Caronte    Ossa      arco d'osso e frecce, elmo a teschio
    boss07  Guardiano di Ganimede   Tuono     due lame corte elettriche
    boss08  Guardiano di Fobos      Sangue    bastone lungo rosso, armatura macchiata
    boss09  Guardiano di Nereide    Abisso    falce gigante, armatura viola scuro
    boss10  Guardiano di Miranda    Peste     mazza chiodata, armatura verde corrosa
    boss11  Guardiano di Umbriel    Ombra     artigli di metallo, armatura nera e oro
    boss12  Oberon, il Re           —         scettro dorato, corona, l'armatura piu' ricca

### Stato attuale

    boss01  fatte: idle walk attack special hurt   mancano: jump punch kick ko
    boss02  fatte: idle                            mancano: le altre 8
    boss03  fatte: idle                            mancano: le altre 8
    boss04..boss12  nessuna: 9 pose ciascuno

Ordine consigliato: prima **un idle per boss04..boss12** (9 immagini), cosi' tutti e
dodici i mondi diventano giocabili; poi si riempiono le pose.

## Luna (boss finale) — 1024x2048 VERTICALE

Alta tre volte NightKnight. A 1024x1024 si perderebbero volto e armatura una volta
scalata in gioco: generare in verticale.

Figura femminile enorme in armatura bianco-argentea, luce fredda che le esce
dall'interno attraverso le fessure dell'armatura. Quattro fasi che ne cambiano
l'aspetto, non solo l'attacco:

    luna_idle.png        in piedi, prima che cominci
    luna_fire_1/2.png    fase 1, armatura arroventata, fuoco dalle giunture
    luna_ice_1/2.png     fase 2, brina che le cresce addosso, respiro gelato
    luna_wind_1/2.png    fase 3, capelli e mantello orizzontali, aria visibile
    luna_light_1/2.png   fase 4, tutta la luce rubata che le esce dalle crepe
    luna_hurt.png        colpita
    luna_ko.png          a terra

`luna_light` e' l'immagine piu' importante del gioco: e' l'unica volta in cui il
giocatore vede dove e' finita la luce delle persone incontrate per dodici mondi.
Generarla per ultima, quando lo stile delle altre e' assestato.

## Nemici — GIA' FATTI tranne i fantasmi

    zombie_walk1/2.png      zombie putrefatto, braccia tese, due fasi del passo
    skeleton_walk1/2.png    scheletro con spada arrugginita
    crow_1/2.png            corvo NERO, occhi scuri, ali in alto / ali in basso
    ghost_1/2.png           DA FARE: fantasma bianco-azzurro semitrasparente,
                            lenzuolo strappato, occhi neri vuoti,
                            braccia tese / braccia alzate

I corvi neri sono alleati: non attaccano, si radunano e si alzano in massa prima che
compaia il Guardiano. Non devono sembrare minacciosi.

## Oggetti — GIA' FATTI

    lance.png    lancia medievale orizzontale, punta a destra, 1024x256
    door.png     portale di pietra di una cripta, socchiuso, luce verde dentro, 512x1024
    tomb1/2.png  lapidi antiche muschiose, 512x512
    cross.png    croce di pietra storta, 512x512
    tree.png     albero morto contorto, 1024x2048

## Tile del terreno — GIA' FATTI (512x512, senza trasparenza, bordi ripetibili)

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

Per i mondi successivi: `sky_02.png` e seguenti. Se mancano si riusa il precedente.
Ogni satellite ha un cielo suo — su Titano il cielo non si vede affatto (foschia
arancione), su Nix e Caronte si vede Plutone enorme, su Io si vede Giove, su Umbriel
il buio quasi totale.
