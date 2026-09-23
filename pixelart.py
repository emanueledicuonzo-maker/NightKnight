"""Pixel art di riserva (usata quando manca l'immagine in assets/) e font."""
import pygame
from functools import lru_cache
from pathlib import Path

PAL = {
    "K": (20, 18, 30), "W": (245, 245, 245), "S": (250, 200, 160), "s": (200, 140, 100),
    "A": (205, 210, 225), "a": (120, 125, 150), "H": (205, 210, 225), "R": (220, 40, 40),
    "r": (140, 20, 20), "B": (60, 80, 200), "b": (100, 60, 30), "G": (110, 170, 90),
    "g": (60, 110, 50), "Y": (250, 210, 60), "y": (230, 140, 30), "D": (120, 80, 50),
    "d": (80, 50, 35), "L": (70, 130, 60), "l": (35, 85, 40), "T": (150, 150, 170),
    "t": (95, 95, 115), "O": (150, 60, 190), "o": (90, 30, 120), "C": (80, 200, 255),
    "M": (90, 90, 110), "m": (50, 50, 70), "k": (70, 40, 20), "h": (150, 90, 40),
    "E": (120, 60, 40), "e": (60, 30, 20), "I": (150, 220, 255), "i": (60, 120, 200),
    "N": (255, 230, 120), "n": (200, 120, 20), "V": (60, 200, 120), "v": (20, 120, 70),
    "X": (240, 240, 250), "x": (160, 160, 180),
}

_cache = {}


def sprite(rows, remap=None, flip=False, scale=1):
    key = (tuple(rows), tuple(sorted((remap or {}).items())), flip, scale)
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
    if scale != 1:
        surf = pygame.transform.scale(surf, (w * scale, h * scale))
    _cache[key] = surf
    return surf


# ---- cavaliere 16x24
HEAD = [
    "......HHHH......", ".....HHHHHH.....", "....HHHHHHHH....", "..RRRRRRRRRRR...",
    ".R..SSSSSSSS....", "....SSKSSSKS....", "....SSSSSSSS....", ".....SSssSS.....",
]
TORSO = {
    "idle": ["....AAAAAAAA....", "...AAAAAAAAAA...", "..AAAaAAAAaAAA..", "..AA.AAAAAA.AA..", "..SS.AAAAAA.SS..", ".....aAAAAa....."],
    "jump": ["..S.AAAAAAAA.S..", "..A.AAAAAAAA.A..", "..AAAaAAAAaAAA..", "....AAAAAAAA....", "....AAAAAAAA....", ".....aAAAAa....."],
    "punch": ["....AAAAAAAA....", "...AAAAAAAAAA...", "..AAAaAAAAaAAA..", "..AA.AAAAAAAAASS", "..SS.AAAAAA.....", ".....aAAAAa....."],
    "throw": ["....AAAAAAAA....", "...AAAAAAAAAA...", "..AAAaAAAAaAAAS.", "..AA.AAAAAAAAAS.", "..SS.AAAAAA.....", ".....aAAAAa....."],
    "hado": ["....AAAAAAAA....", "...AAAAAAAAAA...", "...AAaAAAAaAAAA.", "...AAAAAAAAAAASS", "...AAAAAAAAAAASS", ".....aAAAAa....."],
}
LEGS = {
    "idle": [".....BBBBBB.....", ".....BBBBBB.....", ".....BBBBBB.....", ".....BB..BB.....", ".....BB..BB.....",
             ".....BB..BB.....", ".....BB..BB.....", ".....bb..bb.....", "....bbb..bbb....", "....bbb..bbb...."],
    "run1": [".....BBBBBB.....", ".....BBBBBB.....", ".....BBBBBB.....", "....BB....BB....", "...BB......BB...",
             "...BB......BB...", "..BB........BB..", "..bb........bb..", ".bbb........bbb.", "................"],
    "run2": [".....BBBBBB.....", ".....BBBBBB.....", ".....BBBBBB.....", ".....BB..BBB....", "....BB....BBB...",
             "...BB......BB...", "...BB.......BB..", "...bb.......bb..", "..bbb.......bbb.", "................"],
    "jump": [".....BBBBBB.....", ".....BBBBBB.....", "....BBB..BBB....", "....BB....BB....", "...bbb....bbb...",
             "...bbb....bbb...", "................", "................", "................", "................"],
    "kick": [".....BBBBBB.....", ".....BBBBBB.....", ".....BB.BBBBB...", ".....BB..BBBBBBb", ".....BB.....bbbb",
             ".....BB.........", ".....BB.........", ".....bb.........", "....bbb.........", "................"],
    "climb": [".....BBBBBB.....", ".....BBBBBB.....", "....BBB..BBB....", "...BB......BB...", "...bb......bb...",
              "..bbb......bbb..", "................", "................", "................", "................"],
}
PLAYER_FRAMES = {
    "idle": ("idle", "idle"), "run1": ("idle", "run1"), "run2": ("idle", "run2"),
    "jump": ("jump", "jump"), "punch": ("punch", "idle"), "kick": ("idle", "kick"),
    "throw": ("throw", "idle"), "hado": ("hado", "idle"), "airpunch": ("punch", "jump"),
    "airkick": ("punch", "kick"), "airthrow": ("throw", "jump"), "climb": ("jump", "climb"),
}
BONES = ["................", "....WW..W.......", "...W..WWWW.W....", "..WWWWWWWWWWW...", ".WWWWWWWWWWWWWW.", "..W.WWWWWWWW.W.."]

ZOMBIE = [
    ["......GGGG......", ".....GGGGGG.....", ".....GRGGRG.....", ".....GGGGGG.....", "......GGGG......", ".....gggggg.....",
     "....gggggggGGGG.", "....gggggggGGGG.", "....gggggg......", "....gggggg......", "....gggggg......", "....gggggg......",
     ".....gggg.......", ".....gggg.......", ".....KK.KK......", ".....KK.KK......", ".....KK.KK......", ".....KK.KK......",
     ".....KK.KK......", ".....KK.KK......", ".....KK.KK......", ".....KK.KK......", "....KKK.KKK.....", "....KKK.KKK....."],
    ["......GGGG......", ".....GGGGGG.....", ".....GRGGRG.....", ".....GGGGGG.....", "......GGGG......", ".....gggggg.....",
     "....gggggggGGGG.", "....gggggggGGGG.", "....gggggg......", "....gggggg......", "....gggggg......", "....gggggg......",
     ".....gggg.......", ".....gggg.......", "....KK..KK......", "....KK...KK.....", "...KK.....KK....", "...KK.....KK....",
     "..KK......KK....", "..KK.......KK...", "..KK.......KK...", ".KK........KK...", ".KKK.......KKK..", "................"],
]
SKELETON_MAP = {"G": "X", "g": "x", "K": "x", "R": "R"}
CROW = [
    ["..KK............", ".KKKK...........", "KKKKKKKKKKKK....", ".KKKKKKKKKKKKKK.", "..KKKKKKKKKK....", "...KKKK.........", "....KK..........", "...y............"],
    ["................", "................", "KKKKKKKKKKKK....", ".KKKKKKKKKKKKKK.", "..KKKKKKKKKK....", "...KKKKKKKKK....", "....KKKKKKKKK...", "...y....KKK....."],
]
DEMON = [
    "....rr..........rr......", "....rrr........rrr......", ".....rRRRRRRRRRRr.......", ".....RRRRRRRRRRRR.......",
    ".....RRYRRRRRRYRR.......", ".....RRRRRRRRRRRR.......", "......RRRWRRWRRR........", "......RRRRRRRRRR........",
    ".......RRRRRRRR.........", "rr...RRRRRRRRRRRR...rr..", "rrr.RRRRRRRRRRRRRR.rrr..", "rrrrRRRRRRRRRRRRRRrrrr..",
    "rrrrRRRRRRRRRRRRRRrrrr..", ".rrrRRRRRRRRRRRRRRrrr...", "..rrRRRRRRRRRRRRRRrr....", "...rRRRRRRRRRRRRRRr.....",
    "....RRRRRRRRRRRRRR......", "....RRRR.RRRRR.RRRR.....", "....RRR..RRRRR..RRR.....", "...YYY...RRRRR...YYY....",
    ".........RRRRR..........", "........RRR.RRR.........", ".......RRR...RRR........", "......RRR.....RRR.......",
    "......RRR.....RRR.......", "......rrr.....rrr.......", ".....rrrr.....rrrr......", "........................",
]
DEMON_ATTACK = list(DEMON)
DEMON_ATTACK[17] = "....RRRR.RRRRR.RRRRRRRR."
DEMON_ATTACK[18] = "....RRR..RRRRR..RRRRRYYY"
DEMON_ATTACK[19] = "...YYY...RRRRR.......YYY"

GRASS = ["LLLLLLLLLLLLLLLL", "LlLLLlLLLLlLLLlL", "llllllllllllllll", "DdDDDDDdDDDDDDdD", "DDDDDDDDDDDDDDDD", "DDDdDDDDDDdDDDDD",
         "DDDDDDDDDDDDDDDD", "dDDDDDdDDDDDDDdD", "DDDDDDDDDDDDDDDD", "DDDDdDDDDDdDDDDD", "DDDDDDDDDDDDDDDD", "DdDDDDDDdDDDDDDD",
         "DDDDDDDDDDDDDDdD", "DDDdDDDDDDDdDDDD", "DDDDDDDDDDDDDDDD", "dDDDDDdDDDDDDDDD"]
DIRT = ["DDDdDDDDDDDdDDDD", "DDDDDDDDDDDDDDDD", "dDDDDDdDDDDDDDDD"] + GRASS[3:]
SLAB = ["TTTTTTTTTTTTTTTT", "TtTTTTtTTTTTtTTT", "tttttttttttttttt", "mMMMMMMMmMMMMMMM", "mMMMMMMMmMMMMMMM", "mmmmmmmmmmmmmmmm",
        "MMMmMMMMMMMmMMMM", "MMMmMMMMMMMmMMMM", "mmmmmmmmmmmmmmmm", "mMMMMMMMmMMMMMMM", "mMMMMMMMmMMMMMMM", "mmmmmmmmmmmmmmmm",
        "MMMmMMMMMMMmMMMM", "MMMmMMMMMMMmMMMM", "MMMmMMMMMMMmMMMM", "mmmmmmmmmmmmmmmm"]
STONE = ["MMMMMMMmMMMMMMMm", "MMMMMMMmMMMMMMMm", "MMMMMMMmMMMMMMMm", "mmmmmmmmmmmmmmmm", "MMMmMMMMMMMmMMMM", "MMMmMMMMMMMmMMMM",
         "MMMmMMMMMMMmMMMM", "mmmmmmmmmmmmmmmm"] * 2
LADDER = ["k..............k", "k..............k", "kkkkkkkkkkkkkkkk", "k..............k", "k..............k", "k..............k",
          "kkkkkkkkkkkkkkkk", "k..............k", "k..............k", "k..............k", "kkkkkkkkkkkkkkkk", "k..............k",
          "k..............k", "k..............k", "kkkkkkkkkkkkkkkk", "k..............k"]
SPIKES = ["................", "................", "................", "................", "................", "................",
          "...X.......X....", "...X.......X....", "..XxX.....XxX...", "..XxX.....XxX...", ".XxxxX...XxxxX..", ".XxxxX...XxxxX..",
          "XxxxxxX.XxxxxxX.", "XxxxxxX.XxxxxxX.", "mmmmmmmmmmmmmmmm", "mmmmmmmmmmmmmmmm"]
DOOR = ["....TTTTTTTT....", "...TTttttttTT...", "..TTteeeeeetTT..", "..TteeEEEEeetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..",
        "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEYEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..",
        "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..",
        "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..",
        "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..", "..TteEEEEEEetT..",
        ".TTTTTTTTTTTTTT.", "TTTTTTTTTTTTTTTT"]
TOMB = [".....TTTTTT.....", "....TTTTTTTT....", "...TTTTTTTTTT...", "...TTTTTTTTTT...", "...TTtTtTtTTT...", "...TTtTtTtTTT...",
        "...TTTTTTTTTT...", "...TTttttttTT...", "...TTTTTTTTTT...", "...TTTTTTTTTT...", "...TTTTTTTTTT...", "...TTTTTTTTTT...",
        "...TTTTTTTTTT...", "...TTTTTTTTTT...", "..tttttttttttt..", "................"]
CROSS = ["......TTTT......", "......TTTT......", "..TTTTTTTTTTTT..", "..TTTTTTTTTTTT..", "......TTTT......", "......TTTT......",
         "......TTTT......", "......TTTT......", "......TTTT......", "......TTTT......", "......TTTT......", "......TTTT......",
         "......TTTT......", "......TTTT......", "....tttttttt....", "................"]
TREE = [".k..........k...", ".kk........kk...", "..kk..kk..kk....", "...kk.kk.kk.....", "....kkkkkk......", ".....kkkk.......",
        ".....kkkk.......", ".....kkkkk......", ".....kkkk.......", ".....kkkk.......", ".....kkkkk......", ".....kkkk.......",
        ".....kkkk.......", ".....kkkk.......", ".....kkkk.......", ".....kkkkk......", ".....kkkk.......", ".....kkkk.......",
        ".....kkkk.......", ".....kkkk.......", ".....kkkk.......", ".....kkkk.......", "....kkkkkk......", "................"]
POT = ["................", "................", "......nnnn......", ".....nNNNNn.....", "....nNNNNNNn....", "....nNNNNNNn....",
       "...nNNNNNNNNn...", "...nNNNNNNNNn...", "...nNNNNNNNNn...", "...nNNNNNNNNn...", "....nNNNNNNn....", "....nNNNNNNn....",
       ".....nNNNNn.....", "......nnnn......", "................", "................"]
CHEST = ["................", "................", "................", "................", "..kkkkkkkkkkkk..", ".khhhhhhhhhhhhk.",
         ".khhhhhhhhhhhhk.", ".kkkkkkkkkkkkkk.", ".khhhhhhYYhhhhk.", ".khhhhhhYYhhhhk.", ".khhhhhhhhhhhhk.", ".khhhhhhhhhhhhk.",
         ".khhhhhhhhhhhhk.", ".kkkkkkkkkkkkkk.", "................", "................"]
GHOST = [
    ["....WWWWWWWW....", "...WWWWWWWWWW...", "..WWWWWWWWWWWW..", "..WWKKWWWWKKWW..", "..WWKKWWWWKKWW..", "..WWWWWWWWWWWW..",
     "..WWWWWKKWWWWW..", "..WWWWWWWWWWWW..", "..WWWWWWWWWWWW..", "..WWWWWWWWWWWW..", "..WWWWWWWWWWWW..", "..WWWWWWWWWWWW..",
     "..WWWWWWWWWWWW..", "..WWWWWWWWWWWW..", "..WW.WWW.WWW.WW.", "..W...W...W...W."],
    ["....WWWWWWWW....", "...WWWWWWWWWW...", "..WWWWWWWWWWWW..", "..WWKKWWWWKKWW..", "..WWKKWWWWKKWW..", "..WWWWWWWWWWWW..",
     "..WWWWWKKWWWWW..", "..WWWWWWWWWWWW..", "..WWWWWWWWWWWW..", "..WWWWWWWWWWWW..", "..WWWWWWWWWWWW..", "..WWWWWWWWWWWW..",
     "..WWWWWWWWWWWW..", ".WWWWWWWWWWWWWW.", ".W.WWW.WWW.WWW.W", "....W...W...W..."],
]
LANCE = ["................", "................", "..NNNNNNNNNNNNNX", "..NNNNNNNNNNNNNX", "................", "................"]
FIREBALL = [
    [".....WWWWW......", "...WWWCCCWWWW...", "..WCCCCCCCCWWWW.", ".WCCCCCCCCCWWWWW", ".WCCCCCCCCCWWWWW", "..WCCCCCCCCWWWW.", "...WWWCCCWWWW...", ".....WWWWW......"],
    [".....WWWWW......", "...WWWCCCWWW....", "..WCCCCCCCCWWW..", ".WCCCCCCCCCWWWWW", ".WCCCCCCCCCWWWWW", "..WCCCCCCCCWWW..", "...WWWCCCWWW....", ".....WWWWW......"],
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
    "/": "..#..#.#.#..#..", "'": ".#..#..........", ",": ".............#.#.", " ": "...............",
}


@lru_cache(maxsize=32)
def _font(scale):
    if not pygame.font.get_init():
        pygame.font.init()
    name = "DejaVuSerif.ttf" if scale >= 7 else "Lato-Semibold.ttf"
    path = Path(__file__).resolve().parent / "assets" / "fonts" / name
    return pygame.font.Font(str(path), max(12, int(scale * 6)))


@lru_cache(maxsize=256)
def _text_image(text, color, scale):
    font = _font(scale)
    ink = font.render(text, True, color)
    shadow = font.render(text, True, (4, 7, 10))
    out = pygame.Surface((ink.get_width() + 4, ink.get_height() + 4), pygame.SRCALPHA)
    out.blit(shadow, (2, 3))
    out.blit(ink, (0, 0))
    return out


def draw_text(surf, text, x, y, color=(245, 245, 245), scale=4):
    surf.blit(_text_image(text, tuple(color), scale), (x, y))


def text_width(text, scale=4):
    return _font(scale).size(text)[0]
