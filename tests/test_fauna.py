import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pathlib import Path
import tempfile
import unittest

import pygame

import goblin


class FaunaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.game = goblin.Game(windowed=True, save_path=Path(cls.temp.name) / "save.json")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        g = self.game
        g.new_game()
        g.state = "play"
        g.skels, g.crows = [], []
        g.player.x = 30 * goblin.TILE
        for w in g.waves.waves:
            w.state = "done"

    def jelly(self, dx=500, dy=-200):
        p = self.game.player
        j = goblin.Flyer(p.x + dx, p.y + dy, "jelly")
        self.game.crows.append(j)
        return j

    def test_jellyfish_go_straight_for_you_and_stick(self):
        g, j = self.game, self.jelly()
        for _ in range(200):
            g.update()
            if j.stuck is not None:
                break
        self.assertIsNotNone(j.stuck)
        self.assertEqual(g.player.jellies, 1)

    def test_stuck_jellyfish_slow_you_and_drain_life(self):
        g = self.game
        for i in range(4):
            self.jelly(20 * i, 0)
        for _ in range(3 * goblin.JELLY_EVERY):
            g.update()
        self.assertEqual(g.player.jellies, goblin.JELLY_MAX)       # mai piu' di tre
        self.assertLess(g.player.hp, goblin.PLAYER_HP)

    def test_a_slash_knocks_one_off_the_spinning_kick_all(self):
        g = self.game
        for i in range(3):
            self.jelly(20 * i, 0)
        for _ in range(5):
            g.update()
        self.assertEqual(g.player.jellies, 3)
        g.key(pygame.K_z)
        g.update()
        self.assertEqual(g.player.jellies, 2)
        g.player.attack = None
        g.player.on_ground, g.player.vx = False, goblin.RUN_MAX
        g.key(pygame.K_c)
        g.update()
        self.assertEqual(g.player.jellies, 0)

    def test_worms_walk_towards_you(self):
        g = self.game
        w = goblin.Walker(g.player.x + 600, "worm")
        g.skels.append(w)
        x0 = w.x
        for _ in range(60):
            g.update()
        self.assertLess(w.x, x0)

    def test_a_burrower_travels_hidden_and_bursts_under_your_feet(self):
        g = self.game
        p = g.player
        w = goblin.Walker(p.x + 500, "burrower")
        g.skels.append(w)
        g.update()
        self.assertTrue(w.hidden)
        p.hp = goblin.PLAYER_HP
        hurt, surfaced = False, False
        for _ in range(300):
            g.update()
            surfaced = surfaced or not w.hidden
            hurt = hurt or p.hp < goblin.PLAYER_HP
            if hurt:
                break
        self.assertTrue(surfaced)
        self.assertTrue(hurt)
        self.assertLess(abs(w.rect.centerx - p.rect.centerx), 120)

    def test_a_hidden_burrower_cannot_be_hit(self):
        g = self.game
        p = g.player
        w = goblin.Walker(p.rect.right + 20, "burrower")
        w.x -= 200                       # lontano dai piedi: resta sotto
        g.skels.append(w)
        p.facing, p.attack = 1, ("throw", 6)
        g.update()
        self.assertTrue(w.alive)


if __name__ == "__main__":
    unittest.main()
