# NightKnight — la storia

Protagonista **NightKnight** · compagna **Bianca** · antagonista **Luna** · 12 mondi + 1

## Sinossi

Luna si sta staccando. Ogni anno si allontana dalla Terra di quattro centimetri,
e non e' una deriva: e' una fuga. Per andarsene le serve luce, e la luce la prende
dai vivi.

Chi l'ha guardata in faccia e ha resistito conserva il corpo e perde la volonta':
cammina ancora, e lo chiamiamo zombi. Chi e' fuggito conserva la volonta' e perde
il corpo: vola, ed e' un corvo nero. I corvi neri sono dalla parte di NightKnight —
non attaccano, si radunano, si alzano in massa qualche istante prima che compaia il
Guardiano. Sono l'unica cosa che avverte.

Poi ci sono quelli che Luna ha beccato a meta' volo, sbiancandoli prima che la
trasformazione finisse. Uno di loro ha scelto NightKnight, e si chiama Bianca.

Dodici satelliti hanno risposto alla chiamata di Luna. Su ciascuno ha lasciato un
Guardiano in armatura d'oro e un cimitero pieno di quello che resta degli uomini.
NightKnight porta l'ultima armatura d'argento lunare mai forgiata: metallo suo, che
lei puo' richiamare. Per arrivare fino a lei deve attraversare i dodici mondi,
imparare a muoversi sotto la loro gravita' e battere ogni Guardiano. Quando cade
l'ultimo, tra i due resta solo il cielo.

## Le tre regole

**Perche' si perde l'armatura.** E' forgiata con l'argento di Luna. Ogni colpo
incassato e' un pezzo che lei si riprende. Sotto non c'e' un eroe indebolito: c'e'
un uomo che corre piu' veloce e muore prima.

**La barra speciale si chiama Albedo.** In astronomia l'albedo e' quanta luce un
corpo rimanda indietro. NightKnight non produce energia: accumula quella che gli
viene tirata addosso e la restituisce. Serve per l'ultima fase dello scontro finale.

**Ogni mondo pesa diverso.** Le gravita' sono quelle vere. Le prove atletiche
prima di ogni duello servono a imparare quanto si salta su quel satellite. Non sono
un intermezzo: sono il tutorial di un mondo che cambia sotto i piedi.

## Schermata d'apertura

> Quattro centimetri l'anno.
>
> Nessuno se n'era accorto: nessuno guarda in alto abbastanza a lungo.
>
> Quando ce ne siamo accorti, chi aveva resistito camminava gia' senza parlare,
> e chi era fuggito aveva le ali.
>
> Dodici satelliti hanno risposto alla sua chiamata. Uno solo ha risposto alla nostra.
>
> Ti abbiamo forgiato un'armatura con il suo stesso argento.
>
> Lei se la riprendera', pezzo per pezzo.
>
> Non sarai solo: qualcosa di bianco ti sta gia' seguendo.

## Bianca

Un corvo bianco, colpito da Luna a meta' trasformazione e rimasto fra le due forme.
Segue NightKnight dal primo cimitero e non lo lascia piu'. All'inizio e' piccola e
non combatte.

Ogni dieci zombi abbattuti Bianca cresce — **per tutta la campagna, non per livello**.
Il conteggio vive in `progress.py` insieme al checkpoint: e' quello che la rende una
compagna invece di un potenziamento. Se un Guardiano la prende cade stordita e torna
dopo venti secondi. Non muore mai.

Porta anch'essa il nome di un satellite di Urano, come i Guardiani. E' l'unica che lo
porta senza servire Luna.

| Zombi | Stadio | Cosa fa |
| --- | --- | --- |
| 0–9 | pulcino | segue e osserva, non combatte |
| 10–29 | giovane | becca gli zombi che arrivano da dietro |
| 30–59 | adulta | attacca in picchiata: zombi, scheletri, fantasmi |
| 60+ | grande | quasi alta quanto NightKnight, l'unica che puo' colpire un Guardiano |

La scala cresce in continuo a ogni decina; lo sprite cambia solo ai quattro stadi.

## I dodici mondi

Ogni Guardiano porta il nome del satellite che difende ed e' alto **il doppio** di
NightKnight. Il duello si vince al meglio dei tre round.

Le gravita' sono quelle reali. «Salto xN» e' l'altezza raggiunta rispetto alla Terra
(9,81 m/s²) a parita' di spinta.

| # | Mondo | Elemento | Gravita' | Salto | Arma |
| --- | --- | --- | --- | --- | --- |
| 01 | Titano | Nebbia · Saturno | 1,352 m/s² | x7,3 | spada lunga |
| 02 | Nix | Corvi · Plutone | 0,003 m/s² | x3270 | ascia bipenne |
| 03 | Io | Fuoco · Giove | 1,796 m/s² | x5,5 | martello infuocato |
| 04 | Europa | Gelo · Giove | 1,315 m/s² | x7,5 | lancia di ghiaccio |
| 05 | Rea | Radici · Saturno | 0,264 m/s² | x37 | catene con uncini |
| 06 | Caronte | Ossa · Plutone | 0,288 m/s² | x34 | arco d'osso |
| 07 | Ganimede | Tuono · Giove | 1,428 m/s² | x6,9 | due lame elettriche |
| 08 | Fobos | Sangue · Marte | 0,0057 m/s² | x1721 | bastone lungo rosso |
| 09 | Nereide | Abisso · Nettuno | 0,072 m/s² | x136 | falce gigante |
| 10 | Miranda | Peste · Urano | 0,079 m/s² | x124 | mazza chiodata |
| 11 | Umbriel | Ombra · Urano | 0,200 m/s² | x49 | artigli di metallo |
| 12 | Oberon | Il Re · Urano | 0,346 m/s² | x28 | scettro dorato |

**Titano** — l'unico satellite con un'atmosfera vera, cosi' densa e arancione che
dalla superficie il cielo non esiste. Piove metano. Il cimitero e' sul fondo di un
lago che non bagna, e il Guardiano combatte dentro la sua stessa foschia: lo vedi
solo quando colpisce.

**Nix** — porta il nome della dea greca della notte e ruota in modo caotico, senza
mai presentare la stessa faccia due volte. La gravita' e' quasi assente: i corvi non
volano, restano sospesi. Primo mondo dove saltare e' piu' pericoloso che restare a
terra.

**Io** — il corpo piu' vulcanico del sistema solare: quattrocento vulcani attivi,
pennacchi di zolfo alti trecento chilometri, una superficie che si rifa' da capo ogni
pochi secoli. Nessuna tomba resta al suo posto. Il Guardiano difende l'unico punto
che non brucia.

**Europa** — crosta di ghiaccio spessa chilometri sopra un oceano d'acqua liquida
piu' grande di tutti i mari della Terra messi insieme. I morti non sono sepolti: sono
sospesi nel ghiaccio, visibili, alla profondita' in cui sono caduti.

**Rea** — dalla titanessa che nascose il figlio per sottrarlo al padre che lo avrebbe
divorato. Unico mondo dove qualcosa cresce ancora, e cresce sbagliato: radici che si
muovono, edera che stringe. Il Guardiano aspetta che sia il terreno a tenerti fermo.

**Caronte** — il traghettatore. E' cosi' grande rispetto a Plutone che i due non si
orbitano: girano attorno a un punto vuoto sospeso fra loro. Qui arrivano i morti di
tutti gli altri mondi, e il Guardiano tiene il conto.

**Ganimede** — il satellite piu' grande del sistema solare, piu' grande di Mercurio,
l'unico con un campo magnetico proprio. Ha aurore che oscillano quando Giove lo
schiaccia. Il duello si combatte a intermittenza, fra un lampo e il buio che segue.

**Fobos** — il Terrore, figlio del dio della guerra. Sta cadendo su Marte di due
centimetri l'anno e fra qualche decina di milioni di anni si spacchera' in un anello
di detriti. E' gia' segnato: lo sa, e combatte come chi non ha niente da conservare.

**Nereide** — ninfa degli abissi, e l'orbita piu' eccentrica del sistema solare: da un
milione e mezzo a quasi dieci milioni di chilometri da Nettuno. Per tre quarti del suo
anno e' nel buio totale. Il Guardiano combatte solo lontano dalla luce.

**Miranda** — sembra fatta di pezzi di mondi diversi incollati male, come se fosse
esplosa e si fosse rimessa insieme sbagliando. Ci sta Verona Rupes, la rupe piu' alta
conosciuta: venti chilometri di caduta verticale.

**Umbriel** — il satellite piu' scuro conosciuto: riflette meno del sedici per cento
della luce che riceve, e nessuno sa perche'. Il nome viene da *umbra*. Unico mondo
dove l'Albedo non si carica: qui la luce non torna indietro, e si vince senza.

**Oberon** — il re. Ultimo satellite prima del vuoto, il piu' esterno fra i grandi di
Urano, con una montagna alta undici chilometri che si staglia contro il nero quando
il satellite passa davanti al pianeta. Il duello finale dei dodici si combatte lassu'.

### Nota di bilanciamento

Nix (x3270) e Fobos (x1721) non sono giocabili con i valori veri: un salto
attraverserebbe il livello intero. Servono due mondi a fisica speciale — su Nix ci si
spinge dalle superfici invece di saltare, su Fobos si resta ancorati e si combatte in
caduta — oppure un tetto alla velocita' verticale in `levels.py`. Gli altri dieci
stanno fra x5,5 e x136: scalabili con un solo moltiplicatore per livello.

## Luna — il tredicesimo satellite

Non ha un Guardiano perche' e' lei. Dopo Oberon non c'e' un altro cimitero: c'e' il
cielo, e il salto che lo attraversa. Alta **tre volte** NightKnight, una volta e
mezza qualunque Guardiano.

Porta quattro armi. Le prime tre sono quelle che ha prestato ai suoi — fuoco,
ghiaccio, vento — e si schivano. La quarta e' la luce che ha rubato per dodici mondi,
e quella non si schiva.

| Fase | Arma | Come si batte |
| --- | --- | --- |
| 1 | Fuoco | schivare, colpire nelle pause fra le ondate |
| 2 | Ghiaccio | il terreno diventa scivoloso: torna utile il salto con rincorsa |
| 3 | Vento | tiene lontano: da soli non la si raggiunge, ci si arriva in volo su Bianca |
| 4 | Luce | non si schiva e non si para: si rimanda indietro con l'Albedo |

La fase 3 e' il pagamento di Bianca. Se il giocatore l'ha cresciuta fino allo stadio
grande, vola; se l'ha trascurata, la fase 3 e' un muro. E' l'unico punto del gioco
dove la compagna non e' un aiuto ma la condizione per proseguire — e c'e' un conto in
sospeso, perche' e' Luna che l'ha sbiancata a meta' volo.

## Le discipline sono abilita'

Le prove non sono un livello a parte: sono **dove NightKnight impara**. Ogni
disciplina sblocca un'abilita' permanente, che da quel momento si usa nei cimiteri
per attraversare posti dove prima non si passava. Un mondo gia' visitato torna
percorribile in modo nuovo.

L'input e' alla *Decathlon*: si alterna rapidamente Z e X per caricare, e si
cronometra il rilascio. Non e' un tasto che esegue l'abilita': e' lo sforzo che la
produce.

### La rincorsa e' il verbo

Non e' un'abilita' fra le altre: e' la barra che le alimenta quasi tutte. Si carica
correndo, e **il contesto decide cosa ne esce**. Stesso input, quattro mosse.

| Se davanti c'e' | Esce |
| --- | --- |
| un fosso | salto in lungo |
| un ostacolo alto | salto in alto — piu' e' alto, piu' rincorsa serve |
| una liana a portata | lancio in volo |
| un Guardiano | sprint con la spada alzata |

### Fase 1 — gli otto mondi che insegnano

Ogni mondo insegna l'abilita' di cui ha bisogno: e' l'ostacolo del posto a rendere
necessaria proprio quella.

| Mondo | Disciplina | Abilita' | Perche' proprio li' |
| --- | --- | --- | --- |
| 01 Titano | salto in lungo | **Rincorsa** | nella nebbia il fosso non si vede: ci si fida della spinta, non degli occhi |
| 02 Nix | liana | **Presa** | gravita' quasi nulla, non si atterra: ci si aggrappa. Da qui la liana lancia anche in alto |
| 03 Io | salto in alto | **Salto in alto** | la gravita' piu' alta dei dodici, e le colate da scavalcare |
| 04 Europa | giavellotto | **Giavellotto** | sul ghiaccio non ci si avvicina: raggiunge un Guardiano da meta' arena |
| 05 Rea | pugnali | **Pugnali** | fra le radici serve un taglio corto e veloce |
| 06 Caronte | lancio del disco | **Disco** (arma che si vince) | il traghettatore va e torna, e cosi' il disco: colpisce all'andata e al ritorno |
| 07 Ganimede | corsa con spada alzata | **Sprint d'assalto** | si carica nel buio fra un lampo e l'altro |
| 08 Fobos | ostacoli a cavallo | **Cavalcata** | dove non pesi niente il cavallo non si ferma piu' |

Il **disco** e' l'unica disciplina che consegna un'arma invece di un movimento. Uno
solo in aria per volta.

### Fase 2 — gli ultimi quattro misurano

Su Nereide, Miranda, Umbriel e Oberon le prove diventano **record**. Si ripetono per
migliorare l'abilita': rincorsa piu' lunga, disco piu' veloce, presa piu' salda. La
gravita' del mondo entra nel punteggio, quindi il record di Miranda non e'
confrontabile con quello di Io — ogni satellite ha la sua classifica.

Le discipline non restano nell'area delle prove: un fosso da salto in lungo, un muro
da salto in alto, una liana sopra una voragine compaiono dentro ai cimiteri, ogni
tanto, dal mondo in cui sono state imparate in poi.

## Nomi e diritti

I nomi dei satelliti, le loro gravita' e i miti greci a cui sono intitolati sono di
pubblico dominio. Il gioco nasce come omaggio a *Ghosts 'n Goblins* e a *I Cavalieri
dello Zodiaco*, ma non usa nomi ne' elementi di quelle opere: il protagonista e'
NightKnight, la barra speciale si chiama Albedo, i dodici sono Guardiani e portano
nomi di lune vere.
