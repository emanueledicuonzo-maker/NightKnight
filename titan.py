"""Insidie e presenze di Titano: criovulcani, sfiati di azoto, Spenti da liberare,
stazioni d'ossigeno."""
import math

import pygame

# Disegni caricati dal gioco (goblin.Gfx): senza, si disegna tutto in codice.
ART = {}
# Il getto del criovulcano: vapore gelido cartoon (contorno, ombra, luce) e fango.
JET_H, JET_PUFFS = 330, 26
JET_INK, JET_SHADE, JET_LIGHT, JET_MUD = (40, 30, 34), (170, 196, 206), (236, 244, 244), (120, 104, 92)
_flips = {}
# quanto in alto arriva il getto (px sopra il suolo) nei cinque disegni dell'eruzione
ERUPT_REACH = (60, 160, 330, 360, 400)


def _flipped(img):
    """L'immagine specchiata, calcolata una volta sola (non a ogni fotogramma)."""
    key = id(img)
    if key not in _flips:
        _flips[key] = (img, pygame.transform.flip(img, True, False))
    return _flips[key][1]
SINK = 8           # gli oggetti affondano un poco nel suolo: poggiano, non galleggiano
_shadows = {}


def ground_shadow(screen, cx, floor, w):
    """Ombra di contatto: una macchia scura e morbida dove l'oggetto tocca terra."""
    w = max(20, int(w))
    if w not in _shadows:
        sh = pygame.Surface((w, 22), pygame.SRCALPHA)
        for i in range(8, 0, -1):
            k = i / 8
            pygame.draw.ellipse(sh, (20, 10, 6, int(40 * (1 - k) + 18)),
                                (w * (1 - k) / 2, 11 * (1 - k), w * k, 22 * k))
        _shadows[w] = sh
    sh = _shadows[w]
    screen.blit(sh, (cx - w // 2, floor - 13))


class Geyser:
    """Criovulcano: fango gelido d'acqua e ammoniaca che erompe a ciclo (su Titano
    e' un'ipotesi di Cassini; i geyser veri sono su Encelado)."""
    # Un ciclo inizia sempre con un lungo riposo: nessun getto a sorpresa.
    REST, WARNING, ERUPTION = 180, 90, 180
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
        h = self.column
        return pygame.Rect(self.x - 60, self.floor - h, 120, h)

    def update(self, player):
        self.previous_phase = self.phase
        if abs(player.rect.centerx - self.x) < 750:
            self.started = True
        if self.started:
            self.age += 1
        # fa male solo quando il getto e' una colonna vera, non un filo di vapore
        return (self.phase == "eruption" and self.column >= 200
                and self.hitbox.colliderect(player.hurtbox()))

    def draw(self, screen, cam):
        if "geyser" in ART:
            return self.draw_art(screen, cam)
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


    def intensity(self):
        """Quanto e' forte l'eruzione in questo istante, da 0 (il filo) a 4 (la
        colonna piena): sale, oscilla irregolare fra i disegni piu' forti, cala.
        Restituisce (disegno, disegno successivo, dissolvenza fra i due)."""
        k = (self.age % self.PERIOD - self.REST - self.WARNING) / self.ERUPTION
        if k < 0.15:
            level = k / 0.15 * 4                                  # sale fino al massimo
        elif k > 0.85:
            level = (1 - (k - 0.85) / 0.15) * 4                   # cala
        else:
            # irregolare: tre onde di periodo diverso, fra la colonna media e la piena
            t = self.age + self.x * 0.37
            level = 3.1 + 0.55 * math.sin(t * 0.11) + 0.35 * math.sin(t * 0.29 + 1) + 0.25 * math.sin(t * 0.53 + 2)
        level = max(0.0, min(4.0, level))
        a = int(level)
        return a, min(4, a + 1), level - a

    @property
    def column(self):
        """Altezza della colonna che fa male, secondo il disegno in scena."""
        if self.phase != "eruption" or "erupt" not in ART:
            return 330
        a, b, f = self.intensity()
        return int(ERUPT_REACH[a] * (1 - f) + ERUPT_REACH[b] * f)

    def draw_art(self, screen, cam):
        """A riposo e in avviso i nostri due disegni; in eruzione i cinque disegni
        interi, in dissolvenza l'uno nell'altro secondo quanto spinge il getto."""
        x, floor = int(self.x - cam), self.floor
        if not -400 < x < screen.get_width() + 400:
            return
        phase = self.phase
        if phase == "eruption" and "erupt" in ART:
            a, b, f = self.intensity()
            frames = ART["erupt"]
            ground_shadow(screen, x, floor, frames[a].get_width() * 0.8)
            for idx, alpha in ((a, 255), (b, int(255 * f))):
                if alpha <= 4 or (idx == a and idx == b):
                    continue
                img = frames[idx]
                img.set_alpha(alpha)
                wob = int(math.sin(self.age * 0.9 + idx) * 2)
                screen.blit(img, (x - img.get_width() // 2 + wob, floor - img.get_height() + SINK))
            frames[a].set_alpha(255)
            return
        base = ART["geyser"][0 if phase == "rest" else 1]
        if phase == "warning" and (self.age // 4) % 2:
            x += 2                                # il cono trema prima dell'eruzione
        ground_shadow(screen, x, floor, base.get_width() * 0.9)
        screen.blit(base, (x - base.get_width() // 2, floor - base.get_height() + SINK))
        if phase == "eruption":
            self.draw_jet(screen, x, floor - base.get_height() * 2 // 3 + SINK)


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
        ground_shadow(screen, x, self.floor, img.get_width() * 0.95)
        screen.blit(img, (x-img.get_width()//2, self.floor-img.get_height() + SINK))


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
        ground_shadow(screen, x, f, img.get_width() * 0.9)
        screen.blit(img, (x - img.get_width() // 2, f - img.get_height() + SINK))
        if active:
            for i in range(4):                      # sbuffi d'aria mentre si ricarica
                k = ((self.t * 3 + i * 25) % 100) / 100
                pygame.draw.circle(screen, (220, 240, 245), (x + 30 + int(14 * math.sin(i + self.t / 9)),
                                   int(f - img.get_height() * 0.45 - k * 70)), int(3 + k * 7), 2)


class GasVent:
    """Condotta rotta della colonia: a ciclo soffia un getto di azoto criogenico
    di lato, rasoterra. Chi ci passa dentro gela e rallenta: si salta o si aspetta."""
    REST, ACTIVE = 240, 300
    PERIOD = REST + ACTIVE
    REACH = 450              # lunghezza del getto: 7 tessere
    MOUTH = 70               # altezza della bocca sopra il suolo

    def __init__(self, x, floor, facing=-1):
        self.x, self.floor, self.facing = x, floor, facing
        self.age = 0
        self.started = False

    @property
    def active(self):
        return self.age % self.PERIOD >= self.REST

    @property
    def hitbox(self):
        y = self.floor - self.MOUTH - 55
        return pygame.Rect(self.x if self.facing > 0 else self.x - self.REACH, y, self.REACH, 110)

    def update(self, player):
        if abs(player.rect.centerx - self.x) < 900:
            self.started = True
        if self.started:
            self.age += 1
        k = self.age % self.PERIOD - self.REST
        return self.active and k > 12 and self.hitbox.colliderect(player.rect)

    def draw(self, screen, cam):
        x, f = int(self.x - cam), self.floor
        if not -450 < x < screen.get_width() + 450:
            return
        k = (self.age % self.PERIOD - self.REST) if self.active else -1
        if "vent" in ART:
            pipe = ART["vent"][1 if k >= 0 and (k // 6) % 3 else 0]
            if self.facing < 0:
                pipe = _flipped(pipe)
            w = ART["vent"][0].get_width()
            px = x - w // 2 if self.facing > 0 else x + w // 2 - pipe.get_width()
            ground_shadow(screen, x, f, w * 1.1)
            screen.blit(pipe, (px, f - pipe.get_height() + SINK))
        else:
            pygame.draw.ellipse(screen, (20, 16, 14), (x - 34, f - 14, 68, 18))
        if k < 0:
            return
        # il getto: sbuffi che partono dalla bocca e si allargano, sempre piu' trasparenti
        grow = min(1, k / 18)
        jet = pygame.Surface((self.REACH + 120, 220), pygame.SRCALPHA)
        for i in range(90):
            life = ((self.age * (1.1 + (i % 5) * 0.15) + i * 23) % 60) / 60
            if life > grow:
                continue
            cx = 40 + life * self.REACH
            if self.facing < 0:
                cx = jet.get_width() - cx                  # soffia verso sinistra
            cy = 110 + math.sin(i * 1.7 + self.age * 0.08) * (8 + life * 34)
            rad = int(10 + life * 36)
            pygame.draw.circle(jet, (214, 238, 248, int(92 * (1 - life))), (int(cx), int(cy)), rad)
        mouth = x + self.facing * 40
        screen.blit(jet, (mouth - 40 if self.facing > 0 else mouth - jet.get_width() + 40, f - self.MOUTH - 110))
