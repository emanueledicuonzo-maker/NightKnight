"""I 12 cimiteri: configurazione e generazione delle mappe (sopra, sottoterra, arena).

Legenda tile:
  # erba   D terra   = lastra   S muro cripta   H scala   ^ punte   E porta d'uscita
  t lapide  + croce  Y albero   p anfora  c forziere   k scheletro   v corvo   . vuoto
"""
import random

ROWS = 17
GROUND = 14

CEMETERIES = [
    ("Nebbia", "Cavaliere della Nebbia", (150, 160, 180), "pierce"),
    ("Corvi", "Cavaliere dei Corvi", (40, 40, 60), "double"),
    ("Fuoco Fatuo", "Cavaliere del Fuoco", (240, 110, 30), "fire"),
    ("Ghiaccio", "Cavaliere del Gelo", (120, 200, 255), "ice"),
    ("Radici", "Cavaliere delle Radici", (90, 140, 60), "bounce"),
    ("Ossa", "Cavaliere delle Ossa", (230, 230, 220), "big"),
    ("Fulmini", "Cavaliere del Tuono", (250, 230, 90), "pierce"),
    ("Sangue", "Cavaliere del Sangue", (190, 30, 40), "double"),
    ("Abisso", "Cavaliere dell'Abisso", (60, 40, 120), "fire"),
    ("Peste", "Cavaliere della Peste", (120, 160, 40), "ice"),
    ("Ombra", "Cavaliere dell'Ombra", (50, 50, 60), "bounce"),
    ("Oro Nero", "Re dei Cimiteri", (240, 190, 60), "big"),
]
ARMOR_NAMES = {
    "pierce": "lancia perforante", "double": "lancia doppia", "fire": "lancia di fuoco",
    "ice": "lancia di ghiaccio", "bounce": "lancia rimbalzante", "big": "lancia gigante",
}


def cfg(i):
    name, boss, color, power = CEMETERIES[i]
    return {
        "index": i, "num": i + 1, "name": name, "boss": boss, "color": color, "power": power,
        "boss_hp": 100 + 25 * i, "boss_speed": 2.2 + 0.25 * i, "boss_dmg": 12 + 2 * i,
        "zombie_every": max(50, 130 - 7 * i), "zombie_speed": 1.4 + 0.12 * i,
        "crows": 1 + i // 2, "skeletons": 1 + i // 3,
    }


def _grid(cols):
    return [["." for _ in range(cols)] for _ in range(ROWS)]


def gen_surface(c):
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
            gap = rnd.randrange(2, 4 + min(2, c["index"] // 3))
            # lastre sopra il fosso
            top = rnd.choice((10, 11))
            for cc in range(x - 1, min(cols, x + gap + 1)):
                if rnd.random() < 0.8:
                    g[top][cc] = "="
            x += gap
    for cc in range(cols - 12, cols):        # zona finale piena
        g[GROUND][cc] = "#"; g[GROUND + 1][cc] = "D"; g[GROUND + 2][cc] = "D"
        for r in range(8, GROUND):
            if g[r][cc] == "=":
                g[r][cc] = "."
    for cc in range(0, 8):                   # partenza piena
        g[GROUND][cc] = "#"; g[GROUND + 1][cc] = "D"; g[GROUND + 2][cc] = "D"
    # piattaforme alte con anfore e forzieri
    for _ in range(6 + c["index"]):
        cc = rnd.randrange(10, cols - 16)
        r = rnd.choice((9, 10, 11, 7))
        w = rnd.randrange(2, 5)
        if all(g[r][cc + k] == "." and g[r + 1][cc + k] == "." for k in range(w) if cc + k < cols):
            for k in range(w):
                g[r][cc + k] = "="
            g[r - 1][cc] = rnd.choice("pcp")
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
            elif v < 0.20:
                g[GROUND - 1][cc] = "p"
    for _ in range(c["crows"] * 3):
        g[rnd.randrange(3, 7)][rnd.randrange(15, cols - 15)] = "v"
    for _ in range(c["skeletons"]):
        cc = rnd.randrange(30, cols - 20)
        if g[GROUND][cc] == "#" and g[GROUND - 1][cc] == ".":
            g[GROUND - 1][cc] = "k"
    g[GROUND - 1][cols - 4] = "E"
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
            for cc in range(x + 2, x + 2 + w):
                g[15][cc] = "^"
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
            g[top - 1][x + 2] = rnd.choice("pc")
            if rnd.random() < 0.5:
                g[14][x + 7] = "k"
            x += 11
        else:                                  # corridoio basso con scheletro
            for cc in range(x + 1, x + 8):
                for r in range(1, 11):
                    g[r][cc] = "S"
            g[14][x + 4] = "k"
            if rnd.random() < 0.5:
                g[14][x + 6] = "p"
            x += 10
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
