import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
import unittest.mock

import pygame

import goblin
import knights
import levels

TILE = 64
G = levels.GROUND


class NixGuardianTests(unittest.TestCase):
    """Il Guardiano di Nix si batte da vicino: sassi rimandati, lancia piantata,
    anello che gira i comandi, mantello che spegne il visore."""

    @classmethod
    def setUpClass(cls):
        goblin.fonts._font.cache_clear()
        goblin.fonts._text_image.cache_clear()
        cls.temp = tempfile.TemporaryDirectory()
        cls.game = goblin.Game(windowed=True, save_path=Path(cls.temp.name) / "save.json")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        g = self.game
        g.ci, g.lives, g.score, g.luce = 1, 3, 0, 0
        g.start_part("arena")
        g.state = "play"
        g.intro = 0
        self.idle = defaultdict(bool)
        self.p, self.bs = g.player, g.boss
        self.bs.cool = 10 ** 6                       # fermo: si prova una cosa alla volta

    def tick(self, n):
        with unittest.mock.patch("pygame.key.get_pressed", return_value=self.idle):
            for _ in range(n):
                self.game.update()

    def face_off(self, gap=5):
        """9T9T a sinistra del Guardiano, a `gap` tessere, uno di fronte all'altro."""
        p, bs = self.p, self.bs
        bs.x = self.game.lv.w // 2
        p.x = bs.x - gap * TILE
        p.vx = p.vy = 0
        p.facing, bs.facing = 1, -1
        self.game.balls = []
        self.tick(1)

    def test_config(self):
        bs = self.bs
        self.assertEqual(bs.cfg["name"], "Guardiano di Nix")
        self.assertEqual((bs.hp, bs.cfg["gravity_scale"], bs.reach), (320, .55, 190))
        self.assertEqual(bs.cfg["moves"], ["thrust", "thrust", "wave", "dashthrust", "dive", "kick"])

    def test_a_stone_from_the_front_comes_back_as_a_pulse(self):
        g, p, bs = self.game, self.p, self.bs
        self.face_off()
        hp, php = bs.hp, p.hp
        g.balls.append(goblin.Stone(p))
        for _ in range(60):
            self.tick(1)
            if any(getattr(b, "kind", "") == "pulse" for b in g.balls):
                break
        self.assertTrue(any(getattr(b, "kind", "") == "pulse" for b in g.balls), "il piatto rimanda il sasso")
        self.assertEqual(bs.hp, hp, "e il sasso non conta")
        self.tick(60)
        self.assertLess(p.hp, php, "l'impulso torna indietro e fa male")

    def test_a_stone_counts_only_behind_him_or_with_the_lance_planted(self):
        g, p, bs = self.game, self.p, self.bs
        self.face_off()
        bs.move = ("dashthrust", 20)                 # mentre attacca il piatto non prende
        hp = bs.hp
        g.balls.append(goblin.Stone(p))
        self.tick(30)
        self.assertEqual(bs.hp, hp, "di fronte, senza piatto aperto, il sasso rimbalza")
        self.assertFalse(any(getattr(b, "kind", "") == "pulse" for b in g.balls))
        self.assertFalse(bs.stone_counts(bs.rect.centerx - 100))
        self.assertTrue(bs.stone_counts(bs.rect.centerx + 100), "alle spalle conta")
        bs.planted = 60
        self.assertTrue(bs.stone_counts(bs.rect.centerx - 100), "con la lancia piantata conta anche di fronte")

    def test_the_dive_plants_the_lance_and_leaves_him_open(self):
        g, p, bs = self.game, self.p, self.bs
        self.face_off(gap=6)
        bs.move = ("dive", 0)
        for f in range(240):
            self.tick(1)
            if bs.planted:
                break
        self.assertGreater(bs.planted, 0, "dopo la picchiata la lancia si pianta")
        self.assertEqual(bs.pose(), "special")
        self.assertTrue(bs.open)
        hp = bs.hp
        p.x = bs.x - 4 * TILE
        g.balls.append(goblin.Stone(p))
        self.tick(30)
        self.assertLess(bs.hp, hp, "scoperto: il sasso conta")
        self.tick(bs.planted + 2)
        self.assertEqual(bs.planted, 0)

    def test_the_pulse_ring_runs_both_ways_and_swaps_the_controls(self):
        g, p, bs = self.game, self.p, self.bs
        self.face_off(gap=4)
        bs.move = ("wave", 0)
        self.tick(20)
        waves = [b for b in g.balls if getattr(b, "kind", "") == "wave"]
        self.assertEqual(sorted(b.d for b in waves), [-1, 1], "l'anello corre da tutte e due le parti")
        p.invuln = 0
        for _ in range(60):
            self.tick(1)
            if getattr(p, "swap_t", 0):
                break
        self.assertGreater(p.swap_t, 0, "colpito dall'anello: comandi girati")
        self.tick(1)
        self.assertTrue(p.swapped)
        self.tick(130)
        self.assertFalse(p.swapped, "per due secondi")

    def test_the_mantle_eats_the_visor_light_from_afar(self):
        g, p, bs = self.game, self.p, self.bs
        self.face_off(gap=20)
        self.tick(120)
        self.assertGreater(g.dark, 0.9, "lontano: buio")
        self.assertGreater(g.mantle_k, 0.9)
        self.face_off(gap=4)
        self.tick(120)
        self.assertLess(g.dark, levels.cfg(1)["night"] + 0.05, "vicino: la notte normale di Nix")
        self.assertLess(g.mantle_k, 0.1)

    def test_the_sequence_changes_after_a_hit(self):
        bs = self.bs
        seq = []
        for _ in range(6):
            seq.append(bs.choose(300, self.p))
        self.assertEqual(seq, bs.cfg["moves"])
        with unittest.mock.patch("random.randrange", return_value=3):
            bs.hit(12)
        self.assertEqual(bs.seq_i, 3)

    def test_he_jumps_with_the_gravity_of_nix(self):
        g, bs = self.game, self.bs
        self.face_off(gap=8)
        bs.move = ("dive", 0)
        top = bs.y
        for _ in range(120):
            self.tick(1)
            top = min(top, bs.y)
            if bs.on_ground and bs.move is None:
                break
        # la salita della picchiata dura 20 fotogrammi: su Titano arriva a ~3,4 tessere, qui oltre 4
        self.assertGreater((G * TILE - bs.h - top) / TILE, 4, "la picchiata sale alto come un salto di Nix")


if __name__ == "__main__":
    unittest.main()
