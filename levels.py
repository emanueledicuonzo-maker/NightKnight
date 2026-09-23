"""Titano: configurazione e mappe (il percorso con ondate e traversata, l'arena del duello).

Legenda:
  # crosta   D roccia   H scala di servizio   S parete invisibile dell'arena
  E portello d'uscita   q geyser   u prigioniero   o stazione d'ossigeno
  c sfiato di gas criogenico   . vuoto (o lago di metano)
"""
ROWS = 17
GROUND = 14

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
# Nella traversata pochissimi nemici: (specie, colonna dall'inizio[, riga per i volanti]).
TITAN_PASS_FOES = [("lizard", 28), ("skeleton", 74), ("crow", 100, 4)]
# Nel duello, di tanto in tanto, un volante in aiuto al Guardiano (mai piu' di due).
TITAN_ARENA_FLYERS = ["crow", "jelly", "skeleton_fly"]
TITAN_ARENA_FLYERS_MAX = 2


def gen_titan_surface():
    """Esplorazione e quattro arene: fra un'ondata e l'altra laghi di metano,
    geyser e prigionieri; le rive restano libere per la rincorsa."""
    cols = 216
    g = _grid(cols)
    for col in range(cols):
        g[GROUND][col] = "#"
        g[GROUND+1][col] = g[GROUND+2][col] = "D"
    lakes = ((16, 18), (55, 57), (66, 69), (107, 109), (118, 121), (159, 161), (169, 172), (208, 210))
    for start, end in lakes:
        for col in range(start, end):
            for row in range(GROUND, ROWS):
                g[row][col] = "."
    # q = geyser (due dentro l'arena dello sciame); u = prigioniero
    for col in (10, 61, 82, 94, 113, 165, 212):
        g[GROUND-1][col] = "q"
    for col in (6, 13, 20, 53, 59, 71, 104, 111, 122, 152, 157, 167, 174, 206, 213):
        g[GROUND-1][col] = "u"
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


def _lake(g, c0, c1):
    for c in range(c0, c1):
        for r in range(GROUND, ROWS):
            g[r][c] = "."


def _ladder(g, c, h):
    """Scala di servizio accostata a una parete alta h."""
    for r in range(GROUND - h, GROUND):
        g[r][c] = "H"


TITAN_PASS_START = 216       # dove finiscono le ondate e comincia la traversata
TITAN_PASS_ROPE = TITAN_PASS_START + 82      # colonna del cavo sopra il lago grande


def gen_titan_pass():
    """Seconda parte di Titano: attraversare il satellite. Cumuli di rocce,
    pareti da scalare con le scale di servizio, pilastri sopra i laghi di
    metano, un cavo sopra il lago grande. Con la gravita' di Titano si salta
    alto (circa 5 tessere) e lontano (quasi 6): le pareti sono alte 7."""
    cols = 128
    g = _grid(cols)
    _rock(g, 0, cols, 0)
    _rock(g, 10, 13, 1); _rock(g, 13, 16, 2); _rock(g, 16, 19, 3)      # gradini di roccia
    _lake(g, 22, 27)
    _rock(g, 35, 45, 7); _ladder(g, 34, 7)                              # prima parete
    _lake(g, 57, 71)
    _rock(g, 60, 62, 2); _rock(g, 65, 67, 2)                            # pilastri nel lago
    for c in (60, 61, 65, 66):
        for r in range(GROUND, ROWS):
            g[r][c] = "D"
    _lake(g, 78, 87)                                                     # lago del cavo
    _rock(g, 93, 96, 2); _rock(g, 96, 105, 4)
    _lake(g, 106, 111)
    g[GROUND - 1][50] = "q"
    for c, h in ((30, 0), (40, 7), (90, 0), (100, 4), (116, 0)):
        g[GROUND - 1 - h][c] = "u"
    for c in (5, 47, 88, 119):
        g[GROUND - 1][c] = "o"
    for c in (20, 54, 114):
        g[GROUND - 1][c] = "c"
    g[GROUND - 1][cols - 4] = "E"
    return g


def gen_surface(c=None):
    """Un unico percorso: le ondate, poi il terreno si fa difficile."""
    first, second = gen_titan_surface(), gen_titan_pass()
    return [a + b for a, b in zip(first, second)]


def gen_arena(c=None):
    """L'arena del duello: uno schermo di terreno fra due pareti invisibili."""
    cols = 30
    g = _grid(cols)
    for cc in range(cols):
        g[GROUND][cc] = "#"; g[GROUND + 1][cc] = "D"; g[GROUND + 2][cc] = "D"
    for r in range(ROWS):
        g[r][0] = "S"; g[r][cols - 1] = "S"
    return g
