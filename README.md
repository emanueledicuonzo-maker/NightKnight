# NightKnight

Gioco 2D per Linux in Python e Pygame: NightKnight attraversa 12 satelliti-colonia.
Ogni livello e' un unico percorso di circa dieci minuti: le ondate, poi una
traversata piu' difficile, poi il duello contro il Guardiano. Prima della partita si sceglie una delle 12 armi; gravita', atmosfera,
fauna e insidie cambiano da satellite a satellite.
Storia e regole in `STORY.md`; stato del lavoro e prossimi passi in `HANDOFF.md`
(in inglese); prompt delle immagini in `assets/PROMPT.md`.

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
| Z | Fendente con l'arma scelta; premuto a ritmo fa una combo di tre (il terzo fa un passo avanti) |
| X | Lancio del sasso |
| C | Calcio; in salto, calcio volante |
| V | Bianca in incursione: un'unita' di Luce (25), abbatte fino a 5 nemici uno alla volta |
| B | Nova: dal 10° colono liberato, una volta per livello, spazza via tutti i nemici in scena |
| Doppio tocco di freccia tenuta, o Maiusc | Corsa: piu' veloce e salti piu' lunghi, ma l'aria cala due volte e mezzo |
| E | Afferra / lascia il cavo |
| Esc o P | Pausa / ripresa |
| M | Attiva / silenzia la musica, lasciando gli effetti |
| Su / Giu e Invio | Selezione nei menu |

La perdita del focus mette automaticamente in pausa la partita.
Dal menu di pausa si puo' tornare al titolo o uscire.

## Struttura dei livelli

Ogni satellite e' un'unica ambientazione in tre parti: 4/5 minuti di superficie
con ondate e insidie, 2/3 minuti di traversata con pochissimi nemici, 2/3 minuti di
duello contro il Guardiano, da solo, in un'arena larga due schermi. Regole, nemici e
tabelle dei satelliti sono in `STORY.md`.

Oggi e' giocabile **solo Titano**, dall'inizio alla fine: un unico percorso fra
colline e montagne da scalare (la piu' alta ha la sua scala di servizio), con due ondate, una di terra e una di volanti (non bloccano mai, si puo' scappare), e
lungo tutta la strada gruppetti di nemici continui; laghi di metano, criovulcani,
condotte d'azoto che respingono e gelano, solo quattro stazioni d'ossigeno in
tutto il livello (senz'aria non si muore, ma si rallenta, si ansima e ogni colpo
vale mezzo sasso) e quaranta prigionieri; poi la traversata,
un labirinto che non va dritto: una rupe da salire a zig-zag su tre cengie con le
scale di servizio, la cresta, le guglie dentro un lago di metano e il cavo fra
due gru, un crepaccio in cui scendere, gallerie buie (si vede solo la luce della
visiera) con un vicolo cieco, un passaggio basso e una pozza di metano, un pozzo
che risale in superficie, il doppio cavo e il triplo cavo agganciato in alto su
un lago largo (dall'altra parte si arriva solo lasciando il cavo dall'alto);
infine il duello a un round col Guardiano, alto il doppio di NightKnight, con
alabarda e gancio. Gli altri undici satelliti arriveranno.

**Bianca** segue il cavaliere e non muore. Quando sullo schermo ci sono piu' di
4 volanti parte da sola e ne abbatte fino a 5, uno alla volta, poi riposa 12
secondi. Ogni prigioniero liberato da' 5 Luce; con `V` Bianca spende un'unita' da
25 e va in incursione su volanti e nemici di terra (fino a 5); nel duello toglie
al Guardiano il 5%. Luce e prigionieri liberati restano anche dopo una vita persa.

**Nova**: i coloni liberati ricaricano il nucleo della tuta. Al decimo, una volta
per livello, `B` fa salire 9T9T in una colonna di luce: calcio girato, due
bagliori, un'onda d'urto, e tutti i nemici in scena spariscono (al Guardiano il 10%).

Il cavo si prende al volo toccandone l'impugnatura in salto; le frecce danno
slancio, Spazio lascia la presa. In salto, muovendosi, `C` e' il calcio volante
girato (da fermo resta il calcio volante semplice): colpisce tutto intorno, ma
all'atterraggio si resta scoperti per un attimo.

La telecamera segue NightKnight anche in altezza, si avvicina quando combatte
contro pochi nemici (resta larga in mezzo alla folla) e nel duello tiene in
quadro anche il Guardiano. Dietro il mondo ci sono cinque piani di parallasse con
la foschia di Titano fra l'uno e l'altro, e sagome scure in primo piano.

**Prossimo lavoro** (dettagli in `HANDOFF.md`): portare Titano a dieci minuti
con piu' azione e pianificazione (ossigeno che cala combattendo, fatica, diluvio
di metano e tempeste, meduse che si attaccano, presa al bordo), gravita' e meteo
che pesano di piu' e una sensazione dei colpi da gioco d'azione moderno.

## Progressi

`savegame.json` conserva il record e un checkpoint locale all'inizio di ogni
sezione e a ogni **tappa**: sei in superficie e sei nella traversata. Perdendo
una vita si riparte dall'ultima tappa raggiunta, e **Continua** fa lo stesso, con
vite, punteggio, arma, Luce e prigionieri liberati; le ondate gia' alle spalle
restano superate.
Una vita persa aggiorna il checkpoint. Al **game over** si sceglie fra
**Continua** (dall'ultima tappa, con tre vite, punteggio da zero) e **Nuova
partita**; il record resta. Il completamento cancella il checkpoint. Nuova partita sostituisce il checkpoint.
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

I test simulano i salti delle fosse, ogni passaggio del labirinto con la fisica
del gioco (e che le scorciatoie non esistano), la telecamera, l'attraversamento
dei geyser, i prigionieri e la raffica di Bianca. Verificano anche il flusso
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
