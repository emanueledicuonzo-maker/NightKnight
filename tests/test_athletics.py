import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pygame

import athletics
import goblin
import levels
import progress


class AthleticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.game = goblin.Game(windowed=True, save_path=Path(cls.temp.name)/"save.json")

    @classmethod
    def tearDownClass(cls):
        # Font surfaces are shared by the other integration tests in this process.
        cls.temp.cleanup()

    def setUp(self):
        self.game.new_game(part="trials")
        self.game.state = "play"

    def test_running_approach_increases_jump_and_clears_trial(self):
        g = self.game
        p = g.player
        keys = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_LSHIFT: True, pygame.K_SPACE: True})
        while p.x < 12*64-p.w-8:
            g.trials.update_player(p, keys, g.lv)
        self.assertGreater(p.vx, goblin.RUN_MAX)
        p.do_jump()
        self.assertLess(p.vy, goblin.JUMP_V)
        for _ in range(100):
            g.trials.update_player(p, keys, g.lv)
            if p.on_ground:
                break
        self.assertIn(0, g.trials.done)
        self.assertGreater(g.trials.best_jump, 384)

    def test_rope_can_be_grabbed_and_crossed(self):
        g = self.game
        p = g.player
        p.x = 30*64
        p.do_jump()
        keys = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_SPACE: True})
        grabbed = False
        for _ in range(180):
            g.trials.update_player(p, keys, g.lv)
            if not grabbed:
                g.trials.interact(p, g.lv)
                grabbed = g.trials.attached
            elif g.trials.rope.body.position.x > g.trials.rope.anchor.x + 120:
                g.trials.release(p)
                break
        self.assertTrue(grabbed)
        self.assertFalse(g.trials.attached)
        self.assertGreater(p.vx, 0)
        for _ in range(120):
            g.trials.update_player(p, keys, g.lv)
            if p.on_ground:
                break
        self.assertIn(1, g.trials.done, (p.x, p.y))

    def test_mount_hurdles_and_dismount(self):
        g = self.game
        p = g.player
        p.x = g.trials.horse_x-p.w/2
        g.key(pygame.K_e)
        self.assertTrue(p.mounted)
        keys = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_SPACE: True})
        for _ in range(400):
            if p.on_ground and any(0 < x*64-p.rect.right < 180 for x in (52, 58, 64)):
                p.do_jump()
            g.trials.update_player(p, keys, g.lv)
            if 2 in g.trials.done and p.on_ground:
                break
        self.assertIn(2, g.trials.done)
        g.key(pygame.K_e)
        self.assertFalse(p.mounted)

    def test_targets_require_correct_projectile_and_score_once(self):
        g = self.game
        for target in g.trials.targets:
            p = g.player
            p.x = target["rect"].x - 360
            p.y = athletics.FLOOR-p.h
            p.facing = 1
            g.cam = max(0, int(p.x - goblin.W//2))
            shot = athletics.WeaponShot(target["weapon"], p)
            points = 0
            for _ in range(40):
                shot.update(g.lv, g.cam)
                points += g.trials.check_targets([shot])
                if not shot.alive:
                    break
            self.assertTrue(target["hit"])
            self.assertEqual(points, 250)
            self.assertEqual(g.trials.check_targets([shot]), 0)
        self.assertTrue({3, 4}.issubset(g.trials.done))

    def test_wrong_weapon_does_not_complete_target(self):
        g = self.game
        target = g.trials.targets[0]
        shot = athletics.WeaponShot("dagger", g.player)
        shot.rect = target["rect"].copy()
        self.assertEqual(g.trials.check_targets([shot]), 0)
        self.assertFalse(target["hit"])

    def test_actual_throw_input_hits_target_during_game_update(self):
        g = self.game
        target = g.trials.targets[0]
        g.player.x = target["rect"].x - 360
        g.key(pygame.K_f)
        self.assertEqual(len(g.balls), 1)
        for _ in range(40):
            g.update()
        self.assertTrue(target["hit"])
        self.assertEqual(g.score, 250)

    def test_horse_frames_reach_same_baseline(self):
        frames = self.game.trials.horse_frames
        self.assertEqual(len(frames), 8)
        self.assertTrue(all(frame.get_bounding_rect().bottom == 210 for frame in frames))

    def test_trial_checkpoint_and_exit_gate(self):
        g = self.game
        self.assertEqual(progress.load(g.save_path)["checkpoint"]["part"], "trials")
        g.next_part()
        self.assertEqual(g.part, "trials")
        g.trials.done = set(range(5))
        g.next_part()
        self.assertEqual(g.part, "arena")

    def test_running_and_punching_have_distinct_frames_and_damage(self):
        g = self.game
        p = g.player
        p.vx = 4
        p.run_t = 0
        a = p.sheet_frame(g.gfx)
        if a is None:
            self.skipTest("No run sheet installed")
        p.run_t = 2
        b = p.sheet_frame(g.gfx)
        self.assertNotEqual(pygame.image.tobytes(a, "RGBA"), pygame.image.tobytes(b, "RGBA"))
        g.key(pygame.K_x)
        p.attack = ("punch", 5)
        if "punch" in g.gfx.sheets:
            self.assertIsNotNone(p.sheet_frame(g.gfx))
        box, damage = p.attack_box()
        self.assertGreater(damage, 0)
        self.assertGreater(box.right, p.rect.right)

    def test_zombie_hit_uses_flesh_sound(self):
        g = self.game
        zombie = goblin.Zombie(500, levels.cfg(0))
        with patch.object(g.jb, "fx") as fx:
            g.hit_enemy(zombie, 3)
            fx.assert_called_once_with("flesh_hit")
