"""Le ondate della superficie: partono quando si entra nella zona, ma non bloccano mai.
Si puo' sempre andare avanti o scappare: chi e' in campo insegue, i rinforzi smettono."""
import random

TILE = 64
GROUND = 14
W = 1920
SPAWN_EVERY = 28          # fotogrammi fra un nemico e il successivo
ALIVE = 8                 # nemici in campo insieme, se l'ondata non dice altro
FLEE = 900                # oltre questa distanza dalla zona l'ondata smette di mandare rinforzi
VIEW_HALF = 640           # meta' della vista del mondo (1280 px con lo zoom)
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

    def __init__(self, arenas, specs, make_walker, make_flyer, seed=0, flyer_y=(150, 420)):
        rnd = random.Random(seed)
        self.waves = [Wave(col * TILE, spec, rnd) for col, spec in zip(arenas, specs)]
        self.make_walker, self.make_flyer = make_walker, make_flyer
        self.rnd = rnd
        self.side = 1
        self.flyer_y = flyer_y

    @property
    def active(self):
        return next((w for w in self.waves if w.state == "fighting"), None)

    def lock(self):
        """Le ondate non chiudono mai il passaggio."""
        return None

    def update(self, player, walkers, flyers):
        """Aggiorna le ondate; restituisce un evento ("start", onda) / ("clear", onda) o None."""
        w = self.active
        if w is None:
            for w in self.waves:
                if w.state == "waiting" and w.x0 + 240 < player.rect.centerx < w.x1:
                    w.state = "fighting"
                    return ("start", w)
            return None
        if player.rect.centerx > w.x1 + FLEE or player.rect.centerx < w.x0 - FLEE:
            # NightKnight e' scappato: niente piu' rinforzi, chi c'e' lo insegue
            w.queue.clear()
        w.timer -= 1
        alive = sum(1 for e in w.members if e.alive)
        if w.queue and w.timer <= 0 and alive < w.alive_max:
            w.timer = SPAWN_EVERY
            kind = w.queue.pop()
            self.side = -self.side
            # i rinforzi entrano dai bordi della vista, attorno a NightKnight
            cx = player.rect.centerx
            if kind in FLYING:
                x = cx - VIEW_HALF - 80 if self.side < 0 else cx + VIEW_HALF + 20
                e = self.make_flyer(x, self.rnd.randrange(*self.flyer_y), kind)
                flyers.append(e)
            else:
                # chi cammina entra dal bordo; il verme emerge dal suolo dove capita
                if kind == "worm":
                    x = cx + self.side * self.rnd.randrange(250, 550)
                else:
                    x = cx - VIEW_HALF - 60 if self.side < 0 else cx + VIEW_HALF + 20
                e = self.make_walker(x, kind)
                walkers.append(e)
            w.members.append(e)
        if not w.queue and not any(e.alive for e in w.members):
            w.state = "done"
            return ("clear", w)
        return None
