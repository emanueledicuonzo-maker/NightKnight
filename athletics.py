"""I cavi sopra i laghi: corde fisiche a cui aggrapparsi per attraversare.
Stanno a gruppi (uno, due o tre di fila) sotto un portale di due gru della colonia."""
import math

import pygame
import pymunk

import levels


TILE = 64
ART = {}           # pilone e impugnatura disegnati (caricati dal gioco)
FLOOR = levels.GROUND * TILE
BED = FLOOR + levels.LAKE_DEPTH * TILE      # il fondo dei laghi
_pylons = {}       # gru scalate all'altezza di ogni portale
GRAB = 130         # in salto, a questa distanza dall'impugnatura ci si aggrappa


class Rope:
    ANCHOR_Y = FLOOR - 656

    def __init__(self, x, y=ANCHOR_Y, length=500):
        self.anchor = pymunk.Vec2d(x, y)
        self.length = length
        self.space = pymunk.Space()
        self.space.gravity = (0, 2700)
        self.space.damping = 0.999
        self.body = pymunk.Body(1, float("inf"))
        self.body.position = self.anchor + pymunk.Vec2d(-length * 0.65, length * math.sqrt(1 - 0.65**2))
        self.joint = pymunk.PinJoint(self.space.static_body, self.body, self.anchor, (0, 0))
        self.space.add(self.body, self.joint)

    def update(self, steering=0):
        for _ in range(2):
            self.body.apply_force_at_local_point((steering * 1600, 0))
            self.space.step(1 / 120)

    def draw(self, screen, cam):
        a = (int(self.anchor.x) - cam, int(self.anchor.y))
        b = (int(self.body.position.x) - cam, int(self.body.position.y))
        pygame.draw.line(screen, (32, 39, 28), a, b, 9)
        pygame.draw.line(screen, (124, 130, 88), a, b, 4)
        # impugnatura ben visibile: e' li' che ci si aggrappa saltando
        handle = ART.get("handle")
        if handle:
            screen.blit(handle, (b[0] - handle.get_width() // 2, b[1] - handle.get_height() // 3))
        else:
            pygame.draw.circle(screen, (24, 18, 14), b, 17)
            pygame.draw.circle(screen, (236, 190, 96), b, 13, 5)


def draw_portal(screen, cam, left, right, top):
    """Due gru della colonia ai lati del gruppo di cavi e una trave che le unisce."""
    left, right, top = left - cam, right - cam, int(top)
    pygame.draw.line(screen, (36, 32, 28), (left - 12, top), (right + 12, top), 20)
    pygame.draw.line(screen, (108, 95, 73), (left - 12, top - 5), (right + 12, top - 5), 4)
    source = ART.get("pylon")
    for x, flip in ((left, False), (right, True)):
        if source:
            h = BED - top + 30            # piantate sul fondo del lago: la parte immersa non si vede
            if h not in _pylons:
                k = h / source.get_height()
                img = pygame.transform.smoothscale(source, (int(source.get_width() * k), h))
                _pylons[h] = (img, pygame.transform.flip(img, True, False))     # specchiata una volta sola
            img = _pylons[h][1 if flip else 0]
            foot = int(img.get_width() * 0.22)
            screen.blit(img, (x + foot - img.get_width() if flip else x - foot, BED - img.get_height()))
        else:
            pygame.draw.line(screen, (36, 32, 28), (x, FLOOR), (x, top - 12), 18)
            pygame.draw.line(screen, (108, 95, 73), (x - 3, FLOOR), (x - 3, top - 12), 4)


class Cable:
    """Un cavo solo: la corda, la presa, il lancio quando si lascia."""

    def __init__(self, x, y=Rope.ANCHOR_Y, length=500):
        self.rope = Rope(x, y, length)
        self.attached = False
        self.regrab = 0

    def reach(self, p):
        hand = pymunk.Vec2d(p.rect.centerx, p.y + 45)
        return hand.get_distance(self.rope.body.position)

    def interact(self, p, lv):
        if self.attached:
            self.release(p)
            return
        if self.reach(p) < 140:
            self.grab(p)

    def grab(self, p):
        self.attached = True
        p.attack = None
        p.climbing = False
        p.on_ground = False
        p.coyote = p.jump_buffer = 0

    def release(self, p):
        self.attached = False
        self.regrab = 30          # appena lasciato, non riprenderlo subito
        p.vx = max(-12, min(12, self.rope.body.velocity.x / 60))
        p.vy = max(-22, min(-8, self.rope.body.velocity.y / 60 - 8))
        p.on_ground = False
        p.coyote = p.jump_buffer = 0

    def hold(self, p):
        body = self.rope.body
        p.x = body.position.x - p.w / 2
        p.y = body.position.y - 45
        if not p.attack:
            p.facing = 1 if body.velocity.x >= 0 else -1
        # posa: gambe indietro o avanti secondo da che parte oscilla
        swing = (body.position.x - self.rope.anchor.x) / self.rope.length * p.facing
        p.hanging = -1 if swing < -0.2 else (1 if swing > 0.2 else 0)
        p.vx = p.vy = 0
        p.on_ground = False
        p.jumped = False
        p.advance_attack()        # la spada si puo' usare anche appesi

    def update_player(self, p, keys, lv):
        Cables([[self]]).update_player(p, keys, lv)

    def draw(self, screen, cam):
        a = self.rope.anchor
        draw_portal(screen, cam, a.x - 5 * TILE, a.x + 5 * TILE, a.y)
        self.rope.draw(screen, cam)


class Cables:
    """Tutti i cavi del livello, a gruppi: al massimo uno in mano alla volta; in
    salto basta toccare l'impugnatura di uno qualunque per aggrapparsi."""

    def __init__(self, groups):
        self.groups = groups
        self.all = [c for group in groups for c in group]

    @property
    def attached(self):
        return any(c.attached for c in self.all)

    @property
    def current(self):
        return next((c for c in self.all if c.attached), None)

    def interact(self, p, lv):
        if self.current:
            self.current.release(p)
            return
        near = min(self.all, key=lambda c: c.reach(p))
        near.interact(p, lv)

    def release(self, p):
        if self.current:
            self.current.release(p)

    def update_player(self, p, keys, lv):
        steering = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        for c in self.all:
            c.rope.update(steering if c.attached else 0)
            c.regrab = max(0, c.regrab - 1)
        if not self.attached and not p.on_ground:
            for c in self.all:
                if not c.regrab and c.reach(p) < GRAB:
                    c.grab(p)
                    break
        if self.current:
            self.current.hold(p)
            return
        p.update(keys, lv)

    def draw_portals(self, screen, cam):
        """Le gru, dietro la roccia: si disegnano prima del terreno."""
        for group in self.groups:
            xs = [c.rope.anchor.x for c in group]
            draw_portal(screen, cam, min(xs) - 5 * TILE, max(xs) + 5 * TILE, min(c.rope.anchor.y for c in group))

    def draw(self, screen, cam):
        """Cavi e impugnature, davanti."""
        for c in self.all:
            c.rope.draw(screen, cam)
