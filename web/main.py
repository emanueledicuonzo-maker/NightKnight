"""Avvio nel browser (pygbag): lo stesso ciclo di Game.run(), ma asincrono,
perche' il browser deve riprendere il controllo a ogni fotogramma."""
# /// script
# dependencies = ["numpy", "pymunk"]
# ///
import asyncio

import numpy
import pygame

import goblin
import music

# Nel browser l'audio di SDL non sopporta di essere chiuso e riaperto con un'altra
# frequenza o un altro buffer (Web Audio: «buffer length mismatch», «divide by zero»).
# Il Jukebox lo riaprirebbe a 22050 Hz: qui si tiene quello aperto da pygame e i suoni,
# sintetizzati a 22050 Hz, si allungano a mano alla frequenza vera.
_init = pygame.mixer.init
pygame.mixer.quit = lambda: None
pygame.mixer.init = lambda *a, **k: None if pygame.mixer.get_init() else _init()
_make_sound = pygame.sndarray.make_sound


def _make_sound_web(arr):
    freq = pygame.mixer.get_init()[0]
    if freq != music.SR:
        idx = (numpy.arange(int(len(arr) * freq / music.SR)) * music.SR // freq).astype(int)
        arr = numpy.ascontiguousarray(arr[idx])
    return _make_sound(arr)


pygame.sndarray.make_sound = _make_sound_web


async def main():
    game = goblin.Game(windowed=True)
    while game.running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                game.running = False
            if e.type == pygame.WINDOWFOCUSLOST and game.state not in ("title", "end", "gameover"):
                game.set_paused(True)
            if e.type == pygame.KEYDOWN:
                game.key(e.key)
        if not game.running:
            break
        game.update()
        game.draw()
        game.clock.tick(goblin.FPS)
        await asyncio.sleep(0)
    game.save_progress()


asyncio.run(main())
