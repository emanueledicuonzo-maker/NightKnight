import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
from pathlib import Path
import tempfile
import unittest

import pygame
import goblin
import levels
import titan


class TitanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # La suite precedente chiude pygame: non riusare font legati a SDL chiuso.
        goblin.fonts._font.cache_clear()
        goblin.fonts._text_image.cache_clear()
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

    def test_prisoners_give_light_once_and_stay_freed_after_a_death(self):
        g = self.game
        first = lambda: min(g.spenti, key=lambda s: s.x)     # il primo, a terra
        spento = first()
        g.player.x = spento.x - g.player.w / 2
        for _ in range(4):
            g.update()
        self.assertTrue(spento.liberated)
        self.assertEqual(g.player.albedo, goblin.LUCE_PER_PRISONER)
        g.spawn()                                  # vita persa: si riparte dalla sezione
        self.assertTrue(first().liberated)
        self.assertEqual(g.player.albedo, goblin.LUCE_PER_PRISONER)
        g.player.x = first().x - g.player.w / 2
        g.update()
        self.assertEqual(g.player.albedo, goblin.LUCE_PER_PRISONER)

    def sortie_scene(self, flyers, walkers):
        g = self.game
        g.waves.patrols = None
        for w in g.waves.waves:
            w.state = "done"
        g.skels, g.crows = [], []
        p = g.player
        p.x, p.y = 128 * goblin.TILE, levels.GROUND * goblin.TILE - p.h
        g.bianca = goblin.Bianca(p)
        for _ in range(20):
            g.update()
        for i in range(flyers):
            g.crows.append(goblin.Flyer(p.x + 150 + 60 * i, p.y - 200, "crow"))
            g.crows[-1].state = "wait"
        for i in range(walkers):
            w = goblin.Walker(p.x - 350 - 40 * i, "skeleton")
            w.frozen = 10 ** 6
            g.skels.append(w)
        for c in g.crows:
            c.frozen = 10 ** 6
        return g, list(g.crows), list(g.skels)

    def run_frames(self, g, n):
        for _ in range(n):
            g.update()
            g.player.hp, g.player.invuln = goblin.PLAYER_HP, 5

    def test_bianca_attacks_alone_only_flyers_five_at_most(self):
        g, crows, skels = self.sortie_scene(flyers=7, walkers=3)
        self.run_frames(g, 400)
        self.assertEqual(sum(not c.alive for c in crows), goblin.BIANCA_SORTIE)
        self.assertTrue(all(k.alive for k in skels))              # i nemici di terra no
        self.assertGreater(g.bianca.rest, 0)                        # poi riposa

    def test_bianca_does_not_move_for_few_flyers(self):
        g, crows, _ = self.sortie_scene(flyers=goblin.BIANCA_CROWD, walkers=0)
        self.run_frames(g, 300)
        self.assertTrue(all(c.alive for c in crows))

    def test_v_sends_bianca_on_anyone_for_one_unit_of_light(self):
        g, crows, skels = self.sortie_scene(flyers=1, walkers=6)
        g.player.albedo = 60
        self.assertTrue(g.luce_burst())
        self.assertEqual(g.player.albedo, 35)                       # un'unita' da 25
        self.run_frames(g, 400)
        self.assertFalse(crows[0].alive)
        self.assertEqual(sum(not k.alive for k in skels), goblin.BIANCA_SORTIE - 1)

    def test_v_takes_five_percent_from_the_guardian(self):
        g = self.game
        g.start_part("arena")
        g.state = "play"
        g.player.albedo = 100
        hp = g.boss.hp
        g.luce_burst()
        self.assertEqual(hp - g.boss.hp, round(g.boss.max_hp * 0.05))
        g.start_part("surface")
        g.state = "play"

    def test_nova_needs_ten_colonists_and_works_once(self):
        g, crows, skels = self.sortie_scene(flyers=3, walkers=3)
        far = goblin.Walker(g.player.x + 3000, "skeleton")
        g.skels.append(far)
        g.freed = {(0, "surface", i) for i in range(goblin.NOVA_PRISONERS - 1)}
        self.assertFalse(g.start_nova())                             # nove non bastano
        g.freed.add((0, "surface", 99))
        self.assertTrue(g.start_nova())
        for _ in range(goblin.NOVA_FRAMES + 2):
            g.update()
        self.assertTrue(all(not e.alive for e in crows + skels))     # chi era in scena
        self.assertTrue(far.alive)                                   # chi era lontano no
        self.assertFalse(g.start_nova())                             # una sola per livello
        self.assertTrue(g.player.on_ground)

    def test_nova_takes_a_tenth_from_the_guardian(self):
        g = self.game
        g.start_part("arena")
        g.state = "play"
        g.freed = {(0, "surface", i) for i in range(goblin.NOVA_PRISONERS)}
        g.nova_used = False
        hp = g.boss.hp
        self.assertTrue(g.start_nova())
        for _ in range(goblin.NOVA_FRAMES + 2):
            g.update()
        self.assertEqual(hp - g.boss.hp, round(g.boss.max_hp * goblin.NOVA_BOSS))
        g.start_part("surface")
        g.state = "play"

    def test_titan_render_all_phases(self):
        g = self.game
        for age in (0, titan.Geyser.REST, titan.Geyser.REST + titan.Geyser.WARNING):
            for vent in g.geysers:
                vent.age = age
            g.draw()
        g.start_part("arena")
        self.assertEqual(g.geysers, [])
        self.assertEqual(g.spenti, [])
