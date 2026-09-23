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
| Z | Colpo con l'arma scelta |
| X | Lancio del sasso |
| C | Calcio; in salto, calcio volante |
| V | Bianca: raffica di Luce (tutte le unita' da 25 disponibili) |
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

Ogni satellite e' un'unica ambientazione in tre parti: 4/5 minuti di superficie
con ondate e insidie, 2/3 minuti di prove con pochissimi nemici, 2/3 minuti di
duello contro il Guardiano, aiutato solo da pochi volanti. Regole, nemici e
tabelle dei satelliti sono in `STORY.md`.

Oggi e' giocabile **Titano**: quattro arene chiuse da porte stagne (le ondate),
geyser e laghi di metano fra un'arena e l'altra, quindici prigionieri, le prove
atletiche con tre nemici e il Guardiano, alto il doppio di NightKnight, con
alabarda e gancio. Gli altri undici satelliti usano ancora il vecchio impianto.

**Bianca** segue NightKnight e non muore. Ogni prigioniero liberato da' 5 Luce;
con `V` Bianca attraversa il cielo e scarica tutte le unita' da 25: abbatte i
volanti sullo schermo e toglie al Guardiano il 5% della vita per unita' (fino al
20%). Luce e prigionieri liberati restano anche dopo una vita persa.

Nelle prove: rincorsa con Maiusc, E per afferrare la liana o salire a cavallo,
F e G per giavellotto e pugnali sui bersagli. La porta si apre dopo le cinque prove.

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
La corsa raggiunge 5.8 pixel per fotogramma.

L'interfaccia usa font antialias inclusi nel progetto, con licenze in
`assets/fonts/`. La musica e' solo basso e percussioni leggere, sintetizzati:
in esplorazione il basso e' suonato al contrario, nel duello torna dritto. Ogni
evento ha il suo effetto (fendente, sasso, calcio, ossa, prigioniero, geyser,
porte stagne, gancio, raffica di Bianca...).

I test simulano i salti delle fosse, l'attraversamento dei geyser, i prigionieri
e la raffica di Bianca. Verificano anche il flusso
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

I test si lanciano come in **Verifica**.
