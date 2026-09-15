#!/usr/bin/env python3
"""Goblin - 12 cimiteri. Sopra, sottoterra, duello col Cavaliere. Linux 1920x1080."""
import math
import random
import sys

import pygame

import assets
import knights
import levels
import music
import pixelart as px

W, H = 1920, 1080
FPS = 60
TILE = 64
ROWS = 17
GROUND = levels.GROUND
GRAVITY = 0.75
MAX_FALL = 18
RUN_ACC = 0.25
RUN_MAX = 3.2
JUMP_V = -20.0
CLIMB = 5
PLAYER_HP = 100
SOLID = set("#D=S")
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

PS = 8          # scala pixel art personaggi
PW, PH = 16 * PS, 24 * PS


# ---------------------------------------------------------------- grafica
def player_images(armor):
    out = {}
    remap = None if armor else px.UNDERWEAR
    pre = "arthur_" if armor else "arthur_nude_"
    for name, (torso, legs) in px.PLAYER_FRAMES.items():
        rows = px.HEAD + px.TORSO[torso] + px.LEGS[legs]
        file = {"run1": "run1", "run2": "run2", "jump": "jump", "punch": "punch", "kick": "kick",
                "throw": "throw", "hado": "special", "airpunch": "punch", "airkick": "kick",
                "airthrow": "throw", "climb": "climb", "idle": "idle"}[name]
        chain = [pre + file, pre + "idle", pre + "run1"]
        if not armor:
            chain += ["arthur_" + file, "arthur_idle", "arthur_run1"]
        fname = next((n for n in chain if assets.has(n)), pre + file)
        img = assets.load(fname, PW, PH, assets.pix(rows, remap, PS), by_height=True)
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
        self.player = {True: player_images(True), False: player_images(False)}
        self.sheets = {}
        for armor, pre in ((True, "arthur_"), (False, "arthur_nude_")):
            d = {}
            for pose, file in (("run", "run_sheet"), ("punch", "punch_sheet"), ("kick", "kick_sheet"),
                               ("jump", "jump_sheet"), ("throw", "spear_lunge_sheet")):
                fr = assets.sheet(pre + file, PH)
                if fr:
                    d[pose] = (fr, [assets.flip(f) for f in fr])
            self.sheets[armor] = d
        self.bones = px.sprite(px.BONES, scale=PS)
        self.zombie = [assets.load(f"zombie_walk{i + 1}", PW, PH, assets.pix(px.ZOMBIE[i], scale=PS), by_height=True) for i in range(2)]
        self.skeleton = [assets.load(f"skeleton_walk{i + 1}", PW, PH, assets.pix(px.ZOMBIE[i], px.SKELETON_MAP, PS), by_height=True) for i in range(2)]
        self.crow = [assets.load(f"crow_{i + 1}", 16 * PS, 8 * PS, assets.pix(px.CROW[i], scale=PS)) for i in range(2)]
        self.ghost = [assets.load(f"ghost_{i + 1}", 16 * PS, 16 * PS, assets.pix(px.GHOST[i], scale=PS), by_height=True) for i in range(2)]
        self.boss_cache = {}
        self.bg_cache = {}

    def knight(self, num, color):
        if num not in self.boss_cache:
            self.boss_cache[num] = knights.knight_images(self, num, color)
        return self.boss_cache[num]

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
                if g[r][c] in "kvgE":
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
            self.vy = min(self.vy + GRAVITY, MAX_FALL)
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
        self.armor = True
        self.hp = PLAYER_HP
        self.cosmo = 0
        self.invuln = 0
        self.anim = 0.0
        self.run_t = 0.0
        self.attack = None
        self.climbing = False
        self.last_down = -999
        self.last_fwd = -999
        self.power = None

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
        if name == "cosmo" and 4 <= f <= 38 and f % 5 == 0:
            return pygame.Rect(r.right if self.facing > 0 else r.left - 170, r.top + 30, 170, 130), 12
        return None, 0

    def update(self, keys, lv):
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up = keys[pygame.K_UP] or keys[pygame.K_w]
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        jump = keys[pygame.K_SPACE] or up
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
        if self.attack and self.attack[0] == "cosmo":
            self.vx = 4 * self.facing
        elif not grounded_attack:
            if right and not left:
                self.vx = min(self.vx + RUN_ACC, RUN_MAX); self.facing = 1
            elif left and not right:
                self.vx = max(self.vx - RUN_ACC, -RUN_MAX); self.facing = -1
            else:
                self.vx *= 0.8 if self.on_ground else 0.98
                if abs(self.vx) < 0.3:
                    self.vx = 0
        else:
            self.vx = 0
        if not jump and self.vy < -8:
            self.vy = -8
        self.move(lv)
        if self.vy >= 0 and not self.on_ground:
            r = self.rect
            for fx in (r.left + 4, r.right - 5):
                if lv.tile_at(fx, r.bottom) == "H" and lv.tile_at(fx, r.bottom - TILE) != "H" and (r.bottom % TILE) <= self.vy + 1:
                    self.y = r.bottom // TILE * TILE - self.h
                    self.vy = 0
                    self.on_ground = True
                    break
        self.anim += abs(self.vx) / 40      # un passo ogni 8 fotogrammi a velocita' piena
        self.run_t += abs(self.vx) / RUN_MAX * 0.125   # passo: un fotogramma ogni 8 frame
        if self.attack:
            name, f = self.attack
            f += 1
            limit = {"punch": 14, "kick": 18, "throw": 22 if self.power == "double" else 14, "cosmo": 40}[name]
            self.attack = None if f >= limit else (name, f)
        if self.invuln:
            self.invuln -= 1

    def do_jump(self):
        if self.climbing:
            self.climbing = False
            self.vy = JUMP_V * 0.7
            return True
        if self.on_ground:
            self.vy = JUMP_V
            self.on_ground = False
            return True
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
            if name == "cosmo":
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
        sheets = gfx.sheets[self.armor]
        side = 0 if self.facing > 0 else 1
        if self.climbing:
            return None
        if self.attack:
            name, f = self.attack
            base = {"punch": "punch", "kick": "kick", "throw": "throw", "cosmo": "punch"}[name]
            if base not in sheets:
                return None
            fr = sheets[base][side]
            if name == "cosmo":
                return fr[(f // 2) % len(fr)]
            limit = {"punch": 14, "kick": 18, "throw": 22 if self.power == "double" else 14}[name]
            return fr[min(len(fr) - 1, f * len(fr) // limit)]
        if not self.on_ground:
            if "jump" not in sheets:
                return None
            fr = sheets["jump"][side]
            n = len(fr)
            if self.vy < 0:
                i = min(n // 2 - 1, int((JUMP_V - self.vy) / -JUMP_V * (n // 2)))
            else:
                i = n // 2 + min(n // 2 - 1, int(self.vy / 14 * (n // 2)))
            return fr[max(0, i)]
        if abs(self.vx) > 0.5 and "run" in sheets:
            fr = sheets["run"][side]
            return fr[int(self.run_t) % len(fr)]
        return None

    def draw(self, s, gfx, cam):
        if self.invuln and (self.invuln // 3) % 2 and not (self.attack and self.attack[0] == "cosmo"):
            return
        img = self.sheet_frame(gfx)
        if img is not None:
            self.draw_img(s, img, cam)
            if self.attack and self.attack[0] == "cosmo":
                t = self.attack[1]
                pygame.draw.circle(s, (255, 220, 100), (self.rect.centerx - cam, self.rect.centery), 60 + t * 6, 6)
            return
        name = self.sprite_name()
        frames = gfx.player[self.armor]
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
        if self.attack and self.attack[0] == "cosmo":
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
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption("Goblin")
        self.clock = pygame.time.Clock()
        self.gfx = Gfx()
        self.jb = music.Jukebox()
        self.frame = 0
        self.hi = 0
        self.state = "title"
        self.score = 0
        self.ci = 0
        self.cfg = levels.cfg(0)
        self.powers = []
        self.player = Player(0, 0)
        self.msg = None
        self.effects = []
        self.rounds = [0, 0]

    # ---- flusso
    def new_game(self, ci=0):
        if ci == 0:
            self.score = 0
            self.powers = []
        self.lives = 3
        self.ci = ci
        self.start_part("surface")

    def start_part(self, part):
        c = levels.cfg(self.ci)
        self.cfg = c
        self.part = part
        g = {"surface": levels.gen_surface, "crypt": levels.gen_crypt, "arena": levels.gen_arena}[part](c)
        self.lv = Level(g, part)
        self.rounds = [0, 0]
        self.spawn()
        self.state = "card"
        self.card_t = 150
        self.jb.play({"surface": "surface", "crypt": "crypt", "arena": "arena"}[part])

    def spawn(self):
        lv = self.lv
        self.player = p = Player(2 * TILE, GROUND * TILE - Entity.h)
        p.power = self.powers[-1] if self.powers else None
        self.zombies, self.skels, self.crows, self.ghosts, self.balls = [], [], [], [], []
        for ch, c, r in lv.markers:
            if ch == "k":
                self.skels.append(Skeleton(c, r))
            elif ch == "v":
                self.crows.append(Crow(c, r))
            elif ch == "g":
                self.ghosts.append(Ghost(c, r))
        self.spawn_t = 60
        self.cam = 0
        self.boss = None
        self.msg = None
        self.effects = []
        self.intro = 0
        if self.part == "arena":
            self.start_round()

    def start_round(self):
        c = self.cfg
        self.player.hp = PLAYER_HP
        self.player.x = 3 * TILE
        self.player.armor = True
        self.boss = knights.GoldKnight(W - 5 * TILE, knights.knight_cfg(self.ci), self.gfx)
        self.balls = []
        self.intro = 150
        self.round_no = self.rounds[0] + self.rounds[1] + 1
        self.msg = (f"ROUND {self.round_no}", 90, (250, 210, 60))
        self.ko_wait = 0

    def next_part(self):
        if self.part == "surface":
            self.start_part("crypt")
        elif self.part == "crypt":
            self.start_part("arena")
        else:
            self.powers.append(self.cfg["power"])
            self.state = "armor"
            self.card_t = 260
            self.jb.play("victory")

    def after_armor(self):
        self.ci += 1
        if self.ci >= 12:
            self.state = "end"
            self.hi = max(self.hi, self.score)
            self.jb.stop()
        else:
            self.start_part("surface")

    # ---- danni
    def hurt_player(self, dmg, from_x):
        p = self.player
        if p.invuln or self.state != "play" or (p.attack and p.attack[0] == "cosmo"):
            return
        p.invuln = 80
        p.vy = -9
        p.vx = 6 if p.x > from_x else -6
        p.attack = None
        p.climbing = False
        self.jb.fx("hurt")
        if p.armor:
            p.armor = False
            self.effects.append(Effect(p.x, p.y - 30, "ARMATURA!", (255, 120, 120)))
        else:
            p.hp = max(0, p.hp - dmg)
            if p.hp == 0:
                self.die()

    def die(self):
        self.state, self.state_t = "dead", 0
        self.jb.fx("ko")

    def hit_enemy(self, e, dmg, power=None, pts=100):
        e.hp -= dmg
        self.player.cosmo = min(100, self.player.cosmo + 6)
        self.jb.fx("hit")
        if power == "ice":
            e.frozen = 90
        if e.hp <= 0:
            e.alive = False
            self.score += pts

    # ---- aggiornamento
    def update(self):
        self.frame += 1
        if self.state == "card":
            self.card_t -= 1
            if self.card_t <= 0:
                self.state = "play"
            return
        if self.state == "armor":
            self.card_t -= 1
            if self.card_t <= 0:
                self.after_armor()
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
        p.update(keys, self.lv)
        for e in self.effects:
            e.update()
        self.effects = [e for e in self.effects if e.alive]
        target = p.rect.centerx - W // 2
        self.cam = int(max(0, min(target, self.lv.w - W)))
        if p.y > H + 50:
            self.die(); return
        r = p.rect
        # punte
        if self.lv.tile_at(r.centerx, r.bottom - 6) == "^" or (p.on_ground and self.lv.tile_at(r.centerx, r.bottom + 2) == "^"):
            self.hurt_player(30, p.x - 10)
        # uscita
        ec, er = self.lv.exit
        door = pygame.Rect(ec * TILE, (er - 1) * TILE, TILE, TILE * 2)
        if self.part != "arena" and r.colliderect(door):
            self.jb.fx("pickup")
            self.next_part()
            return
        # zombie
        if self.part == "surface":
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
        # lancio della lancia / hadouken / cosmo
        # colpi del giocatore sui nemici
        abox, adm = p.attack_box()
        enemies = [(z, 100) for z in self.zombies if z.rise >= 20] + [(k, 300) for k in self.skels] + [(c, 150) for c in self.crows] + [(gh, 400) for gh in self.ghosts if gh.visible()]
        for e, pts in enemies:
            er = e.rect
            if abox and abox.colliderect(er):
                self.hit_enemy(e, adm * 2, p.power if p.attack[0] == "throw" else None, pts)
                if not (p.attack and p.attack[0] == "cosmo"):
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
                        p.cosmo = max(0, p.cosmo - 2)
                elif p.vy > 0 and r.bottom - er.top < 40 and not isinstance(e, Ghost):
                    self.hit_enemy(e, 10, pts=pts)
                    p.vy = -14
                    self.jb.fx("jump")
                elif not getattr(e, "frozen", 0):
                    self.hurt_player(25, e.x)
            sb = e.attack_box() if isinstance(e, Skeleton) else None
            if sb and sb.colliderect(p.hurtbox()):
                self.hurt_player(30, e.x)
        for b in self.balls:
            if b.owner == "boss" and b.alive and b.rect.colliderect(p.hurtbox()):
                b.alive = False
                self.hurt_player(b.dmg, b.x)
        # boss
        bs = self.boss
        if bs:
            if bs.hp <= 0:
                self.ko_wait += 1
                if self.ko_wait == 1:
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
                if abox and abox.colliderect(br) and bs.hit(adm, p.power if p.attack[0] == "throw" else None):
                    self.score += 50; p.cosmo = min(100, p.cosmo + 8); self.jb.fx("hit")
                if not bs.hidden and p.hurtbox().colliderect(br):
                    if p.vy > 0 and r.bottom - br.top < 50:
                        p.vy = -14
                        if bs.hit(8):
                            self.score += 50; p.cosmo = min(100, p.cosmo + 6)
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
        self.balls = [b for b in self.balls if b.alive]

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state = "gameover"
            self.hi = max(self.hi, self.score)
            self.jb.stop()
        else:
            self.rounds = [0, 0]
            self.spawn()
            self.state = "play"

    # ---- tasti
    def key(self, k):
        p = self.player
        if self.state == "title":
            if k == pygame.K_RETURN:
                self.new_game(0)
            return
        if self.state in ("gameover", "end"):
            if k == pygame.K_RETURN:
                if self.state == "end":
                    self.state = "title"
                else:
                    self.new_game(self.ci)
            return
        if self.state in ("card", "armor"):
            if k == pygame.K_RETURN:
                self.card_t = 0
            return
        if self.state != "play" or (self.part == "arena" and self.intro > 70):
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
            if p.cosmo >= 100 and p.start_attack("cosmo"):
                p.cosmo = 0
                p.invuln = 45
                self.jb.fx("cosmo")

    # ---- disegno
    def bar(self, x, y, w, frac, color, right=False):
        s = self.screen
        pygame.draw.rect(s, (245, 245, 245), (x - 3, y - 3, w + 6, 26))
        pygame.draw.rect(s, (120, 20, 20), (x, y, w, 20))
        fw = int(w * max(0, min(1, frac)))
        pygame.draw.rect(s, color, (x + w - fw if right else x, y, fw, 20))

    def draw_hud(self):
        s, p = self.screen, self.player
        px.draw_text(s, "ARTHUR", 40, 24, scale=5)
        px.draw_text(s, f"X{self.lives}", 200, 24, (250, 210, 60), scale=5)
        self.bar(40, 56, 560, p.hp / PLAYER_HP, (250, 210, 60))
        px.draw_text(s, "COSMO", 40, 92, (150, 220, 255), scale=4)
        self.bar(170, 92, 430, p.cosmo / 100, (100, 200, 255) if p.cosmo < 100 else (255, 255, 255))
        if p.cosmo >= 100 and (self.frame // 15) % 2:
            px.draw_text(s, "V!", 610, 92, (255, 255, 255), scale=4)
        arm = "ARMATURA" if p.armor else "SENZA ARMATURA"
        px.draw_text(s, arm, 40, 126, (200, 220, 255) if p.armor else (255, 120, 120), scale=4)
        if p.power:
            px.draw_text(s, levels.ARMOR_NAMES[p.power], 40, 154, self.cfg["color"], scale=4)
        title = f"CIMITERO {ROMAN[self.ci]} - {self.cfg['name']}"
        px.draw_text(s, title, W // 2 - px.text_width(title, 5) // 2, 24, scale=5)
        sub = {"surface": "SOPRA", "crypt": "SOTTOTERRA", "arena": "IL DUELLO"}[self.part]
        px.draw_text(s, sub, W // 2 - px.text_width(sub, 4) // 2, 60, (200, 200, 220), scale=4)
        sc = f"PUNTI {self.score:08d}"
        px.draw_text(s, sc, W - 40 - px.text_width(sc, 5), 24, (250, 210, 60), scale=5)
        if self.boss:
            name = self.cfg["boss"].upper()
            px.draw_text(s, name, W - 40 - px.text_width(name, 4), 130, scale=4)
            self.bar(W - 600, 56, 560, self.boss.hp / self.boss.max_hp, self.cfg["color"], right=True)
            for i in range(2):
                pygame.draw.circle(s, (250, 210, 60) if i < self.rounds[0] else (80, 80, 90), (W - 580 + i * 40, 102), 12)
                pygame.draw.circle(s, self.cfg["color"] if i < self.rounds[1] else (80, 80, 90), (W - 80 - i * 40, 102), 12)
        if self.msg:
            t, n, col = self.msg
            px.draw_text(s, t, W // 2 - px.text_width(t, 14) // 2, 380, col, scale=14)

    def draw_world(self):
        s, cam, lv = self.screen, self.cam, self.lv
        if self.part == "surface":
            s.blit(self.gfx.background("sky", self.cfg["num"]), (0, 0))
            hills = self.gfx.background("hills", self.cfg["num"])
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
        if self.part == "surface":
            if not hasattr(self, "pit_shade"):
                self.pit_shade = pygame.Surface((TILE, H - GROUND * TILE), pygame.SRCALPHA)
                for yy in range(self.pit_shade.get_height()):
                    a = min(255, 120 + yy * 2)
                    pygame.draw.line(self.pit_shade, (8, 6, 14, a), (0, yy), (TILE, yy))
            for c in range(c0, min(lv.cols, c0 + W // TILE + 3)):
                if lv.g[GROUND][c] == ".":
                    s.blit(self.pit_shade, (c * TILE - cam, GROUND * TILE))
        for c in range(c0, min(lv.cols, c0 + W // TILE + 3)):
            x = c * TILE - cam
            for r in range(ROWS):
                ch = lv.g[r][c]
                if ch == "." or ch in "kvg":
                    continue
                y = r * TILE
                if ch in self.gfx.tiles:
                    s.blit(self.gfx.tiles[ch], (x, y))
                elif ch == "Y":
                    s.blit(self.gfx.deco["Y"], (x - TILE // 2, y - TILE * 2))
                elif ch == "E":
                    s.blit(self.gfx.deco["E"], (x, y - TILE))
                elif ch == "t" and "t2" in self.gfx.deco and c % 2:
                    s.blit(self.gfx.deco["t2"], (x, y))
                elif ch in self.gfx.deco:
                    s.blit(self.gfx.deco[ch], (x, y))

    def draw_center(self, text, y, color=(245, 245, 245), scale=8):
        px.draw_text(self.screen, text, W // 2 - px.text_width(text, scale) // 2, y, color, scale)

    def draw(self):
        s = self.screen
        if self.state == "title":
            s.blit(self.gfx.background("sky", 1), (0, 0))
            self.draw_center("GOBLIN", 260, (250, 210, 60), 24)
            self.draw_center("12 CIMITERI", 420, (200, 200, 220), 8)
            self.draw_center("SAME COURAGE, NEW NIGHTMARES", 500, (150, 160, 190), 4)
            if (self.frame // 30) % 2:
                self.draw_center("PREMI INVIO", 700, scale=6)
            self.draw_center("FRECCE MUOVI  SPAZIO SALTA  Z AFFONDO DI LANCIA  X PUGNO  C CALCIO", 900, (150, 160, 190), 4)
            self.draw_center("V COSMO: RAFFICA DI PUGNI     SU/GIU SULLE SCALE", 940, (150, 160, 190), 4)
            img = self.gfx.player[True]["idle"][0]
            s.blit(pygame.transform.scale(img, (PW * 2, PH * 2)), (W // 2 - PW, 560 + 40))
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
            self.draw_center(f"CIMITERO {ROMAN[self.ci]}", 300, (250, 210, 60), 14)
            self.draw_center(self.cfg["name"].upper(), 440, scale=10)
            sub = {"surface": "SOPRA", "crypt": "SOTTOTERRA", "arena": "IL DUELLO"}[self.part]
            self.draw_center(sub, 560, (200, 200, 220), 8)
            self.draw_center(f"GUARDIANO: {self.cfg['boss'].upper()}", 680, self.cfg["color"], 5)
        elif self.state == "armor":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 190)); s.blit(ov, (0, 0))
            self.draw_center("VITTORIA", 260, (250, 210, 60), 14)
            self.draw_center("HAI CONQUISTATO L'ARMATURA", 420, scale=7)
            self.draw_center(f"DEL {self.cfg['boss'].upper()}", 500, self.cfg["color"], 7)
            self.draw_center(levels.ARMOR_NAMES[self.cfg["power"]].upper(), 640, (200, 220, 255), 9)
            self.draw_center("PREMI INVIO", 820, (150, 160, 190), 5)
        elif self.state == "gameover":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 170)); s.blit(ov, (0, 0))
            self.draw_center("GAME OVER", 380, (230, 40, 40), 16)
            self.draw_center(f"INVIO: RIPROVA IL CIMITERO {ROMAN[self.ci]}", 600, scale=6)
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
