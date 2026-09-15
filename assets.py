"""Caricamento immagini: assets/<nome>.png se esiste, altrimenti pixel art ingrandita."""
import os

import pygame

import pixelart as px

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_cache = {}


def _fit(img, w, h):
    """Scala mantenendo le proporzioni dentro w x h, ancorata in basso al centro."""
    iw, ih = img.get_size()
    k = min(w / iw, h / ih)
    nw, nh = max(1, int(iw * k)), max(1, int(ih * k))
    scaled = pygame.transform.smoothscale(img, (nw, nh))
    out = pygame.Surface((w, h), pygame.SRCALPHA)
    out.blit(scaled, ((w - nw) // 2, h - nh))
    return out


def _trim(img):
    r = img.get_bounding_rect()
    return img.subsurface(r).copy() if r.w and r.h else img


def load(name, w, h, fallback=None, exact=False):
    """Immagine di nome `name` scalata a (w, h). fallback: funzione che restituisce una Surface."""
    key = (name, w, h)
    if key in _cache:
        return _cache[key]
    path = os.path.join(DIR, name + ".png")
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (w, h)) if exact else _fit(_trim(img), w, h)
    else:
        img = fallback() if fallback else pygame.Surface((w, h), pygame.SRCALPHA)
        if img.get_size() != (w, h):
            img = _fit(img, w, h) if not exact else pygame.transform.scale(img, (w, h))
    _cache[key] = img
    return img


def has(name):
    return os.path.exists(os.path.join(DIR, name + ".png"))


def flip(img):
    key = ("flip", id(img))
    if key not in _cache:
        _cache[key] = pygame.transform.flip(img, True, False)
    return _cache[key]


def pix(rows, remap=None, scale=6):
    return lambda: px.sprite(rows, remap, scale=scale)
