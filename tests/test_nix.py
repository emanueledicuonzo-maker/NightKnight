import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
from pathlib import Path
import tempfile
import unittest
import unittest.mock

import pygame

import goblin
import levels
import nix

TILE = 64
G = levels.GROUND


class NixMapTests(unittest.TestCase):
    """La superficie di Nix: quello che STORY.md promette c'e', e sta sul suolo."""

    @classmethod
    def setUpClass(cls):
        cls.g = levels.gen_nix_field()
        cls.lv = goblin.Level(levels.gen_nix_surface(), "surface")

    def count(self, ch):
        return sum(row.count(ch) for row in self.g)

    def test_markers(self):
        self.assertEqual(len(self.g[0]), levels.NIX_SURFACE_COLS)
        self.assertEqual(self.count("u"), 30)
        self.assertEqual(self.count("o"), 4)
        self.assertEqual(self.count("b"), 4)
        self.assertEqual(self.count("s"), 3)
        self.assertEqual(self.count("P"), 1)
        self.assertEqual(self.count("q"), 0)       # niente criovulcani su Nix

    def test_markers_stand_on_the_ground(self):
        for r, row in enumerate(self.g):
            for c, ch in enumerate(row):
                if ch in "uobsP":
                    self.assertIn(self.g[r + 1][c], "#", (ch, c, r))
                    self.assertEqual(self.g[r - 1][c], ".", (ch, c, r))

    def test_crevasses_have_no_bottom(self):
        b0, b1 = levels.NIX_BRIDGE
        for c0, c1 in levels.NIX_CREVASSES:
            for c in range(c0, c1):
                rows = [r for r in range(len(self.g)) if self.g[r][c] in "#D"]
                if b0 <= c < b1:
                    self.assertEqual(rows, [G], c)      # il ponte: una riga sola
                else:
                    self.assertEqual(rows, [], c)

    def test_stages_and_props_stand_on_solid_ground(self):
        full = self.lv.g
        for col, row in levels.NIX_STAGES:
            self.assertIn(full[row][col], "#", (col, row))
            self.assertEqual(full[row - 1][col], ".", (col, row))
        for col, _ in levels.NIX_PROPS:
            self.assertIsNotNone(self.lv.floor_near((col + .5) * TILE, G * TILE, reach=12), col)

    def test_runner_crosses_the_whole_surface(self):
        """Un automa che corre a destra e salta davanti a crepacci e pareti arriva alla
        traversata con la gravita' di Nix, senza mai cadere nel vuoto."""
        lv = self.lv
        p = goblin.Player(0, 0)
        p.gravity_scale = levels.cfg(1)["gravity_scale"]
        p.x, p.y = 2 * TILE, G * TILE - p.h
        p.on_ground = True
        run = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_LSHIFT: True})
        goal = levels.NIX_SURFACE_COLS * TILE
        for frame in range(60 * 90):
            r = p.rect
            front = r.right + 6
            if p.on_ground:
                wall = lv.solid(front, r.bottom - 8)
                floor = lv.floor_near(front + TILE // 2, r.bottom, 6)
                gap = floor is None or floor > r.bottom + 5 * TILE
                if wall or gap:
                    p.do_jump()
            p.update(run, lv)
            self.assertFalse(lv.drowned(p.rect), f"caduto nel vuoto alla colonna {r.centerx // TILE}")
            if p.x > goal:
                break
        self.assertGreater(p.x, goal, f"fermo alla colonna {p.rect.centerx // TILE}")


class NixGameTests(unittest.TestCase):
    """Insidie e nemici di Nix dentro il gioco."""

    @classmethod
    def setUpClass(cls):
        goblin.fonts._font.cache_clear()
        goblin.fonts._text_image.cache_clear()
        cls.temp = tempfile.TemporaryDirectory()
        cls.game = goblin.Game(windowed=True, save_path=Path(cls.temp.name) / "save.json")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        g = self.game
        g.ci, g.lives, g.score = 1, 3, 0
        g.luce, g.freed, g.stage = 0, set(), 0
        g.start_part("surface")
        g.state = "play"
        self.idle = defaultdict(bool)

    def put(self, col, row=G):
        g, p = self.game, self.game.player
        p.x, p.y = col * TILE + (TILE - p.w) / 2, row * TILE - p.h
        p.vx = p.vy = 0
        p.on_ground = True
        g.cam = int(p.x - goblin.DW // 2)
        return p

    def tick(self, frames, keys=None):
        with unittest.mock.patch("pygame.key.get_pressed", return_value=keys or self.idle):
            for _ in range(frames):
                self.game.update()

    def test_both_satellites_load_and_titan_is_unchanged(self):
        titan, nixc = levels.cfg(0), levels.cfg(1)
        self.assertEqual((titan["name"], titan["gravity_scale"], titan["oxygen_seconds"], len(titan["stages"])),
                         ("Titano", .84, 150, 15))
        self.assertEqual((nixc["name"], nixc["gravity_scale"], nixc["oxygen_seconds"], nixc["boss"]),
                         ("Nix", .55, 100, "Guardiano di Nix"))
        g = self.game
        self.assertEqual(g.cfg["name"], "Nix")
        self.assertEqual(g.player.gravity_scale, .55)
        self.assertAlmostEqual(g.o2_drain, goblin.OXYGEN_MAX / (100 * 60))
        self.assertEqual(len(g.ossuaries), 4 + 2)          # quattro in superficie, due nella traversata
        self.assertEqual(len(g.sirens), 3 + 2)
        self.assertEqual(sorted({k.kind for k in g.skels}), ["copy", "keeper", "skeleton_2x", "spider"])
        self.assertEqual(len(g.gratings), len(levels.NIX_GRATINGS))

    def test_siren_swaps_left_and_right_and_dies_in_three_hits(self):
        g = self.game
        siren = min(g.sirens, key=lambda s: s.x)
        siren.age = 0                                   # pulsa
        p = self.put(int(siren.x // TILE) - 4)
        self.tick(2)
        self.assertTrue(siren.pulsing)
        self.assertTrue(p.swapped)
        x0 = p.x
        self.tick(20, defaultdict(bool, {pygame.K_RIGHT: True}))
        self.assertLess(p.x, x0, "con la sirena accesa la destra porta a sinistra")
        siren.age = siren.ON + 1                        # tace
        self.tick(2)
        self.assertFalse(p.swapped)
        before = len(g.spenti)
        for _ in range(3):
            self.assertTrue(siren.hit())
        self.tick(2)
        self.assertTrue(siren.dead)
        self.assertEqual(len(g.spenti), before + 1, "la sirena spenta libera il prigioniero del basamento")
        self.assertFalse(siren.pulsing)

    def test_ossuary_cloud_doubles_the_oxygen_drain(self):
        g = self.game
        oss = next(o for o in g.ossuaries if o.floor == G * TILE)
        p = self.put(int(oss.x // TILE))
        self.assertEqual(oss.phase, "rest")
        oss.started = True
        oss.age = oss.REST + oss.WARNING + 80           # nube piena
        self.tick(1)
        self.assertEqual(oss.phase, "cloud")
        self.assertTrue(g.dusty)
        o2 = p.oxygen
        self.tick(10)
        dusty_drop = o2 - p.oxygen
        oss.age = 0; oss.started = False
        self.tick(1)
        self.assertFalse(g.dusty)
        o2 = p.oxygen
        self.tick(10)
        self.assertAlmostEqual(dusty_drop, 2 * (o2 - p.oxygen), places=4)

    def test_keeper_guard_blocks_until_kicked(self):
        g = self.game
        p = self.put(110)                   # lontano dalle crepe dei pipistrelli
        g.skels = [goblin.Walker(p.x + 90, "keeper")]
        k = g.skels[0]
        k.y = G * TILE - k.h; k.on_ground = True; k.facing = -1
        k.frozen = 10 ** 6                  # fermo come nell'azoto: si prova solo la guardia
        g.crows = []
        hp = k.hp
        p.facing = 1
        p.start_attack("throw")
        self.tick(8)
        self.assertEqual(k.hp, hp, "di fronte, a guardia chiusa, il fendente non conta")
        p.attack = None; p.recover = 0
        p.start_attack("kick")
        self.tick(8)
        self.assertGreater(k.guard_open, 0, "il calcio apre la guardia")
        p.attack = None; p.recover = 0
        p.start_attack("throw")
        self.tick(8)
        self.assertLess(k.hp, hp, "a guardia aperta il fendente conta")

    def test_copy_mimics_the_jump_with_a_delay(self):
        g = self.game
        p = self.put(110)                   # lontano dalle crepe dei pipistrelli
        g.skels = [goblin.Walker(p.x + 400, "copy")]
        c = g.skels[0]
        c.y = G * TILE - c.h; c.on_ground = True
        g.crows = []
        self.tick(2)
        p.do_jump()
        self.tick(goblin.COPY_DELAY - 4)
        self.assertTrue(c.on_ground, "la copia aspetta il ritardo")
        self.tick(10)
        self.assertFalse(c.on_ground, "poi salta anche lei")

    def test_bats_come_out_of_the_crack_and_the_moth_blinds(self):
        g = self.game
        g.crows = []
        c0, c1 = levels.NIX_CREVASSES[0]
        p = self.put(c0 - 6)
        self.tick(2)
        # quelli della crepa escono da sotto il suolo (l'ondata ne manda altri dal cielo)
        bats = [c for c in g.crows if c.kind == "bat" and c.y > G * TILE]
        self.assertGreaterEqual(len(bats), 3, "escono dal crepaccio, sotto il suolo")
        self.assertLessEqual(len(bats), 5)
        g.crows = [goblin.Flyer(p.rect.centerx, p.rect.top + 20, "moth")]
        g.crows[0].goal = (p.rect.centerx, p.rect.top + 20)
        hp = p.hp
        self.tick(3)
        self.assertGreater(g.blind, 0, "la falena davanti al visore spegne la vista")
        self.assertEqual(p.hp, hp, "ma non fa male")


class PassageTests(unittest.TestCase):
    """Da Titano a Nix: caduto il Guardiano di Titano si atterra su Nix, e Continua
    riporta li'."""

    @classmethod
    def setUpClass(cls):
        goblin.fonts._font.cache_clear()
        goblin.fonts._text_image.cache_clear()
        cls.temp = tempfile.TemporaryDirectory()
        cls.game = goblin.Game(windowed=True, save_path=Path(cls.temp.name) / "save.json")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_after_titan_comes_nix_and_continue_remembers_it(self):
        g = self.game
        g.new_game("arena")
        self.assertEqual(g.cfg["name"], "Titano")
        g.lives, g.score = 2, 12345
        g.after_victory()
        self.assertEqual((g.ci, g.cfg["name"], g.part, g.state), (1, "Nix", "surface", "card"))
        self.assertEqual((g.lives, g.score), (2, 12345), "vite e punteggio restano")
        self.assertEqual(g.player.gravity_scale, .55)
        cp = goblin.progress.load(g.save_path)["checkpoint"]
        self.assertEqual((cp["satellite"], cp["part"]), (1, "surface"))
        g.new_game()
        self.assertEqual(g.cfg["name"], "Titano")
        g.saved = goblin.progress.load(g.save_path)
        g.saved["checkpoint"] = cp
        g.continue_game()
        self.assertEqual((g.ci, g.cfg["name"]), (1, "Nix"))
        # dopo l'ultimo satellite costruito, la schermata finale
        g.ci = len(levels.SATELLITES) - 1
        g.start_part("arena")
        g.after_victory()
        self.assertEqual(g.state, "end")


if __name__ == "__main__":
    unittest.main()
