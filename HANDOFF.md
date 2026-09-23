# NightKnight — handoff

State of the project, how it is built, how the owner likes to work, and what
comes next. Design and rules live in `STORY.md` (Italian); image prompts in
`assets/PROMPT.md`. This file is the entry point for whoever picks the work up.

## What it is

A 2D action platformer in Python + Pygame (pygame-ce), 1920x1080 logical
resolution. NightKnight, a lone space knight, crosses twelve abandoned
satellite-colonies, each ending with a Guardian. Tone: Ghosts 'n Goblins pace,
Saint Seiya's twelve Guardians, Philip K. Dick / Blade Runner colonies. Visual
style: dark 2D cartoon (bold black outlines, flat cel shading).

The project is also a **portfolio case study** for the owner's web agency: the
goal is a build playable in the browser (pygbag) that makes people say "these
people are good" and start playing. Quality bar set by the owner: *Hollow Knight:
Silksong*, *Shinobi: Art of Vengeance*, *Ninja Gaiden: Ragebound*, *Prince of
Persia: The Lost Crown*.

## Run and test

```sh
./goblin.sh --windowed          # or ./goblin.sh for fullscreen
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m unittest discover -s tests
```

The owner plays on a **4K display**: windows use `pygame.SCALED`, so everything
must stay readable when scaled up 2x.

## What is playable today

Only **Titan**, start to finish (the other eleven satellites are not built yet;
after the Guardian an end screen says so):

1. **Surface** — one continuous map (`levels.gen_surface()`): four waves that
   start when NightKnight enters their zone and never lock the way
   (`waves.py`); methane lakes, geysers, cryogenic gas vents, oxygen stations,
   fifteen prisoners (5 Light each).
2. **Traversal** — same map, after column `TITAN_PASS_START`: rock steps, two
   walls with service ladders, pillars over lakes, a cable over the big lake
   (grabbed automatically when touched mid-jump). Few enemies. Dying here
   restarts from the traversal.
3. **Duel** — one round against the Guardian of Titan (2x NightKnight's height,
   halberd and a hook thrown on a chain), helped by at most two flyers.

Player kit: sword (Z, 3 slashes/s, counts 2), stone (X, 2 throws/s, counts 1,
half the sword), kick (C), flying kick (C in the air from standing), spinning
flying kick (C in the air while moving: hits all around, counts 2, short
recovery on landing), sprint (Shift), Bianca's Light burst (V: every 25 Light
kills all flyers on screen and takes 5% of the Guardian's life, max 20%).
Oxygen drains outdoors (~100 s) and refills at stations. Enemy life is counted
in hits (see `WALKERS` / `FLYERS` in `goblin.py`, and `STORY.md`).

## Code map

| File | Role |
| --- | --- |
| `goblin.py` | game loop, player, enemies (`Walker`, `Flyer`), Bianca, HUD, drawing, zoom |
| `levels.py` | Titan config, weapons, map generation (surface + traversal, arena), wave data |
| `waves.py` | wave director (independent waves, spawn at view edges, flee rule) |
| `knights.py` | the Guardian: moves, AI, projectiles (hook), pose loading |
| `titan.py` | geysers, prisoners, oxygen stations, gas vents |
| `athletics.py` | the physical cable (pymunk pendulum) |
| `assets.py` | image loading; sprite sheets split **by silhouette**, not by grid |
| `music.py` | synthesized bass + light percussion tracks and all sound effects |
| `fonts.py` | UI text |
| `progress.py` | atomic save of record and checkpoint |

Rendering: sky and parallax hills are drawn at full resolution; the world
(tiles, entities, effects) is drawn on a `VW x H` surface and scaled by `ZOOM`
(1.5) so characters read large; then drizzle, vignette and HUD.

## Asset pipeline

The owner generates images with ChatGPT "Create image" from the prompts in
`assets/PROMPT.md` and drops them in `~/Scaricati`. Then:

- always attach `knight_idle.png` as style/scale reference;
- check transparency (some come with a real alpha, some don't; one came with
  alpha but a pure-black background that had to be keyed);
- enemy images have two frames side by side: split them with
  `assets._figures(img, 2, 1)` and save them **facing right** (the game flips);
- knight strips and the Guardian strip are split by silhouette at load time
  (`assets.sheet(..., typical=True)` scales on the typical figure, so a raised
  sword doesn't shrink the sheet);
- rename to the names the code expects, move old versions to `assets/inutili/`.

## How the owner works (important)

- **Decide together before writing.** Propose lists/tables, wait for a yes,
  then implement. Don't invent design on your own; when a gap forces a choice,
  make it small, say so plainly, and make it easy to undo.
- The owner writes in quick, informal Italian and often sends new requests while
  work is running: acknowledge them in a line and fold them in.
- Nothing from the old Goblin prototype may survive (crypts, zombies, pixel art,
  armour loss, athletic trials, hint text). The second part of a level is a
  **traversal**, not "athletic trials".
- No on-screen hint text, no "suitable / not suitable" weapon verdict.
- Show screenshots of what changed; run the tests; commit in small steps.

## Next steps (agreed direction, in order)

1. **Make Titan a ten-minute level** built on action + skill + planning:
   - oxygen drains faster while fighting, sprinting and jumping, so long fights
     force a stop at a station;
   - fatigue: after sustained effort NightKnight breathes hard (audible), slows
     down and jumps less; resting recovers;
   - acid rain that wears the suit when out in the open (shelter under rocks,
     canopies, in tunnels); storms that push and cut visibility;
   - stone tunnels to climb, cavities, tighter passages;
   - geysers drawn and animated (new art), more spectacular hazards;
   - jellyfish that stick to you, slow you and drain life until knocked off;
   - a longer map and more varied pacing between the waves.
2. **Gravity, atmosphere and weather must matter more** on every satellite
   (jump, fall, inertia, projectiles, enemy behaviour): it is the game's
   differentiator.
3. **Game feel**: hit-stop, knockback, snappier acceleration and fall, camera
   look-ahead, dash/combos (to be agreed), enemy reactions.
4. **Parallax with many layers** so the scene feels almost 3D.
5. Browser build (pygbag; pymunk must be replaced by a hand-written pendulum)
   and the case-study page.
6. The other eleven satellites, Saturn's rings, Luna (see `STORY.md`,
   "Ancora da decidere").

## Known gaps

- `Player` still keeps its Light in the attribute `albedo` (old name).
- The Guardian's movement code (`knights.py`) still carries generic moves from
  the prototype; only four are used by Titan's Guardian.
- The gas cloud, the lakes' shimmer and the ladders are drawn in code, not art.
