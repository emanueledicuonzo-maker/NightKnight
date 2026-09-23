import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
from pathlib import Path
import tempfile
import unittest

import pygame
import goblin
import titan


class TitanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # La suite precedente chiude pygame: non riusare font legati a SDL chiuso.
        goblin.px._font.cache_clear()
        goblin.px._text_image.cache_clear()
        cls.temp = tempfile.TemporaryDirectory()
        cls.game = goblin.Game(windowed=True, save_path=Path(cls.temp.name) / "save.json")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.game.set_paused(False)
        self.game.new_game()
        self.game.state = "play"

    def test_warning_is_safe_eruption_hurts_and_pause_freezes(self):
        g = self.game
        vent = g.geysers[0]
        g.player.x = vent.x - g.player.w / 2
        vent.age = vent.REST
        g.update()
        self.assertEqual(vent.phase, "warning")
        self.assertEqual(g.player.hp, 100)
        g.set_paused(True)
        age = vent.age
        g.update()
        self.assertEqual(vent.age, age)
        g.set_paused(False)
        vent.age = vent.REST + vent.WARNING - 1
        g.update()
        self.assertEqual(g.player.hp, 75)
        g.update()
        self.assertEqual(g.player.hp, 75)  # invulnerabilita': niente danni ogni frame

    def test_each_geyser_can_be_crossed_during_rest(self):
        g = self.game
        keys = defaultdict(bool, {pygame.K_RIGHT: True})
        for vent in g.geysers:
            with self.subTest(x=vent.x):
                p = goblin.Player(vent.x - 180, vent.floor - goblin.Player.h)
                p.on_ground = True
                vent.age = 0
                for _ in range(65):
                    p.update(keys, g.lv)
                    self.assertFalse(vent.update(p))
                self.assertGreater(p.rect.left, vent.hitbox.right)
                self.assertTrue(p.on_ground)

    def test_spenti_award_albedo_once_and_reset_with_section(self):
        g = self.game
        spento = g.spenti[0]
        g.player.x = spento.x - g.player.w / 2
        for _ in range(4):
            g.update()
        self.assertTrue(spento.liberated)
        self.assertEqual(g.player.albedo, 20)
        self.assertEqual(g.zombies, [])
        g.spawn()
        self.assertFalse(g.spenti[0].liberated)
        self.assertEqual(g.player.albedo, 0)

    def test_titan_render_all_phases(self):
        g = self.game
        for age in (0, titan.Geyser.REST, titan.Geyser.REST + titan.Geyser.WARNING):
            for vent in g.geysers:
                vent.age = age
            g.draw()
        g.start_part("crypt")
        self.assertEqual(g.geysers, [])
        self.assertEqual(g.spenti, [])
