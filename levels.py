"""I satelliti: configurazione e mappe (il percorso con ondate e traversata, l'arena del duello).

Legenda:
  # crosta   D roccia   H scala di servizio   S parete invisibile dell'arena
  E portello d'uscita   q geyser   u prigioniero   o stazione d'ossigeno
  c sfiato di gas criogenico   P capsula d'atterraggio   ~ lago di metano   . vuoto
  b ossario (nube ossea)   s sirena psichica
"""
# Sopra la superficie restano SKY righe di cielo per salire (la rupe del
# labirinto), sotto la crosta DEPTH righe di roccia in cui scavare le gallerie.
SKY = 10
GROUND = 14 + SKY
DEPTH = 14
ROWS = GROUND + 3 + DEPTH
LAKE_DEPTH = 3
# Le gallerie sotto Titano sono lunghe: CAVE_EXTRA colonne in piu' dopo il passaggio
# basso; tutto quello che viene dopo (pozzo, cavi, torre, portello) e' spostato.
CAVE_EXTRA = 135

# La scelta e' deliberatamente senza conferma: una volta entrati nella campagna
# si porta la stessa arma fino alla fine. L'affinita' giusta evita le resistenze
# della fauna locale, le altre restano utilizzabili ma rendono gli scontri duri.
WEAPONS = [
    ("spada termica", "cryo", 1.35, "Scioglie la fauna gelata di Titano."),
    ("lancia luminosa", "lumen", 1.30, "Porta luce dove la notte non finisce."),
    ("martello sismico", "thermal", 1.45, "Spezza zolfo, roccia e corazze."),
    ("falce a fusione", "thermal", 1.20, "Taglia il ghiaccio e cio' che vi si nasconde."),
    ("arco magnetico", "lumen", 1.20, "Colpisce da lontano fra gli anelli."),
    ("scettro aurorale", "thermal", 1.15, "Luce fredda contro le ombre del transito."),
    ("mazza magnetica", "lumen", 1.35, "Devasta ossa e metallo fra i piloni."),
    ("balestra cinetica", "kinetic", 1.25, "Per bersagli rapidi a gravita' minima."),
    ("tridente termico", "thermal", 1.25, "Calore contro gli abissi di metano."),
    ("frusta a impulsi", "kinetic", 1.10, "Tiene lontani i nemici sui ponti."),
    ("pugnale dell'eclissi", "lumen", 1.25, "Piccolo e feroce nel buio."),
    ("spada orbitale", "kinetic", 1.40, "La reliquia del re."),
]


def weapon_cfg(i):
    name, affinity, damage, description = WEAPONS[i]
    return {"index": i, "name": name, "affinity": affinity, "damage": damage,
            "description": description}


def cfg(i=0):
    """Configurazione del satellite i (0 Titano, 1 Nix): nome, Guardiano, gravita',
    aria, e tutto il mondo (fondali, terreno, mappe, tappe, ondate, cavi).
    Le mappe sono funzioni, chiamate quando il livello parte."""
    import knights
    sat = SATELLITES[i]
    boss, _, _, color, _ = knights.KNIGHTS[i]
    return dict(sat, index=i, num=i + 1, boss=boss, color=color)


def _grid(cols):
    return [["." for _ in range(cols)] for _ in range(ROWS)]


# Le quattro ondate di Titano. Partono quando NightKnight entra nella zona e
# non bloccano mai il passaggio. Titano usa scheletri normali e volanti; la
# sua fauna: corvi, meduse, minatori, lucertole criogeniche e vermi di silicio.
TITAN_ARENAS = [140, 300]
TITAN_WAVES = [
    dict(name="dal suolo", roster=[("skeleton", 6), ("lizard", 4), ("miner", 1), ("worm", 2)]),
    dict(name="dal cielo", roster=[("crow", 10), ("jelly", 3), ("skeleton_fly", 3)]),
]
# Lungo tutta la strada non si e' mai soli: ogni `every` colonne di strada nuova
# arriva un gruppetto di 2-4 nemici della fauna di Titano (i vermi sono i piu' comuni);
# se per `quiet` fotogrammi non c'e' nessuno attorno ne arriva uno comunque (nella
# traversata solo volanti).
TITAN_PATROLS = dict(every=14, size=(2, 4), start=12,
                     pool=["skeleton", "skeleton", "lizard", "lizard", "lizard", "miner", "worm", "worm",
                           "crow", "jelly", "skeleton_fly"],
                     quiet=180, flyers=["crow", "crow", "jelly", "skeleton_fly"])
# Nella traversata pochi nemici, otto sottoterra.
# (specie, colonna dall'inizio, riga: quella dei piedi per chi cammina, del volo per i volanti)
TITAN_PASS_FOES = [("lizard", 26, GROUND - 4), ("crow", 32, GROUND - 20),
                   ("skeleton", 92, GROUND + 10), ("burrower", 108, GROUND + 10), ("worm", 113, GROUND + 10),
                   ("worm", 122, GROUND + 10), ("miner", 134, GROUND + 10), ("burrower", 142, GROUND + 10),
                   ("jelly", 180 + CAVE_EXTRA, GROUND - 6), ("crow", 236 + CAVE_EXTRA, GROUND - 18)]
# Le tappe: perdendo una vita si riparte dall'ultima raggiunta, (colonna, riga dei
# piedi). In superficie prima delle arene, nella traversata a ogni tratto nuovo.
def _stages():
    p = TITAN_PASS_START
    return [(2, GROUND), (70, GROUND), (132, GROUND), (216, GROUND), (292, GROUND), (360, GROUND),
            (p + 1, GROUND), (p + 50, GROUND - LEDGES[2]), (p + 104, CAVE_FLOOR),
            (p + 152, CAVE_FLOOR), (p + 201, CAVE_FLOOR), (p + 230, CAVE_FLOOR),
            (p + 150 + CAVE_EXTRA, GROUND), (p + 206 + CAVE_EXTRA, GROUND), (p + 270 + CAVE_EXTRA, GROUND)]


# Nel duello il Guardiano e' solo: nessun altro nemico.


# Rilievi della superficie: (prima colonna, [(larghezza, altezza), ...]) a gradini di
# 1-3 tessere, che si salgono saltando; la montagna grande ha la sua scala. Le
# arene delle ondate, le tappe e le rive dei laghi restano in piano.
TITAN_HILLS = [
    (24, [(3, 1), (3, 2), (3, 3), (3, 2), (3, 1)]),
    (42, [(3, 3), (6, 6), (2, 4)]),
    (74, [(3, 2), (3, 4), (4, 7), (3, 4), (2, 2)]),
    (106, [(3, 2), (5, 5), (2, 2)]),
    (176, [(4, 3), (4, 6), (3, 9), (1, 5)]),
    (240, [(9, 10), (3, 7), (3, 4), (1, 2)]),          # la montagna, con la scala
    (262, [(3, 2), (3, 3), (3, 2)]),
    (334, [(3, 3), (4, 6), (2, 3)]),
    (376, [(3, 2), (3, 5), (4, 8), (3, 5), (3, 2)]),
    (405, [(4, 3), (5, 6), (4, 3)]),
]
TITAN_BIG_LADDER = 237       # la scala di servizio della montagna grande


def surface_heights(cols=432):
    hts = [0] * cols
    for c0, steps in TITAN_HILLS:
        for w, h in steps:
            for c in range(c0, c0 + w):
                hts[c] = h
            c0 += w
    return hts


def gen_titan_surface():
    """Esplorazione e due arene: colline e montagne da salire, laghi di metano,
    criovulcani e prigionieri; le rive restano libere per la rincorsa."""
    cols = 432
    g = _grid(cols)
    hts = surface_heights(cols)
    for c, h in enumerate(hts):
        _rock(g, c, c + 1, h)
    _ladder_rows(g, TITAN_BIG_LADDER, GROUND - 10, GROUND)
    lakes = ((16, 18), (55, 57), (66, 69), (100, 103), (118, 121), (150, 152), (165, 168), (190, 193),
             (205, 207), (228, 231), (258, 260), (276, 279), (300, 302), (318, 321), (345, 347),
             (368, 371), (395, 398), (420, 422))
    for start, end in lakes:
        _lake(g, start, end)
    top = lambda c: GROUND - hts[c] - 1          # la cella appena sopra il suolo, anche in collina
    # q = criovulcano (in piano, con spazio per passarci); u = prigioniero (trenta)
    for col in (10, 61, 94, 128, 145, 159, 172, 198, 214, 222, 283, 310, 327, 353, 426):
        g[top(col)][col] = "q"
    for col in (6, 15, 20, 34, 47, 53, 65, 71, 88, 104, 111, 123, 138, 154, 177, 184, 202, 209,
                218, 236, 247, 263, 287, 296, 305, 322, 340, 349, 389, 415):
        g[top(col)][col] = "u"
    g[top(1)][1] = "P"                      # la capsula con cui NightKnight e' arrivato
    for col in (3, 186, 378):               # stazioni d'ossigeno: poche, vanno pianificate
        g[top(col)][col] = "o"
    for col in (140, 298, 366):             # condotte d'azoto: il getto non passa su criovulcani ne' laghi
        g[top(col)][col] = "c"
    return g


def _rock(g, c0, c1, h):
    """Cumulo o parete di roccia alta h tessere, da colonna c0 a c1 esclusa."""
    for c in range(c0, c1):
        for r in range(GROUND - h, ROWS):
            g[r][c] = "#" if r == GROUND - h else "D"


def _lake(g, c0, c1, top=GROUND):
    """Lago di metano profondo LAKE_DEPTH tessere, con la roccia sotto."""
    for c in range(c0, c1):
        for r in range(top, top + LAKE_DEPTH):
            g[r][c] = "~"


def _ladder(g, c, h):
    """Scala di servizio accostata a una parete alta h."""
    for r in range(GROUND - h, GROUND):
        g[r][c] = "H"


TITAN_PASS_START = 432       # dove finiscono le ondate e comincia la traversata
TITAN_PASS_ROPE = TITAN_PASS_START + 83      # colonna del cavo sopra il lago delle guglie
# I cavi, a gruppi sotto lo stesso portale: (colonna dall'inizio della traversata,
# altezza dell'aggancio sopra il suolo in pixel, lunghezza del cavo).
# Le impugnature stanno piu' in alto del punto da cui si salta: si salta verso
# l'alto per prenderle. Lunghezze un po' diverse: ogni cavo oscilla col suo ritmo,
# e il salto si fa cercando il momento in cui si allineano.
# Ogni impugnatura, nel punto piu' basso, sta ROPE_ABOVE sopra i piedi di chi salta
# dal punto di lancio: sopra la testa, la si prende solo saltando.
ROPE_ABOVE = 320
TITAN_TOWER = 5              # la torre da cui si parte per il triplo
_SPIRE, _STEP = 4, 3         # l'ultima guglia e lo scalino del doppio cavo
ROPE_TOP, ROPE_MID, ROPE_HIGH = (_SPIRE * 64 + ROPE_ABOVE + 500, _STEP * 64 + ROPE_ABOVE + 470,
                                 TITAN_TOWER * 64 + ROPE_ABOVE + 480)
# Velocita' del dondolio di ogni cavo, nell'ordine: ognuno un po' diverso dall'altro.
ROPE_SPEEDS = (1.0, 1.1, 0.9, 1.2, 0.8, 1.1)
TITAN_CABLES = [
    [(83, ROPE_TOP, 500)],                                     # il lago delle guglie
    [(170 + CAVE_EXTRA, ROPE_MID, 470), (184 + CAVE_EXTRA, ROPE_MID, 500)],  # il doppio cavo
    [(217 + CAVE_EXTRA, ROPE_HIGH, 480), (230 + CAVE_EXTRA, ROPE_HIGH, 520),
     (243 + CAVE_EXTRA, ROPE_HIGH, 460)],                      # il triplo, dall'alto
]
# Da che parte soffiano gli sfiati d'azoto (colonna assoluta -> verso): verso chi
# arriva; sulla cengia media si arriva da destra.
VENT_FACING = {TITAN_PASS_START + 34: 1}
# Il labirinto di Titano (il "labyrinth terrain" visto da Cassini: altopiani
# sciolti dalla pioggia di metano in gole, guglie e pozzi). Altezze in tessere
# sopra il suolo; le gallerie stanno sotto la crosta.
LEDGES = (4, 10, 17)          # le tre cengie della rupe
CAVE_TOP, CAVE_FLOOR = GROUND + 3, GROUND + 10    # prima riga libera e pavimento delle gallerie


# Decorazioni delle gallerie (colonna dall'inizio della traversata, oggetto):
# 0 stalattite organica appesa al soffitto, 1 stalagmite, 2 puntello di miniera,
# 3 condotta rotta, 4 lampada da lavoro spenta. MOUTH: l'imbocco dal crepaccio.
CAVE_PROPS = ((89, 2), (91, 0), (95, 1), (105, 4), (108, 0), (111, 2), (122, 3),
              (130, 0), (135, 1), (138, 2), (143, 0)) + tuple(
              (c, (0, 2, 1, 0, 4, 3)[i % 6]) for i, c in enumerate(range(150, 146 + CAVE_EXTRA, 7)))
CAVE_MOUTH = 103


def _ledge(g, c0, c1, h):
    """Cengia sottile sospesa, alta h tessere, da c0 a c1 esclusa."""
    for c in range(c0, c1):
        g[GROUND - h][c] = "#"


def _pillar(g, c0, c1, h):
    """Guglia di roccia che sale dal fondo (anche dentro un lago)."""
    for c in range(c0, c1):
        for r in range(GROUND - h, ROWS):
            g[r][c] = "#" if r == GROUND - h else "D"


def _dig(g, c0, c1, r0, r1):
    """Scava una galleria: righe da r0 a r1 escluse."""
    for c in range(c0, c1):
        for r in range(r0, r1):
            g[r][c] = "."


def _ladder_rows(g, c, r0, r1, width=3):
    """Scala di servizio larga `width` tessere, da c verso destra."""
    for r in range(r0, r1):
        for cc in range(c, c + width):
            g[r][cc] = "H"


def gen_titan_pass():
    """Seconda parte di Titano, un labirinto che non va dritto:
    1. la rupe: tre cengie a zig-zag, si sale a destra, si torna indietro a
       sinistra, si risale a destra; scale di servizio alle estremita';
    2. la cresta in cima, poi le guglie che scendono dentro il lago di metano
       e il cavo per l'ultima campata;
    3. il crepaccio: oltre la riva una parete troppo alta, si scende a salti;
    4. le gallerie: a sinistra un vicolo cieco con due prigionieri, a destra un
       passaggio basso, una pozza di metano, l'azoto; un pozzo risale in superficie;
    5. il doppio cavo: due cavi di fila sopra un lago, da uno all'altro in volo;
    6. la torre e il triplo cavo, agganciato in alto sopra il lago grande: la
       riva di la' e' uno scalino alto, lo si raggiunge solo lasciando l'ultimo
       cavo dall'alto; poi l'ultimo tratto fino al portello.
    Con la gravita' di Titano si salta alto circa 5 tessere e lontano quasi 6."""
    X = CAVE_EXTRA
    cols = 320 + X
    g = _grid(cols)
    _rock(g, 0, cols, 0)
    l1, l2, l3 = LEDGES
    # 1. la rupe
    _rock(g, 12, 14, 2)                                   # gradino per la prima cengia
    _ledge(g, 15, 44, l1)                                 # cengia bassa, verso destra
    _ladder_rows(g, 40, GROUND - l2, GROUND - l1)         # scala a destra
    _ledge(g, 15, 40, l2)                                 # cengia media, si torna a sinistra
    for c in (27, 28):                                    # un buco da saltare
        g[GROUND - l2][c] = "."
    _ladder_rows(g, 15, GROUND - l3, GROUND - l2)         # scala a sinistra
    _ledge(g, 18, 44, l3)                                 # cengia alta, di nuovo a destra
    _rock(g, 44, 63, l3)                                  # la massa della rupe e la cresta
    # 2. le guglie nel lago e il cavo
    _lake(g, 63, 87)
    for c0, h in ((66, 13), (70, 10), (74, 7), (78, 4)):
        _pillar(g, c0, c0 + 2, h)
    # 3. il crepaccio, chiuso oltre da una parete troppo alta da scalare
    _dig(g, 97, 103, GROUND, CAVE_FLOOR)
    g[GROUND + 4][97] = g[GROUND + 4][98] = "#"           # sporgenze per scendere a salti
    g[GROUND + 7][101] = g[GROUND + 7][102] = "#"
    _rock(g, 103, 111, 8)
    # 4. le gallerie sotto la crosta
    _dig(g, 87, 97, CAVE_TOP, CAVE_FLOOR)                 # vicolo cieco a sinistra
    _dig(g, 103, 148 + X, CAVE_TOP, CAVE_FLOOR)           # la galleria lunga verso il pozzo
    for c in range(114, 121):                             # passaggio basso
        for r in range(CAVE_TOP, CAVE_FLOOR - 3):
            g[r][c] = "D"
    _lake(g, 124, 127, top=CAVE_FLOOR)                    # pozza di metano
    # il tratto lungo: passaggi bassi, pozze, gradini di roccia
    for c0, c1 in ((163, 169), (214, 221), (258, 264)):   # passaggi bassi
        for c in range(c0, c1):
            for r in range(CAVE_TOP, CAVE_FLOOR - 3):
                g[r][c] = "D"
    for c0 in (180, 234, 270):                            # pozze di metano
        _lake(g, c0, c0 + 3, top=CAVE_FLOOR)
    for c0, c1, h in ((192, 197, 2), (242, 246, 1), (246, 250, 3), (250, 253, 1)):
        for c in range(c0, c1):                           # gradini di roccia sul pavimento
            for r in range(CAVE_FLOOR - h, CAVE_FLOOR):
                g[r][c] = "D"
    _dig(g, 145 + X, 148 + X, GROUND, CAVE_TOP)           # pozzo verso la superficie
    _ladder_rows(g, 145 + X, GROUND, CAVE_FLOOR)
    for c in range(cols):                                 # pavimento e gradini delle gallerie
        for r in range(CAVE_TOP, CAVE_FLOOR + 1):
            if g[r][c] == "D" and g[r - 1][c] in ".H":
                g[r][c] = "#"
    # 5. il doppio cavo, fra due scalini di roccia da cui lanciarsi e su cui atterrare
    _rock(g, 162 + X, 167 + X, 3)
    _lake(g, 167 + X, 194 + X)
    _rock(g, 194 + X, 204 + X, 3)
    # 6. la torre, il triplo cavo sul lago grande, lo scalino della riva di la'
    _pillar(g, 210 + X, 215 + X, TITAN_TOWER)
    _ladder_rows(g, 207 + X, GROUND - TITAN_TOWER, GROUND)
    _lake(g, 215 + X, 253 + X)
    _rock(g, 253 + X, 268 + X, 4)
    # prigionieri, ossigeno, gas, criovulcani, uscita
    floor, cave = GROUND - 1, CAVE_FLOOR - 1
    for c, r in ((30, GROUND - l1 - 1), (18, GROUND - l2 - 1), (54, GROUND - l3 - 1), (89, cave), (94, cave),
                 (129, cave), (175, cave), (226, cave), (248, CAVE_FLOOR - 4), (268, cave),
                 (152 + X, floor), (202 + X, GROUND - 4), (212 + X, GROUND - TITAN_TOWER - 1),
                 (262 + X, GROUND - 5)):
        g[r][c] = "u"
    for c, r in ((205, cave), (149 + X, floor)):  # una stazione a meta' delle gallerie, una fuori
        g[r][c] = "o"
    for c, r in ((34, GROUND - l2 - 1), (133, cave), (238, cave)):
        g[r][c] = "c"
    for c in (91, 157 + X):
        g[floor][c] = "q"
    g[floor][cols - 4] = "E"
    return g


def gen_surface(c=None):
    """Un unico percorso: le ondate, poi il terreno si fa difficile."""
    first, second = gen_titan_surface(), gen_titan_pass()
    return [a + b for a, b in zip(first, second)]


def gen_arena(c=None):
    """L'arena del duello: due schermi di terreno fra due pareti invisibili, per
    avere spazio da tenere il Guardiano a distanza."""
    cols = 60
    g = _grid(cols)
    _rock(g, 0, cols, 0)
    for r in range(GROUND):
        g[r][0] = "S"; g[r][cols - 1] = "S"
    return g


TITAN_STAGES = _stages()


def _cave_worms():
    """Le gallerie sono piene di vermi che strisciano: uno ogni poche colonne dove il
    pavimento e' in piano (niente pozze, gradini, passaggi bassi, oggetti), e ogni
    tanto uno che corre sotto la roccia alla Tremors."""
    g = gen_titan_pass()
    free = lambda c: (g[CAVE_FLOOR][c] == "#" and g[CAVE_FLOOR - 1][c] == "."
                      and all(g[r][c] == "." for r in range(CAVE_TOP, CAVE_FLOOR)))
    out, last = [], -99
    for c in range(106, 144 + CAVE_EXTRA):
        if c - last < 4 or not all(free(k) for k in range(c - 2, c + 3)):
            continue
        out.append(("burrower" if len(out) % 5 == 4 else "crawler", c, CAVE_FLOOR))
        last = c
    return out


TITAN_PASS_FOES = [f for f in TITAN_PASS_FOES if f[0] not in ("worm", "burrower", "crawler")] + _cave_worms()


# ---------------------------------------------------------------- i satelliti
# Ogni satellite e' un dizionario: quello che cambia da un mondo all'altro sta
# qui, il codice del gioco legge solo da cfg(). I fondali: cielo (non si ripete),
# piani di parallasse (nome, velocita', spostamento verticale, foschia che
# stende sui piani dietro), primo piano, colore della foschia e del fondo.
TITAN = {
    "name": "Titano", "gravity": "bassa", "gravity_scale": .84, "air": "densa, azoto e metano",
    "climate": "nebbia arancione, pioviggine di metano", "affinity": "cryo",
    "fauna": ("corvi", "meduse", "minatori", "lucertole criogeniche", "vermi di silicio"),
    "oxygen_seconds": 150,
    "sky": "sky_01", "parallax": (("hills_far", 0.07, 0, 70), ("hills_01", 0.16, 0, 45),
                                  ("colony_ruins", 0.28, 90, 30), ("hills_02", 0.42, 0, 38)),
    "foreground": "foreground", "fog_color": (196, 112, 58), "bg_color": (34, 16, 8),
    "ground": "titan_ground_grass", "ground_top_cut": True, "rock": "titan_rock",
    "station": "stazione_ossigeno", "caves": True, "night": 0.0, "drizzle": True,
    "props": [], "prop_images": {}, "haze": True, "crevasses": (), "gratings": (), "pylon": None,
    "arena_props": [],
    "surface": gen_surface, "arena": gen_arena, "pass_start": TITAN_PASS_START,
    "stages": TITAN_STAGES, "arenas": TITAN_ARENAS, "waves": TITAN_WAVES, "patrols": TITAN_PATROLS,
    "pass_foes": TITAN_PASS_FOES, "cables": TITAN_CABLES, "rope_speeds": ROPE_SPEEDS,
}


# ---------------------------------------------------------------- Nix
# La superficie di Nix (STORY.md, "Nix, il secondo satellite"): il campo delle
# antenne (0-210) col cratere grande dell'atterraggio, poi le miniere (210-430).
# Rilievi come su Titano (altezza positiva: roccia che sale) e crateri a conca
# (altezza negativa: il suolo scende a gradini di una tessera). I crepacci sono
# colonne senza suolo: chi ci cade dentro perde una vita.
NIX_SURFACE_COLS = 430
NIX_HILLS = [
    (8, [(2, -1), (2, -2), (2, -3), (20, -4), (2, -3), (2, -2), (2, -1)]),       # il cratere grande
    (52, [(1, -1), (4, -2), (1, -1)]),                                          # conche del campo
    (78, [(1, -1), (1, -2), (5, -3), (1, -2), (1, -1)]),
    (140, [(3, 1), (3, 2), (4, 3), (3, 2), (3, 1)]),
    (165, [(1, -1), (8, -2), (1, -1)]),
    (214, [(3, 2), (3, 4), (5, 6), (3, 4), (2, 2)]),                            # le miniere
    (262, [(3, 3), (4, 6), (6, 9), (4, 6), (3, 3)]),                            # il rilievo del 2x
    (296, [(1, -1), (1, -2), (8, -3), (1, -2), (1, -1)]),
    (326, [(3, 2), (3, 4), (3, 2)]),
    (398, [(4, 2), (4, 4), (4, 2)]),
]
NIX_CREVASSES = ((66, 69), (95, 99), (186, 192), (248, 255), (318, 322), (384, 391))
NIX_BRIDGE = (248, 255)      # il ripetitore caduto fa da ponte sul quarto crepaccio
# Oggetti del paesaggio, in piedi sul suolo: (colonna, oggetto)
NIX_PROPS = [(48, "antenna"), (72, "antenna"), (92, "antenna"), (110, "repeater"), (120, "antenna"),
             (130, "repeater"), (148, "antenna"), (160, "repeater"), (178, "antenna"), (200, "antenna"),
             (240, "door"), (284, "antenna"), (340, "repeater"), (410, "repeater"), (420, "door")]
# immagine e altezza (in altezze di 9T9T) di ogni oggetto
NIX_PROP_IMAGES = {"antenna": ("nix_antenna", 4.0), "repeater": ("nix_repeater", 1.15),
                   "door": ("nix_door", 1.5)}


def nix_heights(cols=NIX_SURFACE_COLS):
    hts = [0] * cols
    for c0, steps in NIX_HILLS:
        for w, h in steps:
            for c in range(c0, c0 + w):
                hts[c] = h
            c0 += w
    return hts


def gen_nix_field():
    """Il campo delle antenne e le miniere: crateri, rilievi, crepacci,
    prigionieri, stazioni e la capsula."""
    cols = NIX_SURFACE_COLS
    g = _grid(cols)
    hts = nix_heights(cols)
    gaps = {c for c0, c1 in NIX_CREVASSES for c in range(c0, c1)}
    for c, h in enumerate(hts):
        if c not in gaps:
            _rock(g, c, c + 1, h)
    for c in range(*NIX_BRIDGE):            # il ponte: una riga sola, il vuoto sotto
        g[GROUND][c] = "#"
    top = lambda c: GROUND - hts[c] - 1     # la cella sopra il suolo, anche nei crateri
    for col in (6, 16, 20, 28, 36, 45, 60, 74, 90, 106, 118, 126, 136, 150, 158, 172, 182, 198,
                206, 222, 236, 258, 275, 288, 300, 312, 330, 345, 362, 400):
        g[top(col)][col] = "u"
    g[top(1)][1] = "P"
    for col in (3, 104, 212, 426):          # quattro stazioni: capsula, campo, imbocco, fine
        g[top(col)][col] = "o"
    for col in (232, 348, 356, 364):        # gli ossari: uno all'imbocco, tre per l'ondata 4
        g[top(col)][col] = "b"
    for col in (259, 303, 378):             # le sirene: ai piedi del rilievo del 2x, nella
        g[top(col)][col] = "s"              # conca, davanti all'ultimo crepaccio
    return g


# ---- la traversata di Nix: il campo dei crateri (STORY.md, "2->3")
# Colonne dall'inizio della traversata. Con la gravita' di Nix si salta alto
# ~7,5 tessere e lungo ~9: i crepacci larghi fino a 7 si passano, la fretta no.
NIX_PASS_COLS = 455
NIX_PASS_GAPS = ((12, 17), (22, 28), (33, 39), (60, 134), (165, 228),     # crateri, passerelle, cavi
                 (330, 334), (360, 366), (395, 401), (420, 425))          # i pozzi del lato alto
NIX_GRATING_W = 5
NIX_GRATINGS = tuple((c, GROUND) for c in range(62, 130, 9))   # (prima colonna, riga): 5 piene, 4 di vuoto
NIX_LAUNCH, NIX_LANDING, NIX_TOP = 3, 8, 20   # scalino di lancio, lato alto dove si atterra, altopiano finale
# Il salto di corsa su Nix arriva a quasi 10 tessere: l'altopiano finale sta 12
# sopra il lato alto, cosi' ci si arriva solo dal ritorno (cengia 12, cengia 16).
# Con la gravita' di Nix si salta piu' alto e si vola piu' lontano dopo il
# rilascio: le impugnature stanno piu' in alto (420 px sopra i piedi di lancio,
# 320 su Titano) e i cavi piu' distanti (16 colonne, 13 su Titano).
NIX_ROPE_ABOVE = 420
NIX_ROPE_TOP = NIX_LAUNCH * 64 + NIX_ROPE_ABOVE + 480
NIX_CABLES = [[(170, NIX_ROPE_TOP, 480), (186, NIX_ROPE_TOP, 480), (202, NIX_ROPE_TOP, 480),
               (218, NIX_ROPE_TOP, 480)]]
NIX_ROPE_SPEEDS = (1.0, 1.15, 0.85, 1.05)
NIX_PASS_CRACKS = (15, 36, 363, 398)
NIX_PASS_PROPS = [(8, "antenna"), (50, "repeater"), (145, "antenna"), (262, "pylon", GROUND - 16),
                  (320, "repeater", GROUND - NIX_TOP), (380, "antenna", GROUND - NIX_TOP),
                  (445, "repeater", GROUND - NIX_TOP)]
# pochi nemici, piazzati: ragni sopra le passerelle, custodi davanti ai due
# prigionieri nascosti, una copia sul traliccio
NIX_PASS_FOES = [("spider", 78, GROUND - 6), ("spider", 111, GROUND - 6),
                 ("keeper", 257, GROUND - 22), ("keeper", 267, GROUND - 22), ("copy", 262, GROUND - 16)]


def gen_nix_pass():
    """La traversata di Nix, il campo dei crateri:
    1. orli di cratere e vuoti: si salta da orlo a orlo;
    2. il crepaccio delle passerelle: griglie di servizio che cedono mezzo
       secondo dopo il passo, da una all'altra senza fermarsi;
    3. lo scalino di lancio e i quattro cavi sopra il crepaccio grande (55
       colonne), fino al lato alto (8 tessere);
    4. il ritorno: il lato alto finisce contro la parete dell'altopiano (12
       tessere, troppo alta anche per il salto di Nix); si salta sulla cengia a
       12 e si torna a sinistra fino in fondo, con un salto si prende la cengia a
       16 e si riparte a destra, e dalla sua fine un salto porta sull'altopiano a
       20; sopra la cengia alta una piattaforma nascosta con due prigionieri e i
       custodi; l'altopiano prosegue con i pozzi fino ai piedi del ripetitore.
    Chi salta forte puo' accorciare (dal lato alto alla cengia 16, dalla cengia
    12 all'altopiano): perde il giro, e i due prigionieri nascosti."""
    cols = NIX_PASS_COLS
    g = _grid(cols)
    gaps = {c for c0, c1 in NIX_PASS_GAPS for c in range(c0, c1)}
    hts = [0] * cols
    for c0, c1, h in ((8, 12, 1), (17, 22, 2), (28, 33, 1), (40, 46, 1),       # orli dei crateri
                      (160, 165, NIX_LAUNCH), (228, 300, NIX_LANDING),         # lancio e lato alto
                      (300, cols, NIX_TOP)):                                   # l'altopiano finale
        for c in range(c0, c1):
            hts[c] = h
    for c, h in enumerate(hts):
        if c not in gaps:
            _rock(g, c, c + 1, h)
    for c0, row in NIX_GRATINGS:                                   # le passerelle
        for c in range(c0, c0 + NIX_GRATING_W):
            g[row][c] = "G"
    _ledge(g, 244, 297, 12)                 # il ritorno: dalla fine del lato alto si salta su, e si torna a sinistra
    _ledge(g, 248, 293, 16)                 # in fondo, un salto in su: la cengia alta, e di nuovo a destra
    _ledge(g, 256, 269, 22)                 # la piattaforma nascosta, sei tessere sopra la cengia alta
    def top(c):
        return next(r for r in range(ROWS) if g[r][c] in "#G") - 1
    for c in (10, 30, 50, 145, 155, 238, 266, 290, 261, 264, 350, 436):
        g[top(c)][c] = "u"
    for c in (150, 310):
        g[top(c)][c] = "o"
    for c in (44, 380):
        g[top(c)][c] = "b"
    for c in (270, 410):
        g[top(c)][c] = "s"
    g[top(cols - 4)][cols - 4] = "E"
    return g


def gen_nix_surface():
    first, second = gen_nix_field(), gen_nix_pass()
    return [a + b for a, b in zip(first, second)]


# Sei tappe in superficie: capsula, uscita dal cratere grande, prima delle
# ondate 2, 3 e 4, fine delle miniere (la traversata aggiunge le sue).
NIX_STAGES = [(2, GROUND), (41, GROUND), (100, GROUND), (256, GROUND), (338, GROUND), (424, GROUND)]
# ... e nove nella traversata: ingresso, dopo il primo crepaccio, prima e dopo le
# passerelle, prima dei cavi, dopo i cavi sul lato alto, a meta' del ritorno, al
# traliccio della piattaforma nascosta, ai piedi del ripetitore.
NIX_STAGES += [(NIX_SURFACE_COLS + c, GROUND - h) for c, h in
               ((2, 0), (47, 0), (56, 0), (140, 0), (162, NIX_LAUNCH), (236, NIX_LANDING), (250, 12),
                (252, 16), (440, NIX_TOP))]
# Le ondate dal direttore: la prima sul fondo del cratere grande, la seconda nel
# campo delle antenne, la quarta dentro la nube degli ossari. La terza (il 2x in
# cima al rilievo coi due custodi ai piedi) e' fatta di nemici piazzati.
NIX_ARENAS = [12, 100, 338]
NIX_WAVES = [
    dict(name="dal cratere", roster=[("skeleton_fly", 3), ("bat", 4)]),
    dict(name="il campo delle antenne", roster=[("skeleton_fly", 12), ("bat", 8)]),
    dict(name="gli ossari", roster=[("skeleton_fly", 20), ("bat", 10), ("moth", 6)], alive=10),
]
NIX_PATROLS = dict(every=14, size=(2, 4), start=12,
                   pool=["skeleton_fly", "skeleton_fly", "skeleton_fly", "bat", "bat", "keeper"],
                   quiet=180, flyers=["bat"])
# Nemici piazzati in superficie: (specie, colonna, riga dei piedi o dell'aggancio).
# Il 2x in cima al rilievo, i custodi davanti a prigionieri e stazioni, le copie
# nelle miniere, i ragni appesi ai tralicci delle antenne.
NIX_SURFACE_FOES = [("skeleton_2x", 271, GROUND - 9), ("keeper", 260, GROUND), ("keeper", 283, GROUND),
                    ("keeper", 223, GROUND - 4), ("keeper", 237, GROUND), ("keeper", 289, GROUND),
                    ("keeper", 313, GROUND), ("keeper", 331, GROUND - 4), ("keeper", 401, GROUND - 2),
                    ("copy", 245, GROUND), ("copy", 410, GROUND),
                    ("spider", 120, GROUND - 7), ("spider", 148, GROUND - 7), ("spider", 284, GROUND - 7)]
# Le crepe da cui escono i pipistrelli: i crepacci
NIX_CRACKS = tuple((c0 + c1) // 2 for c0, c1 in NIX_CREVASSES)
NIX = {
    "name": "Nix", "gravity": "minima", "gravity_scale": .55, "air": "nessuna",
    "climate": "notte, stelle fisse, Plutone nel cielo", "affinity": "lumen",
    "fauna": ("pipistrelli del vuoto", "falene ossee", "custodi senza volto", "ragni da condotto",
              "copie difettose"),
    "oxygen_seconds": 100,
    "sky": "nix_sky", "parallax": (("nix_hills_far", 0.07, 0, 0), ("nix_hills_01", 0.16, 0, 0),
                                   ("nix_ruins", 0.28, 90, 0), ("nix_hills_02", 0.42, 0, 0)),
    "foreground": "nix_foreground", "fog_color": (0, 0, 0), "bg_color": (0, 0, 0),
    "ground": "nix_ground", "ground_top_cut": False, "rock": "nix_rock",
    "station": "nix_station", "caves": False, "night": 0.75, "drizzle": False,
    "surface": gen_nix_surface, "arena": gen_arena, "pass_start": NIX_SURFACE_COLS,
    # la piattaforma del ripetitore principale: i due tralicci dell'antenna madre ai
    # lati, l'antenna sul fondo
    "arena_props": [(5, "pylon"), (54, "pylon"), (30, "antenna"), (14, "repeater"), (45, "repeater")],
    "props": NIX_PROPS + [(NIX_SURFACE_COLS + c, *rest) for c, *rest in NIX_PASS_PROPS],
    "prop_images": dict(NIX_PROP_IMAGES, pylon=("nix_pylon", 5.0)), "haze": False,
    "crevasses": NIX_CREVASSES + tuple((NIX_SURFACE_COLS + a, NIX_SURFACE_COLS + b) for a, b in NIX_PASS_GAPS),
    "stages": NIX_STAGES, "arenas": NIX_ARENAS, "waves": NIX_WAVES, "patrols": NIX_PATROLS,
    "surface_foes": NIX_SURFACE_FOES, "cracks": NIX_CRACKS + tuple(NIX_SURFACE_COLS + c for c in NIX_PASS_CRACKS),
    "pass_foes": NIX_PASS_FOES, "cables": NIX_CABLES, "rope_speeds": NIX_ROPE_SPEEDS,
    "gratings": NIX_GRATINGS, "pylon": "nix_pylon",
}
SATELLITES = [TITAN, NIX]
# i dodici satelliti, in ordine, e i numeri in lettere per le scritte di fine livello
SATELLITES_NAMES = ("Titano", "Nix", "Io", "Europa", "Rea", "Caronte", "Ganimede", "Fobos", "Nereide",
                    "Miranda", "Umbriel", "Oberon")
IN_WORDS = ("ZERO", "UNO", "DUE", "TRE", "QUATTRO", "CINQUE", "SEI", "SETTE", "OTTO", "NOVE", "DIECI", "UNDICI", "DODICI")
