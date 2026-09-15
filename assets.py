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


def _fit_h(img, h):
    """Scala all'altezza h mantenendo le proporzioni (la larghezza e' libera)."""
    iw, ih = img.get_size()
    k = h / ih
    return pygame.transform.smoothscale(img, (max(1, int(iw * k)), h))


def load(name, w, h, fallback=None, exact=False, by_height=False, crop_top=0.0):
    """Immagine di nome `name` scalata a (w, h). fallback: funzione che restituisce una Surface.
    by_height: i personaggi vengono scalati sull'altezza, la larghezza segue l'immagine."""
    key = (name, w, h, exact, by_height, crop_top)
    if key in _cache:
        return _cache[key]
    path = os.path.join(DIR, name + ".png")
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if crop_top:
            ct = int(img.get_height() * crop_top)
            img = img.subsurface((0, ct, img.get_width(), img.get_height() - ct)).copy()
        if exact:
            img = pygame.transform.smoothscale(img, (w, h))
        elif by_height:
            img = _fit_h(_trim(img), h)
        else:
            img = _fit(_trim(img), w, h)
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


def _main_blob(cell):
    """Rettangolo della figura principale della cella: la striscia di colonne piene piu' larga,
    cosi' i pezzi sconfinati dalle celle vicine (punta della lancia, piede) vengono ignorati."""
    b = cell.get_bounding_rect()
    if not (b.w and b.h):
        return None
    alpha = pygame.surfarray.pixels_alpha(cell)
    cols_full = (alpha > 8).any(axis=1)
    del alpha
    best, cur_start, best_run = None, None, 0
    w = len(cols_full)
    for x in range(w + 1):
        full = x < w and cols_full[x]
        if full and cur_start is None:
            cur_start = x
        elif not full and cur_start is not None:
            if x - cur_start > best_run:
                best_run, best = x - cur_start, (cur_start, x)
            cur_start = None
    if not best:
        return b
    sub = cell.subsurface((best[0], 0, best[1] - best[0], cell.get_height())).get_bounding_rect()
    return pygame.Rect(best[0] + sub.x, sub.y, sub.w, sub.h)


def sheet(name, h, cols=4, rows=2):
    """Foglio di sprite a griglia: restituisce la lista dei fotogrammi, tutti della stessa dimensione,
    scalati con lo stesso fattore (altezza del personaggio -> h) e allineati ai piedi. None se manca."""
    key = ("sheet", name, h, cols, rows)
    if key in _cache:
        return _cache[key]
    path = os.path.join(DIR, name + ".png")
    if not os.path.exists(path):
        _cache[key] = None
        return None
    img = pygame.image.load(path).convert_alpha()
    cw, ch = img.get_width() // cols, img.get_height() // rows
    cells, boxes = [], []
    for r in range(rows):
        for c in range(cols):
            cell = img.subsurface((c * cw, r * ch, cw, ch))
            b = _main_blob(cell)
            if b and b.w and b.h:
                cells.append(cell); boxes.append(b)
    if not cells:
        _cache[key] = None
        return None
    top = min(b.top for b in boxes); bottom = max(b.bottom for b in boxes)
    k = h / (bottom - top)
    frames = []
    for cell, b in zip(cells, boxes):
        crop = cell.subsurface(b).copy()
        fw, fh = max(1, int(b.w * k)), max(1, int(b.h * k))
        scaled = pygame.transform.smoothscale(crop, (fw, fh))
        # tela comune: larghezza del fotogramma, altezza h, piedi in basso alla stessa quota
        canvas = pygame.Surface((fw, h), pygame.SRCALPHA)
        canvas.blit(scaled, (0, h - fh))
        frames.append(canvas)
    _cache[key] = frames
    return frames
