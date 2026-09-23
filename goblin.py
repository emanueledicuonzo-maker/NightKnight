#!/usr/bin/env python3
"""Goblin - 12 cimiteri. Sopra, sottoterra, duello col Cavaliere. Linux 1920x1080."""
import math
import os
import argparse
import random

import pygame

import assets
import athletics
import knights
import levels
import music
import pixelart as px
import progress
import titan

W, H = 1920, 1080
FPS = 60
TILE = 64
SKY_PAN = 360        # di quanto scorre il cielo dall'inizio alla fine del livello
TITAN_N = 6          # il terreno di Titano copre 6x6 tessere
ROWS = 17
GROUND = levels.GROUND
GRAVITY = 0.75
MAX_FALL = 18
RUN_ACC = 0.65
RUN_MAX = 5.8
SPRINT_MAX = 10.0
JUMP_V = -20.0
SHORT_JUMP_V = -16.0
CLIMB = 5
COYOTE_FRAMES = 6
JUMP_BUFFER_FRAMES = 7
PLAYER_HP = 100
SOLID = set("#D=S^")
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

PS = 8          # scala pixel art personaggi
PW, PH = 16 * PS, 24 * PS


# ---------------------------------------------------------------- grafica
def player_images():
    out = {}
    pre = "knight_"
    for name, (torso, legs) in px.PLAYER_FRAMES.items():
        rows = px.HEAD + px.TORSO[torso] + px.LEGS[legs]
        file = {"run1": "run1", "run2": "run2", "jump": "jump", "punch": "punch", "kick": "kick",
                "throw": "throw", "hado": "special", "airpunch": "punch", "airkick": "kick",
                "airthrow": "throw", "climb": "climb", "idle": "idle"}[name]
        chain = [pre + file, pre + "idle", pre + "run1"]
        fname = next((n for n in chain if assets.has(n)), pre + file)
        img = assets.load(fname, PW, PH, assets.pix(rows, None, PS), by_height=True)
        out[name] = (img, assets.flip(img))
        if fname != pre + file and assets.has(fname):
            out.setdefault("_fallback", set()).add(name)     # posa vera mancante: si anima la posa di ripiego
    out.setdefault("_fallback", set())
    return out


def tinted(img, color):
    """Copia dello sprite pixel-art con il rosso sostituito dal colore del boss."""
    s = img.copy()
    pa = pygame.PixelArray(s)
    dark = tuple(max(0, int(v * 0.55)) for v in color)
    pa.replace(px.PAL["R"], color)
    pa.replace(px.PAL["r"], dark)
    del pa
    return s


def white_copy(surf):
    s = surf.copy()
    s.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return s


class Gfx:
    def __init__(self):
        self.tiles = {
            "#": assets.load("ground_grass", TILE, TILE, assets.pix(px.GRASS, scale=4), exact=True),
            "D": assets.load("ground_dirt", TILE, TILE, assets.pix(px.DIRT, scale=4), exact=True),
            "=": assets.load("slab", TILE, TILE, assets.pix(px.SLAB, scale=4), exact=True, crop_top=0.12),
            "S": assets.load("stone_wall", TILE, TILE, assets.pix(px.STONE, scale=4), exact=True),
            "H": assets.load("ladder", TILE, TILE, assets.pix(px.LADDER, scale=4), exact=True),
            "^": assets.load("spikes", TILE, TILE, assets.pix(px.SPIKES, scale=4), exact=True),
        }
        # Terreno di Titano: l'immagine e' un'unica sezione di suolo alla Huygens.
        # Si scala a TITAN_N x TITAN_N tessere, cosi' i ciottoli restano leggibili:
        # la riga in alto e' la crosta calpestabile, le altre il sottosuolo.
        self.titan_ground = None
        if assets.has("titan_ground_grass"):
            img = pygame.image.load(os.path.join(assets.DIR, "titan_ground_grass.png")).convert()
            top = img.get_height() // 30          # striscia scura sopra la superficie
            img = img.subsurface((0, top, img.get_width(), img.get_height() - top))
            self.titan_ground = pygame.transform.smoothscale(img, (TILE * TITAN_N, TILE * TITAN_N))
        self.titan_lake = pygame.Surface((TILE, H - GROUND * TILE), pygame.SRCALPHA)
        self.titan_lake.fill((23, 12, 13, 255))
        for y in range(18, self.titan_lake.get_height(), 24):
            pygame.draw.line(self.titan_lake, (143, 66, 24, 155), (5, y), (TILE - 5, y), 2)
        self.deco = {
            "t": assets.load("tomb1", TILE, TILE, assets.pix(px.TOMB, scale=4)),
            "+": assets.load("cross", TILE, TILE, assets.pix(px.CROSS, scale=4)),
            "Y": assets.load("tree", TILE * 2, TILE * 3, assets.pix(px.TREE, scale=8)),
            "p": assets.load("pot", TILE, TILE, assets.pix(px.POT, scale=4)),
            "c": assets.load("chest", TILE, TILE, assets.pix(px.CHEST, scale=4)),
            "E": assets.load("door", TILE, TILE * 2, assets.pix(px.DOOR, scale=4)),
        }
        if assets.has("tomb2"):
            self.deco["t2"] = assets.load("tomb2", TILE, TILE)
        # Lapidi, croci e alberi erano l'arredo da cimitero fantasy: senza il loro
        # disegno non si mostrano, invece di ripiegare sui pixel di riserva.
        for ch, name in (("t", "tomb1"), ("+", "cross"), ("Y", "tree")):
            if not assets.has(name):
                del self.deco[ch]
        self.player = player_images()
        self.sheets = {}
        # posa -> (file, colonne, righe): i fogli cartoon hanno griglie diverse
        for pose, (file, cols, rows) in {
                "run": ("run_sheet", 4, 2), "jump": ("jump_sheet", 4, 2),
                "throw": ("sword_sheet", 4, 1), "punch": ("stone_sheet", 4, 1),
                "kick": ("kick_sheet", 3, 1), "flykick": ("flykick_sheet", 3, 1),
                "spinkick": ("spinkick_sheet", 4, 2)}.items():
            fr = assets.sheet("knight_" + file, PH, cols, rows, typical=True)
            if fr:
                self.sheets[pose] = (fr, [assets.flip(f) for f in fr])
        self.bones = px.sprite(px.BONES, scale=PS)
        self.zombie = [assets.load(f"zombie_walk{i + 1}", PW, PH, assets.pix(px.ZOMBIE[i], scale=PS), by_height=True) for i in range(2)]
        # Sagome provvisorie ottenute dagli asset esistenti, senza nuove immagini.
        # Prigionieri: coloni chiusi in una capsula, poco piu' alta di NightKnight.
        if assets.has("prigioniero_spento") and assets.has("prigioniero_acceso"):
            self.spento_sleeping = assets.load("prigioniero_spento", PW * 2, PH * 5 // 4, by_height=True)
            self.spento_awake = assets.load("prigioniero_acceso", PW * 2, PH * 5 // 4, by_height=True)
        else:
            self.spento_sleeping = self.zombie[0].copy()
            self.spento_sleeping.fill((70, 62, 52, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.spento_awake = self.zombie[0].copy()
            self.spento_awake.fill((90, 63, 25, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.skeleton = [assets.load(f"skeleton_walk{i + 1}", PW, PH, assets.pix(px.ZOMBIE[i], px.SKELETON_MAP, PS), by_height=True) for i in range(2)]
        if assets.has("crow_1") and assets.has("crow_2"):
            self.crow = assets.frames(["crow_1", "crow_2"], 10 * PS)
        else:
            self.crow = [assets.load(f"crow_{i + 1}", 16 * PS, 8 * PS, assets.pix(px.CROW[i], scale=PS)) for i in range(2)]
        # Bianca resta pulcino nei primi quattro cimiteri: due pose di volo.
        self.bianca = [assets.load(f"bianca_chick_{i + 1}", 150, 105, by_height=True) for i in range(2)]
        self.ghost = [assets.load(f"ghost_{i + 1}", 16 * PS, 16 * PS, assets.pix(px.GHOST[i], scale=PS), by_height=True) for i in range(2)]
        self.titan_hills_near = assets.load("hills_02", W, H, exact=True) if assets.has("hills_02") else None
        self.boss_cache = {}
        self.bg_cache = {}

    def knight(self, num, color):
        if num not in self.boss_cache:
            self.boss_cache[num] = knights.knight_images(self, num, color)
        return self.boss_cache[num]

    def titan_tile(self, ch, c, r):
        if self.titan_ground is None or ch not in "#D":
            return None
        row = 0 if ch == "#" else 1 + r % (TITAN_N - 1)
        return self.titan_ground.subsurface(((c % TITAN_N) * TILE, row * TILE, TILE, TILE))

    def wide_sky(self, num, pan):
        """Cielo allargato di `pan` pixel, in proporzione, ancorato in basso."""
        key = ("wide_sky", num, pan)
        if key not in self.bg_cache:
            sky = self.background("sky", num)
            k = (W + pan) / sky.get_width()
            self.bg_cache[key] = pygame.transform.smoothscale(sky, (W + pan, int(sky.get_height() * k)))
        return self.bg_cache[key]

    def mirrored(self, img):
        """Striscia [immagine | immagine specchiata]: ripetuta, non mostra cuciture."""
        key = ("mirrored", id(img))
        if key not in self.bg_cache:
            strip = pygame.Surface((img.get_width() * 2, img.get_height()), pygame.SRCALPHA)
            strip.blit(img, (0, 0))
            strip.blit(pygame.transform.flip(img, True, False), (img.get_width(), 0))
            self.bg_cache[key] = strip
        return self.bg_cache[key]

    def background(self, kind, num):
        key = (kind, num)
        if key in self.bg_cache:
            return self.bg_cache[key]
        name = None
        for n in range(num, 0, -1):
            if assets.has(f"{kind}_{n:02d}"):
                name = f"{kind}_{n:02d}"
                break
        img = assets.load(name, W, H, exact=True) if name else self.make_bg(kind, num)
        self.bg_cache[key] = img
        return img

    def make_bg(self, kind, num):
        rnd = random.Random(num)
        if kind == "hills":
            s = pygame.Surface((W + 800, 360), pygame.SRCALPHA)
            for i in range(0, W + 800, 680):
                pygame.draw.ellipse(s, (32, 20, 60), (i, 90, 960, 480))
            for i in range(360, W + 800, 840):
                pygame.draw.ellipse(s, (24, 15, 48), (i, 170, 800, 400))
            for i in range(60, W + 800, 230):
                pygame.draw.rect(s, (22, 16, 40), (i, 250 + rnd.randrange(40), 40, 110))
            return s
        s = pygame.Surface((W, H))
        if kind == "sky":
            top, bot = (10, 6, 34), (58, 26, 88)
        elif kind == "crypt_bg":
            top, bot = (12, 14, 18), (30, 34, 40)
        else:
            top, bot = (20, 8, 30), (70, 20, 60)
        for y in range(H):
            t = y / H
            pygame.draw.line(s, [int(top[i] + (bot[i] - top[i]) * t) for i in range(3)], (0, y), (W, y))
        if kind != "crypt_bg":
            for _ in range(160):
                pygame.draw.rect(s, (200, 200, 225), (rnd.randrange(W), rnd.randrange(600), 3, 3))
            pygame.draw.circle(s, (240, 235, 200), (1560, 180), 80)
            pygame.draw.circle(s, top, (1595, 160), 66)
        else:
            for i in range(0, W, 320):
                pygame.draw.rect(s, (40, 44, 52), (i + 100, 64, 60, H))
                pygame.draw.rect(s, (60, 130, 60), (i + 122, 380, 16, 30))
                pygame.draw.ellipse(s, (90, 200, 90), (i + 116, 350, 28, 40))
        return s


# ---------------------------------------------------------------- livello
class Level:
    def __init__(self, g, kind):
        self.g = g
        self.kind = kind
        self.cols = len(g[0])
        self.w = self.cols * TILE
        self.markers = []
        for r in range(ROWS):
            for c in range(self.cols):
                if g[r][c] in "kvgEqu":
                    self.markers.append((g[r][c], c, r))
        self.exit = next(((c, r) for ch, c, r in self.markers if ch == "E"), (self.cols - 4, GROUND - 1))

    def at(self, c, r):
        if c < 0 or c >= self.cols:
            return "S"
        if r < 0 or r >= ROWS:
            return "."
        return self.g[r][c]

    def solid(self, x, y):
        return self.at(int(x // TILE), int(y // TILE)) in SOLID

    def tile_at(self, x, y):
        return self.at(int(x // TILE), int(y // TILE))


# ---------------------------------------------------------------- entita'
class Entity:
    w, h = 70, 176
    ox, oy = 29, 16       # offset sprite -> hitbox

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.alive = True
        self.facing = 1

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def move(self, lv, gravity=True):
        self.x += self.vx
        r = self.rect
        if self.vx > 0:
            for py in (r.top + 2, r.centery, r.bottom - 2):
                if lv.solid(r.right - 1, py):
                    self.x = (r.right - 1) // TILE * TILE - self.w
                    self.vx = 0
                    break
        elif self.vx < 0:
            for py in (r.top + 2, r.centery, r.bottom - 2):
                if lv.solid(r.left, py):
                    self.x = (r.left // TILE + 1) * TILE
                    self.vx = 0
                    break
        if gravity:
            self.vy = min(self.vy + GRAVITY * getattr(self, "gravity_scale", 1.0), MAX_FALL)
        self.y += self.vy
        r = self.rect
        self.on_ground = False
        if self.vy > 0:
            if lv.solid(r.left + 2, r.bottom) or lv.solid(r.right - 3, r.bottom):
                self.y = r.bottom // TILE * TILE - self.h
                self.vy = 0
                self.on_ground = True
        elif self.vy < 0:
            if lv.solid(r.left + 2, r.top) or lv.solid(r.right - 3, r.top):
                self.y = (r.top // TILE + 1) * TILE
                self.vy = 0

    def draw_img(self, s, img, cam):
        r = self.rect
        s.blit(img, (r.centerx - img.get_width() // 2 - cam, r.bottom - img.get_height()))


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.hp = PLAYER_HP
        self.albedo = 0
        self.invuln = 0
        self.anim = 0.0
        self.run_t = 0.0
        self.attack = None
        self.climbing = False
        self.last_down = -999
        self.last_fwd = -999
        self.power = None
        self.coyote = 0
        self.jump_buffer = 0
        self.jumped = False
        self.mounted = False
        self.weapon = levels.weapon_cfg(0)
        self.gravity_scale = 1.0

    def hurtbox(self):
        return self.rect.inflate(-10, -6)

    def attack_box(self):
        if not self.attack:
            return None, 0
        name, f = self.attack
        r = self.rect
        if name == "punch" and 3 <= f <= 9:
            return pygame.Rect(r.right if self.facing > 0 else r.left - 90, r.top + 50, 90, 46), 6
        if name == "kick" and 4 <= f <= 12:
            return pygame.Rect(r.right if self.facing > 0 else r.left - 110, r.top + 76, 110, 60), 9
        if name == "throw" and (4 <= f <= 10 or (self.power == "double" and 14 <= f <= 19)):
            reach = 170 + (60 if self.power == "pierce" else 0) + (100 if self.power == "big" else 0)
            dmg = 12 * (2 if self.power in ("fire", "big") else 1)
            if self.power == "bounce":
                return pygame.Rect(r.left - reach, r.top + 50, r.w + reach * 2, 50), dmg
            return pygame.Rect(r.right if self.facing > 0 else r.left - reach, r.top + 50, reach, 50), dmg
        if name == "albedo" and 4 <= f <= 38 and f % 5 == 0:
            return pygame.Rect(r.right if self.facing > 0 else r.left - 170, r.top + 30, 170, 130), 12
        return None, 0

    def update(self, keys, lv):
        self.jumped = False
        self.coyote = COYOTE_FRAMES if self.on_ground else max(0, self.coyote - 1)
        self.jump_buffer = max(0, self.jump_buffer - 1)
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up = keys[pygame.K_UP] or keys[pygame.K_w]
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        jump = keys[pygame.K_SPACE] or up
        speed_limit = 12.0 if self.mounted else SPRINT_MAX if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else RUN_MAX
        if not self.on_ground:
            speed_limit = max(speed_limit, abs(self.vx))
        r = self.rect
        on_ladder = lv.tile_at(r.centerx, r.centery) == "H"
        ladder_below = lv.tile_at(r.centerx, r.bottom + 2) == "H"
        if not self.climbing and ((on_ladder and (up or down)) or (ladder_below and down and self.on_ground)):
            self.climbing = True
            self.attack = None
            if ladder_below and not on_ladder:
                self.y += 8
        if self.climbing:
            if not (on_ladder or ladder_below):
                self.climbing = False
            else:
                self.vx = 0
                self.vy = 0
                feet_row = r.bottom // TILE
                at_top = lv.at(r.centerx // TILE, feet_row) == "H" and lv.at(r.centerx // TILE, feet_row - 1) != "H"
                if up and at_top and r.bottom - feet_row * TILE <= CLIMB * 4:
                    self.y = feet_row * TILE - self.h      # in piedi sulla cima della scala
                    self.climbing = False
                    self.on_ground = True
                    return
                if up:
                    self.y -= CLIMB
                elif down:
                    self.y += CLIMB
                if left and not right:
                    self.x -= 2; self.facing = -1
                elif right and not left:
                    self.x += 2; self.facing = 1
                self.anim += 0.5 if (up or down) else 0
                self.move(lv, gravity=False)
                if self.on_ground and down:
                    self.climbing = False
                if self.invuln:
                    self.invuln -= 1
                return
        grounded_attack = self.attack and self.on_ground
        if self.attack and self.attack[0] == "albedo":
            self.vx = 4 * self.facing
        elif not grounded_attack:
            if right and not left:
                self.vx = min(self.vx + RUN_ACC, speed_limit); self.facing = 1
            elif left and not right:
                self.vx = max(self.vx - RUN_ACC, -speed_limit); self.facing = -1
            else:
                self.vx *= 0.8 if self.on_ground else 0.98
                if abs(self.vx) < 0.3:
                    self.vx = 0
        else:
            self.vx = 0
        if not jump and self.vy < SHORT_JUMP_V:
            self.vy = SHORT_JUMP_V
        self.move(lv)
        if self.vy >= 0 and not self.on_ground:
            r = self.rect
            for fx in (r.left + 4, r.right - 5):
                if lv.tile_at(fx, r.bottom) == "H" and lv.tile_at(fx, r.bottom - TILE) != "H" and (r.bottom % TILE) <= self.vy + 1:
                    self.y = r.bottom // TILE * TILE - self.h
                    self.vy = 0
                    self.on_ground = True
                    break
        if self.on_ground and self.jump_buffer:
            self.jumped = self.do_jump()
        self.anim += abs(self.vx) / 40      # un passo ogni 8 fotogrammi a velocita' piena
        self.run_t += abs(self.vx) / RUN_MAX * 0.125   # passo: un fotogramma ogni 8 frame
        if self.attack:
            name, f = self.attack
            f += 1
            limit = {"punch": 14, "kick": 18, "throw": 22 if self.power == "double" else 14, "albedo": 40}[name]
            self.attack = None if f >= limit else (name, f)
        if self.invuln:
            self.invuln -= 1

    def do_jump(self):
        if self.climbing:
            self.climbing = False
            self.on_ground = False
            self.coyote = self.jump_buffer = 0
            self.vy = JUMP_V * 0.7
            return True
        if self.on_ground or self.coyote:
            self.vy = JUMP_V - max(0, abs(self.vx) - RUN_MAX) * 0.7
            self.on_ground = False
            self.coyote = self.jump_buffer = 0
            return True
        self.jump_buffer = JUMP_BUFFER_FRAMES
        return False

    def start_attack(self, name):
        if not self.attack and not self.climbing:
            self.attack = (name, 0)
            return True
        return False

    def sprite_name(self):
        if self.climbing:
            return "climb"
        if self.attack:
            name = self.attack[0]
            if name == "albedo":
                return "hado"
            if not self.on_ground:
                return "air" + name
            return name
        if not self.on_ground:
            return "jump"
        if abs(self.vx) > 0.5:
            return ("run1", "run2")[int(self.anim) % 2]
        return "idle"

    def sheet_frame(self, gfx):
        """Fotogramma dal foglio di sprite, se esiste per la posa corrente."""
        sheets = gfx.sheets
        side = 0 if self.facing > 0 else 1
        if self.climbing:
            return None
        if self.attack:
            name, f = self.attack
            base = {"punch": "punch", "kick": "kick", "throw": "throw", "albedo": "punch"}[name]
            if base == "kick" and not self.on_ground and "flykick" in sheets:
                base = "flykick"
            if base not in sheets:
                return None
            fr = sheets[base][side]
            if name == "albedo":
                return fr[(f // 2) % len(fr)]
            limit = {"punch": 14, "kick": 18, "throw": 22 if self.power == "double" else 14}[name]
            return fr[min(len(fr) - 1, f * len(fr) // limit)]
        if not self.on_ground:
            if "jump" not in sheets:
                return None
            fr = sheets["jump"][side]
            n = len(fr)
            if self.vy < 0:
                i = min(n // 2 - 1, int((self.vy - JUMP_V) / -JUMP_V * (n // 2)))
            else:
                i = n // 2 + min(n // 2 - 1, int(self.vy / 14 * (n // 2)))
            return fr[max(0, i)]
        if abs(self.vx) > 0.5 and "run" in sheets:
            fr = sheets["run"][side]
            return fr[int(self.run_t) % len(fr)]
        return None

    def draw(self, s, gfx, cam):
        if self.invuln and (self.invuln // 3) % 2 and not (self.attack and self.attack[0] == "albedo"):
            return
        if self.mounted:
            img = gfx.player["jump"][0 if self.facing > 0 else 1]
            img = pygame.transform.smoothscale(img, (int(img.get_width()*0.8), int(img.get_height()*0.8)))
            s.blit(img, (self.rect.centerx - img.get_width()//2 - cam, self.rect.bottom - 40 - img.get_height()))
            return
        img = self.sheet_frame(gfx)
        if img is not None:
            self.draw_img(s, img, cam)
            if self.attack and self.attack[0] == "albedo":
                t = self.attack[1]
                pygame.draw.circle(s, (255, 220, 100), (self.rect.centerx - cam, self.rect.centery), 60 + t * 6, 6)
            return
        name = self.sprite_name()
        frames = gfx.player
        img = frames[name][0 if self.facing > 0 else 1]
        if name in frames["_fallback"]:
            # animazione di ripiego: inclina e fa "camminare" la posa ferma
            step = int(self.anim) % 2
            if name in ("run1", "run2"):
                ang, dy = (-9 if step else 9) * self.facing, -8 if step else 0
            elif name in ("punch", "throw", "airpunch", "airthrow", "hado"):
                ang, dy = -14 * self.facing, 0
            elif name in ("kick", "airkick"):
                ang, dy = 12 * self.facing, -6
            elif name == "jump":
                ang, dy = 8 * self.facing, 0
            else:
                ang, dy = 0, 0
            if ang:
                img = pygame.transform.rotate(img, ang)
            r = self.rect
            s.blit(img, (r.centerx - img.get_width() // 2 - cam, r.bottom - img.get_height() + dy))
            return
        self.draw_img(s, img, cam)
        if self.attack and self.attack[0] == "albedo":
            t = self.attack[1]
            rad = 60 + t * 6
            pygame.draw.circle(s, (255, 220, 100), (self.rect.centerx - cam, self.rect.centery), rad, 6)


class Zombie(Entity):
    def __init__(self, x, cfg):
        super().__init__(x, GROUND * TILE - Entity.h)
        self.rise = 0
        self.age = 0
        self.hp = 10
        self.speed = cfg["zombie_speed"]
        self.frozen = 0

    def update(self, lv, player):
        self.age += 1
        if self.frozen:
            self.frozen -= 1
            return
        if self.rise < 40:
            self.rise += 1
            return
        if self.age > 10 * FPS:
            self.rise -= 1
            if self.rise <= 0:
                self.alive = False
            return
        self.facing = 1 if player.x > self.x else -1
        r = self.rect
        ahead = r.right + 2 if self.facing > 0 else r.left - 3
        if lv.solid(ahead, r.bottom + 2) and not lv.solid(ahead, r.centery):
            self.vx = self.speed * self.facing
        else:
            self.vx = 0
        self.move(lv)

    def draw(self, s, gfx, cam):
        h = int(gfx.zombie[0].get_height() * min(1, self.rise / 40))
        if h <= 0:
            return
        img = gfx.zombie[(self.age // 12) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        y = GROUND * TILE - h
        s.blit(img, (self.rect.centerx - img.get_width() // 2 - cam, y), (0, 0, img.get_width(), h))
        if self.frozen:
            pygame.draw.rect(s, (150, 220, 255), (int(self.x) - cam, self.y, self.w, self.h), 4)
        pygame.draw.ellipse(s, (60, 40, 30), (int(self.x) - 30 - cam, GROUND * TILE - 8, self.w + 60, 16))


class Skeleton(Entity):
    def __init__(self, c, r):
        super().__init__(c * TILE + 5, (r + 1) * TILE - Entity.h)
        self.hp = 20
        self.t = random.randrange(90)
        self.facing = -1
        self.frozen = 0
        self.hit_t = 0

    def attack_box(self):
        if 0 < self.hit_t <= 12:
            r = self.rect
            return pygame.Rect(r.right if self.facing > 0 else r.left - 60, r.top + 40, 60, 40)
        return None

    def update(self, lv, player):
        self.t += 1
        if self.frozen:
            self.frozen -= 1
            return
        if self.hit_t:
            self.hit_t -= 1
            self.vx = 0
            self.move(lv)
            return
        dist = player.x - self.x
        if abs(dist) < 700:
            self.facing = 1 if dist > 0 else -1
        if abs(dist) < 90 and abs(player.y - self.y) < 100:
            self.hit_t = 24
        r = self.rect
        ahead = r.right + 2 if self.facing > 0 else r.left - 3
        if lv.solid(ahead, r.bottom + 2) and not lv.solid(ahead, r.centery):
            self.vx = 2.6 * self.facing
        else:
            self.vx = 0
            if abs(dist) >= 700:
                self.facing = -self.facing
        self.move(lv)

    def draw(self, s, gfx, cam):
        img = gfx.skeleton[(self.t // 10) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        self.draw_img(s, img, cam)
        if self.frozen:
            pygame.draw.rect(s, (150, 220, 255), (int(self.x) - cam, self.y, self.w, self.h), 4)


class Crow(Entity):
    w, h = 100, 50
    ox, oy = 14, 7

    def __init__(self, c, r):
        super().__init__(c * TILE, r * TILE)
        self.home = (self.x, self.y)
        self.hp = 5
        self.t = 0
        self.state = "wait"
        self.frozen = 0

    def update(self, lv, player):
        self.t += 1
        if self.frozen:
            self.frozen -= 1
            return
        dx = player.x - self.x
        if self.state == "wait":
            if abs(dx) < 800:
                self.state = "dive"
                self.facing = 1 if dx > 0 else -1
                self.t = 0
        elif self.state == "dive":
            ty = player.y + 30
            self.x += 6 * self.facing
            self.y += (ty - self.y) * 0.04 + math.sin(self.t / 6) * 3
            if self.t > 110:
                self.state = "away"; self.t = 0
        else:
            self.x += 7 * self.facing
            self.y -= 4
            if self.t > 120:
                self.state = "wait"
                self.x, self.y = self.home
                self.t = 0

    def draw(self, s, gfx, cam):
        img = gfx.crow[(self.t // (15 if self.state == "wait" else 5)) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        self.draw_img(s, img, cam)


class Bianca:
    """Compagna di NightKnight: osserva e segue, senza combattere all'inizio."""
    def __init__(self, player):
        self.x = player.x - 150
        self.y = player.y - 110
        self.facing = 1
        self.t = 0

    def update(self, player):
        self.t += 1
        # Resta poco dietro e sopra al protagonista; il ritardo rende il volo vivo.
        offset = -155 if player.facing > 0 else 155
        tx, ty = player.rect.centerx + offset, player.y - 105
        self.x += (tx - self.x) * 0.045
        self.y += (ty - self.y) * 0.055
        if abs(player.vx) > 0.5:
            self.facing = player.facing

    def draw(self, screen, gfx, cam):
        img = gfx.bianca[(self.t // 8) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        bob = int(math.sin(self.t / 11) * 7)
        screen.blit(img, (int(self.x) - img.get_width() // 2 - cam,
                          int(self.y) - img.get_height() // 2 + bob))


class Ghost(Entity):
    w, h = 80, 110
    ox, oy = 24, 18

    def __init__(self, c, r):
        super().__init__(c * TILE, r * TILE)
        self.hp = 15
        self.t = random.randrange(200)
        self.frozen = 0
        self.vis = 1.0        # 0 = invisibile e intoccabile

    def visible(self):
        return self.vis > 0.5

    def update(self, lv, player):
        self.t += 1
        if self.frozen:
            self.frozen -= 1
            return
        cyc = self.t % 240
        self.vis = min(1.0, cyc / 40) if cyc < 150 else max(0.0, 1 - (cyc - 150) / 40)
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - 40 - self.rect.centery
        if abs(dx) < 1000:
            self.facing = 1 if dx > 0 else -1
            sp = 2.2 if self.visible() else 1.0
            self.x += max(-sp, min(sp, dx * 0.02))
            self.y += max(-2, min(2, dy * 0.02)) + math.sin(self.t / 10) * 1.5
        self.y = max(TILE, min(self.y, GROUND * TILE - self.h))

    def draw(self, s, gfx, cam):
        if self.vis <= 0.02:
            return
        img = gfx.ghost[(self.t // 12) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        if self.vis < 1:
            img = img.copy()
            img.set_alpha(int(255 * self.vis))
        self.draw_img(s, img, cam)
        if self.frozen:
            pygame.draw.rect(s, (150, 220, 255), (int(self.x) - cam, self.y, self.w, self.h), 4)


class Effect:
    def __init__(self, x, y, text, color):
        self.x, self.y, self.text, self.color, self.t = x, y, text, color, 0
        self.alive = True

    def update(self):
        self.t += 1
        self.y -= 1.5
        self.alive = self.t < 50


# ---------------------------------------------------------------- gioco
class Game:
    def __init__(self, windowed=False, save_path=progress.DEFAULT_PATH):
        pygame.init()
        flags = 0 if windowed else pygame.FULLSCREEN | pygame.SCALED
        self.screen = pygame.display.set_mode((W, H), flags)
        pygame.display.set_caption("NightKnight")
        self.clock = pygame.time.Clock()
        self.gfx = Gfx()
        self.jb = music.Jukebox()
        self.frame = 0
        self.save_path = save_path
        self.saved = progress.load(save_path)
        self.hi = self.saved["high_score"]
        self.save_error = None
        self.running = True
        self.paused = False
        self.menu_index = 0
        self.state = "title"
        self.score = 0
        self.ci = 0
        self.cfg = levels.cfg(0)
        self.powers = []
        self.weapon_i = 0
        self.player = Player(0, 0)
        self.msg = None
        self.effects = []
        self.rounds = [0, 0]
        self.hud_shade = pygame.Surface((W, 200), pygame.SRCALPHA)
        for y in range(200):
            alpha = int(170 * (1 - y / 200) ** 1.4)
            pygame.draw.line(self.hud_shade, (0, 0, 0, alpha), (0, y), (W, y))

    # ---- flusso
    def save_progress(self, checkpoint=False, clear=False, next_cemetery=False):
        self.hi = max(self.hi, self.score)
        self.saved["high_score"] = self.hi
        if clear:
            self.saved["checkpoint"] = None
        elif checkpoint:
            self.saved["checkpoint"] = {
                "cemetery": self.ci + 1 if next_cemetery else self.ci,
                "part": "surface" if next_cemetery else self.part, "lives": self.lives,
                "score": self.score, "powers": list(self.powers),
            }
        self.save_error = progress.save(self.saved, self.save_path)

    def continue_game(self):
        cp = self.saved["checkpoint"]
        if cp:
            self.ci, self.lives = cp["cemetery"], cp["lives"]
            self.score, self.powers = cp["score"], list(cp["powers"])
            self.start_part(cp["part"])

    def set_paused(self, paused):
        self.paused = paused
        self.menu_index = 0
        if pygame.mixer.get_init():
            (pygame.mixer.pause if paused else pygame.mixer.unpause)()

    def menu_items(self):
        if self.paused:
            return ["RIPRENDI", "TORNA AL TITOLO", "ESCI"]
        return (["CONTINUA"] if self.saved["checkpoint"] else []) + ["NUOVA PARTITA", "PROVE ATLETICHE", "ESCI"]

    def menu_key(self, k):
        items = self.menu_items()
        if k in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % len(items)
        elif k in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % len(items)
        elif k == pygame.K_RETURN:
            action = items[self.menu_index]
            if action == "RIPRENDI":
                self.set_paused(False)
            elif action == "TORNA AL TITOLO":
                self.save_progress()
                self.set_paused(False)
                self.jb.stop()
                self.state = "title"
            elif action == "CONTINUA":
                self.continue_game()
            elif action == "NUOVA PARTITA":
                self.state = "weapon_select"
                self.weapon_i = 0
            elif action == "PROVE ATLETICHE":
                self.state = "weapon_select"
                self.weapon_i = 0
                self.weapon_part = "trials"
            elif action == "ESCI":
                self.running = False

    def new_game(self, ci=0, part="surface"):
        if ci == 0:
            self.score = 0
            self.powers = []
        self.lives = 3
        self.ci = ci
        self.weapon_part = part
        self.start_part(part)

    def start_part(self, part):
        c = levels.cfg(self.ci)
        self.cfg = c
        self.part = part
        g = {"surface": levels.gen_surface, "crypt": levels.gen_crypt, "trials": levels.gen_trials, "arena": levels.gen_arena}[part](c)
        self.lv = Level(g, part)
        self.rounds = [0, 0]
        self.spawn()
        self.state = "card"
        self.card_t = 150
        self.jb.play({"surface": "surface", "crypt": "crypt", "trials": "surface", "arena": "arena"}[part])
        self.save_progress(checkpoint=True)

    def spawn(self):
        lv = self.lv
        floor = 15 if self.part == "crypt" else GROUND
        self.player = p = Player(2 * TILE, floor * TILE - Entity.h)
        p.on_ground = True
        p.power = self.powers[-1] if self.powers else None
        p.weapon = levels.weapon_cfg(self.weapon_i)
        p.gravity_scale = self.cfg["gravity_scale"]
        self.bianca = Bianca(p) if self.ci < 4 else None
        self.geysers, self.spenti = [], []
        self.geyser_hint = False
        self.zombies, self.skels, self.crows, self.ghosts, self.balls = [], [], [], [], []
        for ch, c, r in lv.markers:
            if ch == "q":
                self.geysers.append(titan.Geyser((c + .5) * TILE, (r + 1) * TILE))
            elif ch == "u":
                self.spenti.append(titan.Spento((c + .5) * TILE, (r + 1) * TILE))
            elif ch == "k":
                self.skels.append(Skeleton(c, r))
            elif ch == "v":
                self.crows.append(Crow(c, r))
            elif ch == "g" and assets.has("ghost_1"):
                self.ghosts.append(Ghost(c, r))
        self.spawn_t = 60
        self.cam = 0
        self.boss = None
        self.msg = None
        self.effects = []
        self.intro = 0
        self.trials = athletics.Trials() if self.part == "trials" else None
        if self.part == "arena":
            self.start_round()

    def start_round(self):
        self.player = Player(3 * TILE, GROUND * TILE - Entity.h)
        self.player.on_ground = True
        self.player.power = self.powers[-1] if self.powers else None
        self.player.weapon = levels.weapon_cfg(self.weapon_i)
        self.player.gravity_scale = self.cfg["gravity_scale"]
        self.effects = []
        self.boss = knights.GoldKnight(W - 5 * TILE, knights.knight_cfg(self.ci), self.gfx)
        self.balls = []
        self.intro = 150
        self.round_no = self.rounds[0] + self.rounds[1] + 1
        self.msg = (f"ROUND {self.round_no}", 90, (250, 210, 60))
        self.ko_wait = 0

    def next_part(self):
        if self.state == "victory":
            return
        # Un'unica ambientazione per satellite: dalla superficie si passa alle prove.
        # La cripta resta nel codice per i satelliti dove si vive sotto (Europa).
        if self.part in ("surface", "crypt"):
            self.start_part("trials")
        elif self.part == "trials":
            if not self.trials.complete:
                return
            self.score += max(500, 5000 - self.trials.elapsed // 6)
            self.start_part("arena")
        else:
            self.powers.append(self.cfg["power"])
            self.state = "victory"
            self.card_t = 260
            self.jb.play("victory")
            self.save_progress(checkpoint=True, next_cemetery=True, clear=self.ci == 11)

    def after_victory(self):
        self.ci += 1
        if self.ci >= 12:
            self.state = "end"
            self.hi = max(self.hi, self.score)
            self.jb.stop()
            self.save_progress(clear=True)
        else:
            self.start_part("surface")

    # ---- danni
    def hurt_player(self, dmg, from_x):
        p = self.player
        if (p.invuln or self.state != "play" or (p.attack and p.attack[0] == "albedo")
                or (self.boss and self.boss.hp <= 0)):
            return
        p.invuln = 80
        p.vy = -9
        p.vx = 6 if p.x > from_x else -6
        p.attack = None
        p.climbing = False
        p.coyote = p.jump_buffer = 0
        self.jb.fx("hurt")
        # NightKnight non perde mai l'armatura: un colpo toglie solo vita.
        p.hp = max(0, p.hp - dmg)
        if p.hp == 0:
            self.die()

    def die(self):
        self.state, self.state_t = "dead", 0
        self.jb.fx("ko")

    def hit_enemy(self, e, dmg, power=None, pts=100):
        if not e.alive:
            return
        # Le specie si sono evolute per la loro atmosfera: l'arma affine le
        # ferisce davvero, le altre incidono appena la corazza o l'ectoplasma.
        weapon = self.player.weapon
        multiplier = weapon["damage"] if weapon["affinity"] == self.cfg["affinity"] else 0.35
        e.hp -= max(1, int(dmg * multiplier))
        self.player.albedo = min(100, self.player.albedo + 6)
        self.jb.fx("flesh_hit" if isinstance(e, Zombie) else "hit")
        if power == "ice":
            e.frozen = 90
        if e.hp <= 0:
            e.alive = False
            self.score += pts

    # ---- aggiornamento
    def update(self):
        if self.paused:
            return
        self.frame += 1
        if self.state == "card":
            self.card_t -= 1
            if self.card_t <= 0:
                self.state = "play"
            return
        if self.state == "victory":
            self.card_t -= 1
            if self.card_t <= 0:
                self.after_victory()
            return
        if self.state == "dead":
            self.state_t += 1
            if self.state_t > 110:
                if self.part == "arena":
                    self.rounds[1] += 1
                    if self.rounds[1] >= 2:
                        self.lose_life()
                    else:
                        self.start_round()
                        self.state = "play"
                else:
                    self.lose_life()
            return
        if self.state != "play":
            return
        p = self.player
        if self.msg:
            t, n, col = self.msg
            self.msg = (t, n - 1, col) if n > 1 else None
        if self.part == "arena" and self.intro:
            self.intro -= 1
            if self.intro == 70:
                self.msg = ("FIGHT!", 60, (230, 40, 40))
            if self.intro > 70:
                return
        keys = pygame.key.get_pressed()
        if self.trials:
            self.trials.update_player(p, keys, self.lv)
        else:
            p.update(keys, self.lv)
        if self.bianca:
            self.bianca.update(p)
        if p.jumped:
            self.jb.fx("jump")
        for e in self.effects:
            e.update()
        self.effects = [e for e in self.effects if e.alive]
        target = p.rect.centerx - W // 2
        self.cam = int(max(0, min(target, self.lv.w - W)))
        if p.y > H + 50:
            self.die(); return
        r = p.rect
        for geyser in self.geysers:
            if abs(p.rect.centerx - geyser.x) < 550 and not self.geyser_hint:
                self.msg = ("ATTENDI IL GETTO", 180, (239, 201, 143))
                self.geyser_hint = True
            if geyser.update(p):
                self.hurt_player(25, geyser.x)
            if self.state != "play":
                return
        for spento in self.spenti:
            if spento.update(p):
                p.albedo = min(100, p.albedo + 20)
                self.jb.fx("pickup")
                self.effects.append(Effect(spento.x, spento.floor - 190, "LUCE LIBERATA", (255, 201, 120)))
        # punte
        if any(self.lv.tile_at(x, r.bottom - 6) == "^" or
               (p.on_ground and self.lv.tile_at(x, r.bottom + 2) == "^")
               for x in (r.left + 4, r.centerx, r.right - 5)):
            self.hurt_player(30, p.x - 10)
        if self.state != "play":
            return
        # uscita
        ec, er = self.lv.exit
        door = pygame.Rect(ec * TILE, (er - 1) * TILE, TILE, TILE * 2)
        if self.part != "arena" and r.colliderect(door):
            if self.trials and not self.trials.complete:
                self.msg = (f"PROVE {len(self.trials.done)} / 5", 60, (222, 201, 150))
            else:
                self.jb.fx("pickup")
                self.next_part()
                return
        # zombie
        if self.part == "surface" and self.ci != 0:
            self.spawn_t -= 1
            if self.spawn_t <= 0 and len(self.zombies) < 4 + self.ci // 3:
                self.spawn_t = self.cfg["zombie_every"]
                for _ in range(12):
                    x = p.x + random.choice((-1, 1)) * random.randrange(400, 900)
                    c = int(x // TILE)
                    if self.cam < x < self.cam + W - PW and self.lv.at(c, GROUND) == "#" and self.lv.at(c, GROUND - 1) == "." and self.lv.at(c + 1, GROUND) == "#" and c < self.lv.cols - 8:
                        self.zombies.append(Zombie(x, self.cfg))
                        break
        for z in self.zombies:
            z.update(self.lv, p)
        for k in self.skels:
            k.update(self.lv, p)
        for cr in self.crows:
            cr.update(self.lv, p)
        for gh in self.ghosts:
            gh.update(self.lv, p)
        for b in self.balls:
            b.update(self.lv, self.cam)
        # lancio della lancia / hadouken / albedo
        # colpi del giocatore sui nemici
        enemies = [(z, 100) for z in self.zombies if z.rise >= 20] + [(k, 300) for k in self.skels] + [(c, 150) for c in self.crows] + [(gh, 400) for gh in self.ghosts if gh.visible()]
        for e, pts in enemies:
            if not e.alive:
                continue
            abox, adm = p.attack_box()
            er = e.rect
            if abox and abox.colliderect(er):
                self.hit_enemy(e, adm * 2, p.power if p.attack[0] == "throw" else None, pts)
                if not (p.attack and p.attack[0] == "albedo"):
                    continue
            if not e.alive:
                continue
            if p.hurtbox().colliderect(er):
                if isinstance(e, Crow):
                    # il corvo disturba: spinge, fa sbagliare il colpo, ma non toglie vita
                    if not p.invuln:
                        p.vx = 3 * e.facing
                        p.attack = None
                        p.invuln = 20
                        p.albedo = max(0, p.albedo - 2)
                elif p.vy > 0 and r.bottom - er.top < 40 and not isinstance(e, Ghost):
                    self.hit_enemy(e, 10, pts=pts)
                    p.vy = -14
                    self.jb.fx("jump")
                elif not getattr(e, "frozen", 0):
                    self.hurt_player(25, e.x)
            sb = e.attack_box() if isinstance(e, Skeleton) else None
            if sb and sb.colliderect(p.hurtbox()):
                self.hurt_player(30, e.x)
            if self.state != "play":
                return
        for b in self.balls:
            if b.owner == "player" and b.alive:
                for e, pts in enemies:
                    if e.alive and b.rect.colliderect(e.rect):
                        self.hit_enemy(e, b.dmg, pts=pts)
                        b.alive = False
                        break
                if self.boss and b.alive and b.rect.colliderect(self.boss.rect):
                    if self.boss.hit(b.dmg):
                        self.score += 50
                        p.albedo = min(100, p.albedo + 8)
                        self.jb.fx("hit")
                    b.alive = False
            if b.owner == "boss" and b.alive and b.rect.colliderect(p.hurtbox()):
                b.alive = False
                self.hurt_player(b.dmg, b.x)
                if self.state != "play":
                    return
        # boss
        bs = self.boss
        if bs:
            if bs.hp <= 0:
                self.ko_wait += 1
                if self.ko_wait == 1:
                    self.balls = []
                    self.msg = ("K.O.", 120, (250, 210, 60))
                    self.jb.fx("ko")
                    self.score += 5000 * self.cfg["num"]
                    self.rounds[0] += 1
                bs.update(self.lv, p, self.balls.append)
                if self.ko_wait > 130:
                    if self.rounds[0] >= 2:
                        self.next_part()
                    else:
                        self.start_round()
                    return
            else:
                bs.update(self.lv, p, self.balls.append)
                br = bs.rect
                abox, adm = p.attack_box()
                if abox and abox.colliderect(br) and bs.hit(adm, p.power if p.attack[0] == "throw" else None):
                    self.score += 50; p.albedo = min(100, p.albedo + 8); self.jb.fx("hit")
                if not bs.hidden and p.hurtbox().colliderect(br):
                    if p.vy > 0 and r.bottom - br.top < 50:
                        p.vy = -14
                        if bs.hit(8):
                            self.score += 50; p.albedo = min(100, p.albedo + 6)
                    else:
                        push = 1 if p.x < bs.x else -1
                        p.x -= push * 5
                        bs.x += push * 2
                bb = bs.attack_box()
                if bb and bb.colliderect(p.hurtbox()):
                    self.hurt_player(bs.move_dmg(), bs.x)
        self.zombies = [z for z in self.zombies if z.alive]
        self.skels = [k for k in self.skels if k.alive]
        self.crows = [c for c in self.crows if c.alive]
        self.ghosts = [gh for gh in self.ghosts if gh.alive]
        if self.trials:
            points = self.trials.check_targets(self.balls)
            if points:
                self.score += points
                self.jb.fx("hit")
        self.balls = [b for b in self.balls if b.alive]

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state = "gameover"
            self.hi = max(self.hi, self.score)
            self.jb.stop()
            self.save_progress(clear=True)
        else:
            self.rounds = [0, 0]
            self.spawn()
            self.state = "play"
            self.save_progress(checkpoint=True)

    # ---- tasti
    def key(self, k):
        p = self.player
        if k == pygame.K_m:
            self.jb.toggle_mute()
            return
        if k in (pygame.K_ESCAPE, pygame.K_p):
            if self.state not in ("title", "end", "gameover"):
                self.set_paused(not self.paused)
            elif k == pygame.K_ESCAPE:
                if self.state == "title":
                    self.running = False
                else:
                    self.state = "title"
                    self.menu_index = 0
            return
        if self.paused:
            self.menu_key(k)
            return
        if self.state == "title":
            self.menu_key(k)
            return
        if self.state == "weapon_select":
            if k in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                self.weapon_i = (self.weapon_i - 1) % len(levels.WEAPONS)
            elif k in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                self.weapon_i = (self.weapon_i + 1) % len(levels.WEAPONS)
            elif k == pygame.K_RETURN:
                self.new_game(part=getattr(self, "weapon_part", "surface"))
            elif k == pygame.K_ESCAPE:
                self.state = "title"
            return
        if self.state in ("gameover", "end"):
            if k == pygame.K_RETURN:
                if self.state == "end":
                    self.state = "title"
                    self.menu_index = 0
                else:
                    self.new_game(self.ci)
            return
        if self.state in ("card", "victory"):
            if k == pygame.K_RETURN:
                self.card_t = 0
            return
        if self.state != "play" or (self.part == "arena" and (self.intro > 70 or self.boss.hp <= 0)):
            return
        if self.trials and k == pygame.K_e:
            self.trials.interact(p, self.lv)
            return
        if self.trials and self.trials.attached:
            if k == pygame.K_SPACE:
                self.trials.release(p)
                self.jb.fx("jump")
            return
        if k in (pygame.K_f, pygame.K_g):
            if p.start_attack("throw" if k == pygame.K_f else "punch"):
                self.balls.append(athletics.WeaponShot("javelin" if k == pygame.K_f else "dagger", p))
                self.jb.fx("throw")
            return
        fwd = (pygame.K_RIGHT, pygame.K_d) if p.facing > 0 else (pygame.K_LEFT, pygame.K_a)
        if k in (pygame.K_DOWN, pygame.K_s):
            p.last_down = self.frame
        elif k in fwd:
            p.last_fwd = self.frame
        if k in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            r = p.rect
            near_ladder = self.lv.tile_at(r.centerx, r.centery) == "H" or self.lv.tile_at(r.centerx, r.top - 4) == "H"
            if k == pygame.K_SPACE or not near_ladder:
                if p.do_jump():
                    self.jb.fx("jump")
        elif k == pygame.K_z:
            p.start_attack("throw")
        elif k == pygame.K_x:
            p.start_attack("punch")
        elif k == pygame.K_c:
            p.start_attack("kick")
        elif k == pygame.K_v:
            if p.albedo >= 100 and p.start_attack("albedo"):
                p.albedo = 0
                p.invuln = 45
                self.jb.fx("albedo")

    # ---- disegno
    def bar(self, x, y, w, frac, color, right=False):
        s = self.screen
        pygame.draw.rect(s, (105, 112, 115), (x - 2, y - 2, w + 4, 18), border_radius=3)
        pygame.draw.rect(s, (15, 19, 22), (x, y, w, 14), border_radius=2)
        fw = int(w * max(0, min(1, frac)))
        if fw:
            left = x + w - fw if right else x
            pygame.draw.rect(s, color, (left, y, fw, 14), border_radius=2)
            highlight = tuple(min(255, int(v * 1.2 + 15)) for v in color)
            pygame.draw.line(s, highlight, (left, y + 2), (left + fw - 1, y + 2))

    def draw_hud(self):
        s, p = self.screen, self.player
        s.blit(self.hud_shade, (0, 0))
        px.draw_text(s, "NIGHTKNIGHT", 40, 22, (229, 229, 220), scale=5)
        px.draw_text(s, f"{self.lives} VITE", 350, 28, (181, 190, 194), scale=3)
        self.bar(40, 66, 400, p.hp / PLAYER_HP, (64, 153, 116) if p.hp > 30 else (183, 65, 67))
        px.draw_text(s, f"{p.hp} / {PLAYER_HP}", 460, 60, (213, 220, 219), scale=3)
        px.draw_text(s, "LUCE", 40, 94, (202, 178, 119), scale=3)
        self.bar(130, 98, 310, p.albedo / 100, (186, 155, 82))
        if p.albedo >= 100:
            px.draw_text(s, "PRONTO", 460, 92, (224, 198, 129), scale=3)
        if p.power:
            px.draw_text(s, levels.ARMOR_NAMES[p.power], 40, 152, (202, 178, 119), scale=3)
        weapon = getattr(p, "weapon", None)
        if weapon:
            label = weapon["name"].upper()
            px.draw_text(s, label, 40, 178, (190, 210, 225), scale=3)
        title = f"SATELLITE {ROMAN[self.ci]} - {self.cfg['name']}"
        px.draw_text(s, title, W // 2 - px.text_width(title, 5) // 2, 24, scale=5)
        sub = {"surface": "SUPERFICIE", "crypt": "SOTTO LA CROSTA", "trials": "LE PROVE", "arena": "IL DUELLO"}[self.part]
        px.draw_text(s, sub, W // 2 - px.text_width(sub, 4) // 2, 60, (200, 200, 220), scale=4)
        sc = f"PUNTI {self.score:08d}"
        px.draw_text(s, sc, W - 40 - px.text_width(sc, 5), 24, (222, 201, 150), scale=5)
        if self.boss:
            name = self.cfg["boss"].upper()
            px.draw_text(s, name, W - 40 - px.text_width(name, 4), 130, scale=4)
            self.bar(W - 440, 66, 400, self.boss.hp / self.boss.max_hp, (172, 66, 77), right=True)
            for i in range(2):
                pygame.draw.circle(s, (222, 201, 150) if i < self.rounds[0] else (65, 70, 76), (580 + i * 28, 73), 7)
                pygame.draw.circle(s, (172, 66, 77) if i < self.rounds[1] else (65, 70, 76), (W - 580 - i * 28, 73), 7)
        if self.msg:
            t, n, col = self.msg
            px.draw_text(s, t, W // 2 - px.text_width(t, 14) // 2, 380, col, scale=14)
        if self.trials:
            self.trials.draw_hud(s)

    def draw_world(self):
        s, cam, lv = self.screen, self.cam, self.lv
        # Un'unica ambientazione: anche il duello si combatte sotto lo stesso cielo.
        if self.part in ("surface", "trials", "arena"):
            # Il cielo non si ripete: e' appena piu' largo dello schermo e scorre
            # pochissimo, cosi' Saturno resta uno solo.
            sky = self.gfx.wide_sky(self.cfg["num"], SKY_PAN)
            off = -min(SKY_PAN, int(cam * SKY_PAN / max(1, lv.cols * TILE - W, W)))
            s.blit(sky, (off, H - sky.get_height()))
            hills = self.gfx.background("hills", self.cfg["num"])
            if self.ci == 0 and self.gfx.titan_hills_near:
                # Titano ha due piani di rocce; ognuno si ripete alternando una
                # copia specchiata, cosi' i bordi combaciano senza cuciture.
                for layer, speed in ((self.gfx.mirrored(hills), 0.16),
                                     (self.gfx.mirrored(self.gfx.titan_hills_near), 0.42)):
                    off = -(int(cam * speed) % layer.get_width())
                    for x in range(off, W, layer.get_width()):
                        s.blit(layer, (x, 0))
            else:
                hw = hills.get_width()
                off = -(int(cam * 0.3) % hw)
                y = H - hills.get_height() - 40 if hw > W else 0
                s.blit(hills, (off, y))
                if off + hw < W:
                    s.blit(hills, (off + hw, y))
        elif self.part == "crypt":
            s.blit(self.gfx.background("crypt_bg", self.cfg["num"]), (0, 0))
        else:
            s.blit(self.gfx.background("arena_bg", self.cfg["num"]), (0, 0))
        c0 = max(0, cam // TILE)
        if self.part in ("surface", "trials"):
            if not hasattr(self, "pit_shade"):
                self.pit_shade = pygame.Surface((TILE, H - GROUND * TILE), pygame.SRCALPHA)
                for yy in range(self.pit_shade.get_height()):
                    a = min(255, 120 + yy * 2)
                    pygame.draw.line(self.pit_shade, (8, 6, 14, a), (0, yy), (TILE, yy))
            for c in range(c0, min(lv.cols, c0 + W // TILE + 3)):
                if lv.g[GROUND][c] == ".":
                    pit = self.gfx.titan_lake if self.ci == 0 else self.pit_shade
                    s.blit(pit, (c * TILE - cam, GROUND * TILE))
            if self.ci == 0:
                haze = pygame.Surface((W, 105), pygame.SRCALPHA)
                for yy in range(haze.get_height()):
                    # sale e scende dolcemente: nessun bordo netto sopra il terreno
                    alpha = int(60 * math.sin(math.pi * yy / haze.get_height()))
                    pygame.draw.line(haze, (184, 91, 31, alpha), (0, yy), (W, yy))
                s.blit(haze, (0, GROUND * TILE - 75))
        for c in range(c0, min(lv.cols, c0 + W // TILE + 3)):
            x = c * TILE - cam
            for r in range(ROWS):
                ch = lv.g[r][c]
                if ch == "." or ch in "kvgqu":
                    continue
                y = r * TILE
                if ch in self.gfx.tiles:
                    tile = self.gfx.titan_tile(ch, c, r) if self.ci == 0 else None
                    s.blit(tile or self.gfx.tiles[ch], (x, y))
                elif ch == "Y" and "Y" in self.gfx.deco:
                    s.blit(self.gfx.deco["Y"], (x - TILE // 2, y - TILE * 2))
                elif ch == "E":
                    s.blit(self.gfx.deco["E"], (x, y - TILE))
                elif ch == "t" and "t2" in self.gfx.deco and c % 2:
                    s.blit(self.gfx.deco["t2"], (x, y))
                elif ch in self.gfx.deco:
                    s.blit(self.gfx.deco[ch], (x, y))

    def draw_center(self, text, y, color=(245, 245, 245), scale=8):
        px.draw_text(self.screen, text, W // 2 - px.text_width(text, scale) // 2, y, color, scale)

    def draw_menu(self, y):
        for i, label in enumerate(self.menu_items()):
            color = (222, 201, 150) if i == self.menu_index else (190, 195, 210)
            self.draw_center(label, y + i * 64, color, 6)
            if i == self.menu_index:
                x = W // 2 - px.text_width(label, 6) // 2 - 36
                cy = y + i * 64 + 14
                pygame.draw.polygon(self.screen, color, [(x, cy - 10), (x + 14, cy), (x, cy + 10)])

    def draw_save_status(self):
        if self.save_error:
            self.draw_center("SALVATAGGIO NON DISPONIBILE", H - 40, (255, 120, 120), 4)

    def draw(self):
        s = self.screen
        if self.state == "title":
            s.blit(self.gfx.background("sky", 1), (0, 0))
            self.draw_center("NIGHTKNIGHT", 230, (222, 201, 150), 16)
            self.draw_center("12 CIMITERI", 420, (200, 200, 220), 8)
            self.draw_center("SAME COURAGE, NEW NIGHTMARES", 500, (150, 160, 190), 4)
            self.draw_center(f"RECORD {self.hi:08d}", 560, (200, 200, 220), 4)
            self.draw_menu(610)
            self.draw_center("FRECCE MUOVI  SPAZIO SALTA  Z AFFONDO DI LANCIA  X PUGNO  C CALCIO", 900, (150, 160, 190), 4)
            self.draw_center("V LUCE: RAFFICA DI PUGNI     SU/GIU SULLE SCALE", 940, (150, 160, 190), 4)
            img = self.gfx.player["idle"][0]
            hero = pygame.transform.smoothscale(img, (img.get_width() * 2, img.get_height() * 2))
            s.blit(hero, (260 - hero.get_width() // 2, 880 - hero.get_height()))
            self.draw_save_status()
            pygame.display.flip()
            return
        if self.state == "weapon_select":
            s.blit(self.gfx.background("sky", 1), (0, 0))
            weapon = levels.weapon_cfg(self.weapon_i)
            titan = levels.cfg(0)
            self.draw_center("SCEGLI LA TUA ARMA", 175, (250, 210, 60), 10)
            self.draw_center(f"{self.weapon_i + 1:02d} / 12", 315, (190, 200, 220), 5)
            self.draw_center(weapon["name"].upper(), 400, (225, 235, 245), 9)
            self.draw_center(weapon["description"].upper(), 505, (180, 195, 215), 4)
            self.draw_center("PRIMO APPRODO: TITANO", 620, titan["color"], 5)
            self.draw_center(f"GRAVITA {titan['gravity'].upper()}  |  ARIA {titan['air'].upper()}", 680, (210, 200, 185), 3)
            self.draw_center(f"CLIMA: {titan['climate'].upper()}", 720, (210, 200, 185), 3)
            self.draw_center(f"FAUNA: {titan['enemies'][0].upper()} E {titan['enemies'][1].upper()}", 760, (210, 200, 185), 3)
            good = weapon["affinity"] == titan["affinity"]
            verdict = "ARMA ADATTA A TITANO" if good else "NON ADATTA: I NEMICI RESISTERANNO"
            self.draw_center(verdict, 800, (120, 235, 170) if good else (245, 125, 105), 4)
            self.draw_center("FRECCE SCEGLI   INVIO PARTE   ESC INDIETRO", 920, (150, 160, 190), 4)
            pygame.display.flip()
            return
        if self.state == "end":
            s.blit(self.gfx.background("sky", 12), (0, 0))
            self.draw_center("HAI LIBERATO I 12 CIMITERI", 300, (250, 210, 60), 10)
            self.draw_center(f"PUNTI {self.score}", 480, scale=8)
            self.draw_center("SOME HEROES NEVER DIE", 620, (150, 160, 190), 5)
            self.draw_center("PREMI INVIO", 800, scale=5)
            pygame.display.flip()
            return
        self.draw_world()
        cam = self.cam
        for spento in self.spenti:
            spento.draw(s, cam, self.gfx.spento_sleeping, self.gfx.spento_awake)
        for geyser in self.geysers:
            geyser.draw(s, cam)
        if self.trials:
            self.trials.draw(s, self.gfx, self.player, cam)
        if self.bianca:
            self.bianca.draw(s, self.gfx, cam)
        for z in self.zombies:
            z.draw(s, self.gfx, cam)
        for k in self.skels:
            k.draw(s, self.gfx, cam)
        for cr in self.crows:
            cr.draw(s, self.gfx, cam)
        for gh in self.ghosts:
            gh.draw(s, self.gfx, cam)
        if self.boss:
            self.boss.draw(s, cam)
        for b in self.balls:
            b.draw(s, self.gfx, cam)
        p = self.player
        if self.state == "dead":
            s.blit(self.gfx.bones, (int(p.x) - p.ox - cam, min(int(p.y) + 100, GROUND * TILE - 36)))
        else:
            p.draw(s, self.gfx, cam)
        for e in self.effects:
            px.draw_text(s, e.text, int(e.x) - cam, int(e.y), e.color, 4)
        self.draw_hud()
        if self.state == "card":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 170)); s.blit(ov, (0, 0))
            self.draw_center(f"SATELLITE {ROMAN[self.ci]}", 300, (250, 210, 60), 14)
            self.draw_center(self.cfg["name"].upper(), 440, scale=10)
            sub = {"surface": "SUPERFICIE", "crypt": "SOTTO LA CROSTA", "trials": "LE PROVE", "arena": "IL DUELLO"}[self.part]
            self.draw_center(sub, 560, (200, 200, 220), 8)
            self.draw_center(f"GUARDIANO: {self.cfg['boss'].upper()}", 680, self.cfg["color"], 5)
            self.draw_center(f"GRAVITA {self.cfg['gravity'].upper()}  |  ARIA {self.cfg['air'].upper()}", 755, (210, 210, 220), 3)
            self.draw_center(f"CLIMA: {self.cfg['climate'].upper()}", 790, (210, 210, 220), 3)
            self.draw_center(f"FAUNA: {self.cfg['enemies'][0].upper()} / {self.cfg['enemies'][1].upper()}", 825, (210, 210, 220), 3)
        elif self.state == "victory":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 190)); s.blit(ov, (0, 0))
            self.draw_center("VITTORIA", 260, (250, 210, 60), 14)
            self.draw_center(f"{self.cfg['boss'].upper()} E' CADUTO", 460, self.cfg["color"], 7)
            self.draw_center("PREMI INVIO", 820, (150, 160, 190), 5)
        elif self.state == "gameover":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 170)); s.blit(ov, (0, 0))
            self.draw_center("GAME OVER", 380, (230, 40, 40), 16)
            self.draw_center(f"INVIO: RIPROVA IL SATELLITE {ROMAN[self.ci]}", 600, scale=6)
        if self.paused:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 195))
            s.blit(ov, (0, 0))
            self.draw_center("PAUSA", 300, (250, 210, 60), 14)
            self.draw_menu(520)
        self.draw_save_status()
        pygame.display.flip()

    def run(self):
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.WINDOWFOCUSLOST and self.state not in ("title", "end", "gameover"):
                    self.set_paused(True)
                if e.type == pygame.KEYDOWN:
                    self.key(e.key)
            if not self.running:
                break
            self.update()
            self.draw()
            self.clock.tick(FPS)
        self.save_progress()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--windowed", action="store_true", help="Avvia in finestra")
    args = parser.parse_args()
    try:
        Game(windowed=args.windowed).run()
    finally:
        pygame.quit()
