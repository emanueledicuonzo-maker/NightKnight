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
        """Dall'ultima guglia, aspettando il momento giusto, il cavo porta di la'."""
        import athletics
        g = self.game
        idle = defaultdict(bool)
        keys = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_SPACE: True})
        crossed = False
        for wait in range(0, 170, 10):
            col, top, length = levels.TITAN_CABLES[0][0]
            cables = athletics.Cables([[athletics.Cable((levels.TITAN_PASS_START + col) * TILE + TILE // 2,
                                                        athletics.FLOOR - top, length, levels.ROPE_SPEEDS[0])]])
            cable = cables.all[0]
            p = goblin.Player((levels.TITAN_PASS_START + 78) * TILE, (levels.GROUND - 4) * TILE - goblin.Player.h)
            p.on_ground = True
            for _ in range(wait):
                cables.update_player(p, idle, g.lv)
            p.do_jump()
            for _ in range(400):
                cables.update_player(p, keys, g.lv)
                if cable.attached and cable.rope.body.velocity.x > 0 \
                        and cable.rope.body.position.x > cable.rope.anchor.x + 120:
                    cables.release(p)
                if p.on_ground or g.lv.drowned(p.rect):
                    break
            if p.on_ground and p.rect.left > (levels.TITAN_PASS_ROPE + 4) * TILE:
                crossed = True
                break
        self.assertTrue(crossed)

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

    def test_spinning_kick_in_motion_hits_all_around_and_leaves_you_open(self):
        g = self.game
        p = g.player
        p.on_ground = False
        p.vx = 0                                  # salto da fermo: calcio volante semplice
        g.key(pygame.K_c)
        self.assertEqual(p.attack[0], "kick")
        p.attack = None
        p.vx = goblin.RUN_MAX                     # salto in movimento: calcio girato
        g.key(pygame.K_c)
        self.assertEqual(p.attack[0], "spin")
        p.attack = ("spin", 10)
        box, _ = p.attack_box()
        self.assertLess(box.left, p.rect.left - 100)
        self.assertGreater(box.right, p.rect.right + 100)
        p.on_ground = True
        keys = defaultdict(bool)
        p.update(keys, g.lv)
        self.assertIsNone(p.attack)
        self.assertGreater(p.recover, 0)
        self.assertFalse(p.start_attack("throw"))     # scoperto per un attimo

    def test_oxygen_drains_outdoors_and_refills_at_stations(self):
        g = self.game
        p = g.player
        station = g.stations[1]
        p.x = station.x + 900
        p.oxygen = 50
        for _ in range(60):
            g.update()
        self.assertLess(p.oxygen, 50)
        p.x, p.y = station.x - p.w / 2, station.floor - p.h
        for _ in range(60):
            g.update()
        self.assertEqual(p.oxygen, goblin.OXYGEN_MAX)

    def test_cryogenic_gas_slows_down(self):
        g = self.game
        p = g.player
        vent = g.vents[0]
        vent.started, vent.age = True, vent.REST + 40
        p.x, p.y = vent.x - p.w / 2, vent.floor - p.h
        self.assertTrue(vent.update(p))
        g.update()
        self.assertGreater(p.chill, 0)

    def test_new_game_frees_no_prisoner(self):
        g = self.game
        first = min(g.spenti, key=lambda s: s.x)
        g.player.x = first.x - g.player.w / 2
        g.update()
        self.assertTrue(first.liberated)
        g.lives = 1
        g.lose_life()                             # game over, poi "riprova"
        g.state = "gameover"
        g.key(pygame.K_DOWN)                      # NUOVA PARTITA
        g.key(pygame.K_RETURN)
        self.assertEqual(g.state, "weapon_select")
        g.key(pygame.K_RETURN)
        self.assertEqual(g.part, "surface")
        self.assertFalse(any(s.liberated for s in g.spenti))
        self.assertEqual(g.player.albedo, 0)

    def test_creatures_sound_like_flesh_and_skeletons_like_bone(self):
        g = self.game
        with patch.object(g.jb, "fx") as fx:
            g.hit_enemy(goblin.Walker(500, "lizard"), 0.1)
            fx.assert_called_with("flesh_hit")
            g.hit_enemy(goblin.Walker(500, "skeleton"), 0.1)
            fx.assert_called_with("hit")

    def test_a_lost_life_restarts_from_the_last_stage(self):
        g = self.game
        p = g.player
        col, row = levels.TITAN_STAGES[3]
        p.x, p.y = (col + 2) * TILE, row * TILE - p.h
        g.update()
        self.assertEqual(g.stage, 3)
        g.lose_life()
        self.assertLess(abs(g.player.rect.centerx - (col * TILE + TILE / 2)), TILE)
        self.assertEqual(g.waves.waves[0].state, "done")          # la prima ondata e' alle spalle
        self.assertEqual(g.saved["checkpoint"]["stage"], 3)
        g.continue_game()
        self.assertEqual(g.stage, 3)

    def test_every_stage_stands_on_solid_ground(self):
        g = self.game
        for col, row in levels.TITAN_STAGES:
            with self.subTest(col=col):
                self.assertTrue(g.lv.solid(col * TILE + 32, row * TILE + 2))
                self.assertFalse(g.lv.solid(col * TILE + 32, row * TILE - 2))

    def test_continue_after_game_over_keeps_the_stage(self):
        g = self.game
        p = g.player
        col, row = levels.TITAN_STAGES[4]
        p.x, p.y = (col + 2) * TILE, row * TILE - p.h
        g.update()
        g.freed = {(0, "surface", 1), (0, "surface", 2)}
        g.score = 5000
        g.lives = 1
        g.lose_life()
        self.assertEqual(g.state, "gameover")
        self.assertEqual(g.menu_items()[g.menu_index], "CONTINUA")
        g.key(pygame.K_RETURN)
        self.assertEqual(g.lives, 3)
        self.assertEqual(g.score, 0)                                  # il prezzo del continua
        self.assertEqual(g.stage, 4)
        self.assertEqual(len(g.freed), 2)
        self.assertEqual(g.part, "surface")


if __name__ == "__main__":
    unittest.main()
