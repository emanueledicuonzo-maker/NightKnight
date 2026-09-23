"""Il cavo sopra i laghi: una corda fisica a cui aggrapparsi (E) per attraversare."""
import math

import pygame
import pymunk


TILE = 64
FLOOR = 14 * TILE


class Rope:
    def __init__(self, x, y=240, length=500):
        self.anchor = pymunk.Vec2d(x, y)
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
        left, right = a[0] - 5*TILE, a[0] + 5*TILE      # portale del cavo, sopra le rive
        for x in (left, right):
            pygame.draw.line(screen, (36, 32, 28), (x, FLOOR), (x, a[1]-12), 18)
            pygame.draw.line(screen, (108, 95, 73), (x-3, FLOOR), (x-3, a[1]-12), 4)
        pygame.draw.line(screen, (36, 32, 28), (left-12, a[1]), (right+12, a[1]), 20)
        pygame.draw.line(screen, (108, 95, 73), (left-12, a[1]-5), (right+12, a[1]-5), 4)
        pygame.draw.line(screen, (32, 39, 28), a, b, 9)
        pygame.draw.line(screen, (124, 130, 88), a, b, 4)
        # impugnatura ben visibile: e' li' che ci si aggrappa saltando
        pygame.draw.circle(screen, (24, 18, 14), b, 17)
        pygame.draw.circle(screen, (236, 190, 96), b, 13, 5)


class Cable:
    def __init__(self, x):
        self.rope = Rope(x)
        self.attached = False
        self.regrab = 0

    def interact(self, p, lv):
        if self.attached:
            self.release(p)
            return
        hand = pymunk.Vec2d(p.rect.centerx, p.y + 45)
        if hand.get_distance(self.rope.body.position) < 140:
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

    def update_player(self, p, keys, lv):
        steering = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.rope.update(steering if self.attached else 0)
        self.regrab = max(0, self.regrab - 1)
        if not self.attached and not p.on_ground and not self.regrab:
            # in salto, toccare il capo del cavo basta per aggrapparsi
            hand = pymunk.Vec2d(p.rect.centerx, p.y + 45)
            if hand.get_distance(self.rope.body.position) < 110:
                self.interact(p, lv)
        if self.attached:
            p.x = self.rope.body.position.x - p.w / 2
            p.y = self.rope.body.position.y - 45
            p.facing = 1 if self.rope.body.velocity.x >= 0 else -1
            p.vx = p.vy = 0
            p.on_ground = False
            p.jumped = False
            return
        p.update(keys, lv)

    def draw(self, screen, cam):
        self.rope.draw(screen, cam)
