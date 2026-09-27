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
        g.waves.patrols = None           # niente gruppetti: il test sceglie i nemici

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

    def test_worms_stay_where_they_emerge(self):
        import levels
        g = self.game
        g.player.x, g.player.y = 128 * goblin.TILE, levels.GROUND * goblin.TILE - g.player.h
        w = goblin.Walker(g.player.x + 300, "worm")
        g.skels.append(w)
        x0, y0 = w.x, w.y
        for _ in range(120):
            g.update()
            g.player.hp = goblin.PLAYER_HP
        self.assertEqual((w.x, w.y), (x0, y0))
        rest, bite = g.gfx.foes["worm"]
        self.assertLessEqual(bite.get_height(), rest.get_height() * 1.15)     # attaccando non si solleva

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

    def test_nitrogen_is_a_real_obstacle(self):
        from collections import defaultdict
        g = self.game
        p = g.player
        free = goblin.Player(p.x, p.y)
        free.on_ground = True
        free.do_jump()
        p.on_ground, p.chill = True, goblin.CHILL_FRAMES
        p.do_jump()
        self.assertGreater(p.vy, free.vy)                       # salto piu' corto
        p.on_ground, p.vy, p.vx = True, 0, 0
        keys = defaultdict(bool, {pygame.K_RIGHT: True})
        for _ in range(40):
            p.update(keys, g.lv)
        self.assertLessEqual(p.vx, goblin.RUN_MAX * goblin.CHILL_SPEED + 0.01)
        self.assertGreaterEqual(goblin.CHILL_FRAMES, 120)

    def test_the_cryovolcano_throws_you_off(self):
        g = self.game
        p = g.player
        geyser = g.geysers[0]
        geyser.started, geyser.age = True, geyser.REST + geyser.WARNING + 20
        p.x, p.y = geyser.x - p.w / 2 + 10, geyser.floor - p.h
        p.on_ground, p.invuln = True, 0
        g.update()
        self.assertLess(p.vy, -15)
        self.assertEqual(geyser.ERUPTION, 180)

    def test_without_air_you_do_not_die_but_you_are_weak(self):
        from collections import defaultdict
        g = self.game
        p = g.player
        p.oxygen = 0
        for _ in range(600):
            g.update()
        self.assertEqual(p.hp, goblin.PLAYER_HP)                 # non si muore
        self.assertEqual(p.power(goblin.SWORD_HIT), 0.5)         # un fendente vale mezzo sasso
        skeleton = goblin.Walker(p.rect.right + 20, "skeleton")
        g.skels.append(skeleton)
        g.hit_enemy(skeleton, p.power(goblin.SWORD_HIT))
        self.assertTrue(skeleton.alive)                          # ne servono due
        keys = defaultdict(bool, {pygame.K_RIGHT: True})
        p.on_ground, p.vx = True, 0
        for _ in range(40):
            p.update(keys, g.lv)
        self.assertLessEqual(p.vx, goblin.RUN_MAX * goblin.BREATHLESS_SPEED + 0.01)

    def test_the_nitrogen_jet_pushes_you_back(self):
        from collections import defaultdict
        g = self.game
        p = g.player
        v = min((v for v in g.vents if v.floor == g.player.rect.bottom), key=lambda v: v.x)
        v.started, v.age = True, v.REST + 30
        from unittest.mock import patch
        keys = defaultdict(bool, {pygame.K_RIGHT: True})
        with patch.object(pygame.key, "get_pressed", lambda: keys):
            p.x, p.y = v.x - 300, v.floor - p.h
            x0 = p.x
            for _ in range(60):
                g.update()
        self.assertLess(p.x, x0 + 20)                            # camminandoci contro non si passa
        self.assertGreater(p.chill, 0)

    def test_tremors_only_underground(self):
        import levels
        surface = [k for w in levels.TITAN_WAVES for k, _ in w["roster"]] + levels.TITAN_PATROLS["pool"]
        self.assertNotIn("burrower", surface)
        for kind, col, row in levels.TITAN_PASS_FOES:
            if kind == "burrower":
                self.assertGreater(row, levels.GROUND)

    def test_never_alone_for_long(self):
        import levels
        g = self.game
        g.waves.patrols = levels.TITAN_PATROLS
        g.waves.next_patrol = 10 ** 9            # niente strada nuova: conta solo il silenzio
        g.skels, g.crows = [], []
        for _ in range(levels.TITAN_PATROLS["quiet"] + 5):
            g.update()
            g.player.hp = goblin.PLAYER_HP
        self.assertTrue(g.skels or g.crows)

    def test_a_wave_left_far_behind_closes(self):
        g = self.game
        w = g.waves.waves[0]
        w.state = "fighting"
        straggler = goblin.Walker(w.x0, "skeleton")
        w.members, w.queue = [straggler], []
        g.skels = [straggler]
        g.player.x = w.x1 + 2000
        g.update()
        self.assertEqual(w.state, "done")

    def test_reinforcements_never_appear_inside_rock(self):
        import levels
        g = self.game
        p = g.player
        p.x, p.y = 232 * goblin.TILE, levels.GROUND * goblin.TILE - p.h        # ai piedi della montagna
        for col in range(236, 256):
            with self.subTest(col=col):
                w = g.make_walker(col * goblin.TILE, "lizard")
                r = w.rect
                self.assertFalse(any(g.lv.solid(x, y) for x in (r.left + 4, r.right - 4)
                                     for y in (r.top + 4, r.centery, r.bottom - 4)))

    def walker_run(self, kind, col, target_col, frames):
        import levels
        g = self.game
        hts = levels.surface_heights()
        T = goblin.TILE
        p = g.player
        p.x, p.y = target_col * T, (levels.GROUND - hts[target_col]) * T - p.h
        w = goblin.Walker(col * T, kind)
        w.y = (levels.GROUND - hts[col]) * T - w.h
        w.on_ground = True
        track = []
        for _ in range(frames):
            w.update(g.lv, p)
            track.append((w.rect.centerx, w.rect.bottom, w.facing))
        return w, track

    def test_walkers_jump_up_steps(self):
        import levels
        w, track = self.walker_run("skeleton", 40, 47, 400)
        self.assertLessEqual(min(b for _, b, _ in track), (levels.GROUND - 6) * goblin.TILE)   # in cima

    def test_walkers_hop_over_a_narrow_lake(self):
        w, track = self.walker_run("skeleton", 13, 26, 400)
        self.assertTrue(w.alive)
        self.assertGreater(w.rect.left, 18 * goblin.TILE)

    def test_walkers_turn_back_at_a_wall_they_cannot_climb(self):
        w, track = self.walker_run("skeleton", 233, 244, 300)
        self.assertLess(max(x for x, _, _ in track), 240 * goblin.TILE)
        self.assertIn(-1, [f for _, _, f in track])

    def test_worms_never_appear_on_a_lake(self):
        import levels
        g = self.game
        T = goblin.TILE
        p = g.player
        p.x, p.y = 12 * T, levels.GROUND * T - p.h
        for col in (16, 17, 55, 56):
            with self.subTest(col=col):
                w = g.make_walker(col * T, "worm")
                if w is None:
                    continue
                self.assertNotEqual(g.lv.tile_at(w.rect.centerx, w.rect.bottom + 2), "~")
                self.assertTrue(g.lv.solid(w.rect.centerx, w.rect.bottom + 2))

    def test_ladders_are_climbed_from_the_middle(self):
        from collections import defaultdict
        import levels
        g = self.game
        T = goblin.TILE
        p = goblin.Player(levels.TITAN_BIG_LADDER * T, levels.GROUND * T - goblin.Player.h)
        p.on_ground = True
        p.update(defaultdict(bool, {pygame.K_UP: True}), g.lv)
        self.assertTrue(p.climbing)
        self.assertAlmostEqual(p.rect.centerx, (levels.TITAN_BIG_LADDER + 1.5) * T, delta=2)

    def test_no_nitrogen_jet_blows_over_a_cryovolcano(self):
        g = self.game
        for v in g.vents:
            for q in g.geysers:
                with self.subTest(vent=v.x, geyser=q.x):
                    self.assertFalse(v.hitbox.inflate(160, 0).colliderect(q.hitbox) and abs(v.floor - q.floor) < 200)

    def test_nobody_appears_on_screen(self):
        import levels
        g = self.game
        g.skels, g.crows = [], []
        p = g.player
        for kind in ("skeleton", "worm", "crow", "jelly", "lizard") * 6:
            e = g.waves.spawn(kind, p.rect.centerx, g.skels, g.crows, p.rect.top)
            if e is None:
                continue
            with self.subTest(kind=kind):
                self.assertGreater(abs(e.rect.centerx - p.rect.centerx), goblin.DW // 2 + 60)

    def test_double_tap_and_hold_runs_and_costs_air(self):
        from collections import defaultdict
        from unittest.mock import patch
        import levels
        g = self.game
        p = g.player
        p.x, p.y = 128 * goblin.TILE, levels.GROUND * goblin.TILE - p.h
        keys = defaultdict(bool, {pygame.K_RIGHT: True})
        with patch.object(pygame.key, "get_pressed", lambda: keys):
            g.key(pygame.K_RIGHT)
            g.update()
            g.key(pygame.K_RIGHT)                    # secondo tocco, subito
            for _ in range(40):
                g.update()
            self.assertGreater(p.vx, goblin.RUN_MAX + 1)
            o2 = p.oxygen
            g.update()
            self.assertAlmostEqual(o2 - p.oxygen, goblin.OXYGEN_DRAIN * goblin.SPRINT_O2, places=5)
            keys[pygame.K_RIGHT] = False
            g.update()
            self.assertEqual(p.running, 0)           # lasciata la freccia, si smette

    def test_sword_reaches_further_and_chains_three_slashes(self):
        from collections import defaultdict
        import levels
        g = self.game
        p = g.player
        p.x, p.y, p.on_ground, p.facing = 128 * goblin.TILE, levels.GROUND * goblin.TILE - p.h, True, 1
        far = goblin.Walker(p.rect.right + 200, "skeleton")
        p.attack = ("throw", 6)
        box, _ = p.attack_box()
        self.assertTrue(box.colliderect(far.rect))                 # la spada arriva a 200 px
        p.attack = None
        keys = defaultdict(bool)
        combos, x0 = [], p.x
        for frame in range(90):
            if frame % 8 == 0:
                p.slash()                                          # Z premuto a ritmo
            p.update(keys, g.lv)
            if p.attack:
                combos.append(p.combo)
        self.assertEqual(max(combos), goblin.COMBO_MAX)
        self.assertEqual(sorted(set(combos)), [1, 2, 3])
        self.assertGreater(p.x, x0 + 40)                           # il terzo fa un passo avanti

    def test_worms_emerge_only_on_flat_base_ground(self):
        import levels
        g = self.game
        T = goblin.TILE
        hts = levels.surface_heights()
        p = g.player
        for col in range(20, 420, 3):
            p.x, p.y = (col - 18) * T, (levels.GROUND - hts[col - 18]) * T - p.h
            w = g.make_walker(col * T, "worm")
            if w is None:
                continue                                  # niente posto in piano: niente verme
            c = w.rect.centerx // T
            with self.subTest(col=col):
                self.assertEqual(w.rect.bottom, levels.GROUND * T)
                self.assertTrue(all(hts[k] == 0 for k in range(c - 2, c + 3)))

    def test_crawlers_come_at_you_in_the_galleries_without_jumping(self):
        import levels
        g = self.game
        T = goblin.TILE
        x0 = levels.TITAN_PASS_START
        p = g.player
        p.x, p.y = (x0 + 150) * T, levels.CAVE_FLOOR * T - p.h
        w = goblin.Walker((x0 + 156) * T, "crawler")
        w.y, w.on_ground = levels.CAVE_FLOOR * T - w.h, True
        start, bottoms = w.x, set()
        for _ in range(120):
            w.update(g.lv, p)
            bottoms.add(w.rect.bottom)
        self.assertLess(w.x, start - 60)                     # viene incontro
        self.assertEqual(bottoms, {levels.CAVE_FLOOR * T})   # sempre a terra
        self.assertEqual(len(g.gfx.foes["crawler"]), 4)


if __name__ == "__main__":
    unittest.main()
