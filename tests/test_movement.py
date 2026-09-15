from collections import defaultdict
import unittest

import pygame

import goblin
import levels


def spans(row, value):
    start = None
    for i, cell in enumerate(row + [None]):
        if cell == value and start is None:
            start = i
        elif cell != value and start is not None:
            yield start, i
            start = None


class MovementTests(unittest.TestCase):
    def setUp(self):
        self.lv = goblin.Level(levels.gen_arena(levels.cfg(0)), "arena")
        self.keys = defaultdict(bool)

    def test_every_surface_gap_is_jumpable_both_ways(self):
        for cemetery in range(12):
            lv = goblin.Level(levels.gen_surface(levels.cfg(cemetery)), "surface")
            for start, end in spans(lv.g[levels.GROUND], "."):
                for facing in (1, -1):
                    with self.subTest(cemetery=cemetery + 1, gap=(start, end), facing=facing):
                        x = start * 64 - 32 if facing == 1 else end * 64 - goblin.Player.w + 32
                        p = goblin.Player(x, levels.GROUND * 64 - goblin.Player.h)
                        p.on_ground = True
                        p.vx = facing * goblin.RUN_MAX
                        keys = defaultdict(bool, {pygame.K_SPACE: True,
                                                  pygame.K_RIGHT if facing == 1 else pygame.K_LEFT: True})
                        p.do_jump()
                        for frame in range(90):
                            if end - start == 1 and frame >= 6:
                                keys[pygame.K_SPACE] = False
                            p.update(keys, lv)
                            if p.on_ground:
                                break
                        self.assertTrue(p.on_ground, (p.x, p.y))
                        self.assertLessEqual(p.rect.bottom, levels.GROUND * 64)
                        if facing == 1:
                            self.assertGreater(p.rect.right, end * 64)
                        else:
                            self.assertLess(p.rect.left, start * 64)

    def test_tapped_jump_from_rest_clears_every_surface_gap(self):
        for cemetery in range(12):
            lv = goblin.Level(levels.gen_surface(levels.cfg(cemetery)), "surface")
            for start, end in spans(lv.g[levels.GROUND], "."):
                with self.subTest(cemetery=cemetery + 1, gap=(start, end)):
                    p = goblin.Player(start * 64 - goblin.Player.w - 8,
                                      levels.GROUND * 64 - goblin.Player.h)
                    p.on_ground = True
                    keys = defaultdict(bool, {pygame.K_RIGHT: True})
                    p.do_jump()
                    for _ in range(90):
                        p.update(keys, lv)
                        if p.on_ground:
                            break
                    self.assertTrue(p.on_ground)
                    self.assertGreater(p.rect.right, end * 64)

    def test_every_crypt_has_a_walkable_route_with_spike_jumps(self):
        for cemetery in range(12):
            with self.subTest(cemetery=cemetery + 1):
                lv = goblin.Level(levels.gen_crypt(levels.cfg(cemetery)), "crypt")
                p = goblin.Player(2 * 64, 15 * 64 - goblin.Player.h)
                p.on_ground = True
                hazards = list(spans(lv.g[15], "^"))
                keys = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_SPACE: True})
                exit_x = lv.exit[0] * 64
                for _ in range(lv.w):
                    for start, end in hazards:
                        if p.on_ground and start * 64 - p.w - 12 <= p.x < start * 64 - p.w:
                            p.do_jump()
                    p.update(keys, lv)
                    self.assertLess(p.rect.bottom, goblin.H)
                    if p.on_ground:
                        for x in (p.rect.left + 4, p.rect.right - 5):
                            self.assertNotEqual(lv.tile_at(x, p.rect.bottom + 2), "^")
                    if p.rect.right > exit_x:
                        break
                self.assertGreater(p.rect.right, exit_x, (p.x, p.y))

    def test_late_jump_has_no_double_jump(self):
        p = goblin.Player(200, 600)
        p.coyote = 4
        self.assertTrue(p.do_jump())
        self.assertFalse(p.do_jump())
        self.assertEqual(p.coyote, 0)

    def test_coyote_window_expires_after_walking_off_edge(self):
        p = goblin.Player(200, 200)
        p.coyote = goblin.COYOTE_FRAMES
        for _ in range(goblin.COYOTE_FRAMES + 1):
            p.update(self.keys, self.lv)
        self.assertFalse(p.do_jump())
        self.assertGreater(p.vy, 0)

    def test_buffered_jump_fires_on_landing(self):
        p = goblin.Player(200, levels.GROUND * 64 - goblin.Player.h - 5)
        p.vy = 3
        self.assertFalse(p.do_jump())
        self.keys[pygame.K_SPACE] = True
        for _ in range(3):
            p.update(self.keys, self.lv)
            if p.jumped:
                break
        self.assertTrue(p.jumped)
        self.assertEqual(p.vy, goblin.JUMP_V)
        self.assertFalse(p.on_ground)

    def test_expired_buffer_does_not_jump_on_landing(self):
        p = goblin.Player(200, 200)
        p.do_jump()
        for _ in range(100):
            p.update(self.keys, self.lv)
            self.assertFalse(p.jumped)
        self.assertTrue(p.on_ground)

    def test_spikes_support_feet_instead_of_swallowing_player(self):
        self.lv.g[levels.GROUND][5] = "^"
        p = goblin.Player(5 * 64, levels.GROUND * 64 - goblin.Player.h - 10)
        p.vy = 8
        for _ in range(3):
            p.update(self.keys, self.lv)
        self.assertTrue(p.on_ground)
        self.assertEqual(p.rect.bottom, levels.GROUND * 64)
