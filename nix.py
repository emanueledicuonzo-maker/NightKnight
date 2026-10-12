"""Insidie di Nix: gli ossari che respirano la nube ossea, le sirene psichiche
che scambiano destra e sinistra, gli orli dei crepacci (STORY.md, "Le quattro
insidie")."""
import math

import pygame

from titan import ground_shadow, SINK

# Disegni caricati dal gioco (goblin.Gfx.load_world): "ossuary" (quieto, che
# sfiata), "siren" (spenta, accesa), "crevasse" (orlo sinistro, orlo destro).
ART = {}
TILE = 64


class Ossuary:
    """Una bocca di roccia piena di ossa di coloni: a ciclo respira fuori una nube
    di polvere d'ossa, larga 6 tessere e alta 5, che a gravita' bassa resta
    sospesa e poi ricade piano. Dentro si vede poco, si perde vita e l'ossigeno
    scende al doppio."""
    REST, WARNING, CLOUD = 360, 120, 480          # 6 s, 2 s, 8 s
    PERIOD = REST + WARNING + CLOUD
    W, H = 6 * TILE, 5 * TILE

    def __init__(self, x, floor):
        self.x, self.floor = x, floor
        self.age = 0
        self.started = False
        self.previous_phase = "rest"

    @property
    def phase(self):
        tick = self.age % self.PERIOD
        if tick < self.REST:
            return "rest"
        return "warning" if tick < self.REST + self.WARNING else "cloud"

    @property
    def density(self):
        """Quanto e' fitta la nube, 0-1: sale in fretta, poi ricade piano."""
        tick = self.age % self.PERIOD - self.REST - self.WARNING
        if tick < 0:
            return 0.0
        rise = min(1.0, tick / 60)
        fall = max(0.0, 1 - max(0, tick - self.CLOUD + 150) / 150)
        return rise * fall

    @property
    def cloud_rect(self):
        return pygame.Rect(self.x - self.W // 2, self.floor - self.H, self.W, self.H)

    def update(self, player):
        """True se 9T9T e' dentro la nube."""
        self.previous_phase = self.phase
        if abs(player.rect.centerx - self.x) < 900:
            self.started = True
        if self.started:
            self.age += 1
        return self.density > 0.25 and self.cloud_rect.colliderect(player.rect)

    def draw(self, screen, cam):
        x, f = int(self.x - cam), self.floor
        if not -400 < x < screen.get_width() + 400:
            return
        if "ossuary" in ART:
            img = ART["ossuary"][0 if self.phase == "rest" else 1]
            ground_shadow(screen, x, f, img.get_width() * 0.9)
            screen.blit(img, (x - img.get_width() // 2, f - img.get_height() + SINK))
        else:
            pygame.draw.rect(screen, (60, 56, 52), (x - 60, f - 150, 120, 150))

    def draw_cloud(self, screen, cam):
        """La nube davanti a tutto: sbuffi bianchi che salgono e restano."""
        k = self.density
        x, f = int(self.x - cam), self.floor
        if k <= 0 or not -400 < x < screen.get_width() + 400:
            return
        cloud = pygame.Surface((self.W + 120, self.H + 60), pygame.SRCALPHA)
        for i in range(70):
            life = ((self.age * (0.5 + (i % 7) * 0.08) + i * 31) % 120) / 120
            cx = cloud.get_width() / 2 + math.sin(i * 2.1 + self.age * 0.01) * (40 + life * self.W / 2.2)
            cy = cloud.get_height() - 30 - life * self.H * 0.9
            rad = int(18 + life * 42 + (i % 3) * 6)
            pygame.draw.circle(cloud, (232, 226, 214, int(70 * k * (1 - life * 0.5))), (int(cx), int(cy)), rad)
        screen.blit(cloud, (x - cloud.get_width() // 2, f - cloud.get_height() + 20))


class Siren:
    """Il corno di un ripetitore ancora alimentato: pulsa 3 s ogni 8 e, fino a 10
    tessere, scambia destra e sinistra. Tre colpi la spengono per sempre, e nel
    basamento c'e' un prigioniero."""
    ON, OFF = 180, 300
    PERIOD = ON + OFF
    RANGE = 10 * TILE
    HP = 3

    def __init__(self, x, floor):
        self.x, self.floor = x, floor
        self.age = 0
        self.hp = self.HP
        self.flash = 0
        self.freed = False          # il prigioniero del basamento e' gia' stato messo in scena

    @property
    def dead(self):
        return self.hp <= 0

    @property
    def pulsing(self):
        return not self.dead and self.age % self.PERIOD < self.ON

    @property
    def rect(self):
        return pygame.Rect(self.x - 70, self.floor - 190, 140, 190)

    def hit(self):
        if self.dead:
            return False
        self.hp -= 1
        self.flash = 10
        return True

    def update(self, player):
        """True se 9T9T e' nel raggio mentre pulsa: i comandi si girano."""
        self.age += 1
        self.flash = max(0, self.flash - 1)
        return self.pulsing and abs(player.rect.centerx - self.x) < self.RANGE

    def draw(self, screen, cam):
        x, f = int(self.x - cam), self.floor
        if not -self.RANGE - 100 < x < screen.get_width() + self.RANGE + 100:
            return
        if "siren" in ART:
            img = ART["siren"][1 if self.pulsing else 0]
            ground_shadow(screen, x, f, img.get_width() * 0.9)
            screen.blit(img, (x - img.get_width() // 2, f - img.get_height() + SINK))
            if self.flash:
                white = img.copy()
                white.fill((255, 255, 255, int(160 * self.flash / 10)), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(white, (x - img.get_width() // 2, f - img.get_height() + SINK))
        else:
            pygame.draw.rect(screen, (90, 80, 110), (x - 30, f - 150, 60, 150))
        if not self.pulsing:
            return
        # gli anelli viola che corrono via dal corno, a terra, da tutte e due le parti
        t = self.age % self.PERIOD
        ring = pygame.Surface((self.RANGE * 2 + 40, 160), pygame.SRCALPHA)
        for i in range(3):
            k = ((t / 60.0) + i / 3) % 1
            r = int(k * self.RANGE)
            a = int(150 * (1 - k))
            pygame.draw.ellipse(ring, (190, 120, 255, a), (ring.get_width() // 2 - r, 80 - r // 8, r * 2, r // 4), 4)
        screen.blit(ring, (x - ring.get_width() // 2, f - 80 - 55))


def draw_crevasse_edges(screen, cam, crevasses, ground_y):
    """Gli orli di neve e ghiaccio ai due lati di ogni crepaccio."""
    if "crevasse" not in ART:
        return
    left, right = ART["crevasse"]
    w = screen.get_width()
    for c0, c1 in crevasses:
        x0, x1 = c0 * TILE - cam, c1 * TILE - cam
        if x1 < -left.get_width() or x0 > w + right.get_width():
            continue
        screen.blit(left, (x0 - left.get_width() + 10, ground_y - 26))
        screen.blit(right, (x1 - 10, ground_y - 26))


class Grating:
    """Una griglia di servizio appesa sopra un crepaccio: appena ci si mette il
    piede trema, dopo mezzo secondo si stacca e cade piano nel buio; torna al
    suo posto dopo quattro secondi. Nella griglia del livello e' fatta di
    tessere "G", che spariscono quando cade."""
    SHAKE, FALL, BACK = 30, 150, 240

    def __init__(self, col, row, width):
        self.col, self.row, self.width = col, row, width
        self.x0, self.x1, self.y = col * TILE, (col + width) * TILE, row * TILE
        self.state, self.t = "solid", 0

    def on_it(self, player):
        r = player.rect
        return player.on_ground and abs(r.bottom - self.y) < 4 and r.right > self.x0 and r.left < self.x1

    def set_tiles(self, lv, ch):
        for c in range(self.col, self.col + self.width):
            lv.g[self.row][c] = ch

    def update(self, lv, player):
        """True nel fotogramma in cui si stacca (per il suono)."""
        self.t += 1
        if self.state == "solid":
            if self.on_it(player):
                self.state, self.t = "shake", 0
        elif self.state == "shake":
            if self.t > self.SHAKE:
                self.state, self.t = "fall", 0
                self.set_tiles(lv, ".")
                return True
        elif self.state == "fall":
            if self.t > self.FALL:
                self.state, self.t = "gone", 0
        elif self.t > self.BACK:
            r = player.rect
            if not (r.right > self.x0 - 20 and r.left < self.x1 + 20 and abs(r.bottom - self.y) < 2 * TILE):
                self.state, self.t = "solid", 0
                self.set_tiles(lv, "G")
        return False

    def draw(self, screen, cam):
        if self.state == "gone" or "grating" not in ART:
            return
        img = ART["grating"]
        x = self.x0 - cam
        if not -img.get_width() < x < screen.get_width():
            return
        y = self.y - img.get_height() + 22      # il piano della griglia e' il bordo della tessera
        if self.state == "shake":
            x += (self.t % 3) - 1
            y += (self.t // 2 % 2)
        elif self.state == "fall":
            y += int(self.t * self.t * 0.08)    # cade piano: gravita' di Nix
            if self.t > 60:
                img = img.copy()
                img.set_alpha(max(0, 255 - (self.t - 60) * 3))
        screen.blit(img, (x, y))
