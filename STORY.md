# NightKnight — direzione narrativa

## Premessa

NightKnight è un cavaliere errante in un sistema di dodici satelliti-colonia.
Indossa un'armatura di sopravvivenza costruita come una corazza antica: elmo
sigillato, piastra, guanti, schinieri e mantello. La tecnologia lo tiene vivo,
ma la sua forma resta quella di un cavaliere.

Il mondo unisce avventura arcade, dodici Guardiani rituali e fantascienza
psicologica: colonie abbandonate, memorie poco affidabili, tecnologie diventate
religione e persone trasformate dall'ambiente. I satelliti non sono cimiteri
fantasy: sono miniere, stazioni, serre, laboratori e palazzi ormai morti.

Il simbolo di NightKnight è un teschio sopra due mezzelune incrociate, una rivolta
verso l'alto e una verso il basso. È dipinto sulla spalla dell'armatura.

## Struttura di ogni satellite

Ogni satellite dura circa dieci minuti e ha tre parti:

1. **Superficie — circa 5 minuti.** Esplorazione, atmosfera, insidie e ondate di
   nemici. La sequenza cresce da pochi scheletri a gruppi numerosi, poi a un
   cavaliere 2×, a uno sciame volante e infine a un cavaliere 3×.
2. **Prove — 2/3 minuti.** Salti sui massi, corsa, liane, cavi, laghi,
   piattaforme e ostacoli costruiti attorno alla gravità e all'atmosfera locale.
3. **Guardiano — 2/3 minuti.** Un duello contro il cavaliere che governa il
   satellite. La sua armatura e il suo stile usano l'ambiente del mondo.

La superficie sceglie **2 nemici volanti, 3 terrestri e 4 insidie** dai tre pool
condivisi. Ogni satellite mescola gli elementi in modo diverso.

## Nemici

Gli scheletri restano la famiglia principale: scheletri normali in gruppi da
10–20, scheletri volanti, cavalieri-scheletro 2× e cavalieri-scheletro 3×.

La fauna terrestre aggiunge animali mutanti adattati alle colonie: cani da cava
senza occhi, ratti corazzati, lucertole criogeniche, cinghiali minerari, ragni da
condotto e vermi di silicio. Nel cielo compaiono corvi necrofagi, pipistrelli del
vuoto, arpie di ferraglia, meduse atmosferiche, falene ossee, droni becchino e
angeli corrosi.

## Bianca

Bianca conserva la sua funzione di compagna: segue NightKnight, osserva il
percorso e non può morire. Ora è anche l'arma contro gli sciami volanti.

I prigionieri illuminati sono coloni rimasti bloccati nelle capsule e nelle
strutture delle colonie. Liberarne uno dà **5 Luce**. Premendo `V`, Bianca si
illumina, vola sopra lo schermo e colpisce tutti i nemici volanti presenti e il
Guardiano.

Ogni unità da **25 Luce** vale il **5% della vita massima del Guardiano**. Una
barra piena vale quattro unità, quindi una raffica completa può togliere al
massimo il 20% della vita del Guardiano. La Luce è consumata dalla raffica e si
ricarica liberando altri prigionieri. Bianca non muore e non può essere eliminata
dal combattimento.

## Pool delle insidie

Le insidie sono: geyser, nube ossea, ossigeno scarso, crepacci, vento di frattura,
pioggia di detriti, gas criogenico o corrosivo, piastre magnetiche, porte stagne,
pavimenti instabili, tubi in pressione, sirene psichiche, pozze conduttive e
altri fenomeni specifici del satellite.

L'ossigeno è una risorsa di pressione: scende nelle zone contaminate o senza aria
e si recupera nelle cupole, nelle stazioni e vicino ai terminali funzionanti.

## I dodici satelliti

| # | Satellite | Identità visiva | Arma più adatta |
| --- | --- | --- | --- |
| 01 | Titano | Nebbia arancione, laghi di metano, torri d'estrazione | Spada termica |
| 02 | Nix | Buio quasi totale, ripetitori e neve grigia | Lancia luminosa |
| 03 | Io | Zolfo, vulcani, miniere incandescenti | Martello sismico |
| 04 | Europa | Crosta di ghiaccio, oceano sotterraneo, laboratori | Falce a fusione |
| 05 | Rea | Anelli di Saturno, raffinerie, radici mutanti | Arco magnetico |
| 06 | Caronte | Stazioni di transito, ghiaccio e luce fredda | Scettro aurorale |
| 07 | Ganimede | Aurore, piloni elettrici, città industriale | Mazza magnetica |
| 08 | Fobos | Cava marziana, ascensore orbitale crollato | Balestra cinetica |
| 09 | Nereide | Neve di metano, serre e cupole biologiche | Tridente termico |
| 10 | Miranda | Canyon verticali, ponti e quartieri spezzati | Frusta a impulsi |
| 11 | Umbriel | Eclissi, monoliti e cappella tecnologica | Pugnale dell'eclissi |
| 12 | Oberon | Foresta morta, palazzo-colonia e treno reale | Spada orbitale |

Le armi sono dodici reliquie da cavaliere reinterpretate dalla tecnologia delle
colonie. La scelta iniziale è importante: l'arma affine all'ambiente causa danni
pieni, mentre una scelta sbagliata rende i nemici molto più resistenti.

## Asset esistenti e nuovi disegni

Restano come base visiva gli scheletri, i corvi e i prigionieri illuminati. Sono
nuovi invece NightKnight, Bianca, le varianti volante/2×/3× degli scheletri, gli
animali mutanti, i Guardiani, i fondali dei satelliti, i terreni e le insidie.

Questa è una specifica narrativa e visiva. L'implementazione delle nuove ondate,
dell'ossigeno, delle prove satellitari e dell'attacco di Bianca viene dopo la
chiusura dei relativi asset e delle regole di combattimento.
