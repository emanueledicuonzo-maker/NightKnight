# NightKnight — handoff

State of the project, how it is built, how the owner likes to work, and what
comes next. Design and rules live in `STORY.md` (Italian); image prompts in
`assets/PROMPT.md`. This file is the entry point for whoever picks the work up.

## What it is

A 2D action platformer in Python + Pygame (pygame-ce), 1920x1080 logical
resolution. **NightKnight** is the game; its knight, **9T9T**, crosses twelve abandoned
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
   of 2-4 enemies every 14 columns of new ground (`TITAN_PATROLS`, skeletons,
   lizards and static worms most common), plus a group whenever nobody is around for 3 s (flyers only in the
   traversal, none in the galleries); reinforcements stand on the real ground
   (`Level.floor_near`), always off screen (`waves.SPAWN_AWAY`, never appearing
   out of nowhere); static worms only on flat base ground (`Game.flat_ground`,
   otherwise no worm); a wave left far behind closes; methane lakes;
   cryovolcanoes: our two drawings for rest and warning (`geyser.png`), then
   the eruption blends five full drawings (`geyser_erupt_1..5`) in an irregular
   rhythm (`Geyser.intensity`), hurting only while it is a real column (3 s,
   throws you off);
   nitrogen vents (5 s horizontal jets that push you back, frost you blue: 25%
   speed for 2 s, shorter jumps; never blowing over a cryovolcano or a lake),
   3 oxygen stations, 30 prisoners (5 Light each). Walkers deal with terrain:
   jump steps up to 3 tiles, drop down, hop narrow lakes, else turn back;
   worms never jump.
   Oxygen lasts 150 s; at zero you do not die: you slow down, jump less, pant
   (`knight_tired_sheet`) and every hit is worth half a stone.
2. **Traversal** — same map, after column `TITAN_PASS_START`: a small labyrinth
   (`levels.gen_titan_pass()`, modelled on Titan's real "labyrinth terrain"): a
   cliff climbed zig-zag on three ledges joined by service ladders, the crest,
   spires stepping down into a methane lake, the cable between two cranes, a
   crevasse (the far side is a wall too high to climb), dark galleries lit only
   by the visor: a dead end with two prisoners to the left, then galleries four
   times longer (`CAVE_EXTRA` = 135 columns: low passages, methane pools, rock
   steps, a station, three prisoners, a nitrogen vent), full of **crawling
   worms** (`crawler`, 4-frame sheet: they come at you within 10 tiles, wander
   otherwise, never jump) and a few Tremors-like burrowers; a shaft back to the
   surface; then the **double cable** (two ropes between two rock steps: the
   first alone never carries you across; whoever catches the second always
   lands), a tower and the **triple cable** anchored high over the big lake:
   the far shore is a 4-tile step reached only by letting go of the middle rope
   high in its swing. Ropes **swing on their own** (scripted pendulum,
   `athletics.Rope`, 50 degrees, 2.7 s) each at its own pace
   (`levels.ROPE_SPEEDS` 1, 1.1, 0.9, 1.2, 0.8, 1.1): the player only picks when
   to jump and when to let go; handles hang 5 tiles above every launch point;
   the knight hangs by the tip. Ladders are 3 tiles wide, grabbed in the
   middle, and end with a pull-up over the edge (`knight_ledge_sheet`).
   455 columns, about 25 enemies, 13 prisoners, 2 stations.
   Fifteen restart stages (`levels.TITAN_STAGES`, six on the surface, nine in
   the traversal, three of them in the galleries): a lost life or Continue restarts from the last
   one reached; waves already behind stay done. At game over: **Continue** (last
   stage, three lives, score back to zero) or New game. `tests/test_labyrinth.py`
   plays every passage with the game's physics; the cable tests search waits and
   release points until a crossing exists (and check the wrong ones fail).
3. **Duel** — one round against the Guardian of Titan (2x NightKnight's height,
   halberd and a hook thrown on a chain), alone, in an arena two screens wide
   (60 columns); if he drifts more than 1250 px away he walks back into view;
   the hook leaves from his outstretched fist ("punch" pose) and the chain
   follows his hand.
   Bianca dives on him every 6 s (2%), V takes 5%, Nova 30%. Today he is
   beatable mostly from afar with stones: the owner accepts it for Titan, but
   the next Guardian needs a reason to fight up close (to be designed).

Player kit: sword (Z, 3 slashes/s, counts 2, reach 240 px; pressed in rhythm it
chains a 3-slash combo: the second is a backhand, the third lunges forward and
reaches 60 px further), stone (X, 2 throws/s, counts 1,
half the sword), kick (C), flying kick (C in the air from standing), spinning
flying kick (C in the air while moving: hits all around, counts 2, short
recovery on landing), run (double-tap and hold an arrow, or Shift: oxygen
drains 2.5x). Bianca attacks alone when more than 4 flyers are on screen (up to
5, one at a time, flyers only, then rests 12 s); V spends 25 Light to send her
on up to 5 enemies of any kind (5% of the Guardian's life). Nova (B): at the
10th colonist freed, once per level, a scripted blast (rise, spinning kick, two
flashes, shockwave) that kills every enemy in the scene (30% of the Guardian).
Sword also works on ladders and ropes. Oxygen lasts 150 s outdoors and refills
at stations. Enemy life is counted
in hits (see `WALKERS` / `FLYERS` in `goblin.py`, and `STORY.md`).

## Code map

| File | Role |
| --- | --- |
| `goblin.py` | game loop, player, enemies (`Walker`, `Flyer`), Bianca, HUD, drawing, zoom |
| `levels.py` | Titan config, weapons, map generation (surface + traversal, arena), wave data |
| `waves.py` | wave director (independent waves, spawn at view edges, flee rule) |
| `knights.py` | the Guardian: moves, AI, projectiles (hook), pose loading |
| `titan.py` | cryovolcanoes (`Geyser`), prisoners, oxygen stations, nitrogen vents (horizontal jet) |
| `athletics.py` | the cables: scripted pendulums in groups under two cranes (pymunk only for `Vec2d`) |
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
close (not in a crowd); it pulls back (`looking_down`) to 1.35 at the edge of a
2-4 tile step, 1.2 over a drop or while falling, down to `ZOOM_WIDEST` 1.0 on
high ropes (whole swing and the lake in frame); in the duel it fits both
fighters. The
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
- full frames on a black background with translucent steam (the eruption
  frames): key the black connected to the border, luminance alpha above the
  cone top, only pure black below it, then align the frames on the cone;
- characters' feet sink 12 px (`FEET_SINK`) into the dark band at the top of
  the ground tiles; objects 8 px (`titan.SINK`) with a contact shadow;
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
   - ledge grab while jumping (the sheet is used today only at ladder tops);
   - some cryovolcanoes launch you up to ledges and hidden prisoners;
   - ~~jellyfish that stick to you~~, ~~a longer level~~: done 27/9.
2. **Gravity, atmosphere and weather must matter more** on every satellite
   (jump, fall, inertia, projectiles, enemy behaviour): it is the game's
   differentiator.
3. **Game feel**: hit-stop, knockback, snappier acceleration and fall, camera
   look-ahead, dash/combos (to be agreed), enemy reactions.
4. ~~Parallax with many layers~~ done (27/9); `cliff_bg.png` (a canyon wall
   for when the camera is high on the cliff) and `ledge.png` (drawn ledges) are
   in `assets/` but not used yet.
5. Browser build (pygbag; the ropes no longer need pymunk physics, only
   `Vec2d` is left to replace) and the case-study page. **Not done yet: there
   is no deploy.** Where to publish it (GitHub Pages, Cloudflare Pages, the
   agency site) is still to be decided with the owner.
6. The other eleven satellites, Saturn's rings, Luna (see `STORY.md`,
   "Ancora da decidere").

## Known gaps

- Frame time is ~10-11 ms on the surface and in the galleries; the world
  surface is as wide as the widest zoom. Fine on desktop, to be optimised for
  the browser.
- The eruption frames use a different cone drawing from `geyser.png`: the
  switch from warning to eruption is visible. New frames should reuse our cone.
- The Guardian is beatable mostly from afar with stones (accepted for Titan).
- In the galleries under the edge of the spire lake, the lake is seen from the
  side as a dark band.
- **NightKnight** is the game; the knight is called **9T9T** (decided 27/9).
  Code, comments and some docs still call the knight NightKnight.
- Older chats: the 23/9 transcript was moved into this project's transcript
  folder (the project used to live under `/home/ema`).

- `Player` still keeps its Light in the attribute `albedo` (old name).
- The Guardian's movement code (`knights.py`) still carries generic moves from
  the prototype; only four are used by Titan's Guardian.
- The gas cloud, the lakes' shimmer and the ladders are drawn in code, not art.
