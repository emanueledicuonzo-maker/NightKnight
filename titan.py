"""Primo incontro di Titano: criogeyser immaginari e Spenti da liberare."""
import math

import pygame


class Geyser:
    # Un ciclo inizia sempre con un lungo riposo: nessun getto a sorpresa.
    REST, WARNING, ERUPTION = 180, 90, 90
    PERIOD = REST + WARNING + ERUPTION

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
        return "warning" if tick < self.REST + self.WARNING else "eruption"

    @property
    def hitbox(self):
        return pygame.Rect(self.x - 32, self.floor - 310, 64, 310)

    def update(self, player):
        self.previous_phase = self.phase
        if abs(player.rect.centerx - self.x) < 750:
            self.started = True
        if self.started:
            self.age += 1
        return self.phase == "eruption" and self.hitbox.colliderect(player.hurtbox())

    def draw(self, screen, cam):
        x, floor = int(self.x - cam), self.floor
        if not -120 < x < screen.get_width() + 120:
            return
        phase = self.phase
        pygame.draw.ellipse(screen, (47, 27, 18), (x - 51, floor - 12, 102, 24))
        color = (239, 170, 78) if phase != "rest" else (126, 76, 39)
        pygame.draw.lines(screen, color, False,
                          [(x-43, floor-3), (x-19, floor-9), (x, floor-2),
                           (x+22, floor-10), (x+42, floor-4)], 3)
        if phase == "rest":
            return
        plume = pygame.Surface((200, 370), pygame.SRCALPHA)
        active = phase == "eruption"
        count, height = (90, 330) if active else (18, 80)
        for i in range(count):
            progress = ((self.age * (8 if active else 2) + i * 29) % height) / height
            spread = 7 + progress * (36 if active else 22)
            px = 100 + math.sin(i * 2.4 + self.age * .045) * spread
            py = 352 - progress * height
            radius = int(5 + progress * (22 if active else 10))
            alpha = int((110 if active else 55) * (1 - progress))
            for factor, strength in ((1.7, .15), (1.3, .35), (1, .65), (.65, 1)):
                pygame.draw.circle(plume, (239, 201, 143, int(alpha * strength)),
                                   (int(px), int(py)), max(1, int(radius * factor)))
        if active:
            for i in range(24):
                travel = (self.age * 11 + i * 41) % 290
                dx = math.sin(i * 4.1) * (8 + travel * .08)
                pygame.draw.line(plume, (255, 227, 177, 175),
                                 (int(100+dx), 350-travel), (int(100+dx), 344-travel), 2)
        screen.blit(plume, (x - 100, floor - 352))


class Spento:
    def __init__(self, x, floor):
        self.x, self.floor = x, floor
        self.liberated = False
        self.glow = 0

    def update(self, player):
        newly_liberated = (not self.liberated
                           and abs(player.rect.centerx - self.x) < 135
                           and abs(player.rect.bottom - self.floor) < 200)
        if newly_liberated:
            self.liberated = True
        if self.liberated:
            self.glow = min(60, self.glow + 1)
        return newly_liberated

    def draw(self, screen, cam, sleeping, awake):
        x = int(self.x - cam)
        if not -100 < x < screen.get_width() + 100:
            return
        img = awake if self.liberated else sleeping
        if self.liberated:
            light = pygame.Surface((180, 240), pygame.SRCALPHA)
            for radius in range(85, 10, -10):
                pygame.draw.ellipse(light, (255, 186, 79, int(20 * self.glow / 60)),
                                    (90-radius, 120-radius, radius*2, radius*2))
            screen.blit(light, (x-90, self.floor-220))
        screen.blit(img, (x-img.get_width()//2, self.floor-img.get_height()))


class OxygenStation:
    """Colonnina d'ossigeno della colonia: vicino si respira e la riserva risale."""
    RANGE = 170

    def __init__(self, x, floor):
        self.x, self.floor = x, floor
        self.t = 0

    def near(self, player):
        return abs(player.rect.centerx - self.x) < self.RANGE and abs(player.rect.bottom - self.floor) < 120

    def draw(self, screen, cam, active, img):
        self.t += 1
        x, f = int(self.x - cam), self.floor
        if not -200 < x < screen.get_width() + 200:
            return
        screen.blit(img, (x - img.get_width() // 2, f - img.get_height()))
        if active:
            for i in range(4):                      # sbuffi d'aria mentre si ricarica
                k = ((self.t * 3 + i * 25) % 100) / 100
                pygame.draw.circle(screen, (220, 240, 245), (x + 30 + int(14 * math.sin(i + self.t / 9)),
                                   int(f - img.get_height() * 0.45 - k * 70)), int(3 + k * 7), 2)


class GasVent:
    """Sfiato di gas criogenico: a ciclo rilascia una nube gelata che rallenta."""
    REST, ACTIVE = 260, 170
    PERIOD = REST + ACTIVE
    RADIUS = 150

    def __init__(self, x, floor):
        self.x, self.floor = x, floor
        self.age = 0
        self.started = False

    @property
    def active(self):
        return self.age % self.PERIOD >= self.REST

    def update(self, player):
        if abs(player.rect.centerx - self.x) < 900:
            self.started = True
        if self.started:
            self.age += 1
        center = pygame.Vector2(self.x, self.floor - 90)
        return self.active and center.distance_to(player.rect.center) < self.RADIUS

    def draw(self, screen, cam):
        x, f = int(self.x - cam), self.floor
        if not -250 < x < screen.get_width() + 250:
            return
        pygame.draw.ellipse(screen, (20, 16, 14), (x - 34, f - 14, 68, 18))
        pygame.draw.ellipse(screen, (120, 170, 190), (x - 26, f - 11, 52, 12), 3)
        if not self.active:
            return
        k = min(1, (self.age % self.PERIOD - self.REST) / 30)
        cloud = pygame.Surface((340, 280), pygame.SRCALPHA)
        for i in range(70):
            # sbuffi che salgono dallo sfiato e si allargano, sempre piu' trasparenti
            life = ((self.age * (0.6 + (i % 5) * 0.12) + i * 23) % 120) / 120
            spread = 20 + life * 130
            cx = 170 + math.sin(i * 1.7 + self.age * 0.015) * spread
            cy = 260 - life * 230
            rad = int(10 + life * 34)
            pygame.draw.circle(cloud, (214, 238, 248, int(26 * k * (1 - life))), (int(cx), int(cy)), rad)
        screen.blit(cloud, (x - 170, f - 270))
