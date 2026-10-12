import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict
import itertools
import unittest

import pygame

import athletics
import goblin
import levels
import nix

TILE = 64
G = levels.GROUND
X0 = levels.NIX_SURFACE_COLS
GRAVITY = levels.cfg(1)["gravity_scale"]


class NixPassTests(unittest.TestCase):
    """Il campo dei crateri si attraversa davvero, con la fisica di Nix."""

    @classmethod
    def setUpClass(cls):
        cls.lv = goblin.Level(levels.gen_nix_surface(), "surface")

    def setUp(self):
        self.lv = goblin.Level(levels.gen_nix_surface(), "surface")      # le passerelle cambiano la griglia

    def stand(self, col, h):
        p = goblin.Player(0, 0)
        p.gravity_scale = GRAVITY
        p.x = (X0 + col) * TILE + (TILE - p.w) / 2
        p.y = (G - h) * TILE - p.h
        p.on_ground = True
        p.update(defaultdict(bool), self.lv)
        self.assertTrue(p.on_ground, (col, h))
        return p

    def feet(self, p):
        return G - p.rect.bottom // TILE, p.rect.centerx // TILE - X0

    def go(self, p, direction, until, frames=60 * 60, gratings=(), grating_jump=False):
        """Corre nel verso dato saltando davanti a vuoti e pareti (e subito, se sta
        su una passerella); si ferma quando `until(p)` e' vero. Restituisce True."""
        lv = self.lv
        # salto tenuto premuto: altrimenti e' un salto corto, e sulle passerelle si risalta appena atterrati
        keys = defaultdict(bool, {pygame.K_RIGHT if direction > 0 else pygame.K_LEFT: True, pygame.K_LSHIFT: True,
                                  pygame.K_SPACE: True})
        for frame in range(frames):
            r = p.rect
            front = r.right + 6 if direction > 0 else r.left - 6
            keys[pygame.K_SPACE] = not p.on_ground        # tenuto solo in aria: a terra niente risalti
            if p.on_ground:
                wall = lv.solid(front, r.bottom - 8)
                ahead = front + direction * TILE // 2
                drop = next((k for k in range(7) if lv.solid(ahead, r.bottom + 2 + k * TILE)), None)
                gap = drop is None or drop > 3                           # un dislivello si salta, non si scende
                on_grating = lv.tile_at(r.centerx, r.bottom + 2) == "G"
                if wall or gap or (grating_jump and on_grating):
                    keys[pygame.K_SPACE] = True
                    p.do_jump()
            p.update(keys, lv)
            for gr in gratings:
                gr.update(lv, p)
            self.assertFalse(lv.drowned(p.rect), f"caduto nel vuoto alla colonna {self.feet(p)[1]}")
            if until(p):
                return True
        self.fail(f"fermo alla colonna {self.feet(p)[1]}, altezza {self.feet(p)[0]}")

    def test_crater_rims_are_jumped_one_after_the_other(self):
        p = self.stand(2, 0)
        self.go(p, 1, lambda p: p.on_ground and self.feet(p)[1] >= 56)
        self.assertEqual(self.feet(p)[0], 0)

    def test_gratings_carry_you_only_if_you_keep_jumping(self):
        gratings = [nix.Grating(X0 + c, row, levels.NIX_GRATING_W) for c, row in levels.NIX_GRATINGS]
        p = self.stand(56, 0)
        self.go(p, 1, lambda p: p.on_ground and self.feet(p)[1] >= 140, gratings=gratings, grating_jump=True)
        self.assertTrue(any(gr.state != "solid" for gr in gratings), "qualche passerella deve aver ceduto")
        # fermandosi sulla prima si cade
        self.setUp()
        gratings = [nix.Grating(X0 + c, row, levels.NIX_GRATING_W) for c, row in levels.NIX_GRATINGS]
        p = self.stand(56, 0)
        with self.assertRaises(AssertionError):
            self.go(p, 1, lambda p: p.on_ground and self.feet(p)[1] >= 140, frames=400, gratings=gratings)

    def swing(self, start, h, wait, releases):
        x0 = X0 * TILE
        speeds = iter(levels.NIX_ROPE_SPEEDS)
        cables = athletics.Cables([[athletics.Cable(x0 + col * TILE + TILE // 2, athletics.FLOOR - top, length,
                                                    next(speeds))
                                    for col, top, length in group] for group in levels.NIX_CABLES])
        p = self.stand(start, h)
        idle = defaultdict(bool)
        keys = defaultdict(bool, {pygame.K_RIGHT: True, pygame.K_SPACE: True})
        for _ in range(wait):
            cables.update_player(p, idle, self.lv)
        for _ in range(6):
            cables.update_player(p, keys, self.lv)
        p.do_jump()
        grabs = []
        for frame in range(1500):
            cables.update_player(p, keys, self.lv)
            c = cables.current
            if c:
                i = cables.all.index(c)
                if not grabs or grabs[-1] != i:
                    grabs.append(i)
                body, anchor = c.rope.body, c.rope.anchor
                if body.velocity.x > 0 and body.position.x - anchor.x > releases[len(grabs) - 1] * c.rope.length:
                    c.release(p)
            if self.lv.drowned(p.rect):
                return "caduto", grabs, None, None
            if p.on_ground and frame > 10:
                h, col = self.feet(p)
                return "a terra", grabs, col, h
        return "appeso", grabs, None, None

    def crossings(self, start, h, releases, waits=range(0, 200, 10)):
        out = []
        for wait in waits:
            for rel in itertools.product(*releases):
                out.append((wait, rel, self.swing(start, h, wait, rel)))
        return out

    def test_the_four_cables_reach_the_high_side(self):
        tries = self.crossings(162, levels.NIX_LAUNCH, [(0.35, 0.5, 0.65)] * 4, waits=range(0, 170, 10))
        ok = [t for t in tries if t[2][0] == "a terra" and t[2][1] == [0, 1, 2, 3] and t[2][2] >= 228
              and t[2][3] == levels.NIX_LANDING]
        self.assertTrue(ok, "coi quattro cavi non si arriva mai sul lato alto")
        for wait, rel, (outcome, grabs, col, h) in tries:
            self.assertFalse(outcome == "a terra" and col is not None and col >= 228 and len(grabs) < 4,
                             f"si arriva di la' saltando un cavo: {grabs}")

    def test_handles_hang_above_the_launch_step(self):
        for col, top, length in levels.NIX_CABLES[0]:
            lowest = (top - length) / TILE
            self.assertGreaterEqual(lowest, levels.NIX_LAUNCH + 4.5, col)

    def hop(self, p, direction, runup=0, short=False):
        """Un salto solo nel verso dato (con rincorsa di `runup` fotogrammi), finche'
        si atterra; `short`: il tasto lasciato subito, il salto corto."""
        keys = defaultdict(bool, {pygame.K_SPACE: True, pygame.K_RIGHT if direction > 0 else pygame.K_LEFT: True,
                                  pygame.K_LSHIFT: runup > 0})
        for _ in range(runup):
            p.update(keys, self.lv)
        p.do_jump()
        for frame in range(200):
            keys[pygame.K_SPACE] = not short
            p.update(keys, self.lv)
            if p.on_ground and frame > 3:
                break
        return p

    def test_the_way_back_climbs_to_the_repeater(self):
        p = self.stand(232, levels.NIX_LANDING)
        self.go(p, 1, lambda p: p.on_ground and self.feet(p)[1] >= 298)                       # in fondo al lato alto
        self.assertEqual(self.feet(p)[0], levels.NIX_LANDING)
        self.hop(p, -1, short=True)                                                            # un salto corto: la cengia 12
        self.assertEqual(self.feet(p)[0], 12, "dalla fine del lato alto si sale sulla cengia")
        self.go(p, -1, lambda p: p.on_ground and self.feet(p)[1] <= 246 and self.feet(p)[0] == 12)  # fino in fondo
        self.hop(p, 1)                                                                         # su, sulla cengia 16
        self.assertEqual(self.feet(p)[0], 16, "dalla fine della cengia 12 si sale sulla 16")
        self.go(p, 1, lambda p: p.on_ground and self.feet(p)[1] >= 450)                       # e fino al ripetitore
        self.assertEqual(self.feet(p)[0], levels.NIX_TOP)
        ec, er = self.lv.exit
        self.assertEqual((ec - X0, G - er - 1), (451, levels.NIX_TOP))

    def test_the_plateau_is_not_reached_from_the_high_side(self):
        """Il salto di corsa di Nix arriva a quasi 10 tessere: la parete dell'altopiano e' 12."""
        p = self.stand(292, levels.NIX_LANDING)
        self.hop(p, 1, runup=40)
        self.assertEqual(self.feet(p)[0], levels.NIX_LANDING)

    def test_the_hidden_platform_is_one_jump_up(self):
        p = self.stand(248, 16)                        # da fianco, con rincorsa: da sotto si sbatte la testa
        self.hop(p, 1, runup=24)
        self.assertEqual(self.feet(p)[0], 22)


if __name__ == "__main__":
    unittest.main()
