"""I 12 cimiteri: configurazione e generazione delle mappe (sopra, sottoterra, arena).

Legenda tile:
  # erba   D terra   = lastra   S muro cripta   H scala   ^ punte   E porta d'uscita
  t lapide  + croce  Y albero   k scheletro   v corvo   g fantasma   . vuoto
"""
import random

ROWS = 17
GROUND = 14

CEMETERIES = [
    ("Titano", "Guardiano di Titano", (150, 160, 180), "pierce"),
    ("Nix", "Guardiano di Nix", (40, 40, 60), "double"),
    ("Io", "Guardiano di Io", (240, 110, 30), "fire"),
    ("Europa", "Guardiano di Europa", (120, 200, 255), "ice"),
    ("Rea", "Guardiano di Rea", (90, 140, 60), "bounce"),
    ("Caronte", "Guardiano di Caronte", (230, 230, 220), "big"),
    ("Ganimede", "Guardiano di Ganimede", (250, 230, 90), "pierce"),
    ("Fobos", "Guardiano di Fobos", (190, 30, 40), "double"),
    ("Nereide", "Guardiano di Nereide", (60, 40, 120), "fire"),
    ("Miranda", "Guardiano di Miranda", (120, 160, 40), "ice"),
    ("Umbriel", "Guardiano di Umbriel", (50, 50, 60), "bounce"),
    ("Oberon", "Oberon, il Re", (240, 190, 60), "big"),
]

# Ogni luna ha una fisica e una biosfera proprie.  Gli archetipi restano
# compatibili con gli sprite disponibili: sono la specie, non il disegno,
# a cambiare da una luna all'altra.
SATELLITES = [
    dict(gravity="bassa", gravity_scale=.84, air="densa, azoto e metano", climate="nebbia criogenica", enemies=("scheletri galleggianti", "corvi del metano"), affinity="cryo"),
    dict(gravity="minima", gravity_scale=.55, air="quasi assente", climate="notte senza alba", enemies=("spettri d'ombra", "ossa vaganti"), affinity="lumen"),
    dict(gravity="leggera", gravity_scale=.72, air="zolfo e cenere", climate="eruzioni continue", enemies=("avvoltoi di zolfo", "cadaveri carbonizzati"), affinity="thermal"),
    dict(gravity="bassa", gravity_scale=.68, air="tenue, ossigeno nei crepacci", climate="crosta di ghiaccio", enemies=("meduse di brina", "scheletri subglaciali"), affinity="thermal"),
    dict(gravity="molto bassa", gravity_scale=.48, air="sottile e fredda", climate="anelli di polvere", enemies=("corvi degli anelli", "fantasmi di polvere"), affinity="lumen"),
    dict(gravity="bassa", gravity_scale=.60, air="azoto rarefatto", climate="buio plutoniano", enemies=("scheletri del gelo nero", "spettri di confine"), affinity="thermal"),
    dict(gravity="media", gravity_scale=.90, air="ossigeno tenue", climate="tempeste magnetiche", enemies=("arpie magnetiche", "guardiani ossei"), affinity="lumen"),
    dict(gravity="quasi nulla", gravity_scale=.42, air="inesistente", climate="rocce marziane", enemies=("sciacalli del vuoto", "ossa a razzo"), affinity="kinetic"),
    dict(gravity="molto bassa", gravity_scale=.50, air="metano gelido", climate="oceano sotto il ghiaccio", enemies=("meduse abissali", "scheletri di corallo"), affinity="thermal"),
    dict(gravity="bassa", gravity_scale=.65, air="tenue e corrosiva", climate="scogliere spezzate", enemies=("corvi delle fratture", "spettri verdastri"), affinity="kinetic"),
    dict(gravity="bassa", gravity_scale=.58, air="anidride carbonica gelata", climate="eclissi perenne", enemies=("pipistrelli d'eclissi", "ossa d'ombra"), affinity="lumen"),
    dict(gravity="bassa", gravity_scale=.70, air="ossigeno e polvere d'oro", climate="foreste notturne", enemies=("grifoni reali", "fantasmi della corte"), affinity="kinetic"),
]

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
ARMOR_NAMES = {
    "pierce": "lancia lunga", "double": "doppio affondo", "fire": "lancia di fuoco",
    "ice": "lancia di ghiaccio", "bounce": "lancia a due punte", "big": "lancia gigante",
}


def cfg(i):
    import knights
    name, _, color, power = CEMETERIES[i]
    boss = knights.KNIGHTS[i][0]
    color = knights.KNIGHTS[i][3]
    satellite = SATELLITES[i]
    return {
        "index": i, "num": i + 1, "name": name, "boss": boss, "color": color, "power": power,
        "boss_hp": 100 + 25 * i, "boss_speed": 2.2 + 0.25 * i, "boss_dmg": 12 + 2 * i,
        "zombie_every": max(50, 130 - 7 * i), "zombie_speed": 1.4 + 0.12 * i,
        "crows": 1 + i // 2, "skeletons": 1 + i // 3, "ghosts": 1 + i // 2,
        "gravity": satellite["gravity"], "gravity_scale": satellite["gravity_scale"], "air": satellite["air"], "climate": satellite["climate"],
        "enemies": satellite["enemies"], "affinity": satellite["affinity"],
    }


def _grid(cols):
    return [["." for _ in range(cols)] for _ in range(ROWS)]


def gen_surface(c):
    if c["index"] == 0:
        # Un unico percorso: le ondate, poi il terreno si fa difficile.
        first, second = gen_titan_surface(), gen_titan_pass()
        return [a + b for a, b in zip(first, second)]
    rnd = random.Random(100 + c["index"])
    cols = 110 + 8 * c["index"]
    g = _grid(cols)
    x = 0
    while x < cols:
        seg = rnd.randrange(14, 26)
        for cc in range(x, min(cols, x + seg)):
            g[GROUND][cc] = "#"
            g[GROUND + 1][cc] = "D"
            g[GROUND + 2][cc] = "D"
        x += seg
        if x < cols - 12:
            # Titano apre con un solo tile: insegna a saltare senza trasformare
            # i primi dieci secondi in una punizione.
            gap = 1 if c["index"] == 0 and x <= 26 else rnd.randrange(2, 4)
            x += gap
    for cc in range(cols - 12, cols):        # zona finale piena
        g[GROUND][cc] = "#"; g[GROUND + 1][cc] = "D"; g[GROUND + 2][cc] = "D"
        for r in range(8, GROUND):
            if g[r][cc] == "=":
                g[r][cc] = "."
    for cc in range(0, 8):                   # partenza piena
        g[GROUND][cc] = "#"; g[GROUND + 1][cc] = "D"; g[GROUND + 2][cc] = "D"
    # decorazioni e nemici a terra
    for cc in range(4, cols - 12):
        if g[GROUND][cc] == "#" and g[GROUND - 1][cc] == ".":
            v = rnd.random()
            if v < 0.10:
                g[GROUND - 1][cc] = "t"
            elif v < 0.14:
                g[GROUND - 1][cc] = "+"
            elif v < 0.18:
                g[GROUND - 1][cc] = "Y"
    # La composizione della fauna cambia davvero tra lune: quelle atmosferiche
    # popolano il cielo, quelle del vuoto privilegiano ossa e spettri.
    affinity = c["affinity"]
    crow_count = c["crows"] * (4 if affinity in ("kinetic", "lumen") else 2)
    skeleton_count = c["skeletons"] + (2 if affinity == "kinetic" else 0)
    ghost_count = c["ghosts"] + (2 if affinity == "lumen" else 0)
    for _ in range(crow_count):
        g[rnd.randrange(3, 7)][rnd.randrange(15, cols - 15)] = "v"
    for _ in range(skeleton_count):
        cc = rnd.randrange(30, cols - 20)
        if g[GROUND][cc] == "#" and g[GROUND - 1][cc] == ".":
            g[GROUND - 1][cc] = "k"
    for _ in range(ghost_count):
        g[rnd.randrange(6, 11)][rnd.randrange(20, cols - 15)] = "g"
    g[GROUND - 1][cols - 4] = "E"
    return g


# Le quattro ondate di Titano. Ogni arena e' larga uno schermo (30 tessere):
# quando NightKnight ci entra si chiudono le porte stagne finche' l'ondata non
# e' finita. Titano usa scheletri normali e volanti; la sua fauna: corvi,
# meduse, minatori, lucertole criogeniche e vermi di silicio.
TITAN_ARENAS = [22, 72, 124, 176]
TITAN_WAVES = [
    dict(name="PRIMO CONTATTO", roster=[("skeleton", 3), ("miner", 1)]),
    dict(name="LO SCIAME", roster=[("skeleton", 12), ("lizard", 3), ("miner", 2)], alive=17, every=6),
    dict(name="DAL CIELO E DAL SUOLO", roster=[("skeleton_fly", 6), ("worm", 3)]),
    dict(name="LA NUBE", roster=[("crow", 20), ("jelly", 6), ("skeleton_fly", 4)], alive=12),
]
WAVE_WIDTH = 30
# Nella traversata pochissimi nemici: disturbano, non la trasformano in battaglia.
# (specie, colonna[, riga per i volanti])
# Nel duello, di tanto in tanto, un volante in aiuto al Guardiano (mai piu' di due).
TITAN_ARENA_FLYERS = ["crow", "jelly", "skeleton_fly"]
TITAN_ARENA_FLYERS_MAX = 2
TITAN_PASS_FOES = [("lizard", 28), ("skeleton", 74), ("crow", 100, 4)]   # colonne dall'inizio della traversata


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
    return g


def gen_crypt(c):
    rnd = random.Random(200 + c["index"])
    cols = 90 + 6 * c["index"]
    g = _grid(cols)
    for cc in range(cols):
        g[0][cc] = "S"
        g[15][cc] = "S"; g[16][cc] = "S"
    for r in range(ROWS):
        g[r][0] = "S"; g[r][cols - 1] = "S"
    x = 3
    while x < cols - 14:
        kind = rnd.choice("abcb")
        if kind == "a":                        # fossa di punte
            w = rnd.randrange(2, 4)
            # Il salto deve superare anche l'intera larghezza della hitbox.
            g[15][x + 2] = "^"
            x += w + 5
        elif kind == "b":                      # torre di lastre con scala
            h = rnd.randrange(2, 4)
            top = 14 - 3 * h
            for lvl in range(1, h + 1):
                r = 14 - 3 * lvl
                for cc in range(x + (lvl % 2) * 4, x + (lvl % 2) * 4 + 5):
                    g[r][cc] = "="
                for rr in range(r, r + 3):
                    g[rr][x + 4] = "H"
            if rnd.random() < 0.5:
                g[14][x + 7] = "k"
            x += 11
        else:                                  # corridoio basso con scheletro
            for cc in range(x + 1, x + 8):
                for r in range(1, 11):
                    g[r][cc] = "S"
            g[14][x + 4] = "k"
            x += 10
    for _ in range(c["ghosts"] + 1):
        cc = rnd.randrange(12, cols - 16)
        if g[9][cc] == ".":
            g[9][cc] = "g"
    for cc in range(cols - 12, cols - 1):
        for r in range(11, 15):
            if g[r][cc] in "=H^":
                g[r][cc] = "."
    g[14][cols - 4] = "E"
    return g


def gen_arena(c):
    cols = 30
    g = _grid(cols)
    for cc in range(cols):
        g[GROUND][cc] = "#"; g[GROUND + 1][cc] = "D"; g[GROUND + 2][cc] = "D"
    for r in range(ROWS):
        g[r][0] = "S"; g[r][cols - 1] = "S"
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
    g[GROUND - 1][cols - 4] = "E"
    return g


def gen_trials(c):
    g = _grid(112)
    for cc in range(112):
        for r in range(GROUND, ROWS):
            g[r][cc] = "#" if r == GROUND else "D"
    # Primo esercizio: due tile, abbastanza largo da far capire il salto ma
    # superabile anche senza conoscere ancora la rincorsa.
    for start, end in ((12, 14), (32, 40)):
        for cc in range(start, end):
            for r in range(GROUND, ROWS):
                g[r][cc] = "."
    for cc in (52, 58, 64):
        g[GROUND-1][cc] = "="
    g[GROUND-1][108] = "E"
    return g
