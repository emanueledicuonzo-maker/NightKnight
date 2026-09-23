"""Testo dell'interfaccia: font antialias inclusi nel progetto (licenze in assets/fonts/)."""
from functools import lru_cache
from pathlib import Path

import pygame


@lru_cache(maxsize=32)
def _font(scale):
    if not pygame.font.get_init():
        pygame.font.init()
    name = "DejaVuSerif.ttf" if scale >= 7 else "Lato-Semibold.ttf"
    path = Path(__file__).resolve().parent / "assets" / "fonts" / name
    return pygame.font.Font(str(path), max(12, int(scale * 6)))


@lru_cache(maxsize=256)
def _text_image(text, color, scale):
    font = _font(scale)
    ink = font.render(text, True, color)
    shadow = font.render(text, True, (4, 7, 10))
    out = pygame.Surface((ink.get_width() + 4, ink.get_height() + 4), pygame.SRCALPHA)
    out.blit(shadow, (2, 3))
    out.blit(ink, (0, 0))
    return out


def draw_text(surf, text, x, y, color=(245, 245, 245), scale=4):
    surf.blit(_text_image(text, tuple(color), scale), (x, y))


def text_width(text, scale=4):
    return _font(scale).size(text)[0]
