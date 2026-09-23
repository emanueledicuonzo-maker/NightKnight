# Immagini per NightKnight — prompt per ChatGPT "Crea immagine"

Storia, personaggi e tabelle dei satelliti: `../STORY.md`.

## Regole comuni

- **Stile:** 2D cartoon cupo. Contorni neri marcati, colori piatti con una o due
  tonalità di ombra, forme un po' semplificate, superfici sporche e consumate.
  Mai realistico, 3D, pixel art o anime.
- **Riferimento:** allegare sempre `knight_idle.png`, per lo stile e per la scala.
- **Sfondo:** PNG con trasparenza vera (canale alpha), niente scacchiera disegnata,
  niente terreno, niente ombra a terra, niente testo.
- **Direzione:** NightKnight e Bianca guardano a DESTRA, i nemici a SINISTRA
  (al momento dell'inserimento Claude li gira tutti a destra, come vuole il gioco).
- **Download:** le immagini finiscono in `~/Scaricati`; il nome del file lo dà
  Claude quando le inserisce.

Blocco di stile da mettere in testa a ogni prompt:

```text
STYLE: match the attached character's dark 2D cartoon style exactly: bold clean black outlines, flat colors with one or two cel-shading tones, slightly simplified shapes, worn and dirty surfaces. Not realistic, not 3D, not pixel art. Do not draw the attached character: use him only for style and scale.
```

## Fatto

| File | Cosa |
| --- | --- |
| `knight_idle.png` | NightKnight in piedi |
| `knight_run_sheet.png` | corsa, 4×2 |
| `knight_sword_sheet.png` | colpo di spada, 4 fotogrammi |
| `knight_stone_sheet.png` | lancio del sasso, 4 fotogrammi |
| `knight_kick_sheet.png` | calcio, 3 fotogrammi |
| `knight_flykick_sheet.png` | calcio volante, 3 fotogrammi |
| `knight_spinkick_sheet.png` | calcio volante girato, 4×2 |
| `knight_jump_sheet.png` | salto, 4×2 |
| `bianca_chick_1/2.png` | Bianca, ali in alto / in basso |
| `prigioniero_spento.png`, `prigioniero_acceso.png` | colono nella capsula |
| `sky_01.png`, `hills_01.png`, `hills_02.png`, `titan_ground_grass.png` | Titano |
| `skeleton_walk1/2`, `skeleton_fly_1/2`, `skeleton_2x_1/2`, `skeleton_3x_1/2` | scheletri |
| `crow_1/2`, `lizard_cryo_1/2`, `worm_silicon_1/2` | corvo, lucertola, verme |
| `jelly_atmo_1/2`, `miner_mutant_1/2` | medusa, minatore |
| `boss01_*.png` | Guardiano di Titano: guardia + 8 pose |
| `titan_rock.png` | roccia a strati delle pareti |
| `stazione_ossigeno.png`, `portello.png`, `capsula.png` | stazione, uscita, capsula d'atterraggio |
| `emblema.png` | stemma di NightKnight (titolo e HUD) |

Le strip del cavaliere si possono generare con qualunque numero di fotogrammi:
il gioco separa le figure seguendo le sagome. Nelle nuove strip aggiungere:
`He always holds the SAME very long, thin industrial sword as in the reference.`

## Nemici

Dopo il blocco di stile, questo testo comune e poi la descrizione del nemico.
Ogni immagine contiene **due fotogrammi affiancati**, che Claude separa.

```text
Enemy sprite for a side-scrolling game set in abandoned retro-futurist moon colonies. Two animation frames of the SAME creature side by side, same size, same framing, side view facing LEFT (toward the player), evenly spaced with a wide empty gap between them. Transparent PNG background with real alpha, no ground, no shadow, no text, no numbers.

ENEMY:
```

### Scheletri (famiglia base, ogni satellite ne usa due)

| File | ENEMY |
| --- | --- |
| `skeleton_walk` | A skeleton of a former colonist, same height as the reference knight, wearing tattered remains of an old pressure suit, a cracked helmet ring around the neck, loose cables through the ribs. Walking: frame 1 left leg forward, frame 2 right leg forward. Fragile, comes in swarms. |
| `skeleton_fly` | The same colonist skeleton, flying: a rusty broken jetpack on its back spitting a weak orange flame, legs dangling, arms reaching forward. Frame 1 flame long, frame 2 flame short. |
| `skeleton_2x` | A skeleton knight TWICE as tall as the reference knight: heavier bones, patched plates of colony armor, a large industrial blade. Frame 1 guard stance, frame 2 slashing forward. |
| `skeleton_3x` | A massive skeleton knight THREE times as tall as the reference knight, a broken crowned helmet, torn dark mantle, heavy armor bolted onto the bones, a huge two-handed sword. Slow and terrifying. Frame 1 raising the sword, frame 2 smashing down. |

### Volanti

| File | ENEMY |
| --- | --- |
| `crow` | A scavenger crow of the colonies: black feathers, glowing amber eyes, a few small metal implants, still clearly a crow, about a third of the knight's height. Frame 1 wings up, frame 2 wings down, diving. |
| `bat_void` | A void bat: leathery grey-violet wings with torn membranes, blind white eyes, oversized ears, a faint cold glow inside its mouth. Frame 1 wings spread, frame 2 wings folded in a dive. |
| `harpy_scrap` | A scrap harpy: a gaunt bird-woman creature made half of rusted scrap metal, sheet-metal wings, clawed feet clutching a chunk of debris. Frame 1 hovering, frame 2 throwing the debris. |
| `jelly_atmo` | An atmospheric jellyfish floating in thick air: a translucent pale orange bell with glowing veins, long trailing tentacles crackling with small electric sparks. Frame 1 bell expanded, frame 2 bell contracted with sparks. |
| `drone_grave` | A gravedigger drone: an old boxy maintenance drone with four small rotors, a dented yellow-grey shell, a single red camera eye and a small shovel arm. Frame 1 hovering, frame 2 firing a weak pulse from the eye. |
| `moth_bone` | A bone moth: a large moth with wings of thin pale bone plates and dusty grey fur, dark eye spots on the wings, shedding white dust. Frame 1 wings open, frame 2 wings closed, erratic. |
| `angel_corroded` | A corroded angel: a tall thin winged figure like an old chapel statue, green-stained bronze skin, wings of corroded metal feathers, empty face, as tall as the reference knight. Frame 1 hovering with arms open, frame 2 diving down vertically. |

### Terrestri

| File | ENEMY |
| --- | --- |
| `miner_mutant` | A mutated miner: a hunched colonist in a torn orange mining suit fused with his gear, a helmet lamp flickering, one arm grown into a pickaxe. Frame 1 walking, frame 2 swinging the pickaxe. |
| `keeper_faceless` | A faceless keeper: a tall slow humanoid in a long grey institutional coat, a smooth blank oval face with no features, heavy metal gloves, as tall as the reference knight. Frame 1 standing guard, frame 2 raising a gloved hand to strike. |
| `copy_knight` | A faulty copy of the reference knight: same silhouette and armor but wrong colors, washed-out grey and sickly green, a flickering visor, a cracked sword, jerky posture like a bad recording. Frame 1 guard, frame 2 lunging. |
| `corpse_pressure` | A pressurized corpse: a bloated colonist in a swollen, overinflated pressure suit, glowing warning lights on the chest, hissing valves, about to burst. No gore. Frame 1 shambling, frame 2 swelling up. |
| `golem_scrap` | A scrap golem TWICE as tall as the reference knight: a lumbering body of welded pipes, car doors, tanks and cables, a furnace glowing in the chest. Frame 1 walking, frame 2 throwing a piece of metal. |
| `drone_repair` | A small maintenance drone on four spider legs, low to the ground, a welding torch arm, a blinking green light, knee height. Frame 1 scuttling, frame 2 welding with sparks. |
| `dog_quarry` | An eyeless quarry dog: a lean, hairless grey mining hound with no eyes, a large nose and bared teeth, a broken work collar with a tag. Frame 1 running, frame 2 leaping to bite. |
| `rat_armored` | An armored rat: a cat-sized rat with overlapping metal-like plates on its back, a thick tail, sharp yellow teeth. Frame 1 running, frame 2 rearing up. |
| `lizard_cryo` | A cryogenic lizard: long, low, pale blue-grey scaly body covered in frost, icy crystals along the spine, cold white breath. Frame 1 still and flat, frame 2 lunging with open jaws. |
| `boar_mining` | A mining boar: a heavy boar with a reinforced metal plate welded on its forehead, drill-like tusks, rust-brown bristles. Frame 1 pawing the ground, frame 2 charging head down. |
| `spider_duct` | A duct spider: a long-legged pale spider as big as a dog, hanging from a thread, legs like thin metal tubes, many small glowing eyes. Frame 1 hanging, frame 2 dropping with legs open. |
| `worm_silicon` | A silicon worm emerging from the ground: segmented body made of glassy dark grey mineral plates, a round mouth with crystal teeth. Frame 1 half emerged, frame 2 fully raised spitting shards. |

## Guardiani

Alti il doppio di NightKnight, cavalieri e non soldati, ciascuno con arma e
aspetto del suo satellite. Prima si genera solo la posa in guardia; poi le altre
pose (camminata, attacco, speciale, colpito, a terra) partendo da quella.

### Titano — proposta, da confermare

Armatura di rame e ottone brunita dalla foschia, elmo con una grata che sfiata
nebbia arancione, mantello ruggine, alabarda da estrazione con gancio da pozzo.

```text
The Guardian of Titan, a boss for a side-scrolling game: a knight, not a soldier, TWICE as tall as the attached knight, broad and imposing. Ritual retro-futurist armor of tarnished copper and brass, darkened by the orange haze, with pipes and valves along the back. A tall sealed great helm with a vertical grille instead of a visor, venting thick orange fog that trails around his shoulders and legs. A long heavy mantle of dark rust-red cloth. He wields a long industrial halberd: an axe blade on one side and a hook for methane wells on the other. On his breastplate, a worn emblem of Saturn with its rings.

Full body, side view facing LEFT, standing in guard with the halberd held diagonally, calm and menacing. Transparent PNG background with real alpha, 1024x1024, no ground, no shadow, no text, no frame.
```
