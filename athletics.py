"""Prove atletiche, corde fisiche e armi da lancio."""
import math

import pygame
import pymunk

import assets
import knights
import pixelart as px

TILE = 64
FLOOR = 14 * TILE
NAMES = ("SALTO IN LUNGO", "LIANA", "CAVALLO", "GIAVELLOTTO", "PUGNALI")


class WeaponShot(knights.Projectile):
    def __init__(self, weapon, player):
        super().__init__("arrow", player.rect.centerx, player.y + 64, player.facing,
                         24 if weapon == "javelin" else 10, (220, 225, 226))
        self.weapon = weapon
        self.owner = "player"
        self.w = 130 if weapon == "javelin" else 42
        self.vx = (22 + abs(player.vx) * 0.5 if weapon == "javelin" else 26) * self.d
        self.vy = -3.0 if weapon == "javelin" else 0.0
        if self.d < 0:
            self.x -= self.w
        self.rect = pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self, lv, cam):
        super().update(lv, cam)
        self.vy += 0.12 if self.weapon == "javelin" else 0.015
        self.y += self.vy
        self.rect.y = int(self.y)
        if lv.solid(self.rect.centerx, self.rect.centery) or self.t > 150:
            self.alive = False

    def draw(self, screen, gfx, cam):
        if self.weapon == "javelin":
            img = assets.load("lance", 130, 20)
            if self.d < 0:
                img = assets.flip(img)
            screen.blit(img, (int(self.x) - cam, int(self.y)))
        else:
            x, y = int(self.x) - cam, int(self.y) + 7
            tip, base = (x + 42, x + 13) if self.d > 0 else (x, x + 29)
            pygame.draw.line(screen, (115, 89, 66), (x, y), (x + 42, y), 5)
            pygame.draw.polygon(screen, (212, 224, 230), [(tip, y), (base, y - 6), (base, y + 6)])


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
        left, right = 31*TILE-cam, 41*TILE-cam
        for x in (left, right):
            pygame.draw.line(screen, (36, 32, 28), (x, FLOOR), (x, a[1]-12), 18)
            pygame.draw.line(screen, (108, 95, 73), (x-3, FLOOR), (x-3, a[1]-12), 4)
        pygame.draw.line(screen, (36, 32, 28), (left-12, a[1]), (right+12, a[1]), 20)
        pygame.draw.line(screen, (108, 95, 73), (left-12, a[1]-5), (right+12, a[1]-5), 4)
        pygame.draw.line(screen, (32, 39, 28), a, b, 9)
        pygame.draw.line(screen, (124, 130, 88), a, b, 4)
        pygame.draw.circle(screen, (164, 148, 105), b, 9, 3)


class Trials:
    def __init__(self):
        self.done = set()
        self.elapsed = 0
        self.rope = Rope(36 * TILE)
        self.attached = False
        self.rope_used = False
        self.horse_x = 46 * TILE
        self.horse_frames = assets.sheet("horse_run_sheet", 210)
        self.horse_t = 0.0
        self.takeoff = None
        self.best_jump = 0.0
        self.targets = []
        for weapon, columns in (("javelin", (78, 83, 88)), ("dagger", (96, 100, 104))):
            for col in columns:
                self.targets.append({"weapon": weapon, "rect": pygame.Rect(col*TILE, FLOOR-230, 72, 200), "hit": False})

    @property
    def complete(self):
        return len(self.done) == len(NAMES)

    def interact(self, p, lv):
        if self.attached:
            self.release(p)
            return
        hand = pymunk.Vec2d(p.rect.centerx, p.y + 45)
        if not p.mounted and hand.get_distance(self.rope.body.position) < 140:
            self.attached = self.rope_used = True
            p.attack = None
            p.climbing = False
            p.on_ground = False
            p.coyote = p.jump_buffer = 0
        elif p.mounted and p.on_ground:
            self.horse_x = p.rect.centerx
            p.mounted = False
        elif p.on_ground and abs(p.rect.centerx - self.horse_x) < 150:
            p.mounted = True
            p.attack = None

    def release(self, p):
        self.attached = False
        p.vx = max(-12, min(12, self.rope.body.velocity.x / 60))
        p.vy = max(-22, min(-8, self.rope.body.velocity.y / 60 - 8))
        p.on_ground = False
        p.coyote = p.jump_buffer = 0

    def update_player(self, p, keys, lv):
        steering = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.rope.update(steering if self.attached else 0)
        self.elapsed += 1
        if self.attached:
            p.x = self.rope.body.position.x - p.w / 2
            p.y = self.rope.body.position.y - 45
            p.facing = 1 if self.rope.body.velocity.x >= 0 else -1
            p.vx = p.vy = 0
            p.on_ground = False
            p.jumped = False
            return
        previous_x = p.x
        p.update(keys, lv)
        if self.takeoff is None and not p.on_ground:
            self.takeoff = previous_x
        if p.on_ground and self.takeoff is not None:
            distance = abs(p.x - self.takeoff)
            self.best_jump = max(self.best_jump, distance)
            if self.takeoff < 12*TILE and p.rect.right > 14*TILE:
                self.done.add(0)
            self.takeoff = None
        if self.rope_used and p.on_ground and p.x >= 40*TILE:
            self.done.add(1)
        if p.mounted:
            self.horse_x = p.rect.centerx
            self.horse_t += abs(p.vx) / 35
            if p.x > 66*TILE:
                self.done.add(2)

    def check_targets(self, shots):
        points = 0
        for shot in shots:
            if not shot.alive or shot.owner != "player":
                continue
            for target in self.targets:
                if not target["hit"] and shot.weapon == target["weapon"] and shot.rect.colliderect(target["rect"]):
                    target["hit"] = True
                    shot.alive = False
                    points += 250
                    break
        for index, weapon in ((3, "javelin"), (4, "dagger")):
            if all(t["hit"] for t in self.targets if t["weapon"] == weapon):
                self.done.add(index)
        return points

    def draw(self, screen, gfx, p, cam):
        self.rope.draw(screen, cam)
        if self.horse_frames:
            frame = self.horse_frames[int(self.horse_t) % len(self.horse_frames)]
            if p.mounted and p.facing < 0:
                frame = assets.flip(frame)
            floor = p.rect.bottom if p.mounted else FLOOR
            screen.blit(frame, (int(self.horse_x) - frame.get_width()//2 - cam, floor - frame.get_height()))
        for target in self.targets:
            rect = target["rect"].move(-cam, 0)
            if rect.right < 0 or rect.left > screen.get_width():
                continue
            color = (58, 136, 100) if target["hit"] else (161, 102, 69)
            pygame.draw.line(screen, (89, 79, 65), (rect.centerx, rect.bottom), (rect.centerx, FLOOR), 8)
            pygame.draw.ellipse(screen, (60, 53, 47), rect)
            pygame.draw.ellipse(screen, color, rect.inflate(-8, -8), 5)
            pygame.draw.ellipse(screen, (208, 192, 143), rect.inflate(-30, -70), 3)
        for name, col in zip(NAMES, (5, 28, 45, 74, 92)):
            x = col*TILE-cam
            if -300 < x < screen.get_width():
                px.draw_text(screen, name, x, FLOOR-300, (216, 198, 150), 4)

    def draw_hud(self, screen):
        for i, name in enumerate(NAMES):
            color = (113, 208, 159) if i in self.done else (173, 181, 186)
            px.draw_text(screen, name, 40 + i*285, 202, color, 3)
        px.draw_text(screen, f"{self.elapsed / 60:.1f} s   {len(self.done)} / 5", 1570, 202, (224, 209, 162), 4)
        if 0 not in self.done:
            px.draw_text(screen, "MAIUSC + DESTRA: RINCORSA", 40, 246, (224, 209, 162), 3)
