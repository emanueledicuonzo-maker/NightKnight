# NightKnight

Gioco 2D per Linux in Python e Pygame: NightKnight attraversa 12 satelliti-colonia,
ognuno con superficie, prove atletiche e duello contro un Guardiano. Ogni livello
dura circa dieci minuti: cinque di superficie, due o tre di prove e due o tre di
duello. Prima della partita si sceglie una delle 12 armi; gravita', atmosfera,
fauna e insidie cambiano da satellite a satellite.
Storia completa in `STORY.md`.

## Avvio

```sh
./goblin.sh
./goblin.sh --windowed
```

La risoluzione logica e' 1920x1080. L'avvio normale usa lo schermo intero.
L'ambiente `.venv` presente nella cartella contiene gia' le dipendenze.
Per ricrearlo: `python3 -m venv .venv`, poi `.venv/bin/pip install -r requirements.txt`.

## Comandi

| Tasto | Azione |
| --- | --- |
| Frecce o WASD | Movimento e scale |
| Spazio / Su / W | Salto; tenere premuto per saltare piu' in alto |
| Z | Affondo di lancia |
| X | Pugno |
| C | Calcio |
| V | Bianca: raffica di luce, consumando 25 Luce per un'unita' |
| Maiusc + movimento | Rincorsa: aumenta velocita' e lunghezza del salto |
| F | Lancio del giavellotto |
| G | Lancio del pugnale |
| E | Afferra / lascia la corda, sali / scendi da cavallo |
| Esc o P | Pausa / ripresa |
| M | Attiva / silenzia la musica, lasciando gli effetti |
| Su / Giu e Invio | Selezione nei menu |

La perdita del focus mette automaticamente in pausa la partita.
Dal menu di pausa si puo' tornare al titolo o uscire.

## Struttura dei livelli

Ogni satellite ha tre parti: cinque minuti di superficie con ondate e insidie,
due o tre minuti di prove ambientali e due o tre minuti di duello contro il
Guardiano. La superficie usa due nemici volanti, tre terrestri e quattro insidie
scelti dai pool descritti in `STORY.md`.

Bianca segue NightKnight e non muore. Ogni prigioniero illuminato dà 5 Luce;
premendo `V`, una raffica costa 25 Luce, colpisce tutti i volanti presenti e il
Guardiano. Ogni unità infligge il 5% della vita massima del Guardiano, fino al 20%
con una barra piena.

Le prove riusano il terreno del satellite: massi, laghi, liane, cavi, ponti,
piattaforme, gravita' e ostacoli. I nuovi fondali, nemici e pericoli sono ancora
asset da creare; `STORY.md` è la specifica di riferimento.

<!-- Sezione storica dell'implementazione precedente, conservata temporaneamente.

Da **Nuova partita**, la superficie di Titano contiene tre geyser, quattro
Spenti e tre scheletri. I geyser iniziano ad attivarsi quando ci si avvicina:
3 secondi di riposo, 1,5 secondi di sfiato innocuo, 1,5 secondi di eruzione.
Il getto infligge 25 danni; nella pausa si puo' attraversare a passo normale.
I laghi si saltano e le rive prima del salto sono libere dai getti.

Passare vicino a uno Spento lo illumina e aggiunge 20 punti di Albedo, una sola
volta per tentativo. Questi Spenti usano temporaneamente lo sprite zombi
ricolorato. Alla ripartenza della sezione si azzerano sia le liberazioni sia
l'Albedo: crescita persistente di Bianca e nuovi salvataggi arriveranno dopo.
I geyser di acqua/ammoniaca sono una reinterpretazione fantascientifica.

Dal titolo, **Prove atletiche** avvia una nuova partita direttamente sul percorso
delle prove e sostituisce il checkpoint precedente. Nella campagna il percorso
si trova tra cripta e duello. Comprende cinque specialita': salto in lungo con
rincorsa, attraversamento con liana, ostacoli a cavallo, tre bersagli per il
giavellotto e tre per i pugnali. La porta si apre dopo tutte e cinque le prove;
il tempo impiegato determina un bonus finale.

Per la liana, salta verso la corda e premi E per afferrarla. Le frecce danno
slancio; Spazio lascia la presa conservando velocita'. A cavallo, Spazio salta
gli ostacoli ed E permette di scendere quando si e' a terra. I bersagli accettano
solo l'arma della loro specialita'. I lanci sono disponibili anche fuori dalle
prove. Perdere una vita ricomincia la sezione, comprese le prove.

> Questa e' l'implementazione attuale: cinque prove in un percorso a se'.
> Il progetto in `STORY.md` le trasforma in otto discipline che sbloccano
> abilita' permanenti, usate poi dentro ai cimiteri. Non ancora implementato.

Le corde usano [Pymunk](https://www.pymunk.org/en/latest/pymunk.constraints.html).

-->

## Progressi

`savegame.json` conserva il record e un checkpoint locale all'inizio di ogni
sezione. **Continua riparte dall'inizio della sezione**, con vite, punteggio,
arma e Luce del checkpoint; posizione e round in corso non vengono salvati.
Una vita persa aggiorna il checkpoint. Game over e completamento cancellano
il checkpoint, conservando il record. Nuova partita sostituisce il checkpoint.
La vittoria sul Guardiano salva subito l'accesso al satellite successivo, anche
se si esce durante la schermata della ricompensa.
Se il file non e' scrivibile viene mostrato un avviso; si puo' comunque giocare.

## Asset

I PNG in `assets/` vengono caricati automaticamente, con pixel art di riserva
per quelli mancanti. Gli asset conservati sono scheletri, corvi e prigionieri
illuminati; i nuovi disegni di NightKnight, Bianca, Guardiani, satelliti e fauna
mutante sono descritti in `STORY.md`.
Le specifiche grafiche sono in `assets/PROMPT.md`.

## Giocabilita'

Il salto accetta un piccolo ritardo dopo il bordo (6 fotogrammi) e memorizza
una pressione poco prima dell'atterraggio (7 fotogrammi). Rilasciare il tasto
riduce l'altezza senza troncare il salto. Anche una pressione breve, partendo
da fermo e muovendosi verso il bordo, supera le fosse generate (2-3 celle).
La corsa raggiunge 5.8 pixel per fotogramma; le punte delle cripte sono
dimensionate per essere superate con la velocita' attuale di Arthur.

L'interfaccia usa font antialias inclusi nel progetto, con licenze in
`assets/fonts/`. La musica usa accordi ambient minori, campane soffuse e
percussioni nei duelli, a volume ridotto rispetto agli effetti.

I test simulano i salti delle fosse in entrambe le direzioni e un percorso
senza danni da punte nelle 12 cripte, senza nemici. Verificano anche il flusso
di ricompense fino al finale; non sostituiscono una partita completa per
valutare difficolta' dei combattimenti e ritmo.

## Verifica

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m unittest discover -s tests
```

## Licenza

Codice sorgente: **MIT** (vedi `LICENSE`). Immagini e suoni in `assets/`: **CC0 1.0**,
cioe' pubblico dominio. Puoi usare, modificare, forkare e ridistribuire tutto,
anche a scopo commerciale, senza chiedere permesso.

Nota per chi forka: i nomi dei personaggi e alcuni elementi di scena sono un omaggio
a *Ghosts 'n Goblins* e a *I Cavalieri dello Zodiaco*, che sono marchi dei rispettivi
proprietari. La licenza qui sopra copre il codice e i render originali di questo
repository, non quei marchi: se pubblichi la tua versione, conviene darle nomi propri.

## Contribuire

Ogni contributo e' benvenuto: forka, apri una pull request, oppure apri una issue
per proporre un'idea o segnalare un bug. Non serve chiedere il permesso prima.

Per far girare il progetto in locale:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./goblin.sh --windowed
```

I test si lanciano con `.venv/bin/python -m pytest`.
