"""Le ondate della superficie: arene chiuse da porte stagne finche' l'ondata non e' finita."""
import random

import pygame

TILE = 64
GROUND = 14
W = 1920
SPAWN_EVERY = 28          # fotogrammi fra un nemico e il successivo
ALIVE = 8                 # nemici in campo insieme, se l'ondata non dice altro
FLYING = ("crow", "skeleton_fly", "jelly")


class Wave:
    def __init__(self, x0, spec, rnd):
        self.x0, self.x1 = x0, x0 + W
        self.name = spec["name"]
        self.alive_max = spec.get("alive", ALIVE)
        self.queue = [kind for kind, n in spec["roster"] for _ in range(n)]
        rnd.shuffle(self.queue)
        self.total = len(self.queue)
        self.members = []
        self.timer = 0
        self.state = "waiting"          # waiting -> fighting -> done

    def remaining(self):
        return len(self.queue) + sum(1 for e in self.members if e.alive)


class WaveDirector:
    """Tiene le ondate di una superficie: le attiva quando NightKnight entra
    nell'arena, fa entrare i nemici dai bordi e riapre le porte alla fine."""

    def __init__(self, arenas, specs, make_walker, make_flyer, seed=0):
        rnd = random.Random(seed)
        self.waves = [Wave(col * TILE, spec, rnd) for col, spec in zip(arenas, specs)]
        self.make_walker, self.make_flyer = make_walker, make_flyer
        self.rnd = rnd
        self.side = 1

    @property
    def active(self):
        return next((w for w in self.waves if w.state == "fighting"), None)

    def lock(self):
        """Limiti dell'arena chiusa, oppure None."""
        w = self.active
        return (w.x0, w.x1) if w else None

    def update(self, player, walkers, flyers):
        """Aggiorna le ondate; restituisce un evento ("start", onda) / ("clear", onda) o None."""
        w = self.active
        if w is None:
            for w in self.waves:
                if w.state == "waiting" and w.x0 + 240 < player.rect.centerx < w.x1:
                    w.state = "fighting"
                    return ("start", w)
            return None
        w.timer -= 1
        alive = sum(1 for e in w.members if e.alive)
        if w.queue and w.timer <= 0 and alive < w.alive_max:
            w.timer = SPAWN_EVERY
            kind = w.queue.pop()
            self.side = -self.side
            if kind in FLYING:
                x = (w.x0 - 80) if self.side < 0 else (w.x1 + 20)
                e = self.make_flyer(x, self.rnd.randrange(150, 420), kind)
                flyers.append(e)
            else:
                # chi cammina entra dal bordo; il verme emerge dal suolo dove capita
                if kind == "worm":
                    x = self.rnd.randrange(w.x0 + 200, w.x1 - 300)
                else:
                    x = (w.x0 + 20) if self.side < 0 else (w.x1 - 220)
                e = self.make_walker(x, kind)
                walkers.append(e)
            w.members.append(e)
        if not w.queue and not any(e.alive for e in w.members):
            w.state = "done"
            return ("clear", w)
        return None

    def draw_doors(self, s, cam, lock_h):
        """Porte stagne ai due lati dell'arena chiusa."""
        w = self.active
        if not w:
            return
        for x in (w.x0 - 24, w.x1 - 24):
            r = pygame.Rect(x - cam, GROUND * TILE - lock_h, 48, lock_h)
            pygame.draw.rect(s, (58, 52, 48), r)
            pygame.draw.rect(s, (20, 16, 14), r, 4)
            for y in range(r.top + 10, r.bottom - 10, 36):
                pygame.draw.polygon(s, (226, 176, 48), [(r.left + 4, y), (r.right - 4, y + 12),
                                                         (r.right - 4, y + 24), (r.left + 4, y + 12)])
            pygame.draw.circle(s, (200, 60, 40), (r.centerx, r.top + 18), 7)
