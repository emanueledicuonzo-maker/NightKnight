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
