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
TITAN_ARENAS = [22, 72, 124, 176]
TITAN_WAVES = [
    dict(name="primo contatto", roster=[("skeleton", 3), ("miner", 1)]),
    dict(name="lo sciame", roster=[("skeleton", 12), ("lizard", 3), ("miner", 2)], alive=17, every=6),
    dict(name="dal cielo e dal suolo", roster=[("skeleton_fly", 6), ("worm", 3)]),
    dict(name="la nube", roster=[("crow", 20), ("jelly", 6), ("skeleton_fly", 4)], alive=12),
]
# Nella traversata pochissimi nemici.
# (specie, colonna dall'inizio, riga: quella dei piedi per chi cammina, del volo per i volanti)
TITAN_PASS_FOES = [("lizard", 26, GROUND - 4), ("crow", 32, GROUND - 20), ("skeleton", 136, GROUND + 10)]
# Nel duello, di tanto in tanto, un volante in aiuto al Guardiano (mai piu' di due).
TITAN_ARENA_FLYERS = ["crow", "jelly", "skeleton_fly"]
TITAN_ARENA_FLYERS_MAX = 2


def gen_titan_surface():
    """Esplorazione e quattro arene: fra un'ondata e l'altra laghi di metano,
    geyser e prigionieri; le rive restano libere per la rincorsa."""
    cols = 216
    g = _grid(cols)
    _rock(g, 0, cols, 0)
    lakes = ((16, 18), (55, 57), (66, 69), (107, 109), (118, 121), (159, 161), (169, 172), (208, 210))
    for start, end in lakes:
        _lake(g, start, end)
    # q = geyser (due dentro l'arena dello sciame); u = prigioniero
    for col in (10, 61, 82, 94, 113, 165, 212):
        g[GROUND-1][col] = "q"
    for col in (6, 13, 20, 53, 59, 71, 104, 111, 122, 152, 157, 167, 174, 206, 213):
        g[GROUND-1][col] = "u"
    g[GROUND-1][1] = "P"                    # la capsula con cui NightKnight e' arrivato
    for col in (3, 64, 115, 163):           # stazioni d'ossigeno fra un'ondata e l'altra
        g[GROUND-1][col] = "o"
    for col in (184, 198):                  # gas criogenico nell'ultima ondata
        g[GROUND-1][col] = "c"
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


TITAN_PASS_START = 216       # dove finiscono le ondate e comincia la traversata
TITAN_PASS_ROPE = TITAN_PASS_START + 83      # colonna del cavo sopra il lago delle guglie
# Da che parte soffiano gli sfiati d'azoto (colonna assoluta -> verso): verso chi
# arriva; sulla cengia media si arriva da destra.
VENT_FACING = {TITAN_PASS_START + 34: 1}
# Il labirinto di Titano (il "labyrinth terrain" visto da Cassini: altopiani
# sciolti dalla pioggia di metano in gole, guglie e pozzi). Altezze in tessere
# sopra il suolo; le gallerie stanno sotto la crosta.
LEDGES = (4, 10, 17)          # le tre cengie della rupe
CAVE_TOP, CAVE_FLOOR = GROUND + 3, GROUND + 10    # prima riga libera e pavimento delle gallerie


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


def _ladder_rows(g, c, r0, r1):
    for r in range(r0, r1):
        g[r][c] = "H"


def gen_titan_pass():
    """Seconda parte di Titano, un labirinto che non va dritto:
    1. la rupe: tre cengie a zig-zag, si sale a destra, si torna indietro a
       sinistra, si risale a destra; scale di servizio alle estremita';
    2. la cresta in cima, poi le guglie che scendono dentro il lago di metano
       e il cavo per l'ultima campata;
    3. il crepaccio: oltre la riva una parete troppo alta, si scende a salti;
    4. le gallerie: a sinistra un vicolo cieco con prigioniero e ossigeno, a
       destra un passaggio basso, una pozza di metano, il gas; una scala risale
       al portello in superficie.
    Con la gravita' di Titano si salta alto circa 5 tessere e lontano quasi 6."""
    cols = 160
    g = _grid(cols)
    _rock(g, 0, cols, 0)
    l1, l2, l3 = LEDGES
    # 1. la rupe
    _rock(g, 12, 14, 2)                                   # gradino per la prima cengia
    _ledge(g, 15, 43, l1)                                 # cengia bassa, verso destra
    _ladder_rows(g, 41, GROUND - l2, GROUND - l1)         # scala a destra
    _ledge(g, 15, 41, l2)                                 # cengia media, si torna a sinistra
    for c in (27, 28):                                    # un buco da saltare
        g[GROUND - l2][c] = "."
    _ladder_rows(g, 15, GROUND - l3, GROUND - l2)         # scala a sinistra
    _ledge(g, 16, 44, l3)                                 # cengia alta, di nuovo a destra
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
    _dig(g, 103, 148, CAVE_TOP, CAVE_FLOOR)               # la galleria verso l'uscita
    for c in range(114, 121):                             # passaggio basso
        for r in range(CAVE_TOP, CAVE_FLOOR - 3):
            g[r][c] = "D"
    _lake(g, 124, 127, top=CAVE_FLOOR)                    # pozza di metano
    for c in (145, 146, 147):                             # pozzo verso la superficie
        for r in range(GROUND, CAVE_TOP):
            g[r][c] = "."
    _ladder_rows(g, 146, GROUND, CAVE_FLOOR)
    for c in range(cols):                                 # pavimento delle gallerie
        if g[CAVE_FLOOR][c] == "D" and g[CAVE_FLOOR - 1][c] in ".H":
            g[CAVE_FLOOR][c] = "#"
    # prigionieri, ossigeno, gas, geyser, uscita
    floor, cave = GROUND - 1, CAVE_FLOOR - 1
    for c, r in ((30, floor), (18, GROUND - l2 - 1), (54, GROUND - l3 - 1),
                 (89, cave), (129, cave)):
        g[r][c] = "u"
    for c, r in ((5, floor), (50, GROUND - l3 - 1), (92, cave), (140, cave)):
        g[r][c] = "o"
    for c, r in ((34, GROUND - l2 - 1), (133, cave)):
        g[r][c] = "c"
    g[floor][91] = "q"
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
