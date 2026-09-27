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
        cables = athletics.Cables([[athletics.Cable(x0 + col * TILE + TILE // 2, athletics.FLOOR - top, length)
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

    def test_the_double_cable_needs_both_cables(self):
        outcome, grabs, col, h = self.swing(165, 3, 60, (0.85, 0.5))
        self.assertEqual((outcome, grabs), ("a terra", [1, 2]))
        self.assertGreaterEqual(col, 201)
        self.assertEqual(h, 3)
        for wait in range(0, 170, 10):                   # col primo soltanto non si arriva
            with self.subTest(wait=wait):
                result = self.swing(165, 3, wait, (0.95, 0.95))
                self.assertFalse(result[0] == "a terra" and result[1] == [1])

    def test_the_triple_cable_is_crossed_only_from_high_up(self):
        outcome, grabs, col, h = self.swing(213, 11, 140, (0.65, 0.85, 0.5))
        self.assertEqual((outcome, grabs), ("a terra", [3, 4, 5]))
        self.assertGreaterEqual(col, 253)
        self.assertEqual(h, 5)                                     # sullo scalino alto
        outcome, grabs, _, _ = self.swing(213, 11, 140, (0.65, 0.35, 0.5))
        self.assertEqual(outcome, "annegato")                      # lasciato in basso, in acqua


if __name__ == "__main__":
    unittest.main()
