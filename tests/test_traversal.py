import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

import goblin
import levels

TILE = 64


class TraversalTests(unittest.TestCase):
    """La traversata di Titano: segue le ondate nella stessa mappa, poi il duello."""

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.game = goblin.Game(windowed=True, save_path=Path(cls.temp.name)/"save.json")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.game.new_game()
        self.game.state = "play"

    def test_traversal_follows_the_waves_in_the_same_map(self):
        g = self.game
        self.assertEqual(g.part, "surface")
        self.assertGreater(g.lv.cols, levels.TITAN_PASS_START + 100)
        self.assertIsNotNone(g.cable)
        self.assertNotIn("PROVE ATLETICHE", g.menu_items())

    def test_cable_carries_across_its_lake(self):
        g = self.game
        p = g.player
        p.x = (levels.TITAN_PASS_ROPE - 6) * TILE
        p.y = levels.GROUND * TILE - p.h
        p.do_jump()
        keys = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_SPACE: True})
        grabbed = False
        for _ in range(240):
            g.cable.update_player(p, keys, g.lv)
            if not grabbed:
                g.cable.interact(p, g.lv)
                grabbed = g.cable.attached
            elif g.cable.rope.body.position.x > g.cable.rope.anchor.x + 120:
                g.cable.release(p)
                break
        self.assertTrue(grabbed)
        for _ in range(150):
            g.cable.update_player(p, keys, g.lv)
            if p.on_ground:
                break
        self.assertTrue(p.on_ground)
        self.assertGreater(p.rect.left, (levels.TITAN_PASS_ROPE + 4) * TILE)

    def test_reaching_the_traversal_is_a_restart_point(self):
        g = self.game
        g.player.x = (levels.TITAN_PASS_START + 2) * TILE
        g.update()
        self.assertTrue(g.reached_pass)
        g.spawn()                                       # vita persa
        self.assertGreaterEqual(g.player.x, levels.TITAN_PASS_START * TILE)
        self.assertTrue(all(w.state == "done" for w in g.waves.waves))

    def test_exit_leads_straight_to_the_guardian(self):
        g = self.game
        g.next_part()
        self.assertEqual(g.part, "arena")

    def test_sword_reaches_low_enemies(self):
        g = self.game
        p = g.player
        lizard = goblin.Walker(p.rect.right + 20, "lizard")
        p.facing = 1
        p.attack = ("throw", 6)
        box, dmg = p.attack_box()
        self.assertTrue(box.colliderect(lizard.rect))

    def test_stone_flies_and_hurts(self):
        g = self.game
        p = g.player
        skeleton = goblin.Walker(p.rect.right + 200, "skeleton")
        g.skels.append(skeleton)
        hp = skeleton.hp
        g.key(pygame.K_x)
        self.assertTrue(any(isinstance(b, goblin.Stone) for b in g.balls))
        for _ in range(30):
            g.update()
        self.assertLess(skeleton.hp, hp)

    def test_zombie_hit_uses_flesh_sound(self):
        g = self.game
        zombie = goblin.Zombie(500, levels.cfg(0))
        with patch.object(g.jb, "fx") as fx:
            g.hit_enemy(zombie, 3)
            fx.assert_called_once_with("flesh_hit")


if __name__ == "__main__":
    unittest.main()
