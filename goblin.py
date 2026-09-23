#!/usr/bin/env python3
"""NightKnight - Titano: le ondate, la traversata, il duello col Guardiano. 1920x1080."""
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
import fonts
import progress
import titan
import waves

W, H = 1920, 1080
FPS = 60
TILE = 64
SKY_PAN = 360        # di quanto scorre il cielo dall'inizio alla fine del livello
# Zoom: il mondo si disegna in una vista di VW x VH pixel ingrandita a tutto
# schermo; il terreno resta alla stessa altezza. Cielo, fondali e HUD no.
ZOOM = 1.5
VW, VH = int(W / ZOOM), int(H / ZOOM)
LUCE_MAX, LUCE_UNIT, LUCE_PER_PRISONER = 100, 25, 5
LAKE_LEVEL = 22      # il metano sta un po' sotto il bordo del terreno
BURST_FRAMES = 70    # durata del volo di Bianca durante la raffica
TITAN_N = 6          # il terreno di Titano copre 6x6 tessere
ROWS = 17
GROUND = levels.GROUND
VIEW_Y = int(GROUND * TILE * (1 - 1 / ZOOM))    # riga del mondo in cima alla vista
GRAVITY = 0.75
MAX_FALL = 18
RUN_ACC = 0.65
RUN_MAX = 5.8
SWORD_REACH = 170
SPRINT_MAX = 10.0
JUMP_V = -20.0
SHORT_JUMP_V = -16.0
CLIMB = 5
COYOTE_FRAMES = 6
JUMP_BUFFER_FRAMES = 7
PLAYER_HP = 100
SOLID = set("#DS")

PS = 8          # scala pixel art personaggi
PW, PH = 16 * PS, 24 * PS


# ---------------------------------------------------------------- grafica
def player_images():
    """Le pose senza un foglio proprio usano NightKnight in piedi."""
    img = assets.load("knight_idle", PW, PH, by_height=True)
    return {"idle": (img, assets.flip(img))}


class Gfx:
    def __init__(self):
        # caratteri disegnati come terreno (le pareti "S" dell'arena sono invisibili)
        self.tiles = set("#DH")
        # Terreno di Titano: l'immagine e' un'unica sezione di suolo alla Huygens.
        # Si scala a TITAN_N x TITAN_N tessere, cosi' i ciottoli restano leggibili:
        # la riga in alto e' la crosta calpestabile, le altre il sottosuolo.
        self.titan_ground = None
        if assets.has("titan_ground_grass"):
            img = pygame.image.load(os.path.join(assets.DIR, "titan_ground_grass.png")).convert()
            top = img.get_height() // 30          # striscia scura sopra la superficie
            img = img.subsurface((0, top, img.get_width(), img.get_height() - top))
            self.titan_ground = pygame.transform.smoothscale(img, (TILE * TITAN_N, TILE * TITAN_N))
        # Lago di metano: liquido scuro, un po' sotto il bordo, che riflette il cielo.
        depth = H - GROUND * TILE
        self.titan_lake = pygame.Surface((TILE, depth), pygame.SRCALPHA)
        for y in range(LAKE_LEVEL, depth):
            k = (y - LAKE_LEVEL) / (depth - LAKE_LEVEL)
            top, low = (132, 70, 34), (12, 7, 8)
            color = tuple(int(a + (b - a) * min(1, k * 2.2)) for a, b in zip(top, low))
            pygame.draw.line(self.titan_lake, color + (255,), (0, y), (TILE, y))
        # Vignettatura: bordi dello schermo appena piu' scuri
        self.vignette = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(60):
            a = int(90 * (1 - i / 60) ** 2)
            pygame.draw.rect(self.vignette, (10, 4, 2, a), (i * 6, i * 4, W - i * 12, H - i * 8), 6)
        # Ombra sui fianchi delle rocce
        self.rock_shade = pygame.Surface((18, TILE), pygame.SRCALPHA)
        for x in range(18):
            pygame.draw.line(self.rock_shade, (30, 14, 8, 120 - x * 6), (x, 0), (x, TILE))
        self.rock_shade_r = pygame.transform.flip(self.rock_shade, True, False)
        # Scala di servizio in acciaio, con i contorni del cartoon
        self.titan_ladder = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        for x in (12, TILE - 18):
            pygame.draw.rect(self.titan_ladder, (22, 18, 16), (x - 2, 0, 10, TILE))
            pygame.draw.rect(self.titan_ladder, (104, 100, 96), (x, 0, 6, TILE))
        for y in range(8, TILE, 16):
            pygame.draw.rect(self.titan_ladder, (22, 18, 16), (12, y - 2, TILE - 24, 8))
            pygame.draw.rect(self.titan_ladder, (140, 132, 122), (14, y, TILE - 28, 4))
        # Portello stagno dell'uscita
        self.airlock = pygame.Surface((TILE * 2, TILE * 3), pygame.SRCALPHA)
        a = self.airlock
        pygame.draw.rect(a, (20, 16, 14), a.get_rect(), border_radius=18)
        pygame.draw.rect(a, (92, 86, 80), a.get_rect().inflate(-10, -10), border_radius=14)
        pygame.draw.rect(a, (46, 42, 40), a.get_rect().inflate(-34, -34), border_radius=10)
        for y in range(30, TILE * 3 - 30, 26):
            pygame.draw.polygon(a, (226, 176, 48), [(17, y), (27, y + 10), (27, y + 20), (17, y + 10)])
            pygame.draw.polygon(a, (226, 176, 48), [(TILE * 2 - 17, y), (TILE * 2 - 27, y + 10), (TILE * 2 - 27, y + 20), (TILE * 2 - 17, y + 10)])
        pygame.draw.circle(a, (20, 16, 14), (TILE, TILE + 20), 22)
        pygame.draw.circle(a, (150, 140, 128), (TILE, TILE + 20), 17, 5)
        pygame.draw.circle(a, (110, 220, 140), (TILE, 32), 8)
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
        # Prigionieri: coloni chiusi in una capsula, poco piu' alta di NightKnight.
        self.spento_sleeping = assets.load("prigioniero_spento", PW * 2, PH * 5 // 4, by_height=True)
        self.spento_awake = assets.load("prigioniero_acceso", PW * 2, PH * 5 // 4, by_height=True)
        # Bianca: due pose di volo.
        self.bianca = [assets.load(f"bianca_chick_{i + 1}", 150, 105, by_height=True) for i in range(2)]
        # Nemici: due fotogrammi per specie, stessa scala per entrambi.
        self.foes = {kind: assets.frames([spec["frames"].format(i) for i in (1, 2)], spec.get("h", 10 * PS))
                     for table in (WALKERS, FLYERS) for kind, spec in table.items()}
        self.skeleton, self.crow = self.foes["skeleton"], self.foes["crow"]
        # foschia bassa che lega il terreno ai fondali
        self.haze = pygame.Surface((VW, 105), pygame.SRCALPHA)
        for yy in range(105):
            pygame.draw.line(self.haze, (184, 91, 31, int(60 * math.sin(math.pi * yy / 105))), (0, yy), (VW, yy))
        self.boss_cache = {}
        self.bg_cache = {}

    def knight(self, num, color):
        if num not in self.boss_cache:
            self.boss_cache[num] = knights.knight_images(self, num, color)
        return self.boss_cache[num]

    def title_backdrop(self):
        """Titolo: cielo di Titano smorzato, lo stemma al centro, NightKnight a sinistra."""
        if "title" not in self.bg_cache:
            bg = self.background("sky", 1).copy()
            shade = pygame.Surface((W, H), pygame.SRCALPHA)
            shade.fill((20, 8, 4, 110))
            bg.blit(shade, (0, 0))
            if assets.has("emblema"):
                em = assets.load("emblema", 560, 470, by_height=True)
                bg.blit(em, (W // 2 - em.get_width() // 2, 250))
            if assets.has("knight_idle"):
                hero = assets.load("knight_idle", 900, 820, by_height=True)
                bg.blit(hero, (330 - hero.get_width() // 2, H - hero.get_height() - 20))
            self.bg_cache["title"] = bg
        return self.bg_cache["title"]

    def titan_tile(self, ch, c, r):
        if ch == "H":
            return self.titan_ladder
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

    def sized(self, img, k):
        if k == 1.0:
            return img
        key = ("sized", id(img), k)
        if key not in self.bg_cache:
            self.bg_cache[key] = pygame.transform.smoothscale(img, (int(img.get_width() * k), int(img.get_height() * k)))
        return self.bg_cache[key]

    def white(self, img):
        """Sagoma bianca per il lampo del colpo."""
        key = ("white", id(img))
        if key not in self.bg_cache:
            w = img.copy()
            w.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
            self.bg_cache[key] = w
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

    def background(self, kind, num=1):
        """Fondale disegnato del satellite (sky_01, hills_01...)."""
        key = (kind, num)
        if key not in self.bg_cache:
            self.bg_cache[key] = assets.load(f"{kind}_{num:02d}", W, H, exact=True)
        return self.bg_cache[key]


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
        self.swing = 0
        self.climbing = False
        self.last_down = -999
        self.last_fwd = -999
        self.coyote = 0
        self.jump_buffer = 0
        self.jumped = False
        self.weapon = levels.weapon_cfg(0)
        self.gravity_scale = 1.0

    def hurtbox(self):
        return self.rect.inflate(-10, -6)

    def attack_box(self):
        if not self.attack:
            return None, 0
        name, f = self.attack
        r = self.rect
        if name == "kick" and 4 <= f <= 12:
            return pygame.Rect(r.right if self.facing > 0 else r.left - 110, r.top + 76, 110, 60), 9
        if name == "throw" and 4 <= f <= 10:
            # il fendente scende fino ai piedi: prende anche lucertole e ratti
            return pygame.Rect(r.right if self.facing > 0 else r.left - SWORD_REACH, r.top + 40, SWORD_REACH, r.h - 40), 12
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
        speed_limit = SPRINT_MAX if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else RUN_MAX
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
        if not grounded_attack:
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
            limit = {"punch": 14, "kick": 18, "throw": 14}[name]
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
            self.swing += 1               # ogni colpo tocca ciascun nemico una volta sola
            return True
        return False

    def sheet_frame(self, gfx):
        """Fotogramma dal foglio di sprite della posa corrente, se esiste."""
        sheets = gfx.sheets
        side = 0 if self.facing > 0 else 1
        if self.climbing:
            return None
        if self.attack:
            name, f = self.attack
            base = "flykick" if name == "kick" and not self.on_ground and "flykick" in sheets else name
            if base not in sheets:
                return None
            fr = sheets[base][side]
            limit = {"punch": 14, "kick": 18, "throw": 14}[name]
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
        if self.invuln and (self.invuln // 3) % 2:
            return
        img = self.sheet_frame(gfx)
        if img is None:
            img = gfx.player["idle"][0 if self.facing > 0 else 1]
        self.draw_img(s, img, cam)


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
                self.cawed = True
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
        self.burst = 0

    def update(self, player, cam=0):
        self.t += 1
        if self.burst:
            # raffica: si illumina e attraversa la parte alta dello schermo
            self.burst -= 1
            k = 1 - self.burst / BURST_FRAMES
            self.x, self.y, self.facing = cam - 200 + (VW + 400) * k, VIEW_Y + 90 + math.sin(k * math.pi * 2) * 30, 1
            return
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
        if self.burst:
            glow = pygame.Surface((420, 420), pygame.SRCALPHA)
            for rad in range(200, 20, -20):
                pygame.draw.circle(glow, (255, 240, 200, 14), (210, 210), rad)
            screen.blit(glow, (int(self.x) - 210 - cam, int(self.y) - 210))
        screen.blit(img, (int(self.x) - img.get_width() // 2 - cam,
                          int(self.y) - img.get_height() // 2 + bob))


# Specie dei nemici nuovi. I camminatori ereditano dallo scheletro (colpo
# ravvicinato, pestone, danni), i volanti dal corvo (volo e picchiata).
# h: altezza dello sprite; box: sagoma colpibile; hp: colpi per abbatterlo.
WALKERS = {
    "skeleton":    dict(frames="skeleton_walk{}", h=PH, box=(70, 176), hp=1, speed=2.6, dmg=30, reach=70, pts=300),
    "skeleton_2x": dict(frames="skeleton_2x_{}", h=PH * 2, box=(120, 352), hp=2, speed=1.8, dmg=40, reach=150, pts=1500),
    "skeleton_3x": dict(frames="skeleton_3x_{}", h=PH * 3, box=(170, 528), hp=3, speed=1.3, dmg=55, reach=220, pts=4000),
    "miner":       dict(frames="miner_mutant_{}", h=PH, box=(80, 176), hp=2, speed=2.0, dmg=35, reach=95, pts=500),
    "lizard":      dict(frames="lizard_cryo_{}", h=80, box=(170, 70), hp=1, speed=1.4, dmg=25, reach=60, pts=400, lunge=True),
    "worm":        dict(frames="worm_silicon_{}", h=230, box=(100, 200), hp=1, speed=0, dmg=30, reach=120, pts=600),
}
FLYERS = {
    "crow":         dict(frames="crow_{}", hp=1, dmg=0),
    "skeleton_fly": dict(frames="skeleton_fly_{}", h=PH, box=(80, 150), hp=1, dmg=25, pts=500),
    "jelly":        dict(frames="jelly_atmo_{}", h=150, box=(110, 120), hp=1, dmg=20, pts=350, drift=True),
}


class Stone:
    """Sasso lanciato da NightKnight: arco basso, danno piccolo, sempre disponibile."""
    owner = "player"

    def __init__(self, p):
        self.d = p.facing
        self.x = p.rect.right if self.d > 0 else p.rect.left - 20
        self.y = p.rect.top + 40
        self.vx, self.vy = 15 * self.d, -5.0
        self.dmg = 0.5           # un sasso vale mezzo colpo
        self.alive = True
        self.t = 0
        self.kind = "stone"

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), 22, 22)

    def update(self, lv, cam):
        self.t += 1
        self.x += self.vx
        self.vy += 0.35
        self.y += self.vy
        if lv.solid(self.x + 11, self.y + 11) or self.t > 120:
            self.alive = False

    def draw(self, s, gfx, cam):
        c = (int(self.x) - cam + 11, int(self.y) + 11)
        pygame.draw.circle(s, (20, 16, 14), c, 12)
        pygame.draw.circle(s, (150, 140, 128), c, 9)
        pygame.draw.circle(s, (196, 188, 174), (c[0] - 3, c[1] - 3), 3)


class Walker(Skeleton):
    """Nemico di terra di una specie di WALKERS, piazzato in pixel."""

    def __init__(self, x, kind):
        spec = WALKERS[kind]
        self.w, self.h = spec["box"]
        super().__init__(0, 0)
        self.x, self.y = float(x), float(GROUND * TILE - self.h)
        self.kind, self.spec = kind, spec
        self.hp, self.dmg = spec["hp"], spec["dmg"]
        self.lunge_t = 0
        # nessuno uguale all'altro: taglia e passo cambiano un poco
        self.scale = random.choice((0.92, 0.97, 1.0, 1.04, 1.08))
        self.pace = random.uniform(0.85, 1.15)
        self.flash = 0

    def attack_box(self):
        if 0 < self.hit_t <= 12:
            r, reach = self.rect, self.spec["reach"]
            return pygame.Rect(r.right if self.facing > 0 else r.left - reach, r.top + r.h // 4, reach, r.h // 2)
        return None

    def update(self, lv, player):
        spec = self.spec
        if self.y > H + 200:              # finito in un lago di metano
            self.alive = False
            return
        if spec["speed"] == 0:                 # il verme resta dove emerge
            self.t += 1
            dist = player.x - self.x
            self.facing = 1 if dist > 0 else -1
            if self.hit_t:
                self.hit_t -= 1
            elif abs(dist) < spec["reach"] + 60:
                self.hit_t = 30
            return
        if spec.get("lunge") and not self.hit_t:
            dist = player.x - self.x
            if self.lunge_t:
                self.lunge_t -= 1
            elif abs(dist) < 320 and self.t % 90 == 0:
                self.lunge_t = 28
        speed = 7.0 if self.lunge_t else spec["speed"] * self.pace
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
        self.facing = 1 if dist > 0 else -1
        if abs(dist) < spec["reach"] + 30 and abs(player.rect.bottom - self.rect.bottom) < 100:
            self.hit_t = 24
        r = self.rect
        ahead = r.right + 2 if self.facing > 0 else r.left - 3
        self.vx = speed * self.facing if lv.solid(ahead, r.bottom + 2) else 0
        self.move(lv)

    def draw(self, s, gfx, cam):
        frames = gfx.foes[self.kind]
        attacking = 0 < self.hit_t <= 18 or self.lunge_t
        img = frames[1] if (attacking or (self.spec["speed"] and (self.t // 10) % 2)) else frames[0]
        img = gfx.sized(img, self.scale)
        if self.facing < 0:
            img = assets.flip(img)
        if self.flash:
            self.flash -= 1
            img = gfx.white(img)
        self.draw_img(s, img, cam)
        if self.frozen:
            pygame.draw.rect(s, (150, 220, 255), (int(self.x) - cam, self.y, self.w, self.h), 4)


class Flyer(Crow):
    """Volante di una specie di FLYERS, piazzato in pixel. Il corvo spinge e
    basta; scheletri volanti e meduse fanno male."""

    def __init__(self, x, y, kind):
        spec = FLYERS[kind]
        if "box" in spec:
            self.w, self.h = spec["box"]
        super().__init__(0, 0)
        self.x, self.y = float(x), float(y)
        self.home = (self.x, self.y)
        self.kind, self.spec = kind, spec
        self.hp = spec["hp"]
        self.dmg = spec["dmg"]
        self.harmless = spec["dmg"] == 0
        self.state = "dive"
        self.cawed = kind == "crow"

    def update(self, lv, player):
        if self.spec.get("drift"):
            # la medusa galleggia nell'aria densa e scende piano verso di te
            self.t += 1
            if self.frozen:
                self.frozen -= 1
                return
            self.facing = 1 if player.x > self.x else -1
            self.x += 1.2 * self.facing
            self.y += ((player.y - 80) - self.y) * 0.01 + math.sin(self.t / 25) * 1.2
            return
        super().update(lv, player)
        if self.state == "away" and self.t > 60:
            # chi arriva con un'ondata non torna a casa: rientra da dove e' uscito
            self.state, self.t = "dive", 0
            self.facing = 1 if player.x > self.x else -1

    def draw(self, s, gfx, cam):
        frames = gfx.foes[self.kind]
        img = frames[(self.t // (12 if self.spec.get("drift") else 5)) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        if getattr(self, "flash", 0):
            self.flash -= 1
            img = gfx.white(img)
        self.draw_img(s, img, cam)


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
        # SCALED ingrandisce la risoluzione logica allo schermo: su un 4K anche la
        # finestra occupa lo schermo invece di un quarto. Senza video (test) niente scala.
        headless = os.environ.get("SDL_VIDEODRIVER") == "dummy"
        flags = 0 if headless else (pygame.SCALED | pygame.RESIZABLE if windowed else pygame.FULLSCREEN | pygame.SCALED)
        self.screen = pygame.display.set_mode((W, H), flags)
        self.luce, self.freed = 0, set()      # Luce di Bianca e prigionieri gia' liberati
        self.sparks, self.shake = [], 0       # scintille dei colpi e scossa dello schermo
        self.reached_pass = False             # su Titano: arrivati alla traversata
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
    def save_progress(self, checkpoint=False, clear=False):
        self.hi = max(self.hi, self.score)
        self.saved["high_score"] = self.hi
        if clear:
            self.saved["checkpoint"] = None
        elif checkpoint:
            self.saved["checkpoint"] = {
                "cemetery": 0, "part": self.part, "lives": self.lives, "score": self.score,
                "luce": self.luce, "freed": sorted(list(f) for f in self.freed),
                "pass": self.reached_pass,
            }
        self.save_error = progress.save(self.saved, self.save_path)

    def continue_game(self):
        cp = self.saved["checkpoint"]
        if cp:
            self.ci, self.lives, self.score = 0, cp["lives"], cp["score"]
            self.luce = max(0, min(LUCE_MAX, int(cp.get("luce", 0))))
            self.reached_pass = cp.get("pass") is True
            self.freed = {tuple(f) for f in cp.get("freed", []) if isinstance(f, list) and len(f) == 3}
            self.start_part(cp["part"])

    def set_paused(self, paused):
        self.paused = paused
        self.menu_index = 0
        if pygame.mixer.get_init():
            (pygame.mixer.pause if paused else pygame.mixer.unpause)()

    def menu_items(self):
        if self.paused:
            return ["RIPRENDI", "TORNA AL TITOLO", "ESCI"]
        return (["CONTINUA"] if self.saved["checkpoint"] else []) + ["NUOVA PARTITA", "ESCI"]

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
            elif action == "ESCI":
                self.running = False

    def new_game(self, part="surface"):
        self.score = 0
        self.luce, self.freed = 0, set()
        self.reached_pass = False
        self.lives = 3
        self.ci = 0
        self.start_part(part)

    def start_part(self, part):
        if part != "surface":
            self.reached_pass = False
        c = levels.cfg(self.ci)
        self.cfg = c
        self.part = part
        g = {"surface": levels.gen_surface, "arena": levels.gen_arena}[part]()
        self.lv = Level(g, part)
        self.rounds = [0, 0]
        self.spawn()
        self.state = "card"
        self.card_t = 150
        self.jb.play("trials" if part == "surface" and self.reached_pass else part)
        self.save_progress(checkpoint=True)

    def spawn(self):
        lv = self.lv
        self.player = p = Player(2 * TILE, GROUND * TILE - Entity.h)
        p.on_ground = True
        p.weapon = levels.weapon_cfg(self.weapon_i)
        p.gravity_scale = self.cfg["gravity_scale"]
        self.bianca = Bianca(p)
        # La Luce e i prigionieri liberati restano anche dopo una vita persa
        p.albedo = self.luce
        self.geysers, self.spenti = [], []
        self.skels, self.crows, self.balls = [], [], []
        for ch, c, r in lv.markers:
            if ch == "q":
                self.geysers.append(titan.Geyser((c + .5) * TILE, (r + 1) * TILE))
            elif ch == "u":
                spento = titan.Spento((c + .5) * TILE, (r + 1) * TILE)
                if (self.ci, self.part, int(spento.x)) in self.freed:
                    spento.liberated, spento.glow = True, 60
                self.spenti.append(spento)
        self.cam = 0
        self.boss = None
        self.msg = None
        self.effects = []
        self.intro = 0
        self.cable = None
        if self.part == "surface":
            self.cable = athletics.Cable(levels.TITAN_PASS_ROPE * TILE)
            for kind, col, *row in levels.TITAN_PASS_FOES:
                col += levels.TITAN_PASS_START
                if row:
                    flyer = Flyer(col * TILE, row[0] * TILE, kind)
                    flyer.state = "wait"          # aspetta il passaggio, come i corvi di guardia
                    self.crows.append(flyer)
                else:
                    self.skels.append(Walker(col * TILE, kind))
        self.waves = None
        if self.part == "surface":
            self.waves = waves.WaveDirector(levels.TITAN_ARENAS, levels.TITAN_WAVES, Walker, Flyer, seed=self.ci,
                                            flyer_y=(VIEW_Y + 40, VIEW_Y + 260))
            if self.reached_pass:
                # si era gia' arrivati alla traversata: si riparte da li', ondate superate
                for w in self.waves.waves:
                    w.state = "done"
                p.x = (levels.TITAN_PASS_START + 1) * TILE
        if self.part == "arena":
            self.start_round()

    def start_round(self):
        self.player = Player(3 * TILE, GROUND * TILE - Entity.h)
        self.player.on_ground = True
        self.player.albedo = self.luce          # la Luce arriva intatta al duello
        self.player.weapon = levels.weapon_cfg(self.weapon_i)
        self.player.gravity_scale = self.cfg["gravity_scale"]
        self.effects = []
        self.boss = knights.GoldKnight(W - 5 * TILE, knights.knight_cfg(self.ci), self.gfx)
        self.balls = []
        self.intro = 150
        self.jb.fx("round")
        self.ko_wait = 0

    def next_part(self):
        if self.state == "victory":
            return
        # Titano e' un unico percorso (ondate, poi traversata) e poi il duello.
        if self.part == "surface":
            self.start_part("arena")
        else:
            self.state = "victory"
            self.card_t = 260
            self.jb.play("victory")
            self.save_progress(clear=True)

    def after_victory(self):
        # Per ora il viaggio si ferma a Titano: gli altri satelliti arriveranno.
        self.state = "end"
        self.hi = max(self.hi, self.score)
        self.jb.stop()
        self.save_progress(clear=True)

    # ---- danni
    def burst_sparks(self, x, y, n, color=(255, 214, 150)):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(2, 9)
            self.sparks.append([x, y, math.cos(a) * v, math.sin(a) * v - 2, random.randint(14, 28), color])

    def hurt_player(self, dmg, from_x):
        p = self.player
        if (p.invuln or self.state != "play"
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
        self.shake = 14
        self.burst_sparks(p.rect.centerx, p.rect.centery, 14, (255, 140, 100))
        if p.hp == 0:
            self.die()

    def luce_burst(self):
        """Bianca scarica tutta la Luce in una raffica: abbatte ogni volante sullo
        schermo e toglie al Guardiano il 5% della vita per ogni unita' da 25."""
        p = self.player
        units = min(LUCE_MAX // LUCE_UNIT, p.albedo // LUCE_UNIT)
        if units <= 0 or not self.bianca or self.bianca.burst:
            return False
        p.albedo -= units * LUCE_UNIT
        self.bianca.burst = BURST_FRAMES
        self.jb.fx("luce")
        for c in self.crows:
            if c.alive and self.cam - 100 < c.x < self.cam + VW + 100:
                self.hit_enemy(c, 999, pts=getattr(c, "spec", {}).get("pts", 150))
        if self.boss and self.boss.hp > 0:
            self.boss.hp = max(0, self.boss.hp - max(1, round(self.boss.max_hp * 0.05 * units)))
            self.boss.flash = 20
        return True

    def boss_spawn(self, projectile):
        self.balls.append(projectile)
        if projectile.kind == "hook":
            self.jb.fx("hook")

    def die(self):
        self.state, self.state_t = "dead", 0
        self.jb.fx("death")

    def hit_enemy(self, e, hits, pts=100, weapon=False):
        """La vita dei nemici si conta in colpi. Il fendente con l'arma non affine
        alla fauna del satellite vale mezzo colpo: i nemici diventano piu' resistenti."""
        if not e.alive:
            return
        if weapon and self.player.weapon["affinity"] != self.cfg["affinity"]:
            hits *= 0.5
        e.flash = 6
        if hasattr(e, "rect"):
            self.burst_sparks(e.rect.centerx, e.rect.centery, 10)
        e.hp -= hits
        bony = isinstance(e, Skeleton) and getattr(e, "kind", "skeleton").startswith("skeleton")
        self.jb.fx("hit" if bony else "flesh_hit")
        if e.hp <= 0:
            e.alive = False
            self.score += pts
            if hasattr(e, "rect"):
                self.shake = max(self.shake, 6 if e.rect.h > 300 else 3)
                self.burst_sparks(e.rect.centerx, e.rect.centery, 22)
            if bony:
                self.jb.fx("bones")

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
        if self.cable:
            self.cable.update_player(p, keys, self.lv)
        else:
            p.update(keys, self.lv)
        if self.bianca:
            self.bianca.update(p, self.cam)
        self.luce = p.albedo
        if p.jumped:
            self.jb.fx("jump")
        for e in self.effects:
            e.update()
        self.effects = [e for e in self.effects if e.alive]
        for sp in self.sparks:
            sp[0] += sp[2]; sp[1] += sp[3]; sp[3] += 0.4; sp[4] -= 1
        self.sparks = [sp for sp in self.sparks if sp[4] > 0]
        self.shake = max(0, self.shake - 1)
        target = p.rect.centerx - VW // 2
        self.cam = int(max(0, min(target, self.lv.w - VW)))
        lock = self.waves.lock() if self.waves else None
        if lock:
            # porte stagne chiuse: si resta nell'arena finche' l'ondata non e' finita
            p.x = max(lock[0] + 30, min(p.x, lock[1] - 30 - p.w))
            self.cam = int(max(lock[0], min(target, lock[1] - VW)))
        if p.y > H + 50:
            self.die(); return
        r = p.rect
        for geyser in self.geysers:
            if geyser.update(p):
                self.hurt_player(25, geyser.x)
            if geyser.phase != geyser.previous_phase and abs(geyser.x - p.x) < W:
                self.jb.fx({"warning": "geyser_warn", "eruption": "geyser"}.get(geyser.phase, "none"))
            if self.state != "play":
                return
        for spento in self.spenti:
            if spento.update(p):
                p.albedo = min(LUCE_MAX, p.albedo + LUCE_PER_PRISONER)
                self.freed.add((self.ci, self.part, int(spento.x)))
                self.jb.fx("prisoner")
        if self.state != "play":
            return
        # uscita
        ec, er = self.lv.exit
        door = pygame.Rect(ec * TILE, (er - 1) * TILE, TILE, TILE * 2)
        if self.part != "arena" and r.colliderect(door):
            self.jb.fx("door")
            self.next_part()
            return
        # Nel duello il Guardiano e' aiutato solo da pochi volanti
        if self.part == "arena" and self.boss and self.boss.hp > 0 and not self.intro:
            self.arena_flyer_t = getattr(self, "arena_flyer_t", 300) - 1
            if self.arena_flyer_t <= 0 and sum(c.alive for c in self.crows) < levels.TITAN_ARENA_FLYERS_MAX:
                self.arena_flyer_t = 420
                side = random.choice((-1, 1))
                x = self.cam - 80 if side < 0 else self.cam + VW + 20
                self.crows.append(Flyer(x, random.randrange(VIEW_Y + 40, VIEW_Y + 240), random.choice(levels.TITAN_ARENA_FLYERS)))
        if (self.part == "surface" and not self.reached_pass
                and p.x > levels.TITAN_PASS_START * TILE):
            self.reached_pass = True
            self.jb.play("trials")
            self.save_progress(checkpoint=True)
        if self.waves:
            event = self.waves.update(p, self.skels, self.crows)
            if event:
                kind, wave = event
                self.jb.fx("door")
                if kind == "clear":
                    self.score += 1000 * wave.total // 10
        for k in self.skels:
            k.update(self.lv, p)
        for cr in self.crows:
            cr.update(self.lv, p)
            if getattr(cr, "cawed", False):
                cr.cawed = False
                self.jb.fx("caw")
        for b in self.balls:
            b.update(self.lv, self.cam)
        # lancio della lancia / hadouken / albedo
        # colpi del giocatore sui nemici
        enemies = [(k, k.spec["pts"]) for k in self.skels] + [(c, c.spec.get("pts", 150)) for c in self.crows]
        for e, pts in enemies:
            if not e.alive:
                continue
            abox, adm = p.attack_box()
            er = e.rect
            if abox and abox.colliderect(er) and getattr(e, "swing", None) != p.swing:
                e.swing = p.swing
                self.hit_enemy(e, 1, pts=pts, weapon=p.attack[0] == "throw")
                continue
            if not e.alive:
                continue
            if p.hurtbox().colliderect(er):
                if isinstance(e, Crow) and getattr(e, "harmless", True):
                    # il corvo disturba: spinge, fa sbagliare il colpo, ma non toglie vita
                    if not p.invuln:
                        p.vx = 3 * e.facing
                        p.attack = None
                        p.invuln = 20
                elif p.vy > 0 and r.bottom - er.top < 40:
                    self.hit_enemy(e, 1, pts=pts)
                    p.vy = -14
                    self.jb.fx("stomp")
                elif not getattr(e, "frozen", 0):
                    self.hurt_player(getattr(e, "dmg", 25) or 25, e.x)
            sb = e.attack_box() if isinstance(e, Skeleton) else None
            if sb and sb.colliderect(p.hurtbox()):
                self.hurt_player(getattr(e, "dmg", 30), e.x)
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
                        self.shake = max(self.shake, 5)
                        self.jb.fx("boss_hit")
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
                bs.update(self.lv, p, self.boss_spawn)
                if self.ko_wait > 130:          # un solo round: il Guardiano e' caduto
                    self.next_part()
                    return
            else:
                bs.update(self.lv, p, self.boss_spawn)
                br = bs.rect
                abox, adm = p.attack_box()
                if abox and abox.colliderect(br) and bs.hit(adm):
                    self.score += 50; self.shake = max(self.shake, 5); self.jb.fx("boss_hit")
                if not bs.hidden and p.hurtbox().colliderect(br):
                    if p.vy > 0 and r.bottom - br.top < 50:
                        p.vy = -14
                        if bs.hit(8):
                            self.score += 50
                    else:
                        push = 1 if p.x < bs.x else -1
                        p.x -= push * 5
                        bs.x += push * 2
                bb = bs.attack_box()
                if bb and bb.colliderect(p.hurtbox()):
                    self.hurt_player(bs.move_dmg(), bs.x)
        self.skels = [k for k in self.skels if k.alive]
        self.crows = [c for c in self.crows if c.alive]
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
                self.new_game()
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
        if self.cable and k == pygame.K_e:
            self.cable.interact(p, self.lv)
            return
        if self.cable and self.cable.attached:
            if k == pygame.K_SPACE:
                self.cable.release(p)
                self.jb.fx("jump")
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
            if p.start_attack("throw"):
                self.jb.fx("sword")
        elif k == pygame.K_x:
            if p.start_attack("punch"):
                self.balls.append(Stone(p))
                self.jb.fx("throw")
        elif k == pygame.K_c:
            if p.start_attack("kick"):
                self.jb.fx("swing")
        elif k == pygame.K_v:
            self.luce_burst()

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

    def pill(self, x, y, w, h, frac, color, back=(18, 14, 12, 150)):
        """Barra sottile e arrotondata, con un filo di luce sul riempimento."""
        s = self.screen
        bg = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        pygame.draw.rect(bg, back, bg.get_rect(), border_radius=(h + 4) // 2)
        s.blit(bg, (x - 2, y - 2))
        fw = int(w * max(0, min(1, frac)))
        if fw > h // 2:
            pygame.draw.rect(s, color, (x, y, fw, h), border_radius=h // 2)
            hi = tuple(min(255, v + 45) for v in color)
            pygame.draw.line(s, hi, (x + h // 2, y + 2), (x + fw - h // 2, y + 2), 2)

    def draw_hud(self):
        """HUD essenziale: vita e Luce in alto a sinistra, punti piccoli a destra;
        la vita del Guardiano in basso, solo durante il duello."""
        s, p = self.screen, self.player
        if not hasattr(self, "hud_icon"):
            self.hud_icon = assets.load("emblema", 64, 64, by_height=True) if assets.has("emblema") else None
        x0, y0 = 48, 40
        if self.hud_icon:
            s.blit(self.hud_icon, (x0, y0 - 6))
            x0 += self.hud_icon.get_width() + 18
        hurt = p.hp <= 30
        self.pill(x0, y0, 360, 14, p.hp / PLAYER_HP, (205, 92, 72) if hurt else (238, 226, 204))
        # Luce: quattro tacche, una per unita' di raffica di Bianca
        for i in range(LUCE_MAX // LUCE_UNIT):
            fill = max(0, min(1, (p.albedo - i * LUCE_UNIT) / LUCE_UNIT))
            glow = (255, 214, 120) if fill >= 1 else (186, 150, 92)
            self.pill(x0 + i * 92, y0 + 28, 80, 10, fill, glow)
        for i in range(self.lives):
            pygame.draw.circle(s, (238, 226, 204), (x0 + 380 + i * 22, y0 + 7), 6)
        sc = f"{self.score}"
        fonts.draw_text(s, sc, W - 48 - fonts.text_width(sc, 4), y0 - 6, (238, 226, 204), scale=4)
        if self.boss:
            name = self.cfg["boss"].upper()
            bx, by, bw = W // 2 - 420, H - 70, 840
            fonts.draw_text(s, name, W // 2 - fonts.text_width(name, 3) // 2, by - 34, (238, 226, 204), scale=3)
            self.pill(bx, by, bw, 12, self.boss.hp / self.boss.max_hp, (196, 84, 60))
        if self.msg:
            t, n, col = self.msg
            fonts.draw_text(s, t, W // 2 - fonts.text_width(t, 12) // 2, 380, col, scale=12)

    def draw_world(self):
        """Cielo e fondali, a piena risoluzione dietro la vista del mondo."""
        s, cam, lv = self.screen, self.cam, self.lv
        # Il cielo non si ripete: e' appena piu' largo dello schermo e scorre
        # pochissimo, cosi' Saturno resta uno solo.
        sky = self.gfx.wide_sky(1, SKY_PAN)
        off = -min(SKY_PAN, int(cam * SKY_PAN / max(1, lv.cols * TILE - W, W)))
        s.blit(sky, (off, H - sky.get_height()))
        # Due piani di rocce; ognuno si ripete alternando una copia specchiata,
        # cosi' i bordi combaciano senza cuciture.
        for layer, speed in ((self.gfx.mirrored(self.gfx.background("hills")), 0.16),
                             (self.gfx.mirrored(self.gfx.background("hills", 2)), 0.42)):
            off = -(int(cam * speed) % layer.get_width())
            for x in range(off, W, layer.get_width()):
                s.blit(layer, (x, 0))

    def draw_tiles(self):
        """Terreno, laghi di metano, scale e portello: disegnati nella vista del mondo."""
        s, cam, lv = self.screen, self.cam, self.lv
        c0 = max(0, cam // TILE)
        cols = range(c0, min(lv.cols, c0 + VW // TILE + 3))
        for c in cols:
            if lv.g[GROUND][c] == ".":
                s.blit(self.gfx.titan_lake, (c * TILE - cam, GROUND * TILE))
                # riflessi che scorrono piano sulla superficie del metano
                y = GROUND * TILE + LAKE_LEVEL
                for i in range(3):
                    ph = (self.frame * (0.6 + i * 0.25) + c * 37 + i * 90) % 140
                    if ph < TILE:
                        pygame.draw.line(s, (236, 168, 96), (c * TILE - cam + ph, y + 3 + i * 7),
                                         (c * TILE - cam + min(TILE, ph + 22 - i * 6), y + 3 + i * 7), 2)
        s.blit(self.gfx.haze, (0, GROUND * TILE - 75))
        for c in cols:
            x = c * TILE - cam
            for r in range(ROWS):
                ch = lv.g[r][c]
                y = r * TILE
                if ch in self.gfx.tiles:
                    s.blit(self.gfx.titan_tile(ch, c, r), (x, y))
                    if ch in "#D":
                        self.rock_edges(s, lv, c, r, x, y)
                elif ch == "E":
                    s.blit(self.gfx.airlock, (x - TILE // 2, y + TILE - self.gfx.airlock.get_height()))

    def draw_drizzle(self, s):
        """Pioviggine di metano: gocce lente e pesanti, in diagonale, davanti a tutto."""
        if not hasattr(self, "drops"):
            rnd = random.Random(7)
            self.drops = [(rnd.randrange(W), rnd.randrange(H), rnd.uniform(3, 6)) for _ in range(140)]
        t = self.frame
        for x0, y0, v in self.drops:
            y = (y0 + t * v) % H
            x = (x0 - t * v * 0.35 - self.cam * 0.6) % W
            pygame.draw.line(s, (255, 208, 160), (x, y), (x - 4, y + 16), 1)

    def rock_edges(self, s, lv, c, r, x, y):
        """Contorno e ombra dove la roccia incontra l'aria: le pareti hanno un
        volume invece di sembrare blocchi di texture."""
        air = lambda cc, rr: lv.at(cc, rr) not in SOLID
        if air(c - 1, r):
            s.blit(self.gfx.rock_shade, (x, y))
            pygame.draw.line(s, (24, 14, 10), (x, y), (x, y + TILE), 4)
        if air(c + 1, r):
            s.blit(self.gfx.rock_shade_r, (x + TILE - self.gfx.rock_shade_r.get_width(), y))
            pygame.draw.line(s, (24, 14, 10), (x + TILE - 2, y), (x + TILE - 2, y + TILE), 4)
        if air(c, r - 1) and r < GROUND:
            pygame.draw.line(s, (24, 14, 10), (x, y), (x + TILE, y), 4)

    def draw_center(self, text, y, color=(245, 245, 245), scale=8):
        fonts.draw_text(self.screen, text, W // 2 - fonts.text_width(text, scale) // 2, y, color, scale)

    def draw_menu(self, y):
        for i, label in enumerate(self.menu_items()):
            color = (222, 201, 150) if i == self.menu_index else (190, 195, 210)
            self.draw_center(label, y + i * 64, color, 6)
            if i == self.menu_index:
                x = W // 2 - fonts.text_width(label, 6) // 2 - 36
                cy = y + i * 64 + 14
                pygame.draw.polygon(self.screen, color, [(x, cy - 10), (x + 14, cy), (x, cy + 10)])

    def draw_save_status(self):
        if self.save_error:
            self.draw_center("SALVATAGGIO NON DISPONIBILE", H - 40, (255, 120, 120), 4)

    def draw(self):
        s = self.screen
        if self.state == "title":
            s.blit(self.gfx.title_backdrop(), (0, 0))
            self.draw_center("NIGHTKNIGHT", 40, (238, 222, 190), 16)
            self.draw_center("DODICI SATELLITI, UN CAVALIERE", 205, (230, 205, 170), 4)
            self.draw_menu(760)
            self.draw_center(f"RECORD {self.hi:08d}", 965, (220, 205, 180), 3)
            self.draw_center("FRECCE MUOVI   SPAZIO SALTA   Z SPADA   X SASSO   C CALCIO   V BIANCA", 1010, (225, 210, 185), 3)
            self.draw_save_status()
            pygame.display.flip()
            return
        if self.state == "weapon_select":
            s.blit(self.gfx.title_backdrop(), (0, 0))
            shade = pygame.Surface((W, H), pygame.SRCALPHA); shade.fill((12, 6, 3, 150)); s.blit(shade, (0, 0))
            weapon = levels.weapon_cfg(self.weapon_i)
            titan = levels.cfg(0)
            self.draw_center("SCEGLI LA TUA ARMA", 150, (238, 222, 190), 9)
            self.draw_center(f"{self.weapon_i + 1} / 12", 290, (220, 205, 180), 4)
            self.draw_center(weapon["name"].upper(), 380, (250, 240, 225), 9)
            self.draw_center(weapon["description"].upper(), 490, (225, 210, 185), 4)
            self.draw_center("TITANO", 640, (238, 222, 190), 6)
            self.draw_center(f"GRAVITA {titan['gravity'].upper()}   ARIA {titan['air'].upper()}", 720, (225, 210, 185), 3)
            self.draw_center(titan["climate"].upper(), 760, (225, 210, 185), 3)
            self.draw_center("FRECCE SCEGLI   INVIO PARTE   ESC INDIETRO", 960, (225, 210, 185), 3)
            pygame.display.flip()
            return
        if self.state == "end":
            s.blit(self.gfx.title_backdrop(), (0, 0))
            shade = pygame.Surface((W, H), pygame.SRCALPHA); shade.fill((12, 6, 3, 150)); s.blit(shade, (0, 0))
            self.draw_center("TITANO E' LIBERO", 300, (238, 222, 190), 12)
            self.draw_center(f"{self.score}", 470, (250, 240, 225), 7)
            self.draw_center("GLI ALTRI UNDICI SATELLITI TI ASPETTANO", 620, (225, 210, 185), 4)
            self.draw_center("INVIO", 820, (225, 210, 185), 4)
            pygame.display.flip()
            return
        self.draw_world()
        screen = self.screen
        if getattr(self, "world_surf", None) is None:
            self.world_surf = pygame.Surface((VW, H), pygame.SRCALPHA)
        self.world_surf.fill((0, 0, 0, 0))
        self.screen = s = self.world_surf
        self.draw_tiles()
        cam = self.cam
        for spento in self.spenti:
            spento.draw(s, cam, self.gfx.spento_sleeping, self.gfx.spento_awake)
        for geyser in self.geysers:
            geyser.draw(s, cam)
        if self.cable:
            self.cable.draw(s, cam)
        if self.bianca:
            self.bianca.draw(s, self.gfx, cam)
        for k in self.skels:
            k.draw(s, self.gfx, cam)
        for cr in self.crows:
            cr.draw(s, self.gfx, cam)
        if self.boss:
            self.boss.draw(s, cam)
        for b in self.balls:
            b.draw(s, self.gfx, cam)
        p = self.player
        if self.state == "dead":
            # NightKnight a terra: la posa ferma distesa sul suolo
            fallen = pygame.transform.rotate(self.gfx.player["idle"][0], 90 * p.facing)
            s.blit(fallen, (p.rect.centerx - fallen.get_width() // 2 - cam, GROUND * TILE - fallen.get_height() + 10))
        else:
            p.draw(s, self.gfx, cam)
        for e in self.effects:
            fonts.draw_text(s, e.text, int(e.x) - cam, int(e.y), e.color, 4)
        for x, y, vx, vy, life, color in self.sparks:
            pygame.draw.line(s, color, (int(x) - cam, int(y)), (int(x - vx * 1.5) - cam, int(y - vy * 1.5)), 3)
        # la vista del mondo si ingrandisce sopra cielo e fondali
        self.screen = s = screen
        view = self.world_surf.subsurface((0, VIEW_Y, VW, VH))
        jolt = (random.randint(-self.shake, self.shake), random.randint(-self.shake, self.shake)) if self.shake else (0, 0)
        s.blit(pygame.transform.smoothscale(view, (W, H)), jolt)
        self.draw_drizzle(s)
        s.blit(self.gfx.vignette, (0, 0))
        self.draw_hud()
        if self.state == "card":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((12, 6, 3, 160)); s.blit(ov, (0, 0))
            if self.part == "arena":
                self.draw_center(self.cfg["boss"].upper(), 440, (238, 222, 190), 10)
            else:
                self.draw_center(self.cfg["name"].upper(), 400, (238, 222, 190), 14)
                self.draw_center(f"GRAVITA {self.cfg['gravity'].upper()}   ARIA {self.cfg['air'].upper()}", 590, (225, 210, 185), 3)
        elif self.state == "victory":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 190)); s.blit(ov, (0, 0))
            self.draw_center("VITTORIA", 260, (250, 210, 60), 14)
            self.draw_center(f"{self.cfg['boss'].upper()} E' CADUTO", 460, self.cfg["color"], 7)
            self.draw_center("PREMI INVIO", 820, (150, 160, 190), 5)
        elif self.state == "gameover":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 170)); s.blit(ov, (0, 0))
            self.draw_center("GAME OVER", 380, (230, 40, 40), 16)
            self.draw_center("INVIO: RIPROVA", 600, (238, 222, 190), 6)
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
