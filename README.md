# Goblin

Gioco 2D per Linux in Python e Pygame: 12 cimiteri, ciascuno con superficie,
cripta, prove atletiche e duello al meglio dei tre round contro un Cavaliere d'Oro.

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
| V | Cosmo, quando la barra e' piena |
| Maiusc + movimento | Rincorsa: aumenta velocita' e lunghezza del salto |
| F | Lancio del giavellotto |
| G | Lancio del pugnale |
| E | Afferra / lascia la corda, sali / scendi da cavallo |
| Esc o P | Pausa / ripresa |
| M | Attiva / silenzia la musica, lasciando gli effetti |
| Su / Giu e Invio | Selezione nei menu |

La perdita del focus mette automaticamente in pausa la partita.
Dal menu di pausa si puo' tornare al titolo o uscire.

## Prove Atletiche

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

Le corde usano [Pymunk](https://www.pymunk.org/en/latest/pymunk.constraints.html).

## Progressi

`savegame.json` conserva il record e un checkpoint locale all'inizio di ogni
sezione. **Continua riparte dall'inizio della sezione**, con vite, punteggio e
poteri del checkpoint; posizione e round in corso non vengono salvati.
Una vita persa aggiorna il checkpoint. Game over e completamento cancellano
il checkpoint, conservando il record. Nuova partita sostituisce il checkpoint.
La vittoria sul guardiano salva subito l'accesso al cimitero successivo, anche
se si esce durante la schermata dell'armatura conquistata.
Se il file non e' scrivibile viene mostrato un avviso; si puo' comunque giocare.

## Asset

I PNG in `assets/` vengono caricati automaticamente, con pixel art di riserva
per quelli mancanti. I fogli di Arthur usano 4 colonne e 2 righe. Cielo e colline
scorrono a velocita' diverse; i fondali mancanti riusano quello del cimitero precedente.
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
