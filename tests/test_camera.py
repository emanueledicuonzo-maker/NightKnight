import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from pathlib import Path
import tempfile
import unittest

import goblin
import levels

TILE = goblin.TILE


class CameraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.game = goblin.Game(windowed=True, save_path=Path(cls.temp.name) / "save.json")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def start(self):
        g = self.game
        g.reached_pass = True
        g.new_game()
        g.state = "play"
        for w in g.waves.waves:
            w.state = "done"
        return g

    def test_camera_rests_on_the_surface_at_the_old_height(self):
        g = self.start()
        for _ in range(30):
            g.update()
        self.assertEqual(int(g.camy), goblin.VIEW_Y)

    def test_camera_climbs_with_the_knight(self):
        g = self.start()
        p = g.player
        p.x = (levels.TITAN_PASS_START + 39) * TILE
        p.y = (levels.GROUND - 7) * TILE - p.h
        for _ in range(90):
            g.update()
        self.assertTrue(p.on_ground)
        self.assertEqual(int(g.camy), p.rect.bottom - goblin.FEET_IN_VIEW)

    def test_a_jump_on_flat_ground_barely_moves_the_camera(self):
        g = self.start()
        for _ in range(30):
            g.update()
        g.player.do_jump()
        lowest = g.camy
        for _ in range(60):
            g.update()
            lowest = min(lowest, g.camy)
        self.assertGreater(lowest, goblin.VIEW_Y - 2 * TILE)

    def test_falling_in_a_methane_lake_drowns(self):
        g = self.start()
        start, end = next((c, c + 3) for c in range(g.lv.cols) if g.lv.g[levels.GROUND][c] == "~")
        p = g.player
        p.x = start * TILE + 4
        p.y = (levels.GROUND - 1) * TILE - p.h
        p.on_ground = False
        for _ in range(120):
            g.update()
            if g.state != "play":
                break
        self.assertEqual(g.state, "dead")


if __name__ == "__main__":
    unittest.main()
