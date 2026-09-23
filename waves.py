"""Le ondate della superficie: partono quando si entra nella zona, ma non bloccano mai.
Si puo' sempre andare avanti o scappare: chi e' in campo insegue, i rinforzi smettono."""
import random

TILE = 64
GROUND = 14
W = 1920
SPAWN_EVERY = 28          # fotogrammi fra un nemico e il successivo
ALIVE = 8                 # nemici in campo insieme, se l'ondata non dice altro
FLEE = 1800               # oltre questa distanza dalla zona l'ondata smette di mandare rinforzi
VIEW_HALF = 640           # meta' della vista del mondo (1280 px con lo zoom)
FLYING = ("crow", "skeleton_fly", "jelly")


class Wave:
    def __init__(self, x0, spec, rnd):
        self.x0, self.x1 = x0, x0 + W
        self.name = spec["name"]
        self.alive_max = spec.get("alive", ALIVE)
        self.every = spec.get("every", SPAWN_EVERY)
        self.queue = [kind for kind, n in spec["roster"] for _ in range(n)]
        rnd.shuffle(self.queue)
        self.total = len(self.queue)
        self.members = []
        self.timer = 0
        self.state = "waiting"          # waiting -> fighting -> done

    def remaining(self):
        return len(self.queue) + sum(1 for e in self.members if e.alive)


class WaveDirector:
    """Le ondate di una superficie. Ognuna parte quando NightKnight entra nella
    sua zona e vive per conto suo: non blocca e non aspetta le altre."""

    def __init__(self, arenas, specs, make_walker, make_flyer, seed=0, flyer_y=(150, 420)):
        rnd = random.Random(seed)
        self.waves = [Wave(col * TILE, spec, rnd) for col, spec in zip(arenas, specs)]
        self.make_walker, self.make_flyer = make_walker, make_flyer
        self.rnd = rnd
        self.side = 1
        self.flyer_y = flyer_y

    def lock(self):
        """Le ondate non chiudono mai il passaggio."""
        return None

    def update(self, player, walkers, flyers):
        """Aggiorna tutte le ondate; restituisce l'ultimo evento ("start"/"clear", onda) o None."""
        event = None
        cx = player.rect.centerx
        for w in self.waves:
            if w.state == "waiting" and w.x0 + 240 < cx:
                w.state = "fighting"
                event = ("start", w)
            if w.state != "fighting":
                continue
            if cx > w.x1 + FLEE or cx < w.x0 - FLEE:
                # NightKnight e' scappato: niente piu' rinforzi, chi c'e' lo insegue
                w.queue.clear()
            w.timer -= 1
            alive = sum(1 for e in w.members if e.alive)
            if w.queue and w.timer <= 0 and alive < w.alive_max:
                w.timer = w.every
                w.members.append(self.spawn(w.queue.pop(), cx, walkers, flyers))
            if not w.queue and not any(e.alive for e in w.members):
                w.state = "done"
                event = ("clear", w)
        return event

    def spawn(self, kind, cx, walkers, flyers):
        # i nemici entrano dai bordi della vista, due su tre davanti a NightKnight
        self.side = 1 if self.rnd.random() < 0.67 else -1
        if kind in FLYING:
            x = cx - VIEW_HALF - 80 if self.side < 0 else cx + VIEW_HALF + 20
            e = self.make_flyer(x, self.rnd.randrange(*self.flyer_y), kind)
            flyers.append(e)
            return e
        if kind == "worm":           # il verme emerge dal suolo, non lontano
            x = cx + self.side * self.rnd.randrange(250, 550)
        else:
            x = cx + self.side * (VIEW_HALF + self.rnd.randrange(20, 260))
        e = self.make_walker(x, kind)
        walkers.append(e)
        return e
