#!/usr/bin/env python3
"""Goblin - platform arcade ispirato a Ghosts 'n Goblins. Linux, 1920x1080, 60 fps."""
import random
import sys

import pygame

W, H = 1920, 1080
FPS = 60
GROUND_Y = 920
LEVEL_W = 7200
GRAVITY = 0.9
RUN = 7
JUMP = -20
LANCE_SPEED = 18
MAX_LANCES = 3
ZOMBIE_SPEED = 2.2
ZOMBIE_RISE = 45
ZOMBIE_LIFE = 9 * FPS
SPAWN_EVERY = 75
INVULN = 100
START_LIVES = 3

# terreno: segmenti (x0, x1); tra un segmento e l'altro c'e' un fosso
GROUND = [(0, 2300), (2600, 4300), (4650, LEVEL_W)]
# piattaforme sospese (x, y, larghezza) - si attraversano dal basso
PLATFORMS = [
    (1500, 720, 300), (1900, 600, 260),
    (2280, 760, 200), (2440, 640, 240),   # sopra il primo fosso
    (3100, 700, 300), (3500, 560, 260), (3900, 700, 300),
    (4300, 700, 200), (4520, 620, 200),   # sopra il secondo fosso
    (5200, 720, 300), (5600, 600, 300), (6000, 720, 300),
]
GOAL_X = LEVEL_W - 220

COL_SKY_TOP = (12, 8, 40)
COL_SKY_BOT = (60, 30, 90)
COL_GROUND = (70, 45, 30)
COL_GRASS = (40, 90, 40)
COL_STONE = (110, 110, 120)


def on_ground_segment(x):
    return any(a <= x <= b for a, b in GROUND)


def platform_rects():
    return [pygame.Rect(x, y, w, 24) for x, y, w in PLATFORMS]


class Lance:
    def __init__(self, x, y, d):
        self.rect = pygame.Rect(x, y, 70, 8)
        self.vx = LANCE_SPEED * d
        self.alive = True

    def update(self, cam_x):
        self.rect.x += self.vx
        if self.rect.right < cam_x - 50 or self.rect.left > cam_x + W + 50:
            self.alive = False

    def draw(self, s, cam_x):
        r = self.rect.move(-cam_x, 0)
        pygame.draw.rect(s, (230, 200, 90), r)
        tip = (r.right, r.centery) if self.vx > 0 else (r.left, r.centery)
        base = r.right - 16 if self.vx > 0 else r.left + 16
        pygame.draw.polygon(s, (240, 240, 240),
                            [tip, (base, r.top - 4), (base, r.bottom + 4)])


class Zombie:
    W_, H_ = 56, 96

    def __init__(self, x):
        self.x = float(x)
        self.rise = 0
        self.age = 0
        self.alive = True
        self.dir = -1

    @property
    def rect(self):
        h = int(self.H_ * min(1.0, self.rise / ZOMBIE_RISE))
        return pygame.Rect(int(self.x), GROUND_Y - h, self.W_, h)

    def update(self, player_x):
        self.age += 1
        if self.rise < ZOMBIE_RISE:
            self.rise += 1
            return
        if self.age > ZOMBIE_LIFE:
            self.rise -= 1  # torna sotto terra
            if self.rise <= 0:
                self.alive = False
            return
        self.dir = 1 if player_x > self.x else -1
        nx = self.x + ZOMBIE_SPEED * self.dir
        if on_ground_segment(nx) and on_ground_segment(nx + self.W_):
            self.x = nx

    def draw(self, s, cam_x):
        r = self.rect.move(-cam_x, 0)
        if r.height <= 0:
            return
        # terra smossa
        pygame.draw.ellipse(s, (50, 32, 20), (r.x - 12, GROUND_Y - 10, r.w + 24, 20))
        s.set_clip(pygame.Rect(r.x - 20, 0, r.w + 40, GROUND_Y))
        top = GROUND_Y - r.height
        body = pygame.Rect(r.x + 10, top + 30, 36, 40)
        pygame.draw.rect(s, (70, 110, 60), body)
        head = pygame.Rect(r.x + 14, top, 28, 30)
        pygame.draw.rect(s, (120, 160, 100), head)
        pygame.draw.rect(s, (200, 40, 40), (head.x + 6, head.y + 10, 5, 5))
        pygame.draw.rect(s, (200, 40, 40), (head.x + 17, head.y + 10, 5, 5))
        # braccia tese
        ay = top + 36
        pygame.draw.rect(s, (120, 160, 100), (r.x - 6 if self.dir < 0 else r.right - 10, ay, 16, 10))
        # gambe
        step = (self.age // 8) % 2
        pygame.draw.rect(s, (50, 70, 45), (r.x + 12, top + 70, 12, 26 + step * 2))
        pygame.draw.rect(s, (50, 70, 45), (r.x + 32, top + 70, 12, 28 - step * 2))
        s.set_clip(None)


class Player:
    W_, H_ = 54, 92

    def __init__(self):
        self.reset()

    def reset(self):
        self.x, self.y = 120.0, float(GROUND_Y - self.H_)
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.facing = 1
        self.armor = True
        self.invuln = 0
        self.frame = 0
        self.throw_t = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.W_, self.H_)

    def update(self, keys, plats):
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        self.vx = RUN * ((right > 0) - (left > 0))
        if self.vx:
            self.facing = 1 if self.vx > 0 else -1
            self.frame += 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy = JUMP
            self.on_ground = False
        self.vy = min(self.vy + GRAVITY, 24)
        self.x = max(0.0, min(self.x + self.vx, LEVEL_W - self.W_))
        old_bottom = self.rect.bottom
        self.y += self.vy
        r = self.rect
        self.on_ground = False
        if self.vy >= 0:
            if r.bottom >= GROUND_Y and (on_ground_segment(r.left + 10) or on_ground_segment(r.right - 10)):
                self.y = GROUND_Y - self.H_
                self.vy = 0
                self.on_ground = True
            else:
                for p in plats:
                    if r.colliderect(p) and old_bottom <= p.top + 1:
                        self.y = p.top - self.H_
                        self.vy = 0
                        self.on_ground = True
                        break
        if self.invuln:
            self.invuln -= 1
        if self.throw_t:
            self.throw_t -= 1

    def draw(self, s, cam_x):
        if self.invuln and (self.invuln // 4) % 2:
            return
        r = self.rect.move(-cam_x, 0)
        f = self.facing
        step = (self.frame // 6) % 2 if self.vx else 0
        skin, white = (235, 190, 150), (240, 240, 240)
        if self.armor:
            torso, legc, arm = (200, 200, 215), (150, 150, 170), (200, 200, 215)
        else:
            torso, legc, arm = skin, skin, skin
        # gambe
        pygame.draw.rect(s, legc, (r.x + 10, r.y + 60, 14, 32 - step * 6))
        pygame.draw.rect(s, legc, (r.x + 30, r.y + 60, 14, 26 + step * 6))
        if not self.armor:
            pygame.draw.rect(s, white, (r.x + 8, r.y + 56, 38, 14))  # mutande
        # busto
        pygame.draw.rect(s, torso, (r.x + 8, r.y + 26, 38, 36))
        if self.armor:
            pygame.draw.rect(s, (160, 160, 180), (r.x + 8, r.y + 26, 38, 36), 3)
        # braccio (in avanti quando lancia)
        ax = r.x + 40 if f > 0 else r.x - 6
        ay = r.y + 30 if self.throw_t else r.y + 36
        pygame.draw.rect(s, arm, (ax, ay, 20, 10))
        # testa / elmo
        head = pygame.Rect(r.x + 12, r.y, 30, 28)
        if self.armor:
            pygame.draw.rect(s, (210, 210, 225), head)
            pygame.draw.rect(s, (40, 40, 60), (head.x + (18 if f > 0 else 4), head.y + 10, 8, 6))
            pygame.draw.polygon(s, (220, 40, 40), [(head.centerx, head.y), (head.centerx - 6 * f, head.y - 22),
                                                   (head.centerx - 14 * f, head.y - 6)])
        else:
            pygame.draw.rect(s, skin, head)
            pygame.draw.rect(s, (170, 110, 50), (head.x, head.y - 4, 30, 10))  # capelli
            pygame.draw.rect(s, (30, 30, 30), (head.x + (18 if f > 0 else 6), head.y + 10, 5, 5))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.SCALED)
        pygame.display.set_caption("Goblin")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 36, bold=True)
        self.big = pygame.font.SysFont("monospace", 96, bold=True)
        self.plats = platform_rects()
        self.bg = self.make_background()
        self.deco = self.make_deco()
        self.player = Player()
        self.new_game()

    def new_game(self):
        self.player.reset()
        self.lances, self.zombies = [], []
        self.score, self.lives = 0, START_LIVES
        self.spawn_t = SPAWN_EVERY
        self.state, self.state_t = "play", 0
        self.cam_x = 0

    def make_background(self):
        bg = pygame.Surface((W, H))
        for y in range(H):
            t = y / H
            c = [int(COL_SKY_TOP[i] + (COL_SKY_BOT[i] - COL_SKY_TOP[i]) * t) for i in range(3)]
            pygame.draw.line(bg, c, (0, y), (W, y))
        pygame.draw.circle(bg, (240, 235, 200), (1500, 180), 70)
        pygame.draw.circle(bg, tuple(int(v) for v in (COL_SKY_TOP[0] * 1.5, COL_SKY_TOP[1] * 1.5, COL_SKY_TOP[2] * 1.3)), (1530, 160), 60)
        rnd = random.Random(3)
        for _ in range(120):
            x, y = rnd.randrange(W), rnd.randrange(0, 600)
            bg.set_at((x, y), (200, 200, 220))
        return bg

    def make_deco(self):
        rnd = random.Random(7)
        deco = []
        for a, b in GROUND:
            x = a + 60
            while x < b - 80:
                kind = rnd.choice(["tomb", "tomb", "cross", "tree"])
                deco.append((kind, x))
                x += rnd.randrange(160, 360)
        return deco

    def draw_world(self):
        s, cx = self.screen, self.cam_x
        s.blit(self.bg, (0, 0))
        # colline lontane (parallasse)
        for i in range(-1, 8):
            hx = i * 700 - int(cx * 0.3) % 700
            pygame.draw.ellipse(s, (30, 22, 55), (hx, 700, 900, 400))
        # decorazioni
        for kind, x in self.deco:
            dx = x - cx
            if dx < -200 or dx > W + 200:
                continue
            if kind == "tomb":
                pygame.draw.rect(s, COL_STONE, (dx, GROUND_Y - 70, 50, 70))
                pygame.draw.ellipse(s, COL_STONE, (dx, GROUND_Y - 95, 50, 50))
                pygame.draw.line(s, (80, 80, 90), (dx + 12, GROUND_Y - 60), (dx + 38, GROUND_Y - 60), 3)
            elif kind == "cross":
                pygame.draw.rect(s, COL_STONE, (dx + 20, GROUND_Y - 110, 14, 110))
                pygame.draw.rect(s, COL_STONE, (dx, GROUND_Y - 85, 54, 14))
            else:
                pygame.draw.rect(s, (40, 28, 20), (dx + 20, GROUND_Y - 200, 22, 200))
                pygame.draw.line(s, (40, 28, 20), (dx + 30, GROUND_Y - 160), (dx - 30, GROUND_Y - 230), 10)
                pygame.draw.line(s, (40, 28, 20), (dx + 32, GROUND_Y - 190), (dx + 90, GROUND_Y - 250), 10)
        # terreno
        for a, b in GROUND:
            r = pygame.Rect(a - cx, GROUND_Y, b - a, H - GROUND_Y)
            pygame.draw.rect(s, COL_GROUND, r)
            pygame.draw.rect(s, COL_GRASS, (r.x, r.y, r.w, 14))
        # piattaforme
        for p in self.plats:
            r = p.move(-cx, 0)
            pygame.draw.rect(s, COL_STONE, r)
            pygame.draw.rect(s, (70, 70, 80), r, 3)
        # traguardo
        gx = GOAL_X - cx
        pygame.draw.rect(s, (120, 90, 50), (gx, GROUND_Y - 260, 12, 260))
        pygame.draw.polygon(s, (220, 40, 40), [(gx + 12, GROUND_Y - 260), (gx + 110, GROUND_Y - 230), (gx + 12, GROUND_Y - 200)])

    def draw_hud(self):
        s = self.screen
        s.blit(self.font.render(f"PUNTI {self.score:06d}", True, (255, 255, 255)), (40, 30))
        for i in range(self.lives):
            pygame.draw.rect(s, (210, 210, 225), (40 + i * 40, 90, 24, 30))
        txt = "ARMATURA" if self.player.armor else "MUTANDE!"
        s.blit(self.font.render(txt, True, (200, 200, 220) if self.player.armor else (255, 120, 120)), (W - 260, 30))

    def center_text(self, text, y, font=None, color=(255, 255, 255)):
        img = (font or self.big).render(text, True, color)
        self.screen.blit(img, img.get_rect(center=(W // 2, y)))

    def hit_player(self):
        p = self.player
        if p.invuln or self.state != "play":
            return
        if p.armor:
            p.armor = False
            p.invuln = INVULN
            p.vy = -10
        else:
            self.state, self.state_t = "dead", 0

    def update(self):
        p = self.player
        if self.state == "play":
            keys = pygame.key.get_pressed()
            p.update(keys, self.plats)
            if p.y > H + 100:
                self.state, self.state_t = "dead", 0
            if p.x + p.W_ > GOAL_X:
                self.state, self.state_t = "win", 0
            # zombie
            self.spawn_t -= 1
            if self.spawn_t <= 0 and len(self.zombies) < 6:
                self.spawn_t = SPAWN_EVERY
                for _ in range(10):
                    x = p.x + random.choice([-1, 1]) * random.randrange(350, 900)
                    if self.cam_x - 60 < x < self.cam_x + W and on_ground_segment(x) and on_ground_segment(x + Zombie.W_):
                        self.zombies.append(Zombie(x))
                        break
            for z in self.zombies:
                z.update(p.x)
            for l in self.lances:
                l.update(self.cam_x)
            for z in self.zombies:
                if z.rise >= ZOMBIE_RISE // 2:
                    for l in self.lances:
                        if l.alive and z.alive and l.rect.colliderect(z.rect):
                            l.alive = z.alive = False
                            self.score += 100
                    if z.alive and z.rect.colliderect(p.rect.inflate(-16, -10)):
                        self.hit_player()
            self.zombies = [z for z in self.zombies if z.alive]
            self.lances = [l for l in self.lances if l.alive]
        elif self.state == "dead":
            self.state_t += 1
            if self.state_t > 90:
                self.lives -= 1
                if self.lives <= 0:
                    self.state = "gameover"
                else:
                    p.reset()
                    self.lances, self.zombies = [], []
                    self.state = "play"
        self.cam_x = int(max(0, min(p.x + p.W_ / 2 - W / 2, LEVEL_W - W)))

    def throw(self):
        p = self.player
        if self.state == "play" and len(self.lances) < MAX_LANCES:
            y = p.rect.y + 34
            x = p.rect.right if p.facing > 0 else p.rect.left - 70
            self.lances.append(Lance(x, y, p.facing))
            p.throw_t = 10

    def draw(self):
        self.draw_world()
        for z in self.zombies:
            z.draw(self.screen, self.cam_x)
        for l in self.lances:
            l.draw(self.screen, self.cam_x)
        if self.state == "dead":
            r = self.player.rect.move(-self.cam_x, 0)
            pygame.draw.ellipse(self.screen, (230, 230, 220), (r.x, r.bottom - 24, r.w, 24))  # ossa
            pygame.draw.circle(self.screen, (230, 230, 220), (r.centerx, r.bottom - 34), 14)
        else:
            self.player.draw(self.screen, self.cam_x)
        self.draw_hud()
        if self.state == "gameover":
            self.center_text("GAME OVER", H // 2 - 40)
            self.center_text("INVIO per ricominciare - ESC per uscire", H // 2 + 60, self.font)
        elif self.state == "win":
            self.center_text("LIVELLO COMPLETATO", H // 2 - 40, color=(255, 220, 80))
            self.center_text(f"PUNTI {self.score}   -   INVIO per rigiocare", H // 2 + 60, self.font)
        pygame.display.flip()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        return
                    if e.key in (pygame.K_x, pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_z):
                        self.throw()
                    if e.key == pygame.K_RETURN and self.state in ("gameover", "win"):
                        self.new_game()
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    Game().run()
    pygame.quit()
    sys.exit()
