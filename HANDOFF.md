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

1. **Surface** — one continuous map (`levels.gen_surface()`, 432 columns) with
   hills and mountains climbed in 1-3 tile steps (`TITAN_HILLS`; the big one,
   10 tiles, has a 3-wide ladder), markers placed on top of the relief: two
   waves (one on the ground, one of flyers) that start when the knight enters
   their zone and never lock the way (`waves.py`), and all along the way a group
   of 2-4 enemies every 14 columns of new ground (`TITAN_PATROLS`, worms most
   common), plus a group whenever nobody is around for 3 s (flyers only in the
   traversal, none in the galleries); reinforcements stand on the real ground
   (`Level.floor_near`); a wave left far behind closes; methane lakes, cryovolcanoes (3 s eruptions that throw you off),
   nitrogen vents (5 s horizontal jets that push you back, frost you blue: 25%
   speed for 2 s, shorter jumps), 3 oxygen stations, 30 prisoners (5 Light each).
   Oxygen lasts 150 s; at zero you do not die: you slow down, jump less, pant
   (`knight_tired_sheet`) and every hit is worth half a stone.
2. **Traversal** — same map, after column `TITAN_PASS_START`: a small labyrinth
   (`levels.gen_titan_pass()`, modelled on Titan's real "labyrinth terrain"): a
   cliff climbed zig-zag on three ledges joined by service ladders, the crest,
   spires stepping down into a methane lake, the cable between two cranes, a
   crevasse (the far side is a wall too high to climb), dark galleries lit only
   by the visor (dead end with two prisoners to the left, a low passage, a
   methane pool and a nitrogen vent to the right), a shaft back to the surface;
   then the **double cable** (two ropes in a row between two rock steps: the
   first alone cannot carry you across), a tower and the **triple cable**
   anchored high over the big lake: the far shore is a 5-tile step reached only
   by letting go of the middle rope high in its swing. 320 columns, 13 enemies
   (8 underground; the Tremors-like burrowing worms live only there), 10
   prisoners, 1 station. Ladders are 3 tiles wide.
   Twelve restart stages (`levels.TITAN_STAGES`, six on the surface before each
   arena, six in the traversal): a lost life or Continue restarts from the last
   one reached; waves already behind stay done. `tests/test_labyrinth.py` plays every
   passage with the game's physics, cables included.
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
| `titan.py` | cryovolcanoes (`Geyser`), prisoners, oxygen stations, nitrogen vents (horizontal jet) |
| `athletics.py` | the physical cable (pymunk pendulum) |
| `assets.py` | image loading; sprite sheets split **by silhouette**, not by grid |
| `music.py` | synthesized bass + light percussion tracks and all sound effects |
| `fonts.py` | UI text |
| `progress.py` | atomic save of record and checkpoint |

Rendering: sky and the parallax layers (`PARALLAX`: far mountains, hills,
colony ruins, near rocks) are drawn at full resolution, with Titan's haze baked
into each layer at load time (`Gfx.fogged`); below the crust `cave_bg` replaces
them. The world (tiles, entities, effects) is drawn on a `VW x level height`
surface; the camera crops a piece of it (`view_rect`) and scales it to the
screen: `ZOOM` 1.5 when exploring, up to `ZOOM_FIGHT` 1.75 with a few enemies
close (not in a crowd), `ZOOM_DUEL` 1.6 with the Guardian always in frame. The
camera follows vertically (`follow_y`: feet at a fixed height when grounded,
margins while jumping). Then the foreground silhouettes (fade out underground),
cave darkness with the visor light, drizzle (none underground), vignette, HUD.

The map is `levels.ROWS` rows: `SKY` rows of sky above the surface (for the
cliff), the crust at `GROUND`, `DEPTH` rows of rock below (galleries). Methane
is its own tile `~` (`LAKE_DEPTH` deep): a head under it drowns.

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
- rename to the names the code expects, move old versions to `assets/inutili/`;
- sheets that come on a pure black background: key out only the black connected
  to the image border (outlines are 7-30, the background 0-6), done for
  `knight_climb/wind/ledge_sheet.png`;
- props and multi-object images load with `assets.pieces(name, n, h, ref)`
  (split by silhouette, one common scale);
- keep Titan plausible (see STORY.md, "Titano vero"): water-ice rock, organic
  sediment, methane liquid, no rust, cryovolcanoes, nitrogen.

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

1. **Make Titan a ten-minute level** built on action + skill + planning
   (plan agreed on 23/9, decisions taken on 27/9):
   - oxygen drains faster while fighting, sprinting and jumping, so long fights
     force a stop at a station;
   - fatigue with no bar: NightKnight pants (`knight_tired_sheet` is ready),
     slows down and jumps less; resting recovers;
   - methane downpour instead of acid rain (Titan's rain is not acidic): out in
     the open it freezes the suit's joints, in the labyrinth's channels and
     galleries it brings flash floods; shelters are drawn (`shelter.png`);
   - storms that push and cut visibility (`knight_wind_sheet` is ready);
   - ledge grab (`knight_ledge_sheet` is ready) — agreed, not coded yet;
   - some cryovolcanoes launch you up to ledges and hidden prisoners;
   - jellyfish that stick to you, slow you and drain life until knocked off;
   - a longer surface and more varied pacing between the waves.
2. **Gravity, atmosphere and weather must matter more** on every satellite
   (jump, fall, inertia, projectiles, enemy behaviour): it is the game's
   differentiator.
3. **Game feel**: hit-stop, knockback, snappier acceleration and fall, camera
   look-ahead, dash/combos (to be agreed), enemy reactions.
4. ~~Parallax with many layers~~ done (27/9); `cliff_bg.png` (a canyon wall
   for when the camera is high on the cliff) and `ledge.png` (drawn ledges) are
   in `assets/` but not used yet.
5. Browser build (pygbag; pymunk must be replaced by a hand-written pendulum)
   and the case-study page.
6. The other eleven satellites, Saturn's rings, Luna (see `STORY.md`,
   "Ancora da decidere").

## Known gaps

- Frame time is ~9.5 ms on the surface and ~11 ms in the galleries (darkness
  overlay); fine on desktop, to be optimised for the browser build.
- In the galleries under the edge of the spire lake, the lake is seen from the
  side as a dark band.
- **NightKnight** is the game; the knight is called **9T9T** (decided 27/9).
  Code and docs still call the knight NightKnight in many places.
- Older chats: the 23/9 transcript was moved into this project's transcript
  folder (the project used to live under `/home/ema`).

- `Player` still keeps its Light in the attribute `albedo` (old name).
- The Guardian's movement code (`knights.py`) still carries generic moves from
  the prototype; only four are used by Titan's Guardian.
- The gas cloud, the lakes' shimmer and the ladders are drawn in code, not art.
