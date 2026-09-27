import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
import unittest

import pygame

import athletics
import goblin
import levels

TILE = 64
G = levels.GROUND
X0 = levels.TITAN_PASS_START


class LabyrinthTests(unittest.TestCase):
    """Il labirinto si attraversa davvero, con la fisica del gioco, e non si scavalca."""

    @classmethod
    def setUpClass(cls):
        cls.lv = goblin.Level(levels.gen_surface(), "surface")

    def stand(self, col, h, gravity=levels.cfg()["gravity_scale"]):
        p = goblin.Player(0, 0)
        p.gravity_scale = gravity
        p.x = (X0 + col) * TILE + (TILE - p.w) / 2
        p.y = (G - h) * TILE - p.h
        p.on_ground = True
        p.update(defaultdict(bool), self.lv)
        self.assertTrue(p.on_ground, (col, h))
        return p

    def jump(self, p, direction, sprint=False, frames=150, runup=12):
        keys = defaultdict(bool, {pygame.K_SPACE: True, pygame.K_LSHIFT: sprint,
                                  pygame.K_RIGHT if direction > 0 else pygame.K_LEFT: True})
        for _ in range(runup):                   # rincorsa
            p.update(keys, self.lv)
        p.do_jump()
        for frame in range(frames):
            p.update(keys, self.lv)
            if p.on_ground and frame > 3:
                break
        return p

    def jump_to(self, p, col, frames=150):
        """Salto controllato: freccia tenuta finche' si e' sopra la colonna voluta,
        poi lasciata e, se serve, un colpo nell'altro verso per frenare."""
        target = (X0 + col) * TILE + TILE
        p.do_jump()
        for frame in range(frames):
            keys = defaultdict(bool, {pygame.K_SPACE: True})
            if p.rect.centerx < target - 20:
                keys[pygame.K_RIGHT] = True
            elif p.vx > 1:
                keys[pygame.K_LEFT] = True
            p.update(keys, self.lv)
            if p.on_ground and frame > 3:
                break
        return p

    def feet(self, p):
        return G - p.rect.bottom // TILE, p.rect.centerx // TILE - X0

    def climb(self, p, frames=200):
        keys = defaultdict(bool, {pygame.K_UP: True})
        for _ in range(frames):
            p.update(keys, self.lv)
            if not p.climbing and p.on_ground and _ > 5:
                break
        return p

    def test_the_cliff_zigzags_up(self):
        l1, l2, l3 = levels.LEDGES
        p = self.jump(self.stand(10, 0), 1, runup=0)
        self.assertEqual(self.feet(p)[0], 2)                       # sul gradino
        p = self.jump(p, 1, runup=0)
        self.assertEqual(self.feet(p)[0], l1)                      # prima cengia
        p = self.climb(self.stand(41, l1))
        self.assertEqual(self.feet(p)[0], l2)                      # scala a destra
        p = self.jump(self.stand(29, l2), -1, runup=0)
        self.assertEqual(self.feet(p)[0], l2)                      # il buco della cengia media
        self.assertLess(self.feet(p)[1], 27)                      # anche sotto la cengia alta
        p = self.climb(self.stand(15, l2))
        self.assertEqual(self.feet(p)[0], l3)                      # scala a sinistra, in cima

    def test_ledges_cannot_be_skipped_by_jumping(self):
        l1, l2, l3 = levels.LEDGES
        for col in (20, 35):
            p = self.jump(self.stand(col, l1), 1)
            self.assertEqual(self.feet(p)[0], l1)
        p = self.jump(self.stand(43, 0), -1)
        self.assertLessEqual(self.feet(p)[0], l1)
        p = self.jump(self.stand(43, 0), 1)
        self.assertEqual(self.feet(p)[0], 0)                       # la rupe non si sale

    def test_the_spires_step_down_into_the_lake(self):
        p = self.stand(62, levels.LEDGES[2])
        for col, h in ((66, 13), (70, 10), (74, 7), (78, 4)):
            p = self.jump_to(p, col)
            with self.subTest(spire=col):
                self.assertEqual(self.feet(p)[0], h)
                self.assertIn(self.feet(p)[1], (col, col + 1))

    def test_the_wall_past_the_crevasse_cannot_be_jumped(self):
        p = self.jump(self.stand(95, 0), 1, sprint=True, frames=200)
        h, col = self.feet(p)
        self.assertLess(h, 0)                                      # finito giu' nel crepaccio
        self.assertLess(col, 103)

    def test_the_crevasse_leads_down_to_the_galleries(self):
        p = self.stand(96, 0)
        keys = defaultdict(bool, {pygame.K_RIGHT: True})
        for _ in range(300):
            p.update(keys, self.lv)
        self.assertEqual(self.feet(p)[0], G - levels.CAVE_FLOOR)
        self.assertGreater(self.feet(p)[1], 103)

    def test_the_low_passage_and_the_pool(self):
        p = self.stand(110, G - levels.CAVE_FLOOR)
        keys = defaultdict(bool, {pygame.K_RIGHT: True})
        for _ in range(160):
            p.update(keys, self.lv)
        self.assertGreater(self.feet(p)[1], 121)                   # passaggio basso
        for direction, start, beyond in ((1, 122, 126), (-1, 128, 124)):
            p = self.jump(self.stand(start, G - levels.CAVE_FLOOR), direction)
            with self.subTest(direction=direction):
                self.assertEqual(self.feet(p)[0], G - levels.CAVE_FLOOR)
                self.assertTrue(self.feet(p)[1] > beyond if direction > 0 else self.feet(p)[1] < beyond)

    def test_the_shaft_climbs_back_to_the_surface(self):
        p = self.climb(self.stand(146, G - levels.CAVE_FLOOR), frames=400)
        self.assertEqual(self.feet(p)[0], 0)
        self.assertEqual(self.lv.exit[0] - X0, 316)

    def swing(self, start, h, wait, releases):
        """Si aspetta il momento, si salta verso i cavi tenendo la destra, e da
        ogni cavo si lascia quando l'impugnatura ha superato releases[i] della
        lunghezza nel verso giusto. Restituisce (esito, cavi presi, colonna, altezza)."""
        x0 = X0 * TILE
        speeds = iter(levels.ROPE_SPEEDS)
        cables = athletics.Cables([[athletics.Cable(x0 + col * TILE + TILE // 2, athletics.FLOOR - top, length,
                                                    next(speeds))
                                    for col, top, length in group] for group in levels.TITAN_CABLES])
        p = self.stand(start, h)
        idle = defaultdict(bool)
        keys = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_SPACE: True})
        for _ in range(wait):
            cables.update_player(p, idle, self.lv)
        for _ in range(6):
            cables.update_player(p, keys, self.lv)
        p.do_jump()
        grabs = []
        for frame in range(1200):
            cables.update_player(p, keys, self.lv)
            c = cables.current
            if c:
                i = cables.all.index(c)
                if not grabs or grabs[-1] != i:
                    grabs.append(i)
                body, anchor = c.rope.body, c.rope.anchor
                if body.velocity.x > 0 and body.position.x - anchor.x > releases[len(grabs) - 1] * c.rope.length:
                    c.release(p)
            if self.lv.drowned(p.rect):
                return "annegato", grabs, None, None
            if p.on_ground and frame > 10:
                h, col = self.feet(p)
                return "a terra", grabs, col, h
        return "appeso", grabs, None, None

    def crossings(self, start, h, releases, waits=range(0, 200, 5)):
        """Tutti i modi di passare provando attese e rilasci: [(attesa, rilasci, esito)].
        I cavi dondolano da soli: si sceglie solo quando saltare e quando lasciare."""
        import itertools
        out = []
        for wait in waits:
            for rel in itertools.product(*releases):
                out.append((wait, rel, self.swing(start, h, wait, rel)))
        return out

    def test_the_double_cable_needs_both_cables(self):
        tries = self.crossings(165, 3, [(0.2, 0.35, 0.5, 0.65, 0.75), (0.35, 0.5, 0.65, 0.75)])
        ok = [t for t in tries if t[2][0] == "a terra" and t[2][1] == [1, 2] and t[2][2] >= 196]
        self.assertTrue(ok, "col doppio cavo non si passa mai")
        for wait, rel, (outcome, grabs, col, h) in tries:              # col primo soltanto no
            self.assertFalse(outcome == "a terra" and grabs == [1] and col >= 196)

    def test_the_triple_cable_is_crossed_only_from_high_up(self):
        tries = self.crossings(213, levels.TITAN_TOWER, [(0.35, 0.5, 0.65), (0.5, 0.65), (0.5, 0.65)],
                               waits=range(0, 200, 10))
        ok = [t for t in tries if t[2][0] == "a terra" and t[2][1] == [3, 4, 5] and t[2][2] >= 253]
        self.assertTrue(ok, "col triplo cavo non si passa mai")
        low = self.crossings(213, levels.TITAN_TOWER, [(0.35, 0.5, 0.65), (0.0, 0.2), (0.5, 0.65, 0.75)],
                             waits=range(0, 200, 10))
        self.assertFalse([t for t in low if t[2][0] == "a terra" and t[2][2] >= 253])   # lasciato basso, no

    def test_handles_hang_above_the_launch_points(self):
        cables = levels.TITAN_CABLES
        for group, launch in ((cables[0], 4), (cables[1], 3), (cables[2], levels.TITAN_TOWER)):
            col, top, length = group[0]
            lowest = (top - length) / TILE                  # l'impugnatura nel punto piu' basso
            with self.subTest(col=col):
                self.assertGreaterEqual(lowest, launch + 4.5)  # sopra la testa: si salta per prenderla

    def test_ropes_swing_on_their_own_each_at_its_pace(self):
        rope = athletics.Rope(0, 0, 500, 1.0)
        fast = athletics.Rope(0, 0, 500, 1.2)
        xs, fx = [], []
        for _ in range(int(athletics.ROPE_PERIOD * 60)):     # un'oscillazione completa
            rope.update(steering=1)                          # spingere non conta
            fast.update()
            xs.append(rope.body.position.x)
            fx.append(fast.body.position.x)
        self.assertAlmostEqual(max(xs), -min(xs), delta=5)  # dondola uguale da una parte e dall'altra
        self.assertNotAlmostEqual(xs[-1], fx[-1], delta=20)  # ognuno col suo ritmo
        self.assertEqual(len(levels.ROPE_SPEEDS), sum(len(g) for g in levels.TITAN_CABLES))


if __name__ == "__main__":
    unittest.main()
