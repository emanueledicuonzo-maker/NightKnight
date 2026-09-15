#!/usr/bin/env python3
"""Goblin - mix Ghosts'n Goblins / Mario / Street Fighter. Pixel art 480x270 scalata x4 a 1920x1080."""
import random
import sys

import pygame

SW, SH = 480, 270          # risoluzione interna
FPS = 60
TILE = 16
ROWS = 17
GRAVITY = 0.25
MAX_FALL = 6
RUN_ACC = 0.18
RUN_MAX = 2.2
JUMP_V = -5.8
TIME_START = 300
PLAYER_HP = 100
BOSS_HP = 100

# ---------------------------------------------------------------- palette
PAL = {
    "K": (20, 18, 30), "W": (245, 245, 245), "S": (250, 200, 160), "s": (200, 140, 100),
    "A": (205, 210, 225), "a": (120, 125, 150), "H": (205, 210, 225), "R": (220, 40, 40),
    "r": (140, 20, 20), "B": (60, 80, 200), "b": (100, 60, 30), "G": (110, 170, 90),
    "g": (60, 110, 50), "Y": (250, 210, 60), "y": (230, 140, 30), "D": (150, 90, 50),
    "d": (100, 60, 35), "L": (110, 200, 80), "l": (50, 130, 50), "T": (150, 150, 170),
    "t": (95, 95, 115), "P": (80, 200, 80), "p": (30, 120, 30), "O": (150, 60, 190),
    "o": (90, 30, 120), "C": (80, 200, 255), "M": (200, 110, 60), "m": (110, 50, 30),
    "k": (90, 50, 20), "h": (150, 90, 40),
}
UNDERWEAR = {"H": "h", "A": "S", "a": "s", "B": "W"}

_cache = {}


def sprite(rows, remap=None, flip=False):
    key = (tuple(rows), tuple(sorted((remap or {}).items())), flip)
    if key in _cache:
        return _cache[key]
    w, h = len(rows[0]), len(rows)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            if remap:
                ch = remap.get(ch, ch)
            surf.set_at((x, y), PAL[ch])
    if flip:
        surf = pygame.transform.flip(surf, True, False)
    _cache[key] = surf
    return surf


def white_copy(surf):
    s = surf.copy()
    s.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return s


# ---------------------------------------------------------------- sprite del cavaliere (16x24, guarda a destra)
HEAD = [
    "......HHHH......",
    ".....HHHHHH.....",
    "....HHHHHHHH....",
    "..RRRRRRRRRRR...",
    ".R..SSSSSSSS....",
    "....SSKSSSKS....",
    "....SSSSSSSS....",
    ".....SSssSS.....",
]
TORSO = {
    "idle": [
        "....AAAAAAAA....",
        "...AAAAAAAAAA...",
        "..AAAaAAAAaAAA..",
        "..AA.AAAAAA.AA..",
        "..SS.AAAAAA.SS..",
        ".....aAAAAa.....",
    ],
    "jump": [
        "..S.AAAAAAAA.S..",
        "..A.AAAAAAAA.A..",
        "..AAAaAAAAaAAA..",
        "....AAAAAAAA....",
        "....AAAAAAAA....",
        ".....aAAAAa.....",
    ],
    "punch": [
        "....AAAAAAAA....",
        "...AAAAAAAAAA...",
        "..AAAaAAAAaAAA..",
        "..AA.AAAAAAAAASS",
        "..SS.AAAAAA.....",
        ".....aAAAAa.....",
    ],
    "hado": [
        "....AAAAAAAA....",
        "...AAAAAAAAAA...",
        "...AAaAAAAaAAAA.",
        "...AAAAAAAAAAASS",
        "...AAAAAAAAAAASS",
        ".....aAAAAa.....",
    ],
}
LEGS = {
    "idle": [
        ".....BBBBBB.....",
        ".....BBBBBB.....",
        ".....BBBBBB.....",
        ".....BB..BB.....",
        ".....BB..BB.....",
        ".....BB..BB.....",
        ".....BB..BB.....",
        ".....bb..bb.....",
        "....bbb..bbb....",
        "....bbb..bbb....",
    ],
    "run1": [
        ".....BBBBBB.....",
        ".....BBBBBB.....",
        ".....BBBBBB.....",
        "....BB....BB....",
        "...BB......BB...",
        "...BB......BB...",
        "..BB........BB..",
        "..bb........bb..",
        ".bbb........bbb.",
        "................",
    ],
    "run2": [
        ".....BBBBBB.....",
        ".....BBBBBB.....",
        ".....BBBBBB.....",
        ".....BB..BBB....",
        "....BB....BBB...",
        "...BB......BB...",
        "...BB.......BB..",
        "...bb.......bb..",
        "..bbb.......bbb.",
        "................",
    ],
    "jump": [
        ".....BBBBBB.....",
        ".....BBBBBB.....",
        "....BBB..BBB....",
        "....BB....BB....",
        "...bbb....bbb...",
        "...bbb....bbb...",
        "................",
        "................",
        "................",
        "................",
    ],
    "kick": [
        ".....BBBBBB.....",
        ".....BBBBBB.....",
        ".....BB.BBBBB...",
        ".....BB..BBBBBBb",
        ".....BB.....bbbb",
        ".....BB.........",
        ".....BB.........",
        ".....bb.........",
        "....bbb.........",
        "................",
    ],
}
PLAYER_FRAMES = {
    "idle": ("idle", "idle"), "run1": ("idle", "run1"), "run2": ("idle", "run2"),
    "jump": ("jump", "jump"), "punch": ("punch", "idle"), "kick": ("idle", "kick"),
    "hado": ("hado", "idle"), "airpunch": ("punch", "jump"), "airkick": ("punch", "kick"),
}
BONES = [
    "................",
    "....WW..W.......",
    "...W..WWWW.W....",
    "..WWWWWWWWWWW...",
    ".WWWWWWWWWWWWWW.",
    "..W.WWWWWWWW.W..",
]

ZOMBIE = [
    [
        "......GGGG......", ".....GGGGGG.....", ".....GRGGRG.....", ".....GGGGGG.....",
        "......GGGG......", ".....gggggg.....", "....gggggggGGGG.", "....gggggggGGGG.",
        "....gggggg......", "....gggggg......", "....gggggg......", "....gggggg......",
        ".....gggg.......", ".....gggg.......", ".....KK.KK......", ".....KK.KK......",
        ".....KK.KK......", ".....KK.KK......", ".....KK.KK......", ".....KK.KK......",
        ".....KK.KK......", ".....KK.KK......", "....KKK.KKK.....", "....KKK.KKK.....",
    ],
    [
        "......GGGG......", ".....GGGGGG.....", ".....GRGGRG.....", ".....GGGGGG.....",
        "......GGGG......", ".....gggggg.....", "....gggggggGGGG.", "....gggggggGGGG.",
        "....gggggg......", "....gggggg......", "....gggggg......", "....gggggg......",
        ".....gggg.......", ".....gggg.......", "....KK..KK......", "....KK...KK.....",
        "...KK.....KK....", "...KK.....KK....", "..KK......KK....", "..KK.......KK...",
        "..KK.......KK...", ".KK........KK...", ".KKK.......KKK..", "................",
    ],
]

DEMON = [
    "....rr..........rr......",
    "....rrr........rrr......",
    ".....rRRRRRRRRRRr.......",
    ".....RRRRRRRRRRRR.......",
    ".....RRYRRRRRRYRR.......",
    ".....RRRRRRRRRRRR.......",
    "......RRRWRRWRRR........",
    "......RRRRRRRRRR........",
    ".......RRRRRRRR.........",
    "rr...RRRRRRRRRRRR...rr..",
    "rrr.RRRRRRRRRRRRRR.rrr..",
    "rrrrRRRRRRRRRRRRRRrrrr..",
    "rrrrRRRRRRRRRRRRRRrrrr..",
    ".rrrRRRRRRRRRRRRRRrrr...",
    "..rrRRRRRRRRRRRRRRrr....",
    "...rRRRRRRRRRRRRRRr.....",
    "....RRRRRRRRRRRRRR......",
    "....RRRR.RRRRR.RRRR.....",
    "....RRR..RRRRR..RRR.....",
    "...YYY...RRRRR...YYY....",
    ".........RRRRR..........",
    "........RRR.RRR.........",
    ".......RRR...RRR........",
    "......RRR.....RRR.......",
    "......RRR.....RRR.......",
    "......rrr.....rrr.......",
    ".....rrrr.....rrrr......",
    "................",
]
DEMON = [r.ljust(24, ".") for r in DEMON]
DEMON_ATTACK = list(DEMON)
DEMON_ATTACK[17] = "....RRRR.RRRRR.RRRRRRRR."
DEMON_ATTACK[18] = "....RRR..RRRRR..RRRRRYYY"
DEMON_ATTACK[19] = "...YYY...RRRRR.......YYY"

GRASS = [
    "LLLLLLLLLLLLLLLL", "LlLLLlLLLLlLLLlL", "llllllllllllllll", "DdDDDDDdDDDDDDdD",
    "DDDDDDDDDDDDDDDD", "DDDdDDDDDDdDDDDD", "DDDDDDDDDDDDDDDD", "dDDDDDdDDDDDDDdD",
    "DDDDDDDDDDDDDDDD", "DDDDdDDDDDdDDDDD", "DDDDDDDDDDDDDDDD", "DdDDDDDDdDDDDDDD",
    "DDDDDDDDDDDDDDdD", "DDDdDDDDDDDdDDDD", "DDDDDDDDDDDDDDDD", "dDDDDDdDDDDDDDDD",
]
DIRT = ["DDDdDDDDDDDdDDDD", "DDDDDDDDDDDDDDDD", "dDDDDDdDDDDDDDDD"] + GRASS[3:]
BRICK = [
    "MMMMMMMmMMMMMMMm", "MMMMMMMmMMMMMMMm", "MMMMMMMmMMMMMMMm", "mmmmmmmmmmmmmmmm",
    "MMMmMMMMMMMmMMMM", "MMMmMMMMMMMmMMMM", "MMMmMMMMMMMmMMMM", "mmmmmmmmmmmmmmmm",
] * 2
QBLOCK = [
    "yyyyyyyyyyyyyyyy", "yYyYYYYYYYYYYyYy", "yYYYYYkkkkYYYYYy", "yYYYYkkYYkkYYYYy",
    "yYYYYkkYYkkYYYYy", "yYYYYYYYYkkYYYYy", "yYYYYYYYkkYYYYYy", "yYYYYYYkkYYYYYYy",
    "yYYYYYYkkYYYYYYy", "yYYYYYYYYYYYYYYy", "yYYYYYYkkYYYYYYy", "yYYYYYYkkYYYYYYy",
    "yYYYYYYYYYYYYYYy", "yYYYYYYYYYYYYYYy", "yYyYYYYYYYYYYyYy", "yyyyyyyyyyyyyyyy",
]
UBLOCK = ["mmmmmmmmmmmmmmmm"] + ["mMMMMMMMMMMMMMMm"] * 14 + ["mmmmmmmmmmmmmmmm"]
PIPE_TOP = ["pPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPp", "pPPWPPPPPPPPPPPPPPPPPPPPPPPPPPpp"] + \
           ["pPPWPPPPPPPPPPPPPPPPPPPPPPPPPPpp"] * 12 + ["pPPPPPPPPPPPPPPPPPPPPPPPPPPPPPpp", "pppppppppppppppppppppppppppppppp"]
PIPE_BODY = ["..pPPWPPPPPPPPPPPPPPPPPPPPPPpp.."] * 16
TOMB = [
    ".....TTTTTT.....", "....TTTTTTTT....", "...TTTTTTTTTT...", "...TTTTTTTTTT...",
    "...TTtTtTtTTT...", "...TTtTtTtTTT...", "...TTTTTTTTTT...", "...TTttttttTT...",
    "...TTTTTTTTTT...", "...TTTTTTTTTT...", "...TTTTTTTTTT...", "...TTTTTTTTTT...",
    "...TTTTTTTTTT...", "...TTTTTTTTTT...", "..tttttttttttt..", "................",
]
CROSS = [
    "......TTTT......", "......TTTT......", "..TTTTTTTTTTTT..", "..TTTTTTTTTTTT..",
    "......TTTT......", "......TTTT......", "......TTTT......", "......TTTT......",
    "......TTTT......", "......TTTT......", "......TTTT......", "......TTTT......",
    "......TTTT......", "......TTTT......", "....tttttttt....", "................",
]
TREE = [
    ".k..........k...", ".kk........kk...", "..kk..kk..kk....", "...kk.kk.kk.....",
    "....kkkkkk......", ".....kkkk.......", ".....kkkk.......", ".....kkkkk......",
    ".....kkkk.......", ".....kkkk.......", ".....kkkkk......", ".....kkkk.......",
    ".....kkkk.......", ".....kkkk.......", ".....kkkk.......", ".....kkkkk......",
    ".....kkkk.......", ".....kkkk.......", ".....kkkk.......", ".....kkkk.......",
    ".....kkkk.......", ".....kkkk.......", "....kkkkkk......", "................",
]
MUSHROOM = [
    ".....RRRRRR.....", "...RRWWRRRRWR...", "..RRWWWRRRRRRR..", ".RRRWWRRRWWRRRR.",
    ".RRRRRRRRWWWRRR.", "RRRRRRRRRRWWRRRR", "RRWWRRRRRRRRRWWR", "RRWWRRRRRRRRRWRR",
    "RRRRRRRRRRRRRRRR", "..SSSSSSSSSSSS..", "..SSKSSSSSSKSS..", "..SSKSSSSSSKSS..",
    "..SSSSSSSSSSSS..", "...SSSSSSSSSS...", "................", "................",
]
COIN = [
    ["..YYYY..", ".YYyyYY.", "YYyYYyYY", "YYyYYyYY", "YYyYYyYY", "YYyYYyYY", ".YYyyYY.", "..YYYY.."],
    ["...YY...", "..YyyY..", "..YyyY..", "..YyyY..", "..YyyY..", "..YyyY..", "..YyyY..", "...YY..."],
]
FIREBALL = [
    [".....WWWWW......", "...WWWCCCWWWW...", "..WCCCCCCCCWWWW.", ".WCCCCCCCCCWWWWW",
     ".WCCCCCCCCCWWWWW", "..WCCCCCCCCWWWW.", "...WWWCCCWWWW...", ".....WWWWW......"],
    [".....WWWWW......", "...WWWCCCWWW....", "..WCCCCCCCCWWW..", ".WCCCCCCCCCWWWWW",
     ".WCCCCCCCCCWWWWW", "..WCCCCCCCCWWW..", "...WWWCCCWWW....", ".....WWWWW......"],
]
DEMONBALL = [r.replace("C", "O").replace("W", "o") for r in FIREBALL[0]]
FLAG = [
    "RRRRRRRRRR", "RRRRRRRRR.", "RRRRRRRR..", "RRRRRRR...", "RRRRRR....", "RRRRR.....", "RRRR......", "RRR.......",
]

FONT = {
    "A": ".#.#.#####.##.#", "B": "##.#.###.#.###.", "C": ".###..#..#...##", "D": "##.#.##.##.###.",
    "E": "####..##.#..###", "F": "####..##.#..#..", "G": ".###..#.##.#.##", "H": "#.##.#####.##.#",
    "I": "###.#..#..#.###", "J": "..#..#..##.#.#.", "K": "#.##.###.#.##.#", "L": "#..#..#..#..###",
    "M": "#.###########.#", "N": "##.#.##.##.##.#", "O": ".#.#.##.##.#.#.", "P": "##.#.###.#..#..",
    "Q": ".#.#.##.###..##", "R": "##.#.###.#.##.#", "S": ".###...#...###.", "T": "###.#..#..#..#.",
    "U": "#.##.##.##.####", "V": "#.##.##.##.#.#.", "W": "#.##.########.#", "X": "#.##.#.#.#.##.#",
    "Y": "#.##.#.#..#..#.", "Z": "###..#.#.#..###", "0": "####.##.##.####", "1": ".#.##..#..#.###",
    "2": "##...#.#.#..###", "3": "###..#.##..####", "4": "#.##.####..#..#", "5": "####..##...###.",
    "6": ".###..####.####", "7": "###..#.#..#..#.", "8": "####.#####.####", "9": "####.####..###.",
    ":": "....#.....#....", "!": ".#..#..#.....#.", ".": "............#..", "-": "......###......",
    "/": "..#..#.#.#..#..", " ": "...............",
}


def draw_text(surf, text, x, y, color=(245, 245, 245), scale=1):
    for ch in text.upper():
        g = FONT.get(ch, FONT[" "]).ljust(15, ".")
        for i, c in enumerate(g[:15]):
            if c == "#":
                surf.fill(color, (x + (i % 3) * scale, y + (i // 3) * scale, scale, scale))
        x += 4 * scale


# ---------------------------------------------------------------- livello
SOLID = set("#D=?MU[]()")


def build_level():
    cols = 212
    g = [["." for _ in range(cols)] for _ in range(ROWS)]

    def ground(a, b):
        for c in range(a, b):
            g[14][c] = "#"
            g[15][c] = "D"
            g[16][c] = "D"

    def put(c, r, ch):
        g[r][c] = ch

    def pipe(c, h):
        top = 14 - h
        put(c, top, "["); put(c + 1, top, "]")
        for r in range(top + 1, 14):
            put(c, r, "("); put(c + 1, r, ")")

    ground(0, 42); ground(46, 84); ground(88, 124); ground(128, 212)
    # decorazioni
    for c in (5, 9, 20, 30, 50, 70, 95, 110, 135, 150):
        put(c, 13, "t")
    for c in (14, 36, 62, 104, 142):
        put(c, 13, "+")
    for c in (24, 56, 78, 116, 146):
        put(c, 13, "Y")
    # blocchi e piattaforme
    for c in range(12, 17):
        put(c, 10, "?" if c in (13, 15) else "=")
    for c in range(41, 47):
        put(c, 10, "=")
    put(60, 10, "M")
    for c in range(66, 72):
        put(c, 10, "?" if c in (67, 70) else "=")
    put(68, 6, "?")
    for c in range(82, 90):
        put(c, 11, "=")
    for i in range(4):
        for c in range(100 + i, 104):
            put(c, 13 - i, "=")
    for c in range(105, 109):
        put(c, 9, "?")
    for c in range(122, 129):
        put(c, 11, "=")
    put(125, 7, "M")
    for c in range(136, 141):
        put(c, 10, "=" if c != 138 else "?")
    pipe(52, 2); pipe(92, 3); pipe(154, 2)
    # arena boss: colonne 162-191, poi bandiera
    put(162, 13, "B")
    put(201, 13, "F")
    return g


class Level:
    def __init__(self):
        self.g = build_level()
        self.cols = len(self.g[0])
        self.w = self.cols * TILE
        self.arena_x = 162 * TILE
        self.flag_x = 201 * TILE
        self.tiles = {
            "#": sprite(GRASS), "D": sprite(DIRT), "=": sprite(BRICK), "?": sprite(QBLOCK),
            "M": sprite(QBLOCK), "U": sprite(UBLOCK), "t": sprite(TOMB), "+": sprite(CROSS),
        }
        self.tree = sprite(TREE)
        self.pipe_top = sprite(PIPE_TOP)
        self.pipe_body = sprite(PIPE_BODY)
        self.coin = [sprite(c) for c in COIN]
        self.flag = sprite(FLAG)

    def at(self, c, r):
        if r < 0 or r >= ROWS or c < 0 or c >= self.cols:
            return "=" if c < 0 else "."
        return self.g[r][c]

    def solid(self, px, py):
        return self.at(int(px // TILE), int(py // TILE)) in SOLID

    def draw(self, s, cam_x, frame):
        c0 = max(0, int(cam_x // TILE))
        for c in range(c0, min(self.cols, c0 + SW // TILE + 2)):
            x = c * TILE - cam_x
            for r in range(ROWS):
                ch = self.g[r][c]
                if ch == ".":
                    continue
                y = r * TILE
                if ch in self.tiles:
                    s.blit(self.tiles[ch], (x, y))
                elif ch == "Y":
                    s.blit(self.tree, (x, y - 8))
                elif ch == "[":
                    s.blit(self.pipe_top, (x, y))
                elif ch == "(":
                    s.blit(self.pipe_body, (x, y))
                elif ch == "F":
                    pygame.draw.rect(s, PAL["T"], (x + 7, y - 96, 2, 112))
                    pygame.draw.rect(s, PAL["Y"], (x + 5, y - 100, 6, 5))
                    s.blit(self.flag, (x - 1, y - 92))


# ---------------------------------------------------------------- entita'
class Entity:
    w, h = 10, 22      # hitbox

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.alive = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def move(self, lv, bump=None):
        # asse x
        self.x += self.vx
        r = self.rect
        if self.vx > 0:
            for py in (r.top + 1, r.centery, r.bottom - 1):
                if lv.solid(r.right - 1, py):
                    self.x = (r.right - 1) // TILE * TILE - self.w
                    self.vx = 0
                    break
        elif self.vx < 0:
            for py in (r.top + 1, r.centery, r.bottom - 1):
                if lv.solid(r.left, py):
                    self.x = (r.left // TILE + 1) * TILE
                    self.vx = 0
                    break
        # asse y
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.y += self.vy
        r = self.rect
        self.on_ground = False
        if self.vy > 0:
            if lv.solid(r.left + 1, r.bottom) or lv.solid(r.right - 2, r.bottom):
                self.y = r.bottom // TILE * TILE - self.h
                self.vy = 0
                self.on_ground = True
        elif self.vy < 0:
            hits = [px for px in (r.left + 1, r.right - 2) if lv.solid(px, r.top)]
            if hits:
                self.y = (r.top // TILE + 1) * TILE
                self.vy = 0
                if bump:
                    row = int(r.top // TILE)
                    special = [px for px in hits if lv.at(int(px // TILE), row) in "?M"]
                    px = min(special or hits, key=lambda p: abs(p - r.centerx))
                    bump(int(px // TILE), row)


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.facing = 1
        self.armor = True
        self.hp = PLAYER_HP
        self.invuln = 0
        self.anim = 0
        self.attack = None      # (nome, frame)
        self.last_down = -999
        self.last_fwd = -999

    def frames(self):
        return sprite_frames(self.armor)

    def hurtbox(self):
        return self.rect.inflate(-2, -2)

    def attack_box(self):
        if not self.attack:
            return None, 0
        name, f = self.attack
        r = self.rect
        if name == "punch" and 3 <= f <= 8:
            return pygame.Rect(r.right if self.facing > 0 else r.left - 12, r.top + 8, 12, 6), 5
        if name == "kick" and 4 <= f <= 11:
            return pygame.Rect(r.right if self.facing > 0 else r.left - 14, r.top + 12, 14, 8), 8
        return None, 0

    def update(self, keys, lv, bump):
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        jump = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        grounded_attack = self.attack and self.on_ground
        if not grounded_attack:
            if right and not left:
                self.vx = min(self.vx + RUN_ACC, RUN_MAX); self.facing = 1
            elif left and not right:
                self.vx = max(self.vx - RUN_ACC, -RUN_MAX); self.facing = -1
            else:
                self.vx *= 0.8 if self.on_ground else 0.98
                if abs(self.vx) < 0.1:
                    self.vx = 0
        else:
            self.vx = 0
        if not jump and self.vy < -2:
            self.vy = -2     # salto corto se si rilascia
        self.move(lv, bump)
        self.anim += abs(self.vx)
        if self.attack:
            name, f = self.attack
            f += 1
            limit = {"punch": 12, "kick": 16, "hado": 20}[name]
            self.attack = None if f >= limit else (name, f)
        if self.invuln:
            self.invuln -= 1

    def do_jump(self):
        if self.on_ground:
            self.vy = JUMP_V
            self.on_ground = False

    def start_attack(self, name):
        if not self.attack:
            self.attack = (name, 0)
            return True
        return False

    def sprite_name(self):
        if self.attack:
            name = self.attack[0]
            if not self.on_ground and name != "hado":
                return "air" + name
            return name
        if not self.on_ground:
            return "jump"
        if abs(self.vx) > 0.3:
            return ("run1", "idle", "run2", "idle")[int(self.anim / 6) % 4]
        return "idle"

    def draw(self, s, cam_x):
        if self.invuln and (self.invuln // 3) % 2:
            return
        img = self.frames()[self.sprite_name()][0 if self.facing > 0 else 1]
        s.blit(img, (int(self.x) - 3 - cam_x, int(self.y) - 2))


_frames_cache = {}


def sprite_frames(armor):
    if armor in _frames_cache:
        return _frames_cache[armor]
    remap = None if armor else UNDERWEAR
    out = {}
    for name, (torso, legs) in PLAYER_FRAMES.items():
        rows = HEAD + TORSO[torso] + LEGS[legs]
        out[name] = (sprite(rows, remap), sprite(rows, remap, flip=True))
    _frames_cache[armor] = out
    return out


class Zombie(Entity):
    def __init__(self, x):
        super().__init__(x, 14 * TILE - 22)
        self.rise = 0
        self.age = 0
        self.dir = -1
        self.imgs = [(sprite(f), sprite(f, flip=True)) for f in ZOMBIE]

    def update(self, lv, player):
        self.age += 1
        if self.rise < 40:
            self.rise += 1
            return
        if self.age > 9 * FPS:
            self.rise -= 1
            if self.rise <= 0:
                self.alive = False
            return
        self.dir = 1 if player.x > self.x else -1
        r = self.rect
        ahead = r.right + 1 if self.dir > 0 else r.left - 2
        if lv.solid(ahead, r.bottom + 1) and not lv.solid(ahead, r.centery):
            self.vx = 0.45 * self.dir
        else:
            self.vx = 0
        self.move(lv)

    def draw(self, s, cam_x, frame):
        h = int(24 * min(1, self.rise / 40))
        if h <= 0:
            return
        img = self.imgs[(self.age // 10) % 2][0 if self.dir > 0 else 1]
        y = 14 * TILE - h
        s.blit(img, (int(self.x) - 3 - cam_x, y), (0, 0, 16, h))
        pygame.draw.rect(s, PAL["d"], (int(self.x) - 5 - cam_x, 14 * TILE - 2, 20, 3))


class Mushroom(Entity):
    w, h = 14, 14

    def __init__(self, x, y):
        super().__init__(x, y)
        self.vx = 0.7
        self.img = sprite(MUSHROOM)
        self.pop = 16

    def update(self, lv):
        if self.pop:
            self.pop -= 1
            self.y -= 1
            return
        if self.vx == 0:
            self.vx = 0.7 if random.random() < 0.5 else -0.7
        d = 1 if self.vx > 0 else -1
        self.move(lv)
        if self.vx == 0:
            self.vx = -0.7 * d
        if self.y > SH + 20:
            self.alive = False

    def draw(self, s, cam_x):
        s.blit(self.img, (int(self.x) - 1 - cam_x, int(self.y) - 1))


class CoinPop:
    def __init__(self, x, y):
        self.x, self.y, self.t = x, y, 0
        self.alive = True

    def update(self):
        self.t += 1
        self.y -= 1.5 if self.t < 12 else -0.5
        self.alive = self.t < 24


class Fireball(Entity):
    w, h = 12, 6

    def __init__(self, x, y, d, owner, dmg):
        super().__init__(x, y)
        self.d = d
        self.owner = owner
        self.dmg = dmg
        self.t = 0
        base = FIREBALL if owner == "player" else [DEMONBALL, DEMONBALL]
        self.imgs = [(sprite(f), sprite(f, flip=True)) for f in base]

    def update(self, lv, cam_x):
        self.t += 1
        self.x += 3.2 * self.d
        r = self.rect
        if lv.solid(r.centerx, r.centery) or r.right < cam_x - 20 or r.left > cam_x + SW + 20:
            self.alive = False

    def draw(self, s, cam_x):
        img = self.imgs[(self.t // 5) % 2][0 if self.d > 0 else 1]
        s.blit(img, (int(self.x) - 2 - cam_x, int(self.y) - 1))


class Boss(Entity):
    w, h = 18, 26

    def __init__(self, x):
        super().__init__(x, 14 * TILE - 26)
        self.hp = BOSS_HP
        self.facing = -1
        self.state = "walk"
        self.t = 0
        self.flash = 0
        self.invuln = 0
        self.imgs = (sprite(DEMON), sprite(DEMON, flip=True))
        self.imgs_atk = (sprite(DEMON_ATTACK), sprite(DEMON_ATTACK, flip=True))
        self.white = (white_copy(self.imgs[0]), white_copy(self.imgs[1]))
        self.cycle = 0

    def attack_box(self):
        if self.state == "claw" and 12 <= self.t <= 22:
            r = self.rect
            return pygame.Rect(r.right if self.facing > 0 else r.left - 14, r.top + 10, 14, 10)
        return None

    def update(self, lv, player, arena_x, spawn_ball):
        self.t += 1
        self.cycle += 1
        if self.invuln:
            self.invuln -= 1
        if self.flash:
            self.flash -= 1
        dx = player.x - self.x
        self.facing = 1 if dx > 0 else -1
        if self.state == "walk":
            self.vx = 0.7 * self.facing if abs(dx) > 20 else 0
            if abs(dx) <= 22 and self.on_ground:
                self.state, self.t = "claw", 0
            elif self.cycle % 170 == 0 and self.on_ground:
                self.state, self.t = "jump", 0
                self.vy = -5.5
                self.vx = 1.6 * self.facing
            elif self.cycle % 230 == 115:
                self.state, self.t = "ball", 0
        elif self.state == "claw":
            self.vx = 0
            if self.t > 34:
                self.state = "walk"
        elif self.state == "jump":
            if self.on_ground and self.t > 5:
                self.state, self.t = "walk", 0
        elif self.state == "ball":
            self.vx = 0
            if self.t == 20:
                r = self.rect
                spawn_ball(r.right if self.facing > 0 else r.left - 12, r.top + 8, self.facing)
            if self.t > 40:
                self.state = "walk"
        self.move(lv)
        self.x = max(arena_x + 4, min(self.x, arena_x + SW - self.w - 4))

    def hit(self, dmg):
        if self.invuln:
            return False
        self.hp = max(0, self.hp - dmg)
        self.invuln = 20
        self.flash = 8
        self.vx = 0
        return True

    def draw(self, s, cam_x):
        i = 0 if self.facing > 0 else 1
        img = self.imgs_atk[i] if self.state == "claw" and self.t >= 10 else self.imgs[i]
        pos = (int(self.x) - 3 - cam_x, int(self.y) - 1)
        s.blit(img, pos)
        if self.flash and (self.flash // 2) % 2:
            s.blit(self.white[i], pos)


# ---------------------------------------------------------------- gioco
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SW, SH), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption("Goblin")
        self.clock = pygame.time.Clock()
        self.s = pygame.Surface((SW, SH))
        self.bg = self.make_bg()
        self.hills = self.make_hills()
        self.bones = sprite(BONES)
        self.frame = 0
        self.hi = 0
        self.new_game()

    def make_bg(self):
        bg = pygame.Surface((SW, SH))
        top, bot = (10, 6, 34), (58, 26, 88)
        for y in range(SH):
            t = y / SH
            pygame.draw.line(bg, [int(top[i] + (bot[i] - top[i]) * t) for i in range(3)], (0, y), (SW, y))
        rnd = random.Random(5)
        for _ in range(90):
            bg.set_at((rnd.randrange(SW), rnd.randrange(150)), (190, 190, 215))
        pygame.draw.circle(bg, (240, 235, 200), (390, 45), 18)
        pygame.draw.circle(bg, (18, 12, 46), (398, 40), 15)
        return bg

    def make_hills(self):
        h = pygame.Surface((SW + 200, 80), pygame.SRCALPHA)
        for i in range(0, SW + 200, 170):
            pygame.draw.ellipse(h, (32, 20, 60), (i, 20, 240, 120))
        for i in range(90, SW + 200, 210):
            pygame.draw.ellipse(h, (24, 15, 48), (i, 40, 200, 100))
        return h

    def new_game(self):
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.lv = Level()
        self.checkpoint = 32
        self.boss_started = False
        self.spawn_player()
        self.state = "play"

    def spawn_player(self):
        self.player = Player(self.checkpoint, 14 * TILE - 22)
        self.zombies, self.items, self.balls, self.pops = [], [], [], []
        self.boss = None
        self.arena = False
        self.arena_open = False
        self.intro = 0
        self.msg = None        # (testo, frames, colore)
        self.time = TIME_START
        self.time_acc = 0
        self.spawn_t = 90
        self.state_t = 0
        self.cam_x = int(max(0, min(self.player.x - SW / 2, self.lv.w - SW)))
        if self.boss_started:
            self.start_arena()

    def start_arena(self):
        self.arena = True
        self.boss_started = True
        self.checkpoint = self.lv.arena_x + 24
        self.boss = Boss(self.lv.arena_x + SW - 60)
        self.zombies = []
        self.msg = ("ROUND 1", 70, PAL["Y"])
        self.intro = 120

    # ---- blocchi
    def bump(self, c, r):
        ch = self.lv.at(c, r)
        if ch == "?":
            self.lv.g[r][c] = "U"
            self.pops.append(CoinPop(c * TILE + 4, r * TILE - 8))
            self.coins += 1
            self.score += 200
        elif ch == "M":
            self.lv.g[r][c] = "U"
            self.items.append(Mushroom(c * TILE + 1, r * TILE - 14))

    def hurt_player(self, dmg, from_x):
        p = self.player
        if p.invuln or self.state != "play":
            return
        p.invuln = 70
        p.vy = -2.5
        p.vx = 1.5 if p.x > from_x else -1.5
        p.attack = None
        if p.armor:
            p.armor = False
        else:
            p.hp = max(0, p.hp - dmg)
            if p.hp == 0:
                self.die()

    def die(self):
        self.state, self.state_t = "dead", 0

    def update(self):
        self.frame += 1
        p = self.player
        if self.state == "play":
            if self.msg:
                t, n, col = self.msg
                self.msg = (t, n - 1, col) if n > 1 else None
            if self.arena and self.intro:
                self.intro -= 1
                if self.intro == 60:
                    self.msg = ("FIGHT!", 50, PAL["R"])
                if self.intro > 60:
                    return
            # tempo
            self.time_acc += 1
            if self.time_acc >= FPS:
                self.time_acc = 0
                self.time -= 1
                if self.time <= 0:
                    self.die()
            keys = pygame.key.get_pressed()
            p.update(keys, self.lv, self.bump)
            # limiti arena
            if self.arena:
                p.x = max(p.x, self.lv.arena_x + 2)
                if not self.arena_open:
                    p.x = min(p.x, self.lv.arena_x + SW - p.w - 2)
            if not self.arena and p.x >= self.lv.arena_x:
                self.start_arena()
            if p.y > SH + 10:
                self.die()
            if p.x >= self.lv.flag_x + 4 and self.arena_open:
                self.state, self.state_t = "win", 0
                self.score += self.time * 10
            # zombie
            if not self.arena:
                self.spawn_t -= 1
                if self.spawn_t <= 0 and len(self.zombies) < 5:
                    self.spawn_t = random.randrange(80, 140)
                    for _ in range(10):
                        x = p.x + random.choice((-1, 1)) * random.randrange(90, 230)
                        c = int(x // TILE)
                        if self.cam_x < x < self.cam_x + SW - 16 and c < 160 and self.lv.at(c, 14) == "#" and self.lv.at(c, 13) == "." and self.lv.at(c + 1, 14) == "#":
                            self.zombies.append(Zombie(x))
                            break
            for z in self.zombies:
                z.update(self.lv, p)
            for m in self.items:
                m.update(self.lv)
            for b in self.balls:
                b.update(self.lv, self.cam_x)
            for c in self.pops:
                c.update()
            # hadouken
            if p.attack and p.attack == ("hado", 6) and sum(1 for b in self.balls if b.owner == "player") < 2:
                r = p.rect
                self.balls.append(Fireball(r.right if p.facing > 0 else r.left - 12, r.top + 8, p.facing, "player", 12))
            # colpi del giocatore
            abox, adm = p.attack_box()
            for z in self.zombies:
                if z.rise < 20:
                    continue
                zr = z.rect
                if abox and abox.colliderect(zr):
                    z.alive = False; self.score += 100; continue
                for b in self.balls:
                    if b.owner == "player" and b.alive and b.rect.colliderect(zr):
                        b.alive = z.alive = False; self.score += 100
                if not z.alive:
                    continue
                if p.hurtbox().colliderect(zr):
                    if p.vy > 0 and p.rect.bottom - zr.top < 10:
                        z.alive = False; self.score += 100; p.vy = -3.5
                    else:
                        self.hurt_player(25, z.x)
            for m in self.items:
                if m.alive and not m.pop and m.rect.colliderect(p.rect):
                    m.alive = False; p.armor = True; p.hp = PLAYER_HP; self.score += 1000
            for b in self.balls:
                if b.owner == "boss" and b.alive and b.rect.colliderect(p.hurtbox()):
                    b.alive = False; self.hurt_player(20, b.x)
            # boss
            bs = self.boss
            if bs and bs.alive:
                def spawn_ball(x, y, d):
                    self.balls.append(Fireball(x, y, d, "boss", 20))
                bs.update(self.lv, p, self.lv.arena_x, spawn_ball)
                br = bs.rect
                if abox and abox.colliderect(br) and bs.hit(adm):
                    self.score += 50
                for b in self.balls:
                    if b.owner == "player" and b.alive and b.rect.colliderect(br) and bs.hit(b.dmg):
                        b.alive = False; self.score += 50
                if p.hurtbox().colliderect(br):
                    if p.vy > 0 and p.rect.bottom - br.top < 10:
                        p.vy = -3.5
                        if bs.hit(10):
                            self.score += 50
                    else:   # corpo a corpo: si spingono, niente danno
                        push = 1 if p.x < bs.x else -1
                        p.x -= push * 1.2
                        bs.x += push * 0.6
                bb = bs.attack_box()
                if bb and bb.colliderect(p.hurtbox()):
                    self.hurt_player(30, bs.x)
                if bs.hp <= 0:
                    bs.alive = False
                    self.score += 5000
                    self.msg = ("K.O.", 120, PAL["Y"])
                    self.arena_open = True
                    self.balls = [b for b in self.balls if b.owner == "player"]
            self.zombies = [z for z in self.zombies if z.alive]
            self.items = [m for m in self.items if m.alive]
            self.balls = [b for b in self.balls if b.alive]
            self.pops = [c for c in self.pops if c.alive]
        elif self.state == "dead":
            self.state_t += 1
            if self.state_t > 100:
                self.lives -= 1
                if self.lives <= 0:
                    self.hi = max(self.hi, self.score)
                    self.state = "gameover"
                else:
                    self.spawn_player()
                    self.state = "play"
        elif self.state == "win":
            self.hi = max(self.hi, self.score)
        # camera
        if self.arena and not self.arena_open:
            self.cam_x = self.lv.arena_x
        else:
            target = p.x + p.w / 2 - SW / 2
            if self.arena:
                target = max(target, self.lv.arena_x)
            self.cam_x = max(0, min(target, self.lv.w - SW))
        self.cam_x = int(self.cam_x)

    # ---- eventi
    def key(self, k):
        p = self.player
        if self.state in ("gameover", "win"):
            if k == pygame.K_RETURN:
                self.new_game()
            return
        if self.state != "play" or (self.arena and self.intro > 60):
            return
        fwd = pygame.K_RIGHT if p.facing > 0 else pygame.K_LEFT
        fwd2 = pygame.K_d if p.facing > 0 else pygame.K_a
        if k in (pygame.K_DOWN, pygame.K_s):
            p.last_down = self.frame
        elif k in (fwd, fwd2):
            p.last_fwd = self.frame
        elif k in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            p.do_jump()
        elif k == pygame.K_x:
            if self.frame - p.last_down < 30 and p.last_down <= p.last_fwd and self.frame - p.last_fwd < 20 and p.on_ground:
                p.start_attack("hado")
            else:
                p.start_attack("punch")
        elif k == pygame.K_c:
            p.start_attack("kick")

    # ---- disegno
    def draw_hud(self):
        s, p = self.s, self.player
        draw_text(s, "KNIGHT", 8, 3)
        draw_text(s, f"X{self.lives}", 36, 3, PAL["Y"])
        self.bar(8, 10, p.hp / PLAYER_HP)
        draw_text(s, "TIME", 232, 3)
        draw_text(s, f"{self.time:03d}", 234, 10, PAL["Y"] if self.time > 30 else PAL["R"])
        draw_text(s, f"{self.score:07d}", 8, 18, PAL["Y"])
        s.blit(self.lv.coin[0], (66, 17))
        draw_text(s, f"X{self.coins:02d}", 76, 18, PAL["Y"])
        draw_text(s, "ARMOR" if p.armor else "NO ARMOR", 100, 18, PAL["A"] if p.armor else PAL["R"])
        draw_text(s, f"HI {self.hi:07d}", SW - 8 - 4 * 10, 18, PAL["W"])
        if self.boss:
            draw_text(s, "DEMON", SW - 8 - 4 * 5, 3)
            self.bar(SW - 8 - 140, 10, self.boss.hp / BOSS_HP, right=True)
        if self.msg:
            t, n, col = self.msg
            draw_text(s, t, SW // 2 - len(t) * 6, 100, col, 3)

    def bar(self, x, y, frac, right=False):
        s = self.s
        pygame.draw.rect(s, PAL["W"], (x - 1, y - 1, 142, 7))
        pygame.draw.rect(s, PAL["r"], (x, y, 140, 5))
        w = int(140 * max(0, frac))
        pygame.draw.rect(s, PAL["Y"], (x + 140 - w if right else x, y, w, 5))

    def draw(self):
        s, cx = self.s, self.cam_x
        s.blit(self.bg, (0, 0))
        s.blit(self.hills, (-(int(cx * 0.3) % 170), 150))
        self.lv.draw(s, cx, self.frame)
        for c in self.pops:
            s.blit(self.lv.coin[(self.frame // 6) % 2], (int(c.x) - cx, int(c.y)))
        for m in self.items:
            m.draw(s, cx)
        for z in self.zombies:
            z.draw(s, cx, self.frame)
        if self.boss and self.boss.alive:
            self.boss.draw(s, cx)
        for b in self.balls:
            b.draw(s, cx)
        p = self.player
        if self.state == "dead":
            s.blit(self.bones, (int(p.x) - 3 - cx, min(int(p.y) + 16, 14 * TILE - 6)))
        else:
            p.draw(s, cx)
        self.draw_hud()
        if self.state == "gameover":
            draw_text(s, "GAME OVER", SW // 2 - 9 * 6, 110, PAL["R"], 3)
            draw_text(s, "PREMI INVIO", SW // 2 - 22, 150)
        elif self.state == "win":
            draw_text(s, "YOU WIN!", SW // 2 - 8 * 6, 100, PAL["Y"], 3)
            draw_text(s, f"SCORE {self.score}", SW // 2 - 26, 140)
            draw_text(s, "PREMI INVIO", SW // 2 - 22, 152)
        self.screen.blit(self.s, (0, 0))
        pygame.display.flip()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        return
                    self.key(e.key)
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
    pygame.quit()
    sys.exit()
