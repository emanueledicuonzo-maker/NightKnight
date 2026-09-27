"""Titano: configurazione e mappe (il percorso con ondate e traversata, l'arena del duello).

Legenda:
  # crosta   D roccia   H scala di servizio   S parete invisibile dell'arena
  E portello d'uscita   q geyser   u prigioniero   o stazione d'ossigeno
  c sfiato di gas criogenico   P capsula d'atterraggio   ~ lago di metano   . vuoto
"""
# Sopra la superficie restano SKY righe di cielo per salire (la rupe del
# labirinto), sotto la crosta DEPTH righe di roccia in cui scavare le gallerie.
SKY = 10
GROUND = 14 + SKY
DEPTH = 14
ROWS = GROUND + 3 + DEPTH
LAKE_DEPTH = 3

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
    """Configurazione del satellite. Per ora e' giocabile solo Titano."""
    import knights
    boss, _, _, color, _ = knights.KNIGHTS[0]
    return {
        "index": 0, "num": 1, "name": "Titano", "boss": boss, "color": color,
        "gravity": "bassa", "gravity_scale": .84, "air": "densa, azoto e metano",
        "climate": "nebbia arancione, pioviggine di metano", "affinity": "cryo",
        "fauna": ("corvi", "meduse", "minatori", "lucertole criogeniche", "vermi di silicio"),
    }


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
                   ("jelly", 180, GROUND - 6), ("crow", 236, GROUND - 18)]
# Le tappe: perdendo una vita si riparte dall'ultima raggiunta, (colonna, riga dei
# piedi). In superficie prima delle arene, nella traversata a ogni tratto nuovo.
def _stages():
    p = TITAN_PASS_START
    return [(2, GROUND), (70, GROUND), (132, GROUND), (216, GROUND), (292, GROUND), (360, GROUND),
            (p + 1, GROUND), (p + 50, GROUND - LEDGES[2]), (p + 104, CAVE_FLOOR),
            (p + 150, GROUND), (p + 206, GROUND), (p + 270, GROUND)]


# Nel duello, di tanto in tanto, un volante in aiuto al Guardiano (mai piu' di due).
TITAN_ARENA_FLYERS = ["crow", "jelly", "skeleton_fly"]
TITAN_ARENA_FLYERS_MAX = 2


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
ROPE_TOP, ROPE_MID, ROPE_HIGH = 656, 820, 1050
TITAN_CABLES = [
    [(83, ROPE_TOP, 500)],                                     # il lago delle guglie
    [(173, ROPE_MID, 500), (189, ROPE_MID, 500)],              # il doppio cavo
    [(217, ROPE_HIGH, 500), (230, ROPE_HIGH, 500), (243, ROPE_HIGH, 500)],   # il triplo, dall'alto
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
              (130, 0), (135, 1), (138, 2), (143, 0))
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
    cols = 320
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
    _dig(g, 103, 148, CAVE_TOP, CAVE_FLOOR)               # la galleria verso il pozzo
    for c in range(114, 121):                             # passaggio basso
        for r in range(CAVE_TOP, CAVE_FLOOR - 3):
            g[r][c] = "D"
    _lake(g, 124, 127, top=CAVE_FLOOR)                    # pozza di metano
    _dig(g, 145, 148, GROUND, CAVE_TOP)                   # pozzo verso la superficie
    _ladder_rows(g, 145, GROUND, CAVE_FLOOR)
    for c in range(cols):                                 # pavimento delle gallerie
        if g[CAVE_FLOOR][c] == "D" and g[CAVE_FLOOR - 1][c] in ".H":
            g[CAVE_FLOOR][c] = "#"
    # 5. il doppio cavo, fra due scalini di roccia da cui lanciarsi e su cui atterrare
    _rock(g, 162, 167, 3)
    _lake(g, 167, 201)
    _rock(g, 201, 204, 3)
    # 6. la torre, il triplo cavo sul lago grande, lo scalino della riva di la'
    _pillar(g, 210, 215, 11)
    _ladder_rows(g, 207, GROUND - 11, GROUND)
    _lake(g, 215, 253)
    _rock(g, 253, 268, 5)
    # prigionieri, ossigeno, gas, criovulcani, uscita
    floor, cave = GROUND - 1, CAVE_FLOOR - 1
    for c, r in ((30, GROUND - l1 - 1), (18, GROUND - l2 - 1), (54, GROUND - l3 - 1), (89, cave), (94, cave),
                 (129, cave), (152, floor), (202, GROUND - 4), (212, GROUND - 12), (262, GROUND - 6)):
        g[r][c] = "u"
    for c, r in ((149, floor),):             # una sola stazione nella traversata
        g[r][c] = "o"
    for c, r in ((34, GROUND - l2 - 1), (133, cave)):
        g[r][c] = "c"
    for c in (91, 157):
        g[floor][c] = "q"
    g[floor][cols - 4] = "E"
    return g


def gen_surface(c=None):
    """Un unico percorso: le ondate, poi il terreno si fa difficile."""
    first, second = gen_titan_surface(), gen_titan_pass()
    return [a + b for a, b in zip(first, second)]


def gen_arena(c=None):
    """L'arena del duello: uno schermo di terreno fra due pareti invisibili."""
    cols = 30
    g = _grid(cols)
    _rock(g, 0, cols, 0)
    for r in range(GROUND):
        g[r][0] = "S"; g[r][cols - 1] = "S"
    return g


TITAN_STAGES = _stages()
