"""I 12 Cavalieri d'Oro: arma, mosse di kung fu e intelligenza del duello."""
import math
import os
import random

import pygame

import assets
import pixelart as px

TILE = 64
GROUND = 14
GRAVITY = 0.9
MAX_FALL = 22
W = 1920

# nome, arma, portata arma, colore, mosse
KNIGHTS = [
    ("Guardiano di Titano", "spada", 150, (200, 205, 225), ["combo", "slash", "flykick", "kick"]),
    ("Guardiano di Nix", "ascia", 140, (60, 60, 90), ["heavy", "throw", "sweep", "punch"]),
    ("Guardiano di Io", "martello", 130, (240, 110, 30), ["pound", "uppercut", "jumpsmash", "kick"]),
    ("Guardiano di Europa", "lancia", 230, (120, 200, 255), ["thrust", "spinkick", "dashthrust", "punch"]),
    ("Guardiano di Rea", "catene", 300, (90, 160, 60), ["whip", "spinkick", "combo", "sweep"]),
    ("Guardiano di Caronte", "arco", 90, (235, 235, 220), ["arrow", "backflip", "kick", "roundhouse"]),
    ("Guardiano di Ganimede", "doppie lame", 120, (250, 230, 90), ["combo", "slash", "teleport", "flykick"]),
    ("Guardiano di Fobos", "bastone", 190, (200, 40, 50), ["spin", "polevault", "sweep", "thrust"]),
    ("Guardiano di Nereide", "falce", 200, (110, 70, 200), ["slash", "heavy", "roundhouse", "teleport"]),
    ("Guardiano di Miranda", "mazza", 130, (140, 190, 50), ["dash", "pound", "combo", "heavy"]),
    ("Guardiano di Umbriel", "artigli", 100, (80, 80, 100), ["combo", "dive", "dash", "teleport"]),
    ("Oberon, il Re", "scettro", 160, (255, 200, 60), ["dashthrust", "teleport", "combo", "flykick", "uppercut", "slash"]),
]

# libreria delle mosse: total, finestra attiva (a, b), portata, altezza (offset y, h), danno extra, tipo, pose
MOVES = {
    "punch":      dict(total=24, act=(8, 14), reach=90, box=(40, 40), dmg=0, kind="melee", pose="punch"),
    "combo":      dict(total=48, act=[(8, 12), (22, 26), (36, 40)], reach=95, box=(40, 44), dmg=0, kind="melee", pose="punch", step=4),
    "kick":       dict(total=30, act=(10, 18), reach=125, box=(60, 50), dmg=4, kind="melee", pose="kick"),
    "sweep":      dict(total=30, act=(12, 20), reach=140, box=(130, 40), dmg=3, kind="melee", pose="kick"),
    "roundhouse": dict(total=36, act=(12, 22), reach=155, box=(30, 70), dmg=8, kind="melee", pose="kick"),
    "uppercut":   dict(total=34, act=(8, 18), reach=85, box=(-30, 90), dmg=8, kind="melee", pose="punch", vy=-15),
    "flykick":    dict(total=52, act=(6, 42), reach=110, box=(50, 50), dmg=8, kind="air", pose="kick", vy=-19, vx=9),
    "spinkick":   dict(total=42, act=(10, 32), reach=115, box=(50, 50), dmg=5, kind="melee", pose="kick", both=True),
    "slash":      dict(total=34, act=(14, 22), reach=None, box=(30, 110), dmg=10, kind="weapon", pose="attack"),
    "heavy":      dict(total=50, act=(26, 34), reach=None, box=(20, 130), dmg=18, kind="weapon", pose="attack"),
    "thrust":     dict(total=30, act=(10, 16), reach=None, box=(60, 30), dmg=10, kind="weapon", pose="attack", step=6),
    "dashthrust": dict(total=44, act=(14, 30), reach=None, box=(60, 30), dmg=12, kind="weapon", pose="attack", dash=14),
    "spin":       dict(total=54, act=(10, 46), reach=None, box=(50, 90), dmg=6, kind="weapon", pose="attack", both=True),
    "whip":       dict(total=40, act=(16, 24), reach=None, box=(50, 40), dmg=9, kind="weapon", pose="attack"),
    "pound":      dict(total=48, act=(20, 26), reach=120, box=(100, 60), dmg=10, kind="weapon", pose="attack", proj=("shock", 24)),
    "jumpsmash":  dict(total=70, act=(50, 56), reach=140, box=(100, 60), dmg=12, kind="air", pose="attack", vy=-22, vx=6, proj=("shock2", 50)),
    "throw":      dict(total=44, act=None, reach=None, box=None, dmg=10, kind="ranged", pose="special", proj=("axe", 16)),
    "arrow":      dict(total=36, act=None, reach=None, box=None, dmg=8, kind="ranged", pose="special", proj=("arrow", 14)),
    "wave":       dict(total=44, act=None, reach=None, box=None, dmg=14, kind="ranged", pose="special", proj=("wave", 18)),
    "dash":       dict(total=40, act=(10, 34), reach=None, box=(0, 0), dmg=8, kind="dash", pose="walk", dash=10),
    "teleport":   dict(total=34, act=None, reach=None, box=None, dmg=0, kind="move", pose="special"),
    "backflip":   dict(total=36, act=None, reach=None, box=None, dmg=0, kind="move", pose="jump", vy=-16, vx=-8),
    "polevault":  dict(total=56, act=(20, 44), reach=120, box=(60, 60), dmg=9, kind="air", pose="kick", vy=-21, vx=8),
    "dive":       dict(total=60, act=(24, 50), reach=110, box=(60, 60), dmg=10, kind="air", pose="attack", vy=-20, vx=10),
}
RANGED = {"throw", "arrow", "wave", "pound", "teleport", "dash", "dashthrust", "flykick", "polevault", "dive", "jumpsmash"}
GOLD = {"H": "Y", "A": "Y", "a": "y", "B": "y", "b": "k", "S": "S"}


def knight_cfg(i):
    name, weapon, reach, color, moves = KNIGHTS[i]
    return {"index": i, "num": i + 1, "name": name, "weapon": weapon, "reach": reach, "color": color,
            "moves": moves, "hp": 120 + 30 * i, "dmg": 10 + 2 * i, "speed": 2.2 + 0.2 * i, "cool": max(10, 36 - 2 * i)}


class Projectile:
    def __init__(self, kind, x, y, d, dmg, color, speed_bonus=0):
        self.kind, self.x, self.y, self.d, self.dmg, self.color = kind, float(x), float(y), d, dmg, color
        self.t = 0
        self.alive = True
        self.owner = "boss"
        self.origin = x
        if kind == "axe":
            self.w, self.h, self.vx = 70, 70, 14 * d
        elif kind == "arrow":
            self.w, self.h, self.vx = 90, 14, (22 + speed_bonus) * d
        elif kind == "wave":
            self.w, self.h, self.vx = 110, 150, (9 + speed_bonus) * d
        elif kind == "shock":
            self.w, self.h, self.vx = 60, 50, 9 * d
        else:  # shock2 in entrambe le direzioni: creata due volte
            self.w, self.h, self.vx = 60, 50, 9 * d
        self.rect = pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, lv, cam):
        self.t += 1
        if self.kind == "axe":
            if self.t > 40:
                self.vx = -14 * self.d
            self.x += self.vx
            if self.t > 90:
                self.alive = False
        else:
            self.x += self.vx
        self.rect = pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        r = self.rect
        if self.kind in ("shock", "shock2", "arrow", "wave") and lv.solid(r.centerx, r.centery):
            self.alive = False
        if r.right < cam - 200 or r.left > cam + W + 200:
            self.alive = False

    def draw(self, s, gfx, cam):
        r = self.rect.move(-cam, 0)
        c = self.color
        if self.kind == "axe":
            ang = self.t * 20 * self.d
            pts = []
            for a in (0, 90, 180, 270):
                rad = math.radians(a + ang)
                pts.append((r.centerx + math.cos(rad) * 32, r.centery + math.sin(rad) * 32))
            pygame.draw.polygon(s, (200, 200, 210), pts)
            pygame.draw.circle(s, (120, 80, 40), r.center, 10)
        elif self.kind == "arrow":
            pygame.draw.rect(s, (160, 110, 60), (r.x, r.centery - 3, r.w, 6))
            tip = (r.right, r.centery) if self.d > 0 else (r.left, r.centery)
            base = r.right - 18 if self.d > 0 else r.left + 18
            pygame.draw.polygon(s, (220, 220, 230), [tip, (base, r.centery - 9), (base, r.centery + 9)])
        elif self.kind == "wave":
            for i in range(3):
                pygame.draw.ellipse(s, c, r.inflate(-i * 26, -i * 30), 6)
        else:
            pygame.draw.polygon(s, c, [(r.left, r.bottom), (r.centerx, r.top + (self.t % 4) * 4), (r.right, r.bottom)])


class GoldKnight:
    w, h = 78, 198
    ox, oy = 33, 18

    def __init__(self, x, cfg, gfx):
        self.cfg = cfg
        self.x, self.y = float(x), float(GROUND * TILE - self.h)
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.alive = True
        self.facing = -1
        self.hp = self.max_hp = cfg["hp"]
        self.dmg = cfg["dmg"]
        self.speed = cfg["speed"]
        self.reach = cfg["reach"]
        self.move = None        # (nome, frame)
        self.cool = 60
        self.flash = 0
        self.invuln = 0
        self.frozen = 0
        self.ko_t = 0
        self.t = 0
        self.hidden = False
        self.imgs = gfx.knight(cfg["num"], cfg["color"])

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    # ---- fisica
    def physics(self, lv, gravity=True):
        self.x += self.vx
        r = self.rect
        if self.vx > 0 and (lv.solid(r.right - 1, r.centery) or lv.solid(r.right - 1, r.bottom - 2)):
            self.x = (r.right - 1) // TILE * TILE - self.w; self.vx = 0
        elif self.vx < 0 and (lv.solid(r.left, r.centery) or lv.solid(r.left, r.bottom - 2)):
            self.x = (r.left // TILE + 1) * TILE; self.vx = 0
        if gravity:
            self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.y += self.vy
        r = self.rect
        self.on_ground = False
        if self.vy > 0 and (lv.solid(r.left + 2, r.bottom) or lv.solid(r.right - 3, r.bottom)):
            self.y = r.bottom // TILE * TILE - self.h; self.vy = 0; self.on_ground = True
        elif self.vy < 0 and (lv.solid(r.left + 2, r.top) or lv.solid(r.right - 3, r.top)):
            self.y = (r.top // TILE + 1) * TILE; self.vy = 0
        self.x = max(TILE + 4, min(self.x, W - TILE - self.w - 4))

    # ---- colpi
    def active(self):
        if not self.move:
            return False
        name, f = self.move
        m = MOVES[name]
        act = m["act"]
        if not act:
            return False
        if isinstance(act, list):
            return any(a <= f <= b for a, b in act)
        return act[0] <= f <= act[1]

    def attack_box(self):
        if not self.active():
            return None
        name, f = self.move
        m = MOVES[name]
        if m["kind"] == "dash":
            return self.rect.inflate(30, 0)
        reach = m["reach"] if m["reach"] is not None else self.reach
        bw, bh = m["box"]
        r = self.rect
        if m.get("both"):
            return pygame.Rect(r.left - reach, r.top + 40, r.w + reach * 2, 100)
        top = r.top + 40 + bw if bw >= 0 else r.top
        x = r.right if self.facing > 0 else r.left - reach
        return pygame.Rect(x, top, reach, bh)

    def move_dmg(self):
        return self.dmg + (MOVES[self.move[0]]["dmg"] if self.move else 0)

    # ---- intelligenza
    def choose(self, dist, player):
        moves = self.cfg["moves"]
        far = dist > self.reach + 80
        ranged = [m for m in moves if m in RANGED]
        melee = [m for m in moves if m not in RANGED]
        if far:
            pool = ranged * 3 + melee if ranged else melee
        else:
            pool = melee * 3 + [m for m in ranged if m in ("dash", "flykick", "teleport", "backflip", "polevault", "dive")]
        if player.attack and random.random() < 0.3 and "backflip" in moves:
            return "backflip"
        return random.choice(pool)

    def update(self, lv, player, spawn):
        self.t += 1
        if self.hp <= 0:
            self.ko_t += 1
            self.vx = 0
            self.move = None
            self.physics(lv)
            return
        if self.invuln:
            self.invuln -= 1
        if self.flash:
            self.flash -= 1
        if self.frozen:
            self.frozen -= 1
            self.vx = 0
            self.physics(lv)
            return
        dx = player.rect.centerx - self.rect.centerx
        dist = abs(dx)
        if self.move:
            name, f = self.move
            m = MOVES[name]
            f += 1
            if m["kind"] == "move" and name == "teleport":
                if f == 12:
                    self.hidden = True
                if f == 22:
                    self.hidden = False
                    side = -1 if random.random() < 0.7 else 1      # di solito alle spalle
                    self.x = player.rect.centerx + side * player.facing * 170 - self.w / 2
                    self.x = max(TILE + 4, min(self.x, W - TILE - self.w - 4))
                    self.facing = 1 if player.rect.centerx > self.rect.centerx else -1
                self.vx = 0
            elif m["kind"] == "move" and name == "backflip":
                if f == 2:
                    self.vy = m["vy"]; self.vx = m["vx"] * self.facing; self.invuln = 24
            elif m["kind"] == "air":
                if f == 2:
                    self.vy = m["vy"]; self.vx = m["vx"] * self.facing
                    if name == "dive":
                        self.vx = 10 * self.facing
                if name == "dive" and f > 20 and not self.on_ground:
                    self.vy = max(self.vy, 12)
                if self.on_ground and f > 8:
                    self.vx *= 0.6
            elif m.get("dash") and m["act"] and m["act"][0] <= f <= m["act"][1]:
                self.vx = m["dash"] * self.facing
            elif m.get("step") and self.active():
                self.vx = m["step"] * self.facing
            else:
                self.vx = 0 if self.on_ground else self.vx
            if name == "uppercut" and f == m["act"][0]:
                self.vy = m["vy"]
            pj = m.get("proj")
            if pj and f == pj[1]:
                kind = pj[0]
                r = self.rect
                if kind == "shock2":
                    spawn(Projectile("shock", r.left - 60, r.bottom - 50, -1, self.move_dmg(), self.cfg["color"]))
                    spawn(Projectile("shock", r.right, r.bottom - 50, 1, self.move_dmg(), self.cfg["color"]))
                elif kind == "shock":
                    spawn(Projectile("shock", r.right if self.facing > 0 else r.left - 60, r.bottom - 50, self.facing, self.move_dmg(), self.cfg["color"]))
                elif kind == "arrow":
                    spawn(Projectile("arrow", r.right if self.facing > 0 else r.left - 90, r.top + 60, self.facing, self.move_dmg(), self.cfg["color"], self.cfg["index"] // 2))
                    if self.cfg["index"] >= 5:
                        spawn(Projectile("arrow", r.right if self.facing > 0 else r.left - 90, r.top + 110, self.facing, self.move_dmg(), self.cfg["color"], self.cfg["index"] // 2))
                elif kind == "axe":
                    spawn(Projectile("axe", r.right if self.facing > 0 else r.left - 70, r.top + 50, self.facing, self.move_dmg(), self.cfg["color"]))
                elif kind == "wave":
                    spawn(Projectile("wave", r.right if self.facing > 0 else r.left - 110, r.top + 10, self.facing, self.move_dmg(), self.cfg["color"], self.cfg["index"] // 3))
            self.move = (name, f) if f < m["total"] else None
            if self.move is None:
                self.cool = self.cfg["cool"] + random.randrange(0, 20)
        else:
            self.facing = 1 if dx > 0 else -1
            if self.cool > 0:
                self.cool -= 1
            want = self.reach - 30
            if dist > want:
                self.vx = self.speed * self.facing
            elif dist < want - 80 and random.random() < 0.02:
                self.vx = -self.speed * self.facing
            else:
                self.vx = 0
            if self.cool <= 0 and self.on_ground:
                self.move = (self.choose(dist, player), 0)
        self.physics(lv)

    def hit(self, dmg, power=None):
        if self.invuln or self.hp <= 0 or self.hidden:
            return False
        self.hp = max(0, self.hp - dmg)
        self.invuln = 16
        self.flash = 10
        if power == "ice":
            self.frozen = 50
        if self.move and MOVES[self.move[0]]["kind"] in ("melee", "weapon") and random.random() < 0.35:
            self.move = None          # interrotto
            self.cool = 20
        return True

    # ---- disegno
    def pose(self):
        if self.hp <= 0:
            return "ko"
        if self.flash and (self.flash // 3) % 2:
            return "hurt"
        if self.move:
            m = MOVES[self.move[0]]
            if not self.on_ground and m["pose"] not in ("kick", "attack"):
                return "jump"
            return m["pose"]
        if not self.on_ground:
            return "jump"
        if abs(self.vx) > 0.5:
            return "walk1" if (self.t // 8) % 2 else "walk2"
        return "idle"

    def draw(self, s, cam):
        if self.hidden:
            return
        i = 0 if self.facing > 0 else 1
        pose = self.pose()
        img = self.imgs.get(pose, self.imgs["idle"])[i]
        r = self.rect
        pos = (r.centerx - img.get_width() // 2 - cam, r.bottom - img.get_height())
        if pose == "ko" and "ko" not in self.imgs:
            img = pygame.transform.rotate(self.imgs["idle"][i], 90 if self.facing < 0 else -90)
            pos = (pos[0] - 50, pos[1] + 90)
        s.blit(img, pos)
        if self.flash and (self.flash // 2) % 2 and self.hp > 0:
            s.blit(self.imgs["white"][i], pos)
        if self.imgs.get("pixel") and self.move and MOVES[self.move[0]]["kind"] == "weapon" and self.active():
            self.draw_weapon(s, cam)
        if self.frozen:
            pygame.draw.rect(s, (150, 220, 255), (int(self.x) - cam, self.y, self.w, self.h), 5)

    def draw_weapon(self, s, cam):
        r = self.rect.move(-cam, 0)
        d = self.facing
        x0 = r.right if d > 0 else r.left
        y0 = r.top + 70
        wpn = self.cfg["weapon"]
        gold, steel = (250, 210, 60), (220, 220, 235)
        if wpn in ("spada", "doppie lame", "lancia", "bastone", "scettro"):
            pygame.draw.line(s, steel if wpn != "bastone" else (140, 90, 40), (x0, y0), (x0 + d * self.reach, y0 - 10), 10)
        elif wpn == "ascia":
            pygame.draw.line(s, (140, 90, 40), (x0, y0 + 20), (x0 + d * self.reach * 0.8, y0 - 40), 8)
            pygame.draw.polygon(s, steel, [(x0 + d * self.reach * 0.8, y0 - 80), (x0 + d * self.reach, y0 - 30), (x0 + d * self.reach * 0.6, y0 - 10)])
        elif wpn in ("martello", "mazza"):
            pygame.draw.line(s, (140, 90, 40), (x0, y0 + 20), (x0 + d * self.reach * 0.7, y0 - 30), 8)
            pygame.draw.rect(s, steel, (x0 + d * self.reach * 0.7 - 30, y0 - 70, 60, 60))
        elif wpn == "catene":
            for i in range(0, int(self.reach), 22):
                pygame.draw.circle(s, steel, (x0 + d * i, y0 + int(math.sin(i / 30 + self.t / 3) * 14)), 8, 3)
        elif wpn == "falce":
            pygame.draw.line(s, (140, 90, 40), (x0, y0 + 40), (x0 + d * self.reach * 0.6, y0 - 60), 8)
            pygame.draw.arc(s, steel, (x0 + d * self.reach * 0.6 - 80, y0 - 120, 160, 120), 0, math.pi, 10)
        elif wpn == "artigli":
            for k in range(3):
                pygame.draw.line(s, steel, (x0, y0 - 10 + k * 14), (x0 + d * self.reach, y0 - 30 + k * 18), 5)
        elif wpn == "arco":
            pygame.draw.arc(s, (140, 90, 40), (x0 - 40, y0 - 60, 80, 120), -math.pi / 2, math.pi / 2, 6)


def knight_images(gfx, num, color):
    """Immagini del cavaliere d'oro: boss{num}_*.png oppure il cavaliere pixel art in oro."""
    scale = 9
    bw, bh = 16 * scale, 24 * scale
    remap = dict(GOLD)
    d = {}
    real_any = any(assets.has(f"boss{num:02d}_{p}") for p in ("idle", "walk", "attack"))
    fallback_real = {"walk1": ["walk", "idle"], "walk2": ["idle", "walk"], "jump": ["jump", "walk", "idle"],
                     "punch": ["punch", "attack", "idle"], "kick": ["kick", "attack", "idle"],
                     "attack": ["attack", "idle"], "special": ["special", "attack", "idle"],
                     "hurt": ["hurt", "idle"], "ko": ["ko"], "idle": ["idle"]}
    pix = {"idle": ("idle", "idle"), "walk1": ("idle", "run1"), "walk2": ("idle", "run2"), "jump": ("jump", "jump"),
           "punch": ("punch", "idle"), "kick": ("idle", "kick"), "attack": ("throw", "idle"), "special": ("hado", "idle"),
           "hurt": ("idle", "idle")}
    # Le pose oltre all'idle vengono da una sola strip: stessa scala per tutte,
    # presa sulla figura tipica, cosi' il KO resta sdraiato e il salto sporge in alto.
    raw = {}
    if real_any:
        for name in ("walk", "jump", "punch", "kick", "attack", "special", "hurt", "ko"):
            if assets.has(f"boss{num:02d}_{name}"):
                raw[name] = pygame.image.load(os.path.join(assets.DIR, f"boss{num:02d}_{name}.png")).convert_alpha()
    heights = sorted(i.get_height() for i in raw.values())
    k = bh / heights[len(heights) // 2] if heights else 1
    for pose, chain in fallback_real.items():
        img = None
        if real_any:
            for name in chain:
                if name in raw:
                    r = raw[name]
                    img = pygame.transform.smoothscale(r, (max(1, int(r.get_width() * k)), max(1, int(r.get_height() * k))))
                    break
                if assets.has(f"boss{num:02d}_{name}"):
                    img = assets.load(f"boss{num:02d}_{name}", bw, bh, by_height=True)
                    break
        if img is None and pose in pix:
            torso, legs = pix[pose]
            rows = px.HEAD + px.TORSO[torso] + px.LEGS[legs]
            base = px.sprite(rows, remap, scale=scale)
            img = base.copy()
            pa = pygame.PixelArray(img)
            pa.replace(px.PAL["R"], color)
            del pa
        if img is not None:
            d[pose] = (img, assets.flip(img))
    d["pixel"] = not real_any
    w = d["idle"][0].copy(); w.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
    w2 = d["idle"][1].copy(); w2.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
    d["white"] = (w, w2)
    return d
