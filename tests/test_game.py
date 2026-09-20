import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

import pygame

import assets
import goblin
import levels
import progress
import music
import numpy as np


class ProgressTests(unittest.TestCase):
    def test_invalid_files_start_cleanly(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            for contents in ('{', '[]', '{"checkpoint": {"cemetery": 99}}'):
                path.write_text(contents)
                self.assertIsNone(progress.load(path)["checkpoint"])

    def test_checkpoint_roundtrip_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            cp = {"cemetery": 2, "part": "crypt", "lives": 2, "score": 1234,
                  "powers": [levels.cfg(i)["power"] for i in range(2)]}
            data = {"high_score": 5000, "checkpoint": cp}
            self.assertIsNone(progress.save(data, path))
            self.assertEqual(progress.load(path), data)
            cp["powers"] = []
            path.write_text(json.dumps(data))
            self.assertEqual(progress.load(path), {"high_score": 5000, "checkpoint": None})

    def test_failed_save_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNotNone(progress.save({}, Path(directory) / "missing" / "save.json"))


class GameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.game = goblin.Game(windowed=True, save_path=Path(cls.directory.name) / "save.json")

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls.directory.cleanup()

    def setUp(self):
        self.game.set_paused(False)
        self.game.new_game()

    def test_pause_freezes_world_and_ignores_attacks(self):
        g = self.game
        g.state = "play"
        g.key(pygame.K_ESCAPE)
        before = (g.frame, g.player.x, g.player.y, g.spawn_t)
        g.key(pygame.K_z)
        for _ in range(10):
            g.update()
        self.assertEqual(before, (g.frame, g.player.x, g.player.y, g.spawn_t))
        self.assertIsNone(g.player.attack)
        g.key(pygame.K_RETURN)
        g.update()
        self.assertFalse(g.paused)
        self.assertEqual(g.frame, before[0] + 1)

    def test_continue_restores_section_and_powers(self):
        g = self.game
        g.ci = 2
        g.score = 1200
        g.lives = 2
        g.powers = [levels.cfg(i)["power"] for i in range(2)]
        g.start_part("crypt")
        checkpoint = progress.load(g.save_path)["checkpoint"]
        g.player.x = 2000
        g.score = 9999
        g.save_progress()
        g.continue_game()
        self.assertEqual(g.part, "crypt")
        self.assertEqual(g.score, checkpoint["score"])
        self.assertEqual(g.player.x, 2 * goblin.TILE)
        self.assertEqual(g.player.power, checkpoint["powers"][-1])
        self.assertEqual(g.lives, 2)

    def test_gameover_clears_checkpoint_keeps_record(self):
        g = self.game
        g.score = 999
        g.lives = 1
        g.lose_life()
        saved = progress.load(g.save_path)
        self.assertIsNone(saved["checkpoint"])
        self.assertGreaterEqual(saved["high_score"], 999)

    def test_new_round_resets_combat_state(self):
        g = self.game
        g.powers = ["ice"]
        g.start_part("arena")
        g.player.attack = ("cosmo", 30)
        g.player.vy = -15
        g.player.invuln = 70
        g.player.climbing = True
        g.player.armor = False
        g.start_round()
        self.assertIsNone(g.player.attack)
        self.assertEqual((g.player.vx, g.player.vy, g.player.invuln), (0, 0, 0))
        self.assertFalse(g.player.climbing)
        self.assertTrue(g.player.armor)
        self.assertEqual(g.player.power, "ice")

    def test_victory_is_saved_before_reward_screen_closes(self):
        g = self.game
        g.start_part("arena")
        g.state = "play"
        g.next_part()
        cp = progress.load(g.save_path)["checkpoint"]
        self.assertEqual((cp["cemetery"], cp["part"]), (1, "surface"))
        self.assertEqual(cp["powers"], [levels.cfg(0)["power"]])
        g.next_part()
        self.assertEqual(len(g.powers), 1)
        g.continue_game()
        self.assertEqual((g.ci, g.part), (1, "surface"))

    def test_all_cemetery_rewards_reach_the_ending(self):
        g = self.game
        for i in range(12):
            self.assertEqual(g.ci, i)
            g.state = "play"
            g.next_part()
            self.assertEqual(g.part, "crypt")
            g.state = "play"
            g.next_part()
            self.assertEqual(g.part, "trials")
            g.trials.done = set(range(5))
            g.state = "play"
            g.next_part()
            self.assertEqual(g.part, "arena")
            g.state = "play"
            g.next_part()
            self.assertEqual(g.state, "armor")
            self.assertEqual(len(g.powers), i + 1)
            g.after_armor()
        self.assertEqual(g.state, "end")
        self.assertIsNone(progress.load(g.save_path)["checkpoint"])

    def test_cancelled_attack_does_not_hit_later_enemy(self):
        g = self.game
        g.state = "play"
        p = g.player
        p.on_ground = True
        p.attack = ("throw", 5)
        def enemy(x):
            return SimpleNamespace(x=x, rect=pygame.Rect(x, p.y, 70, 176), alive=True,
                                   hp=100, frozen=0, update=lambda *_: None)
        touching = enemy(p.x)
        ahead = enemy(p.rect.right + 30)
        g.skels = [touching, ahead]
        g.update()
        self.assertIsNone(p.attack)
        self.assertEqual(ahead.hp, 100)

    def test_dead_enemy_cannot_award_points_twice(self):
        g = self.game
        e = SimpleNamespace(hp=1, alive=True)
        g.hit_enemy(e, 10)
        score = g.score
        g.hit_enemy(e, 10)
        self.assertEqual(g.score, score)

    def test_knockout_cannot_turn_into_a_player_death(self):
        g = self.game
        g.start_part("arena")
        g.state = "play"
        g.intro = 0
        g.player.armor = False
        g.player.hp = 1
        g.boss.hp = 0
        g.hurt_player(100, g.player.x)
        self.assertEqual(g.player.hp, 1)
        g.key(pygame.K_x)
        self.assertIsNone(g.player.attack)
        g.update()
        self.assertEqual(g.rounds, [1, 0])
        score = g.score
        g.update()
        self.assertEqual(g.rounds, [1, 0])
        self.assertEqual(g.score, score)

    def test_jump_sheet_advances_during_ascent(self):
        p = self.game.player
        p.on_ground = False
        if "jump" not in self.game.gfx.sheets[True]:
            self.skipTest("No jump sheet installed")
        frames = self.game.gfx.sheets[True]["jump"][0]
        p.vy = goblin.JUMP_V
        self.assertIs(p.sheet_frame(self.game.gfx), frames[0])
        p.vy = -1
        self.assertIs(p.sheet_frame(self.game.gfx), frames[len(frames) // 2 - 1])

    def test_jump_is_available_immediately_after_spawn(self):
        for part in ("surface", "crypt", "trials", "arena"):
            self.game.start_part(part)
            p = self.game.player
            self.assertTrue(p.on_ground)
            self.assertTrue(p.do_jump())
            self.assertLess(p.vy, 0)

    def test_ambient_tracks_have_stereo_signal_without_clipping(self):
        for name in ("surface", "crypt", "arena", "victory"):
            samples = pygame.sndarray.array(music.track(name)).astype(np.int32)
            self.assertEqual(samples.shape[1], 2)
            self.assertGreater(samples.std(), 100)
            self.assertLess(np.abs(samples).max(), 30000)
            self.assertLess(np.abs(samples[-1] - samples[0]).max(), 2000)

    def test_music_mute_leaves_mixer_running(self):
        jb = self.game.jb
        jb.muted = False
        self.game.key(pygame.K_m)
        self.assertTrue(jb.muted)
        self.assertEqual(jb.chan.get_volume(), 0)
        self.assertTrue(pygame.mixer.get_init())
        self.game.key(pygame.K_m)
        self.assertGreater(jb.chan.get_volume(), 0)

    def test_exact_and_fitted_assets_have_separate_cache_entries(self):
        fitted = assets.load("knight_idle", 300, 100)
        exact = assets.load("knight_idle", 300, 100, exact=True)
        self.assertIsNot(fitted, exact)

    def test_render_all_sections_and_menus(self):
        g = self.game
        for part in ("surface", "crypt", "arena"):
            g.start_part(part)
            g.state = "play"
            g.cam = min(1300, g.lv.w - goblin.W)
            g.draw()
            self.assertGreater(pygame.surfarray.array3d(g.screen).std(), 5)
            g.set_paused(True)
            g.draw()
            g.set_paused(False)
        g.state = "title"
        g.draw()


if __name__ == "__main__":
    unittest.main()
