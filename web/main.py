"""Avvio nel browser (pygbag): lo stesso ciclo di Game.run(), ma asincrono,
perche' il browser deve riprendere il controllo a ogni fotogramma."""
# /// script
# dependencies = ["numpy", "pymunk"]
# ///
import asyncio

import pygame

import goblin


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
