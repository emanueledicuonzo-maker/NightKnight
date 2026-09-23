"""Caricamento delle immagini di assets/: scala, fogli di sprite, figure separate per sagoma."""
import os

import pygame


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


def _figures(img, n, rows):
    """Separa le n figure del foglio seguendo le sagome invece della griglia: i fogli generati
    non hanno le figure a distanza costante, e una spada lunga sconfina nella cella accanto.
    I pezzi staccati (un sasso lanciato, le scie) vanno alla figura piu' vicina.
    Restituisce i ritagli in ordine di lettura, oppure None se le figure non sono n."""
    mask = pygame.mask.from_surface(img, 127)
    parts = [m for m in mask.connected_components() if m.count() > 30]
    if len(parts) < n:
        return None
    parts.sort(key=lambda m: m.count(), reverse=True)
    groups = [[m] for m in parts[:n]]
    rects = [m.get_bounding_rects()[0] for m in parts[:n]]
    for m in parts[n:]:
        r = m.get_bounding_rects()[0]
        i = min(range(n), key=lambda j: (pygame.Vector2(rects[j].center) - r.center).length())
        groups[i].append(m)
    per_row = n // rows
    order = sorted(range(n), key=lambda j: rects[j].centery)
    order = [j for r in range(rows) for j in sorted(order[r * per_row:(r + 1) * per_row], key=lambda j: rects[j].centerx)]
    out = []
    for j in order:
        full = pygame.mask.Mask(img.get_size())
        for m in groups[j]:
            full.draw(m, (0, 0))
        box = full.get_bounding_rects()
        box = box[0].unionall(box[1:]) if box else rects[j]
        crop = img.subsurface(box).copy()
        keep = full.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
        crop.blit(keep, (0, 0), box, special_flags=pygame.BLEND_RGBA_MULT)
        out.append(crop)
    return out


def frames(names, h):
    """Fotogrammi separati della stessa figura, scalati con un unico fattore
    (il piu' alto diventa alto h), cosi' il corpo non cambia misura fra una posa e l'altra."""
    key = ("frames", tuple(names), h)
    if key not in _cache:
        imgs = [pygame.image.load(os.path.join(DIR, n + ".png")).convert_alpha() for n in names]
        k = h / max(i.get_height() for i in imgs)
        _cache[key] = [pygame.transform.smoothscale(i, (max(1, int(i.get_width() * k)), max(1, int(i.get_height() * k))))
                       for i in imgs]
    return _cache[key]


def sheet(name, h, cols=4, rows=2, typical=False):
    """Foglio di sprite: restituisce la lista dei fotogrammi, tutti della stessa dimensione,
    scalati con lo stesso fattore (altezza del personaggio -> h) e allineati ai piedi. None se manca."""
    key = ("sheet", name, h, cols, rows, typical)
    if key in _cache:
        return _cache[key]
    path = os.path.join(DIR, name + ".png")
    if not os.path.exists(path):
        _cache[key] = None
        return None
    img = pygame.image.load(path).convert_alpha()
    crops = _figures(img, cols * rows, rows)
    if crops:
        # typical: scala sulla figura tipica, non sulla piu' alta, cosi' una spada
        # alzata non rimpicciolisce tutto il foglio (i fotogrammi alti sporgono sopra)
        heights = sorted(c.get_height() for c in crops)
        k = h / (heights[len(heights) // 2] if typical else heights[-1])
    else:
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
        crops = [cell.subsurface(b).copy() for cell, b in zip(cells, boxes)]
    frames = []
    for crop in crops:
        fw, fh = max(1, int(crop.get_width() * k)), max(1, int(crop.get_height() * k))
        scaled = pygame.transform.smoothscale(crop, (fw, fh))
        # tela comune: larghezza del fotogramma, altezza h, piedi in basso alla stessa quota
        ch = max(h, fh)
        canvas = pygame.Surface((fw, ch), pygame.SRCALPHA)
        # Alcuni fogli includono margine trasparente sotto ai piedi: allineiamo
        # il bordo effettivamente visibile, non quello del rettangolo ritagliato.
        ink = scaled.get_bounding_rect()
        canvas.blit(scaled, (0, ch - ink.bottom))
        frames.append(canvas)
    _cache[key] = frames
    return frames
