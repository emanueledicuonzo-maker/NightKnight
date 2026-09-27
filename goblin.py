#!/usr/bin/env python3
"""NightKnight - Titano: le ondate, la traversata, il duello col Guardiano. 1920x1080."""
import math
import os
import argparse
import random

import numpy
import pygame

import assets
import athletics
import knights
import levels
import music
import fonts
import progress
import titan
import waves

W, H = 1920, 1080
FPS = 60
TILE = 64
SKY_PAN = 360        # di quanto scorre il cielo dall'inizio alla fine del livello
# Zoom: il mondo si disegna in una vista di VW x VH pixel ingrandita a tutto
# schermo; il terreno resta alla stessa altezza. Cielo, fondali e HUD no.
ZOOM = 1.5
VW, VH = int(W / ZOOM), int(H / ZOOM)
LUCE_MAX, LUCE_UNIT, LUCE_PER_PRISONER = 100, 25, 5
LAKE_LEVEL = 22
OXYGEN_MAX = 100
OXYGEN_DRAIN = OXYGEN_MAX / (150 * 60)     # due minuti e mezzo di riserva all'aperto
# Senz'aria non si muore: si rallenta, si salta meno, si ansima, e ogni colpo
# (spada, sasso, calcio) vale mezzo sasso finche' non si trova una stazione.
BREATHLESS_SPEED, BREATHLESS_JUMP, BREATHLESS_HIT = 0.6, 0.8, 0.5
VENT_PUSH = 3.0        # il getto d'azoto respinge chi prova ad attraversarlo
OXYGEN_REFILL = 1.2
CHILL_FRAMES = 120     # l'azoto gela la tuta: due secondi lenti
CHILL_SPEED, CHILL_JUMP = 0.25, 0.78    # velocita' e slancio del salto mentre si e' gelati
GEYSER_LAUNCH = (9, -21)                # il criovulcano sbalza via chi ci finisce dentro
BURST_FRAMES = 70    # durata del volo di Bianca durante la raffica
LADDER_W = 3         # le scale di servizio sono larghe tre tessere
ROCK_N = 4           # la roccia delle pareti copre 4x4 tessere
TITAN_N = 6          # il terreno di Titano copre 6x6 tessere
ROWS = levels.ROWS
GROUND = levels.GROUND
# Da fermo in superficie i piedi stanno FEET_IN_VIEW pixel sotto il bordo alto
# della vista; VIEW_Y e' la cima della vista in quel caso (ondate, duello).
FEET_IN_VIEW = int(14 * TILE / ZOOM)
VIEW_Y = GROUND * TILE - FEET_IN_VIEW
CAM_TOP, CAM_BOTTOM = 70, 150
LADDER_LOOK = TILE         # sulla scala la vista sale di una tessera
# Zoom: in combattimento la telecamera si avvicina, ma non in mezzo alla folla
# (li' serve vedere); nel duello resta un po' piu' vicina per tutto lo scontro.
ZOOM_FIGHT, ZOOM_DUEL = 1.75, 1.6
# Cadendo, appesi al cavo o sul bordo di un vuoto la telecamera si allontana per
# far vedere dove si atterra; il mondo si disegna largo quanto serve a quello zoom.
ZOOM_OUT = 1.2
ZOOM_WIDEST = 1.0    # appesi ai cavi alti: quanto serve per vedere anche il lago sotto
DW, DH = int(W / ZOOM_WIDEST), int(H / ZOOM_WIDEST)
DROP_BIAS = 1.0
EDGE_DROP = 5        # un vuoto di almeno 5 tessere sotto il bordo: tutta larga
STEP_DROP, ZOOM_STEP = 2, 1.35    # un gradino di 2-4 tessere: un po' piu' larga
EDGE_LOOK = 3        # quante tessere avanti si guarda per trovare il bordo
LOW_MARGIN = 110     # il suolo piu' basso li' vicino resta almeno cosi' sopra il fondo della vista      # allontanandosi, la vista scende: si vede sotto i piedi
FIGHT_RANGE = (520, 320)     # distanza (orizzontale, verticale) dei nemici che fanno avvicinare
# Piani di parallasse sopra il cielo: (immagine, velocita', spostamento in giu',
# foschia steso sopra). Il primo piano, davanti al mondo, corre piu' del terreno.
PARALLAX = (("hills_far", 0.07, 0, 70), ("hills_01", 0.16, 0, 45),
            ("colony_ruins", 0.28, 90, 30), ("hills_02", 0.42, 0, 38))
FOG_COLOR = (196, 112, 58)
DARKNESS, VISOR = 140, 640       # buio delle gallerie e raggio della luce della visiera
FOREGROUND_SPEED, FOREGROUND_SINK = 1.35, 230
CROWD = 6                    # con piu' nemici vicini di cosi' la telecamera resta larga      # margini oltre i quali la telecamera insegue un salto o una caduta
GRAVITY = 0.75
MAX_FALL = 18
RUN_ACC = 0.65
RUN_MAX = 5.8
SWORD_REACH = 240       # la spada lunga e sottile arriva lontano
SWORD_FRAMES = 20       # tre fendenti al secondo
# Combo: premendo Z durante un fendente (o appena finito) parte il successivo, fino
# a tre; il terzo fa un passo avanti e arriva ancora piu' lontano.
COMBO_MAX, COMBO_WINDOW, LUNGE_SPEED, LUNGE_REACH = 3, 16, 9.0, 60
STONE_FRAMES = 30       # due sassi al secondo
# Danno in colpi: la spada vale 2, il sasso sempre la meta'.
SWORD_HIT, STONE_HIT = 2, 1
SPIN_REACH = 130
SPIN_MIN_SPEED = 1.0
SPIN_FRAMES = 42
SPIN_RECOVERY = 26      # all'atterraggio dopo il calcio girato si resta scoperti
SPRINT_MAX = 10.0
JUMP_V = -20.0
SHORT_JUMP_V = -16.0
CLIMB = 5
COYOTE_FRAMES = 6
JUMP_BUFFER_FRAMES = 7
PLAYER_HP = 100
# Bianca in incursione: con piu' di BIANCA_CROWD nemici sullo schermo ne abbatte da
# sola fino a BIANCA_SORTIE, uno alla volta (volanti e di terra), poi riposa.
BIANCA_CROWD, BIANCA_SORTIE, BIANCA_SPEED, BIANCA_REST = 4, 5, 17, 12 * 60
# Corsa: doppio tocco della freccia e tenerla premuta (o Maiusc); l'ossigeno cala di piu'.
DOUBLE_TAP, SPRINT_O2 = 14, 2.5
# Nova: al decimo colono liberato, una volta per livello, 9T9T scarica il nucleo
# della tuta: salta, calcio girato, due bagliori, e non resta nessuno sullo schermo.
NOVA_PRISONERS, NOVA_FRAMES, NOVA_FLASH, NOVA_BLAST, NOVA_BOSS = 10, 110, 46, 64, 0.30
# Nel duello Bianca attacca da sola il Guardiano: una picchiata ogni tanto.
BIANCA_BOSS_HIT, BIANCA_BOSS_REST = 0.02, 6 * 60
BOSS_FAR, BOSS_STRIDE = 1250, 4      # oltre questa distanza il Guardiano viene avanti
NOVA_HEIGHT = 260          # quanto sale 9T9T durante la scarica
# larghezza (px) del cono nei cinque disegni dell'eruzione, per allinearli al nostro
GEYSER_ERUPT_CONES = (1388, 1391, 899, 1102, 1053)
GEYSER_CONE = 1.3          # il cono dell'eruzione appena piu' largo del nostro
NOVA_BEAM = 180            # larghezza della colonna di luce
# Meduse: ti puntano appena ti vedono e ti si attaccano (al massimo tre); ognuna
# rallenta e toglie un po' di vita finche' un colpo non la stacca.
# I camminatori sul terreno: gradini da saltare, da scendere, laghi da scavalcare.
WALKER_STEP, WALKER_DROP, WALKER_GAP, WALKER_TURN = 3, 4, 4, 90
WORM_MOUND, WORM_SINK, WORM_FLAT = 45, 18, 2    # il cumulo di terra del verme: piu' largo di lui, e affonda nel suolo
BURROW_RUMBLE, BURROW_OUT = 40, 130     # il verme alla Tremors: preavviso e tempo fuori
JELLY_SPEED, JELLY_MAX, JELLY_SLOW, JELLY_DRAIN, JELLY_EVERY = 4.2, 3, 0.22, 3, 50
LAND_FRAMES, HURT_FRAMES = 10, 22
SOLID = set("#DS")

PS = 8          # scala pixel art personaggi
PW, PH = 16 * PS, 24 * PS


# ---------------------------------------------------------------- grafica
def player_images():
    """Le pose senza un foglio proprio usano NightKnight in piedi."""
    img = assets.load("knight_idle", PW, PH, by_height=True)
    return {"idle": (img, assets.flip(img))}


class Gfx:
    def __init__(self):
        # caratteri disegnati come terreno (le pareti "S" dell'arena sono invisibili)
        self.tiles = set("#DH")
        # Terreno di Titano: l'immagine e' un'unica sezione di suolo alla Huygens.
        # Si scala a TITAN_N x TITAN_N tessere, cosi' i ciottoli restano leggibili:
        # la riga in alto e' la crosta calpestabile, le altre il sottosuolo.
        self.titan_ground = None
        if assets.has("titan_ground_grass"):
            img = pygame.image.load(os.path.join(assets.DIR, "titan_ground_grass.png")).convert()
            top = img.get_height() // 30          # striscia scura sopra la superficie
            img = img.subsurface((0, top, img.get_width(), img.get_height() - top))
            self.titan_ground = pygame.transform.smoothscale(img, (TILE * TITAN_N, TILE * TITAN_N))
        # Roccia delle pareti e dei cumuli: strati di Titano, 4x4 tessere
        rock = pygame.image.load(os.path.join(assets.DIR, "titan_rock.png")).convert()
        self.titan_rock = pygame.transform.smoothscale(rock, (TILE * ROCK_N, TILE * ROCK_N))
        # Lago di metano: liquido scuro, un po' sotto il bordo, che riflette il cielo.
        depth = levels.LAKE_DEPTH * TILE
        self.titan_lake = pygame.Surface((TILE, depth), pygame.SRCALPHA)
        for y in range(LAKE_LEVEL, depth):
            k = (y - LAKE_LEVEL) / (depth - LAKE_LEVEL)
            # metano liquido: arancio scuro che riflette il cielo, non un buco nero
            top, low = (178, 100, 50), (78, 40, 22)
            color = tuple(int(a + (b - a) * min(1, k * 1.4)) for a, b in zip(top, low))
            pygame.draw.line(self.titan_lake, color + (255,), (0, y), (TILE, y))
        pygame.draw.line(self.titan_lake, (240, 176, 104, 255), (0, LAKE_LEVEL), (TILE, LAKE_LEVEL), 3)
        # Vignettatura: bordi dello schermo appena piu' scuri
        # Insidie di Titano disegnate: criovulcano (cono e colonna), condotta dell'azoto
        for key, name, n, h, ref in (("geyser", "geyser", 2, 118, 0), ("geyser_jet", "geyser_jet", 3, 340, 1),
                                     ("vent", "gas_vent", 2, 112, 0)):
            art = assets.pieces(name, n, h, ref)
            if art:
                titan.ART[key] = art
        # l'eruzione: cinque disegni interi (cono e vapore), dal filo alla colonna piena,
        # scalati perche' il loro cono sia largo come il nostro
        if all(assets.has(f"geyser_erupt_{i}") for i in range(1, 6)) and "geyser" in titan.ART:
            cone = titan.ART["geyser"][0].get_width() * GEYSER_CONE
            frames = []
            for i, width in enumerate(GEYSER_ERUPT_CONES, 1):
                im = pygame.image.load(os.path.join(assets.DIR, f"geyser_erupt_{i}.png")).convert_alpha()
                k = cone / width
                im = pygame.transform.smoothscale(im, (int(im.get_width() * k), int(im.get_height() * k)))
                # la cima del vapore sfuma: nei disegni a volte e' tagliata dal bordo
                fade = im.get_height() // 5
                for y in range(fade):
                    im.fill((255, 255, 255, int(255 * (y / fade) ** 0.7)), (0, y, im.get_width(), 1),
                            special_flags=pygame.BLEND_RGBA_MULT)
                frames.append(im)
            titan.ART["erupt"] = frames
            titan.ERUPT_REACH = tuple(int(f.get_height() * 0.9) for f in frames)
        # Il cavo fra due gru della colonia, l'impugnatura, il gancio del Guardiano
        pylon = assets.pieces("cable_pylon", 2, athletics.FLOOR - athletics.Rope.ANCHOR_Y + 30, 0)
        handle = assets.pieces("cable_pylon", 2, 64, 1)
        if pylon and handle:
            athletics.ART.update(pylon=pylon[0], handle=handle[1])
        hook = assets.pieces("hook", 2, 70, 0)
        link = assets.pieces("hook", 2, 22, 1)
        if hook and link:
            knights.ART.update(hook=hook[0], link=pygame.transform.rotate(link[1], 90))
        # Ombra sotto le cengie sospese
        self.ledge_shadow = pygame.Surface((TILE, 26), pygame.SRCALPHA)
        for yy in range(26):
            pygame.draw.line(self.ledge_shadow, (20, 10, 6, int(110 * (1 - yy / 26) ** 1.5)), (0, yy), (TILE, yy))
        # Buio delle gallerie e luce della visiera (un alone che sfuma al buio).
        self.darkness = pygame.Surface((W, H), pygame.SRCALPHA)
        self.visor_light = pygame.Surface((VISOR * 2, VISOR * 2), pygame.SRCALPHA)
        self.visor_light.fill((255, 255, 255, 255))
        for rad in range(VISOR, 0, -4):
            k = rad / VISOR
            pygame.draw.circle(self.visor_light, (255, 255, 255, int(255 * k ** 1.6)), (VISOR, VISOR), rad)
        # Primo piano all'aperto: solo le sagome che salgono dal basso (quelle
        # appese in alto servono sottoterra).
        fg = assets.load("foreground", W, H, exact=True)
        self.foreground_low = fg.subsurface((0, H * 55 // 100, W, H * 45 // 100)).copy()
        self.vignette = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(60):
            a = int(90 * (1 - i / 60) ** 2)
            pygame.draw.rect(self.vignette, (10, 4, 2, a), (i * 6, i * 4, W - i * 12, H - i * 8), 6)
        # Ombra sui fianchi delle rocce
        self.rock_shade = pygame.Surface((18, TILE), pygame.SRCALPHA)
        for x in range(18):
            pygame.draw.line(self.rock_shade, (30, 14, 8, 120 - x * 6), (x, 0), (x, TILE))
        self.rock_shade_r = pygame.transform.flip(self.rock_shade, True, False)
        # Scala di servizio in acciaio, con i contorni del cartoon
        self.titan_ladder = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        for x in (12, TILE - 18):
            pygame.draw.rect(self.titan_ladder, (22, 18, 16), (x - 2, 0, 10, TILE))
            pygame.draw.rect(self.titan_ladder, (104, 100, 96), (x, 0, 6, TILE))
        for y in range(8, TILE, 16):
            pygame.draw.rect(self.titan_ladder, (22, 18, 16), (12, y - 2, TILE - 24, 8))
            pygame.draw.rect(self.titan_ladder, (140, 132, 122), (14, y, TILE - 28, 4))
        # Roccia delle gallerie, decorazioni e imbocco
        self.cave_rock = None
        if assets.has("cave_rock"):
            img = pygame.image.load(os.path.join(assets.DIR, "cave_rock.png")).convert()
            self.cave_rock = pygame.transform.smoothscale(img, (TILE * ROCK_N, TILE * ROCK_N))
        # stalattiti e stalagmiti piu' piccole del puntello, che va da pavimento a soffitto
        self.cave_props = [pygame.transform.smoothscale_by(img, k) for img, k in
                           zip(assets.pieces("cave_props", 5, 7 * TILE - 20, 2) or [], (0.5, 0.6, 1, 0.7, 0.8))]
        self.cave_mouth = assets.load("cave_mouth", 10 * TILE, 9 * TILE) if assets.has("cave_mouth") else None
        # La scala disegnata: una striscia che si ripete in altezza (per riga)
        self.ladder_strip = None
        if assets.has("ladder"):
            img = pygame.image.load(os.path.join(assets.DIR, "ladder.png")).convert_alpha()
            # ritaglio sui pixel ben visibili: il fondo ha un velo quasi trasparente
            box = pygame.mask.from_surface(img, 127).get_bounding_rects()
            img = img.subsurface(box[0].unionall(box[1:])).copy()
            w = LADDER_W * TILE - 16
            h = max(TILE, round(img.get_height() * w / img.get_width() / TILE) * TILE)
            self.ladder_strip = pygame.Surface((LADDER_W * TILE, h), pygame.SRCALPHA)
            self.ladder_strip.blit(pygame.transform.smoothscale(img, (w, h)), (8, 0))
        # Portello stagno dell'uscita, la capsula d'atterraggio, la stazione d'ossigeno
        self.airlock = assets.load("portello", TILE * 5, int(PH * 1.5), by_height=True)
        self.capsule = assets.load("capsula", TILE * 5, int(PH * 1.7), by_height=True)
        self.station = assets.load("stazione_ossigeno", TILE * 3, int(PH * 1.05), by_height=True)
        self.player = player_images()
        self.sheets = {}
        # posa -> (file, colonne, righe): i fogli cartoon hanno griglie diverse
        # scale: le pose piegate si rimpiccioliscono, quelle a braccia alzate crescono,
        # cosi' il cavaliere resta della stessa taglia; typical=False scala sulla figura
        # piu' alta (morte, atterraggio, presa al bordo: le altre sono piu' basse di lui)
        for pose, (file, cols, rows, scale, typical) in {
                "run": ("run_sheet", 4, 2, 1, True), "jump": ("jump_sheet", 4, 2, 1, True),
                "throw": ("sword_sheet", 4, 1, 1, True), "punch": ("stone_sheet", 4, 1, 1, True),
                "kick": ("kick_sheet", 3, 1, 1, True), "flykick": ("flykick_sheet", 3, 1, 1, True),
                "spinkick": ("spinkick_sheet", 4, 2, 1, True),
                "idle": ("idle_sheet", 4, 1, 1, True), "climb": ("climb_sheet", 4, 1, 1.12, True),
                "hang": ("hang_sheet", 4, 1, 1.1, True), "hurt": ("hurt_sheet", 2, 1, 1, True),
                "death": ("death_sheet", 4, 1, 1, False), "land": ("land_sheet", 2, 1, 0.78, False),
                "tired": ("tired_sheet", 4, 1, 0.9, True), "wind": ("wind_sheet", 4, 1, 0.88, True),
                "ledge": ("ledge_sheet", 4, 1, 1.1, False)}.items():
            fr = assets.sheet("knight_" + file, int(PH * scale), cols, rows, typical=typical)
            if fr:
                self.sheets[pose] = (fr, [assets.flip(f) for f in fr])
        # Prigionieri: coloni chiusi in una capsula, poco piu' alta di NightKnight.
        self.spento_sleeping = assets.load("prigioniero_spento", PW * 2, PH * 5 // 4, by_height=True)
        self.spento_awake = assets.load("prigioniero_acceso", PW * 2, PH * 5 // 4, by_height=True)
        # Bianca: due pose di volo.
        self.bianca = [assets.load(f"bianca_chick_{i + 1}", 150, 105, by_height=True) for i in range(2)]
        # Nemici: due fotogrammi per specie, stessa scala per entrambi.
        self.foes = {kind: assets.frames([spec["frames"].format(i) for i in (1, 2)], spec.get("h", 10 * PS))
                     for table in (WALKERS, FLYERS) for kind, spec in table.items()}
        self.skeleton, self.crow = self.foes["skeleton"], self.foes["crow"]
        # il verme resta dov'e': quando attacca sputa schegge ma non si solleva
        for kind in ("worm", "burrower"):
            rest, bite = self.foes[kind]
            h = int(rest.get_height() * 1.12)
            self.foes[kind] = [rest, pygame.transform.smoothscale(bite, (int(bite.get_width() * h / bite.get_height()), h))]
        # foschia bassa che lega il terreno ai fondali
        self.haze = pygame.Surface((DW, 105), pygame.SRCALPHA)
        for yy in range(105):
            pygame.draw.line(self.haze, (184, 91, 31, int(60 * math.sin(math.pi * yy / 105))), (0, yy), (DW, yy))
        self.boss_cache = {}
        self.bg_cache = {}

    def knight(self, num, color):
        if num not in self.boss_cache:
            self.boss_cache[num] = knights.knight_images(self, num, color)
        return self.boss_cache[num]

    def title_backdrop(self):
        """Titolo: cielo di Titano smorzato, lo stemma al centro, NightKnight a sinistra."""
        if "title" not in self.bg_cache:
            bg = self.background("sky", 1).copy()
            shade = pygame.Surface((W, H), pygame.SRCALPHA)
            shade.fill((20, 8, 4, 110))
            bg.blit(shade, (0, 0))
            if assets.has("emblema"):
                em = assets.load("emblema", 560, 470, by_height=True)
                bg.blit(em, (W // 2 - em.get_width() // 2, 250))
            if assets.has("knight_idle"):
                hero = assets.load("knight_idle", 900, 820, by_height=True)
                bg.blit(hero, (330 - hero.get_width() // 2, H - hero.get_height() - 20))
            self.bg_cache["title"] = bg
        return self.bg_cache["title"]

    def titan_tile(self, ch, c, r, part=0):
        if ch == "H":
            if self.ladder_strip:
                # la scala e' larga LADDER_W tessere: part dice quale striscia di lei
                y = (r * TILE) % self.ladder_strip.get_height()
                return self.ladder_strip.subsurface((part % LADDER_W * TILE, y, TILE, TILE))
            return self.titan_ladder
        if self.titan_ground is None or ch not in "#D":
            return None
        if ch == "D" and r > GROUND + 2 and self.cave_rock and c >= levels.TITAN_PASS_START:
            # sotto la crosta: la roccia scura delle gallerie
            return self.cave_rock.subsurface(((c % ROCK_N) * TILE, (r % ROCK_N) * TILE, TILE, TILE))
        if ch == "D" and r < GROUND:
            # sopra il livello del suolo e' parete o cumulo: roccia a strati
            return self.titan_rock.subsurface(((c % ROCK_N) * TILE, (r % ROCK_N) * TILE, TILE, TILE))
        row = 0 if ch == "#" else 1 + r % (TITAN_N - 1)
        return self.titan_ground.subsurface(((c % TITAN_N) * TILE, row * TILE, TILE, TILE))

    def wide_sky(self, num, pan):
        """Cielo allargato di `pan` pixel, in proporzione, ancorato in basso."""
        key = ("wide_sky", num, pan)
        if key not in self.bg_cache:
            sky = self.background("sky", num)
            k = (W + pan) / sky.get_width()
            self.bg_cache[key] = pygame.transform.smoothscale(sky, (W + pan, int(sky.get_height() * k)))
        return self.bg_cache[key]

    def sized(self, img, k):
        if k == 1.0:
            return img
        key = ("sized", id(img), k)
        if key not in self.bg_cache:
            self.bg_cache[key] = pygame.transform.smoothscale(img, (int(img.get_width() * k), int(img.get_height() * k)))
        return self.bg_cache[key]

    def white(self, img):
        """Sagoma bianca per il lampo del colpo."""
        key = ("white", id(img))
        if key not in self.bg_cache:
            w = img.copy()
            w.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
            self.bg_cache[key] = w
        return self.bg_cache[key]

    def mirrored(self, img):
        """Striscia [immagine | immagine specchiata]: ripetuta, non mostra cuciture."""
        key = ("mirrored", id(img))
        if key not in self.bg_cache:
            strip = pygame.Surface((img.get_width() * 2, img.get_height()), pygame.SRCALPHA)
            strip.blit(img, (0, 0))
            strip.blit(pygame.transform.flip(img, True, False), (img.get_width(), 0))
            self.bg_cache[key] = strip
        return self.bg_cache[key]

    def nova_beam(self, h):
        """Colonna di luce di Nova, alta h: chiara al centro, sfumata ai lati."""
        key = ("beam", h // 16)
        if key not in self.bg_cache:
            beam = pygame.Surface((NOVA_BEAM, max(1, h // 16 * 16)), pygame.SRCALPHA)
            for x in range(NOVA_BEAM):
                k = math.exp(-((x - NOVA_BEAM / 2) / (NOVA_BEAM / 6)) ** 2)
                pygame.draw.line(beam, (int(255 * k), int(226 * k), int(160 * k), 255), (x, 0), (x, beam.get_height()))
            self.bg_cache[key] = beam
        return self.bg_cache[key]

    def frosted(self, img):
        """La stessa figura coperta di brina azzurra."""
        key = ("frost", id(img))
        if key not in self.bg_cache:
            out = img.copy()
            out.fill((150, 205, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            out.fill((40, 60, 80, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self.bg_cache[key] = out
        return self.bg_cache[key]

    def layer(self, name):
        """Piano di parallasse a tutto schermo."""
        return self.background(name, None)

    def fogged(self, img, fogs, top=0):
        """L'immagine con sopra, gia' stesa, la foschia dei piani davanti a lei
        (piu' densa verso l'orizzonte): a schermo costa come un'immagine sola."""
        key = ("fogged", id(img), fogs, top)
        if key not in self.bg_cache:
            y = (numpy.arange(img.get_height()) + top) / H
            profile = 0.35 + 0.65 * numpy.exp(-((y - 0.58) / 0.18) ** 2)
            keep = numpy.ones_like(profile)
            for alpha in fogs:
                keep *= 1 - alpha / 255 * profile
            out = img.copy()
            rgb = pygame.surfarray.pixels3d(out)
            rgb[:] = (rgb * keep[None, :, None] + numpy.array(FOG_COLOR) * (1 - keep[None, :, None])).astype("uint8")
            del rgb
            self.bg_cache[key] = out
        return self.bg_cache[key]

    def background(self, kind, num=1):
        """Fondale disegnato del satellite (sky_01, hills_01...)."""
        key = (kind, num)
        if key not in self.bg_cache:
            name = kind if num is None else f"{kind}_{num:02d}"
            self.bg_cache[key] = assets.load(name, W, H, exact=True)
        return self.bg_cache[key]


class Level:
    def __init__(self, g, kind):
        self.g = g
        self.kind = kind
        self.cols = len(g[0])
        self.w = self.cols * TILE
        self.rows = len(g)
        self.h = self.rows * TILE
        self.markers = []
        for r in range(self.rows):
            for c in range(self.cols):
                if g[r][c] in "Equoc":
                    self.markers.append((g[r][c], c, r))
        self.exit = next(((c, r) for ch, c, r in self.markers if ch == "E"), (self.cols - 4, GROUND - 1))

    def at(self, c, r):
        if c < 0 or c >= self.cols:
            return "S"
        if r < 0 or r >= self.rows:
            return "."
        return self.g[r][c]

    def solid(self, x, y):
        return self.at(int(x // TILE), int(y // TILE)) in SOLID

    def tile_at(self, x, y):
        return self.at(int(x // TILE), int(y // TILE))

    def floor_near(self, x, y, reach=8, liquid=False):
        """La quota del suolo (una cima con aria sopra) nella colonna di x piu'
        vicina a y, entro `reach` tessere; None se li' c'e' solo vuoto o metano.
        liquid: anche il pelo di un lago conta (per la telecamera, non per chi cammina)."""
        c = int(x // TILE)
        best = None
        for r in range(max(1, int(y // TILE) - reach), min(self.rows, int(y // TILE) + reach)):
            cell, above = self.at(c, r), self.at(c, r - 1)
            top = (cell in SOLID and above not in SOLID and above != "~") or (liquid and cell == "~" and above != "~")
            if top:
                if best is None or abs(r * TILE - y) < abs(best - y):
                    best = r * TILE
        return best

    def drowned(self, rect):
        """Finito nel metano: la testa e' gia' sotto il pelo del lago."""
        return self.tile_at(rect.centerx, rect.top + 30) == "~" or rect.top > self.h


# ---------------------------------------------------------------- entita'
class Entity:
    w, h = 70, 176
    ox, oy = 29, 16       # offset sprite -> hitbox

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.on_ground = False
        self.alive = True
        self.facing = 1

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def move(self, lv, gravity=True):
        self.x += self.vx
        r = self.rect
        if self.vx > 0:
            for py in (r.top + 2, r.centery, r.bottom - 2):
                if lv.solid(r.right - 1, py):
                    self.x = (r.right - 1) // TILE * TILE - self.w
                    self.vx = 0
                    break
        elif self.vx < 0:
            for py in (r.top + 2, r.centery, r.bottom - 2):
                if lv.solid(r.left, py):
                    self.x = (r.left // TILE + 1) * TILE
                    self.vx = 0
                    break
        if gravity:
            self.vy = min(self.vy + GRAVITY * getattr(self, "gravity_scale", 1.0), MAX_FALL)
        self.y += self.vy
        r = self.rect
        self.on_ground = False
        if self.vy > 0:
            if lv.solid(r.left + 2, r.bottom) or lv.solid(r.right - 3, r.bottom):
                self.y = r.bottom // TILE * TILE - self.h
                self.vy = 0
                self.on_ground = True
        elif self.vy < 0:
            if lv.solid(r.left + 2, r.top) or lv.solid(r.right - 3, r.top):
                self.y = (r.top // TILE + 1) * TILE
                self.vy = 0

    def draw_img(self, s, img, cam):
        r = self.rect
        if self.on_ground:
            # a terra: ombra di contatto e piedi appena dentro il suolo
            titan.ground_shadow(s, r.centerx - cam, r.bottom, r.w * 1.3)
            s.blit(img, (r.centerx - img.get_width() // 2 - cam, r.bottom - img.get_height() + titan.SINK // 2))
            return
        s.blit(img, (r.centerx - img.get_width() // 2 - cam, r.bottom - img.get_height()))


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.hp = PLAYER_HP
        self.albedo = 0
        self.invuln = 0
        self.anim = 0.0
        self.run_t = 0.0
        self.attack = None
        self.swing = 0
        self.recover = 0
        self.oxygen = OXYGEN_MAX
        self.chill = 0
        self.climbing = False
        self.last_down = -999
        self.last_fwd = -999
        self.coyote = 0
        self.jump_buffer = 0
        self.jumped = False
        self.weapon = levels.weapon_cfg(0)
        self.gravity_scale = 1.0
        self.t = 0
        self.combo, self.combo_t, self.slash_queued = 0, 0, False     # combo di spada
        self.new_slash = False
        self.running = 0          # corsa col doppio tocco: verso in cui si corre
        self.last_tap, self.tap_dir = -999, 0
        self.jellies = 0          # meduse attaccate addosso
        self.land_t = self.hurt_t = 0
        self.hanging = None       # appeso al cavo: -1 gambe indietro, 0 dritto, 1 gambe avanti

    def hurtbox(self):
        return self.rect.inflate(-10, -6)

    @property
    def sprinting(self):
        return abs(self.vx) > RUN_MAX + 0.5

    @property
    def breathless(self):
        return self.oxygen <= 0

    def power(self, hits):
        """Senz'aria ogni colpo vale mezzo sasso."""
        return BREATHLESS_HIT if self.breathless else hits

    def attack_box(self):
        if not self.attack:
            return None, 0
        name, f = self.attack
        r = self.rect
        if name == "spin" and 6 <= f <= 34:
            # calcio volante girato: due giri, colpisce tutto intorno, davanti e dietro
            return r.inflate(2 * SPIN_REACH, 60), 14
        if name == "kick" and 4 <= f <= 12:
            return pygame.Rect(r.right if self.facing > 0 else r.left - 110, r.top + 76, 110, 60), 9
        if name == "throw" and 4 <= f <= 10:
            # il fendente scende fino ai piedi: prende anche lucertole e ratti
            reach = SWORD_REACH + (LUNGE_REACH if self.combo == COMBO_MAX else 0)
            return pygame.Rect(r.right if self.facing > 0 else r.left - reach, r.top + 40, reach, r.h - 40), 12
        return None, 0

    def update(self, keys, lv):
        self.t += 1
        self.land_t = max(0, self.land_t - 1)
        self.hurt_t = max(0, self.hurt_t - 1)
        self.hanging = None
        self.jumped = False
        self.coyote = COYOTE_FRAMES if self.on_ground else max(0, self.coyote - 1)
        self.jump_buffer = max(0, self.jump_buffer - 1)
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up = keys[pygame.K_UP] or keys[pygame.K_w]
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        jump = keys[pygame.K_SPACE] or up
        held = (right and not left and self.running > 0) or (left and not right and self.running < 0)
        if not held:
            self.running = 0                        # si corre finche' si tiene premuto
        speed_limit = SPRINT_MAX if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or self.running else RUN_MAX
        if self.chill:
            self.chill -= 1
            speed_limit *= CHILL_SPEED
        speed_limit *= 1 - JELLY_SLOW * self.jellies
        if self.breathless:
            speed_limit *= BREATHLESS_SPEED
        if not self.on_ground:
            speed_limit = max(speed_limit, abs(self.vx))
        r = self.rect
        on_ladder = lv.tile_at(r.centerx, r.centery) == "H"
        ladder_below = lv.tile_at(r.centerx, r.bottom + 2) == "H"
        if not self.climbing and ((on_ladder and (up or down)) or (ladder_below and down and self.on_ground)):
            self.climbing = True
            self.attack = None
            if ladder_below and not on_ladder:
                self.y += 8
            # ci si aggrappa al centro della scala, non a un fianco
            ry = r.centery if on_ladder else r.bottom + 2
            c0 = c1 = r.centerx // TILE
            while lv.tile_at((c0 - 1) * TILE, ry) == "H":
                c0 -= 1
            while lv.tile_at((c1 + 1) * TILE, ry) == "H":
                c1 += 1
            self.x = (c0 + c1 + 1) * TILE / 2 - self.w / 2
        if self.climbing:
            if not (on_ladder or ladder_below):
                self.climbing = False
            else:
                self.vx = 0
                self.vy = 0
                feet_row = r.bottom // TILE
                at_top = lv.at(r.centerx // TILE, feet_row) == "H" and lv.at(r.centerx // TILE, feet_row - 1) != "H"
                if up and at_top and r.bottom - feet_row * TILE <= CLIMB * 4:
                    self.y = feet_row * TILE - self.h      # in piedi sulla cima della scala
                    self.climbing = False
                    self.on_ground = True
                    return
                if up:
                    self.y -= CLIMB
                elif down:
                    self.y += CLIMB
                if left and not right:
                    self.facing = -1                  # ci si gira per colpire, senza scendere
                elif right and not left:
                    self.facing = 1
                self.anim += 0.5 if (up or down) else 0
                self.advance_attack()
                self.move(lv, gravity=False)
                if self.on_ground and down:
                    self.climbing = False
                if self.invuln:
                    self.invuln -= 1
                return
        grounded_attack = self.attack and self.on_ground
        if self.recover:
            # atterraggio pesante dopo il calcio girato: niente comandi per un attimo
            self.recover -= 1
            self.vx *= 0.7
        elif self.attack and self.attack[0] == "spin":
            pass                          # in volo il giro conserva lo slancio
        elif not grounded_attack:
            if right and not left:
                self.vx = min(self.vx + RUN_ACC, speed_limit); self.facing = 1
            elif left and not right:
                self.vx = max(self.vx - RUN_ACC, -speed_limit); self.facing = -1
            else:
                self.vx *= 0.8 if self.on_ground else 0.98
                if abs(self.vx) < 0.3:
                    self.vx = 0
        elif self.attack[0] == "throw" and self.combo == COMBO_MAX and self.attack[1] < 9:
            self.vx = self.facing * LUNGE_SPEED        # il terzo fendente fa un passo avanti
        else:
            self.vx = 0
        if not jump and self.vy < SHORT_JUMP_V:
            self.vy = SHORT_JUMP_V
        falling, airborne = self.vy, not self.on_ground
        self.move(lv)
        if airborne and self.on_ground and falling > 13:
            self.land_t = LAND_FRAMES             # atterraggio da un salto alto: gambe piegate
        if self.vy >= 0 and not self.on_ground:
            r = self.rect
            for fx in (r.left + 4, r.right - 5):
                if lv.tile_at(fx, r.bottom) == "H" and lv.tile_at(fx, r.bottom - TILE) != "H" and (r.bottom % TILE) <= self.vy + 1:
                    self.y = r.bottom // TILE * TILE - self.h
                    self.vy = 0
                    self.on_ground = True
                    break
        if self.on_ground and self.jump_buffer:
            self.jumped = self.do_jump()
        self.anim += abs(self.vx) / 40      # un passo ogni 8 fotogrammi a velocita' piena
        self.run_t += abs(self.vx) / RUN_MAX * 0.125   # passo: un fotogramma ogni 8 frame
        self.advance_attack()
        if self.invuln:
            self.invuln -= 1

    def advance_attack(self):
        """Un fotogramma del colpo in corso (anche sulla scala e appesi al cavo)."""
        if self.attack:
            name, f = self.attack
            f += 1
            limit = {"punch": STONE_FRAMES, "kick": 18, "throw": SWORD_FRAMES, "spin": SPIN_FRAMES}[name]
            self.attack = None if f >= limit else (name, f)
            if name == "spin" and (self.attack is None or self.on_ground):
                self.attack = None
                self.recover = SPIN_RECOVERY
            if name == "throw" and self.attack is None:
                self.combo_t = COMBO_WINDOW            # c'e' ancora un attimo per il prossimo
                if self.slash_queued:
                    self.slash_queued = False
                    self.slash()
        elif self.combo_t:
            self.combo_t -= 1
            if not self.combo_t:
                self.combo = 0

    def do_jump(self):
        if self.climbing:
            self.climbing = False
            self.on_ground = False
            self.coyote = self.jump_buffer = 0
            self.vy = JUMP_V * 0.7
            return True
        if self.on_ground or self.coyote:
            self.vy = JUMP_V - max(0, abs(self.vx) - RUN_MAX) * 0.7
            if self.chill:
                self.vy *= CHILL_JUMP              # gelati si salta meno
            if self.breathless:
                self.vy *= BREATHLESS_JUMP
            self.on_ground = False
            self.coyote = self.jump_buffer = 0
            return True
        self.jump_buffer = JUMP_BUFFER_FRAMES
        return False

    def slash(self):
        """Z: un fendente, oppure il successivo della combo (fino a tre)."""
        if self.attack and self.attack[0] == "throw":
            if self.combo < COMBO_MAX and self.attack[1] > 4:
                self.slash_queued = True               # parte appena finisce questo
            return False
        combo = self.combo + 1 if self.combo_t and self.combo < COMBO_MAX else 1
        if not self.start_attack("throw"):
            return False
        self.combo, self.combo_t = combo, 0
        self.new_slash = True                          # il gioco lo fa suonare
        return True

    def start_attack(self, name):
        # sulla scala e appesi al cavo si puo' usare solo la spada
        if not self.attack and (not self.climbing or name == "throw") and not self.recover:
            self.attack = (name, 0)
            self.swing += 1               # ogni colpo tocca ciascun nemico una volta sola
            return True
        return False

    def sheet_frame(self, gfx):
        """Fotogramma dal foglio di sprite della posa corrente, se esiste."""
        sheets = gfx.sheets
        side = 0 if self.facing > 0 else 1
        if self.hanging is not None and "hang" in sheets and not self.attack:
            return sheets["hang"][side][{-1: 0, 0: 1, 1: 2}[self.hanging]]
        if self.climbing and not self.attack:
            if "climb" not in sheets:
                return None
            return sheets["climb"][0][int(self.anim / 4) % 4]
        if self.hurt_t and not self.attack and "hurt" in sheets:
            return sheets["hurt"][side][0 if self.hurt_t > HURT_FRAMES // 2 else 1]
        if self.attack:
            name, f = self.attack
            base = "flykick" if name == "kick" and not self.on_ground and "flykick" in sheets else name
            base = "spinkick" if name == "spin" else base
            if base not in sheets:
                return None
            fr = sheets[base][side]
            limit = {"punch": STONE_FRAMES, "kick": 18, "throw": SWORD_FRAMES, "spin": SPIN_FRAMES}[name]
            i = min(len(fr) - 1, f * len(fr) // limit)
            if name == "throw" and self.combo == 2:
                i = len(fr) - 1 - i                    # il secondo fendente e' un rovescio
            return fr[i]
        if not self.on_ground:
            if "jump" not in sheets:
                return None
            fr = sheets["jump"][side]
            n = len(fr)
            if self.vy < 0:
                i = min(n // 2 - 1, int((self.vy - JUMP_V) / -JUMP_V * (n // 2)))
            else:
                i = n // 2 + min(n // 2 - 1, int(self.vy / 14 * (n // 2)))
            return fr[max(0, i)]
        if self.land_t and not abs(self.vx) > 2 and "land" in sheets:
            return sheets["land"][side][0 if self.land_t > LAND_FRAMES // 2 else 1]
        if abs(self.vx) > 0.5 and "run" in sheets:
            fr = sheets["run"][side]
            return fr[int(self.run_t) % len(fr)]
        if self.breathless and "tired" in sheets:
            return sheets["tired"][side][(self.t // 10) % 4]   # senz'aria ansima piegato
        if "idle" in sheets:
            return sheets["idle"][side][(self.t // 14) % 4]    # respira
        return None

    def draw(self, s, gfx, cam):
        if self.invuln and (self.invuln // 3) % 2:
            return
        img = self.sheet_frame(gfx)
        if img is None:
            img = gfx.player["idle"][0 if self.facing > 0 else 1]
        if self.chill:
            img = gfx.frosted(img)                 # gelato dall'azoto: brina sulla tuta
        self.draw_img(s, img, cam)


class Skeleton(Entity):
    def __init__(self, c, r):
        super().__init__(c * TILE + 5, (r + 1) * TILE - Entity.h)
        self.hp = 20
        self.t = random.randrange(90)
        self.facing = -1
        self.frozen = 0
        self.hit_t = 0

    def attack_box(self):
        if 0 < self.hit_t <= 12:
            r = self.rect
            return pygame.Rect(r.right if self.facing > 0 else r.left - 60, r.top + 40, 60, 40)
        return None

    def update(self, lv, player):
        self.t += 1
        if self.frozen:
            self.frozen -= 1
            return
        if self.hit_t:
            self.hit_t -= 1
            self.vx = 0
            self.move(lv)
            return
        dist = player.x - self.x
        if abs(dist) < 700:
            self.facing = 1 if dist > 0 else -1
        if abs(dist) < 90 and abs(player.y - self.y) < 100:
            self.hit_t = 24
        r = self.rect
        ahead = r.right + 2 if self.facing > 0 else r.left - 3
        if lv.solid(ahead, r.bottom + 2) and not lv.solid(ahead, r.centery):
            self.vx = 2.6 * self.facing
        else:
            self.vx = 0
            if abs(dist) >= 700:
                self.facing = -self.facing
        self.move(lv)

    def draw(self, s, gfx, cam):
        img = gfx.skeleton[(self.t // 10) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        self.draw_img(s, img, cam)
        if self.frozen:
            pygame.draw.rect(s, (150, 220, 255), (int(self.x) - cam, self.y, self.w, self.h), 4)


class Crow(Entity):
    w, h = 100, 50
    ox, oy = 14, 7

    def __init__(self, c, r):
        super().__init__(c * TILE, r * TILE)
        self.home = (self.x, self.y)
        self.hp = 5
        self.t = 0
        self.state = "wait"
        self.frozen = 0

    def update(self, lv, player):
        self.t += 1
        if self.frozen:
            self.frozen -= 1
            return
        dx = player.x - self.x
        if self.state == "wait":
            if abs(dx) < 800:
                self.state = "dive"
                self.cawed = True
                self.facing = 1 if dx > 0 else -1
                self.t = 0
        elif self.state == "dive":
            ty = player.y + 30
            self.x += 6 * self.facing
            self.y += (ty - self.y) * 0.04 + math.sin(self.t / 6) * 3
            if self.t > 110:
                self.state = "away"; self.t = 0
        else:
            self.x += 7 * self.facing
            self.y -= 4
            if self.t > 120:
                self.state = "wait"
                self.x, self.y = self.home
                self.t = 0

    def draw(self, s, gfx, cam):
        img = gfx.crow[(self.t // (15 if self.state == "wait" else 5)) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        self.draw_img(s, img, cam)


class Bianca:
    """Compagna di NightKnight: osserva e segue, senza combattere all'inizio."""
    def __init__(self, player):
        self.x = player.x - 150
        self.y = player.y - 110
        self.facing = 1
        self.t = 0
        self.burst = 0
        self.target = None        # il nemico su cui sta picchiando
        self.flyers_only = True
        self.sortie = 0           # nemici ancora da abbattere in questa incursione
        self.rest = 0

    def update(self, player, cam=0, camy=VIEW_Y):
        self.t += 1
        if self.burst:
            self.burst -= 1                   # bagliore della Luce appena spesa
        if self.target is not None:
            # in picchiata sul nemico scelto
            to = pygame.Vector2(self.target.rect.center) - (self.x, self.y)
            if to.length() > 1:
                step = to.normalize() * min(BIANCA_SPEED, to.length())
                self.x += step.x
                self.y += step.y
                self.facing = 1 if to.x > 0 else -1
            return
        # Resta poco dietro e sopra al protagonista; il ritardo rende il volo vivo.
        offset = -155 if player.facing > 0 else 155
        tx, ty = player.rect.centerx + offset, player.y - 105
        self.x += (tx - self.x) * 0.045
        self.y += (ty - self.y) * 0.055
        if abs(player.vx) > 0.5:
            self.facing = player.facing

    def draw(self, screen, gfx, cam):
        img = gfx.bianca[(self.t // 8) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        bob = int(math.sin(self.t / 11) * 7)
        if self.burst:
            glow = pygame.Surface((420, 420), pygame.SRCALPHA)
            for rad in range(200, 20, -20):
                pygame.draw.circle(glow, (255, 240, 200, 14), (210, 210), rad)
            screen.blit(glow, (int(self.x) - 210 - cam, int(self.y) - 210))
        screen.blit(img, (int(self.x) - img.get_width() // 2 - cam,
                          int(self.y) - img.get_height() // 2 + bob))


# Specie dei nemici nuovi. I camminatori ereditano dallo scheletro (colpo
# ravvicinato, pestone, danni), i volanti dal corvo (volo e picchiata).
# h: altezza dello sprite; box: sagoma colpibile; hp: vita in colpi di sasso
# (un fendente di spada ne vale due).
WALKERS = {
    "skeleton":    dict(frames="skeleton_walk{}", h=PH, box=(70, 176), hp=1, speed=2.6, dmg=30, reach=70, pts=300),
    "skeleton_2x": dict(frames="skeleton_2x_{}", h=PH * 2, box=(120, 352), hp=2, speed=1.8, dmg=40, reach=150, pts=1500),
    "skeleton_3x": dict(frames="skeleton_3x_{}", h=PH * 3, box=(170, 528), hp=4, speed=1.3, dmg=55, reach=220, pts=4000),
    "miner":       dict(frames="miner_mutant_{}", h=PH, box=(80, 176), hp=4, speed=2.0, dmg=35, reach=95, pts=500),
    "lizard":      dict(frames="lizard_cryo_{}", h=80, box=(170, 70), hp=1, speed=1.4, dmg=25, reach=60, pts=400, lunge=True),
    "worm":        dict(frames="worm_silicon_{}", h=230, box=(100, 200), hp=1, speed=0, dmg=30, reach=120, pts=600),
    # solo nelle gallerie, alla Tremors: corre sotto la roccia (si vede solo il
    # suolo che trema) e sbuca sotto i piedi
    "burrower":    dict(frames="worm_silicon_{}", h=260, box=(110, 230), hp=1, speed=3.4, dmg=35, reach=120, pts=800,
                        burrow=True),
}
FLYERS = {
    "crow":         dict(frames="crow_{}", hp=1, dmg=0),
    "skeleton_fly": dict(frames="skeleton_fly_{}", h=PH, box=(80, 150), hp=1, dmg=25, pts=500),
    "jelly":        dict(frames="jelly_atmo_{}", h=150, box=(110, 120), hp=1, dmg=20, pts=350, drift=True),
}


class Stone:
    """Sasso lanciato da NightKnight: arco basso, danno piccolo, sempre disponibile."""
    owner = "player"

    def __init__(self, p):
        self.d = p.facing
        self.x = p.rect.right if self.d > 0 else p.rect.left - 20
        self.y = p.rect.top + 40
        self.vx, self.vy = 15 * self.d, -5.0
        self.dmg = STONE_HIT          # contro i nemici: meta' della spada
        self.boss_dmg = 6             # contro il Guardiano: meta' del fendente
        self.alive = True
        self.t = 0
        self.kind = "stone"

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), 22, 22)

    @property
    def hit_rect(self):
        """Il sasso prende anche i nemici bassi (lucertole, ratti) sotto la sua traiettoria."""
        return self.rect.inflate(16, 0).union(self.rect.move(0, 110))

    def update(self, lv, cam):
        self.t += 1
        self.x += self.vx
        self.vy += 0.35
        self.y += self.vy
        if lv.solid(self.x + 11, self.y + 11) or self.t > 120:
            self.alive = False

    def draw(self, s, gfx, cam):
        c = (int(self.x) - cam + 11, int(self.y) + 11)
        pygame.draw.circle(s, (20, 16, 14), c, 12)
        pygame.draw.circle(s, (150, 140, 128), c, 9)
        pygame.draw.circle(s, (196, 188, 174), (c[0] - 3, c[1] - 3), 3)


class Walker(Skeleton):
    """Nemico di terra di una specie di WALKERS, piazzato in pixel."""

    def __init__(self, x, kind):
        spec = WALKERS[kind]
        self.w, self.h = spec["box"]
        super().__init__(0, 0)
        self.x, self.y = float(x), float(GROUND * TILE - self.h)
        self.kind, self.spec = kind, spec
        self.hp, self.dmg = spec["hp"], spec["dmg"]
        self.lunge_t = 0
        # nessuno uguale all'altro: taglia e passo cambiano un poco
        self.scale = random.choice((0.92, 0.97, 1.0, 1.04, 1.08))
        self.pace = random.uniform(0.85, 1.15)
        self.flash = 0
        self.under, self.rumble, self.up_t, self.out_t = True, 0, 0, 0
        self.turn = 0
        self.leap = 0.0

    def attack_box(self):
        if 0 < self.hit_t <= 12:
            r, reach = self.rect, self.spec["reach"]
            return pygame.Rect(r.right if self.facing > 0 else r.left - reach, r.top + r.h // 4, reach, r.h // 2)
        return None

    @property
    def hidden(self):
        """Il verme sottoterra non si vede e non si colpisce."""
        return self.spec.get("burrow") and self.under

    def burrow(self, lv, player):
        """Sotto la crosta insegue NightKnight (solo sul suo stesso suolo), trema
        sotto i suoi piedi per un attimo, poi sbuca; resta fuori un po' e torna giu'."""
        self.t += 1
        if self.frozen:
            self.frozen -= 1
            return
        r = self.rect
        dist = player.rect.centerx - r.centerx
        same_floor = abs(player.rect.bottom - r.bottom) < 70 and player.on_ground
        if self.under:
            if self.rumble:
                self.rumble -= 1
                if not self.rumble:
                    self.under, self.up_t, self.out_t = False, 0, 0
                return
            if abs(dist) < 30 and same_floor:
                self.rumble = BURROW_RUMBLE
                return
            self.facing = 1 if dist > 0 else -1
            ahead = r.right + 2 if self.facing > 0 else r.left - 3
            if abs(dist) > 8 and lv.solid(ahead, r.bottom + 2):
                self.x += min(abs(dist), self.spec["speed"] * self.pace) * self.facing
            return
        self.up_t += 1
        self.out_t += 1
        self.facing = 1 if dist > 0 else -1
        if self.hit_t:
            self.hit_t -= 1
        elif abs(dist) < self.spec["reach"] + 60 and self.up_t > 12:
            self.hit_t = 30
        if self.out_t > BURROW_OUT:
            self.under, self.out_t = True, 0

    def update(self, lv, player):
        spec = self.spec
        if lv.drowned(self.rect):         # finito in un lago di metano
            self.alive = False
            return
        if spec.get("burrow"):
            return self.burrow(lv, player)
        if spec["speed"] == 0:                 # il verme resta dove emerge
            self.t += 1
            dist = player.x - self.x
            self.facing = 1 if dist > 0 else -1
            if self.hit_t:
                self.hit_t -= 1
            elif abs(dist) < spec["reach"] + 60:
                self.hit_t = 30
            return
        if spec.get("lunge") and not self.hit_t:
            dist = player.x - self.x
            if self.lunge_t:
                self.lunge_t -= 1
            elif abs(dist) < 320 and self.t % 90 == 0:
                self.lunge_t = 28
        speed = 7.0 if self.lunge_t else spec["speed"] * self.pace
        self.t += 1
        if self.frozen:
            self.frozen -= 1
            return
        if self.hit_t:
            self.hit_t -= 1
            self.vx = 0
            self.move(lv)
            return
        dist = player.x - self.x
        if self.turn:
            self.turn -= 1                    # torna indietro da un ostacolo che non passa
        else:
            self.facing = 1 if dist > 0 else -1
        if abs(dist) < spec["reach"] + 30 and abs(player.rect.bottom - self.rect.bottom) < 100:
            self.hit_t = 24
        if self.on_ground:
            self.vx = self.leap = self.terrain(lv, speed)
        else:
            self.vx = self.leap                # in salto si continua a spingere in avanti
        self.move(lv)

    def terrain(self, lv, speed):
        """Davanti a un gradino o a un lago non si resta fermi: un gradino fino a
        WALKER_STEP tessere si salta, uno piu' basso si scende, un lago o un buco
        stretto si scavalca con un balzo; altrimenti si torna indietro."""
        r, f = self.rect, self.facing
        front = r.right + 2 if f > 0 else r.left - 3
        if lv.solid(front, r.bottom - 8):
            # una parete: quanto e' alta?
            h = next((k for k in range(1, 12) if not lv.solid(front, r.bottom - 8 - k * TILE)), 12)
            if h <= WALKER_STEP and not self.crawls and not lv.solid(r.centerx, r.top - h * TILE):
                self.vy = -math.sqrt(2 * GRAVITY * (h * TILE + 30))
                return speed * f
            return self.turn_back()
        if lv.solid(front, r.bottom + 2):
            return speed * f                  # si cammina
        below = lv.floor_near(front + f * TILE // 2, r.bottom, WALKER_DROP)
        if below is not None and below > r.bottom:
            return speed * f                  # si scende dal gradino
        for k in range(1, WALKER_GAP + 1 if not self.crawls else 1):
            land = lv.floor_near(front + f * k * TILE, r.bottom, 1)
            if land is not None:
                # un lago o un buco stretto: balzo dall'altra parte
                self.vy = -12.0
                air = 2 * 12.0 / GRAVITY
                return f * max(speed, (k * TILE + r.w) / air + 1)
        return self.turn_back()

    @property
    def crawls(self):
        """Chi non salta ne' gradini ne' laghi."""
        return self.kind.startswith("worm")

    def turn_back(self):
        self.facing = -self.facing
        self.turn = WALKER_TURN
        return 0

    def draw_tremor(self, s, cam):
        """Il verme sotto la roccia: il suolo si crepa e la polvere si alza appena."""
        r = self.rect
        k = 1.8 if self.rumble else 1
        x, y = r.centerx - cam, r.bottom
        crack = [(x - 50 * k + i * 20 * k, y - 2 - (6 * k if i % 2 else 0)) for i in range(6)]
        pygame.draw.lines(s, (24, 14, 10), False, crack, 4)
        for i in range(int(8 * k)):
            ph = (self.t * 2 + i * 23) % 24
            px = x + math.sin(i * 2.3 + self.t * 0.25) * 55 * k
            py = y - 2 - abs(math.sin(ph / 24 * math.pi)) * 14 * k       # saltellano, non volano
            pygame.draw.circle(s, (24, 14, 10), (int(px), int(py)), 3 + i % 2)
            pygame.draw.circle(s, (160, 104, 62), (int(px), int(py)), 2 + i % 2)

    def draw(self, s, gfx, cam):
        if self.spec.get("burrow"):
            if self.under:
                return self.draw_tremor(s, cam)
            if self.up_t < 12 or self.out_t > BURROW_OUT - 12:
                # sbuca (o rientra): se ne vede solo la parte fuori dal suolo
                k = min(self.up_t, BURROW_OUT - self.out_t) / 12
                img = gfx.sized(gfx.foes[self.kind][1], self.scale)
                if self.facing < 0:
                    img = assets.flip(img)
                h = int(img.get_height() * max(0.05, k))
                r = self.rect
                s.blit(img, (r.centerx - img.get_width() // 2 - cam, r.bottom - h), (0, 0, img.get_width(), h))
                return
        frames = gfx.foes[self.kind]
        if self.kind.startswith("worm") or (self.spec.get("burrow") and not self.under):
            img = frames[1] if 0 < self.hit_t <= 18 else frames[0]
            img = gfx.sized(img, self.scale)
            if self.facing < 0:
                img = assets.flip(img)
            if self.flash:
                self.flash -= 1
                img = gfx.white(img)
            r = self.rect
            titan.ground_shadow(s, r.centerx - cam, r.bottom, img.get_width() * 0.9)
            s.blit(img, (r.centerx - img.get_width() // 2 - cam, r.bottom - img.get_height() + WORM_SINK))
            return
        attacking = 0 < self.hit_t <= 18 or self.lunge_t
        img = frames[1] if (attacking or (self.spec["speed"] and (self.t // 10) % 2)) else frames[0]
        img = gfx.sized(img, self.scale)
        if self.facing < 0:
            img = assets.flip(img)
        if self.flash:
            self.flash -= 1
            img = gfx.white(img)
        self.draw_img(s, img, cam)
        if self.frozen:
            pygame.draw.rect(s, (150, 220, 255), (int(self.x) - cam, self.y, self.w, self.h), 4)


class Flyer(Crow):
    """Volante di una specie di FLYERS, piazzato in pixel. Il corvo spinge e
    basta; scheletri volanti e meduse fanno male."""

    def __init__(self, x, y, kind):
        spec = FLYERS[kind]
        if "box" in spec:
            self.w, self.h = spec["box"]
        super().__init__(0, 0)
        self.x, self.y = float(x), float(y)
        self.home = (self.x, self.y)
        self.kind, self.spec = kind, spec
        self.hp = spec["hp"]
        self.dmg = spec["dmg"]
        self.harmless = spec["dmg"] == 0
        self.state = "dive"
        self.cawed = kind == "crow"
        self.stuck = None          # medusa attaccata: posizione rispetto a NightKnight

    def update(self, lv, player):
        if self.spec.get("drift"):
            self.t += 1
            if self.stuck is not None:
                # attaccata alla tuta: segue NightKnight dove l'ha preso
                self.x = player.rect.centerx + self.stuck[0] - self.w / 2
                self.y = player.rect.top + self.stuck[1]
                return
            if self.frozen:
                self.frozen -= 1
                return
            # appena ti vede ti punta dritta addosso, pulsando nell'aria densa
            to = pygame.Vector2(player.rect.center) - self.rect.center
            if to.length() > 1:
                step = to.normalize() * JELLY_SPEED * (0.75 + 0.35 * abs(math.sin(self.t / 9)))
                self.x += step.x
                self.y += step.y
            self.facing = 1 if to.x > 0 else -1
            return
        super().update(lv, player)
        if self.state == "away" and self.t > 60:
            # chi arriva con un'ondata non torna a casa: rientra da dove e' uscito
            self.state, self.t = "dive", 0
            self.facing = 1 if player.x > self.x else -1

    def draw(self, s, gfx, cam):
        frames = gfx.foes[self.kind]
        img = frames[(self.t // (12 if self.spec.get("drift") else 5)) % 2]
        if self.facing < 0:
            img = assets.flip(img)
        if getattr(self, "flash", 0):
            self.flash -= 1
            img = gfx.white(img)
        self.draw_img(s, img, cam)


class Effect:
    def __init__(self, x, y, text, color):
        self.x, self.y, self.text, self.color, self.t = x, y, text, color, 0
        self.alive = True

    def update(self):
        self.t += 1
        self.y -= 1.5
        self.alive = self.t < 50


# ---------------------------------------------------------------- gioco
class Game:
    def __init__(self, windowed=False, save_path=progress.DEFAULT_PATH):
        pygame.init()
        # SCALED ingrandisce la risoluzione logica allo schermo: su un 4K anche la
        # finestra occupa lo schermo invece di un quarto. Senza video (test) niente scala.
        headless = os.environ.get("SDL_VIDEODRIVER") == "dummy"
        flags = 0 if headless else (pygame.SCALED | pygame.RESIZABLE if windowed else pygame.FULLSCREEN | pygame.SCALED)
        self.screen = pygame.display.set_mode((W, H), flags)
        self.luce, self.freed = 0, set()      # Luce di Bianca e prigionieri gia' liberati
        self.sparks, self.shake = [], 0       # scintille dei colpi e scossa dello schermo
        self.reached_pass = False             # su Titano: arrivati alla traversata
        self.stage = 0                        # ultima tappa raggiunta (levels.TITAN_STAGES)
        self.nova_used, self.nova_t = False, 0  # Nova: una per livello, e la sequenza in corso
        pygame.display.set_caption("NightKnight")
        self.clock = pygame.time.Clock()
        self.gfx = Gfx()
        self.jb = music.Jukebox()
        self.frame = 0
        self.save_path = save_path
        self.saved = progress.load(save_path)
        self.hi = self.saved["high_score"]
        self.save_error = None
        self.running = True
        self.paused = False
        self.menu_index = 0
        self.state = "title"
        self.score = 0
        self.ci = 0
        self.cfg = levels.cfg(0)
        self.weapon_i = 0
        self.player = Player(0, 0)
        self.msg = None
        self.effects = []
        self.rounds = [0, 0]
        self.hud_shade = pygame.Surface((W, 200), pygame.SRCALPHA)
        for y in range(200):
            alpha = int(170 * (1 - y / 200) ** 1.4)
            pygame.draw.line(self.hud_shade, (0, 0, 0, alpha), (0, y), (W, y))

    # ---- flusso
    def save_progress(self, checkpoint=False, clear=False):
        self.hi = max(self.hi, self.score)
        self.saved["high_score"] = self.hi
        if clear:
            self.saved["checkpoint"] = None
        elif checkpoint:
            self.saved["checkpoint"] = {
                "cemetery": 0, "part": self.part, "lives": self.lives, "score": self.score,
                "luce": self.luce, "freed": sorted(list(f) for f in self.freed),
                "pass": self.reached_pass, "stage": self.stage, "nova": self.nova_used,
            }
        self.save_error = progress.save(self.saved, self.save_path)

    def continue_game(self):
        cp = self.saved["checkpoint"]
        if cp:
            self.ci, self.lives, self.score = 0, cp["lives"], cp["score"]
            self.luce = max(0, min(LUCE_MAX, int(cp.get("luce", 0))))
            self.reached_pass = cp.get("pass") is True
            self.nova_used = cp.get("nova") is True
            stage = cp.get("stage", 0)
            self.stage = stage if type(stage) is int and 0 <= stage < len(levels.TITAN_STAGES) else 0
            self.freed = {tuple(f) for f in cp.get("freed", []) if isinstance(f, list) and len(f) == 3}
            self.start_part(cp["part"])

    def set_paused(self, paused):
        self.paused = paused
        self.menu_index = 0
        if pygame.mixer.get_init():
            (pygame.mixer.pause if paused else pygame.mixer.unpause)()

    def menu_items(self):
        if self.paused:
            return ["RIPRENDI", "TORNA AL TITOLO", "ESCI"]
        if self.state == "gameover":
            return ["CONTINUA", "NUOVA PARTITA"]
        return (["CONTINUA"] if self.saved["checkpoint"] else []) + ["NUOVA PARTITA", "ESCI"]

    def menu_key(self, k):
        items = self.menu_items()
        if k in (pygame.K_UP, pygame.K_w):
            self.menu_index = (self.menu_index - 1) % len(items)
        elif k in (pygame.K_DOWN, pygame.K_s):
            self.menu_index = (self.menu_index + 1) % len(items)
        elif k == pygame.K_RETURN:
            action = items[self.menu_index]
            if action == "RIPRENDI":
                self.set_paused(False)
            elif action == "TORNA AL TITOLO":
                self.save_progress()
                self.set_paused(False)
                self.jb.stop()
                self.state = "title"
            elif action == "CONTINUA":
                self.continue_game()
            elif action == "NUOVA PARTITA":
                self.state = "weapon_select"
                self.weapon_i = 0
            elif action == "ESCI":
                self.running = False

    def new_game(self, part="surface"):
        self.score = 0
        self.luce, self.freed = 0, set()
        self.reached_pass = False
        self.stage = 0
        self.nova_used = False
        self.lives = 3
        self.ci = 0
        self.start_part(part)

    def start_part(self, part):
        if part != "surface":
            self.reached_pass = False
            self.stage = 0
        c = levels.cfg(self.ci)
        self.cfg = c
        self.part = part
        g = {"surface": levels.gen_surface, "arena": levels.gen_arena}[part]()
        self.lv = Level(g, part)
        self.rounds = [0, 0]
        self.nova_t = 0
        self.spawn()
        self.state = "card"
        self.card_t = 150
        self.jb.play("trials" if part == "surface" and self.reached_pass else part)
        self.save_progress(checkpoint=True)

    def spawn(self):
        lv = self.lv
        self.player = p = Player(2 * TILE, GROUND * TILE - Entity.h)
        p.on_ground = True
        p.weapon = levels.weapon_cfg(self.weapon_i)
        p.gravity_scale = self.cfg["gravity_scale"]
        self.bianca = Bianca(p)
        # La Luce e i prigionieri liberati restano anche dopo una vita persa
        p.albedo = self.luce
        self.geysers, self.spenti, self.stations, self.vents = [], [], [], []
        self.skels, self.crows, self.balls = [], [], []
        for ch, c, r in lv.markers:
            if ch == "q":
                self.geysers.append(titan.Geyser((c + .5) * TILE, (r + 1) * TILE))
            elif ch == "o":
                self.stations.append(titan.OxygenStation((c + .5) * TILE, (r + 1) * TILE))
            elif ch == "c":
                self.vents.append(titan.GasVent((c + .5) * TILE, (r + 1) * TILE, levels.VENT_FACING.get(c, -1)))
            elif ch == "u":
                spento = titan.Spento((c + .5) * TILE, (r + 1) * TILE)
                if (self.ci, self.part, int(spento.x)) in self.freed:
                    spento.liberated, spento.glow = True, 60
                self.spenti.append(spento)
        self.cam = 0
        self.camy = self.camy_target = VIEW_Y
        self.zoom, self.focus_x = ZOOM, None
        self.dark = 0.0
        self.boss = None
        self.msg = None
        self.effects = []
        self.intro = 0
        self.cable = None
        if self.part == "surface":
            x0 = levels.TITAN_PASS_START * TILE
            speeds = iter(levels.ROPE_SPEEDS)
            self.cable = athletics.Cables([[athletics.Cable(x0 + col * TILE + TILE // 2, athletics.FLOOR - top, length,
                                                            next(speeds))
                                            for col, top, length in group] for group in levels.TITAN_CABLES])
            for kind, col, row in levels.TITAN_PASS_FOES:
                col += levels.TITAN_PASS_START
                if kind in FLYERS:
                    flyer = Flyer(col * TILE, row * TILE, kind)
                    flyer.state = "wait"          # aspetta il passaggio, come i corvi di guardia
                    self.crows.append(flyer)
                else:
                    walker = Walker(col * TILE, kind)
                    walker.y = row * TILE - walker.h     # sulla cengia o in galleria
                    self.skels.append(walker)
        self.waves = None
        if self.part == "surface":
            self.waves = waves.WaveDirector(levels.TITAN_ARENAS, levels.TITAN_WAVES, self.make_walker, Flyer, seed=self.ci,
                                            flyer_y=(VIEW_Y + 40, VIEW_Y + 260),
                                            patrols=levels.TITAN_PATROLS, patrol_end=levels.TITAN_PASS_START * TILE)
            self.waves.patrol_floor = GROUND * TILE
            # si riparte dall'ultima tappa: le ondate gia' passate restano superate
            col, row = levels.TITAN_STAGES[self.stage]
            p.x, p.y = col * TILE + (TILE - p.w) / 2, row * TILE - p.h
            for w in self.waves.waves:
                if w.x1 < col * TILE:
                    w.state = "done"
            self.waves.next_patrol = max(self.waves.next_patrol, (col + levels.TITAN_PATROLS["every"]) * TILE)
            self.camy = self.camy_target = max(0, p.rect.bottom - FEET_IN_VIEW)
            self.bianca = Bianca(p)
            self.dark = 1.0 if row > levels.CAVE_TOP else 0.0
        if self.part == "arena":
            self.start_round()

    def flat_ground(self, x, feet):
        """Terreno vero per un verme: il suolo base (niente colline, gradini o cengie),
        in piano per WORM_FLAT tessere da ogni lato, senza laghi."""
        if self.part == "surface" and x < levels.TITAN_PASS_START * TILE and feet != GROUND * TILE:
            return False
        for d in range(-WORM_FLAT, WORM_FLAT + 1):
            cx = x + d * TILE
            if not self.lv.solid(cx, feet + 2) or self.lv.solid(cx, feet - 2) or self.lv.tile_at(cx, feet + 2) == "~":
                return False
        return True

    def make_walker(self, x, kind):
        """Un camminatore dei rinforzi, appoggiato sul suolo che c'e' dove entra
        (colline e montagne comprese), il piu' vicino all'altezza di NightKnight."""
        w = Walker(x, kind)
        feet_y = self.player.rect.bottom
        away = -TILE if x < self.player.rect.centerx else TILE
        # dentro una montagna o su un lago non si nasce: ci si sposta lontano da
        # NightKnight (mai verso di lui, per non comparire sullo schermo) finche'
        # c'e' un suolo a una quota vicina alla sua
        x0, step = w.x, away
        for i in range(40 if kind.startswith("worm") else 16):
            feet = self.lv.floor_near(x0 + w.w / 2 + i * step, feet_y, 4)
            if feet is None:
                continue
            w.x, w.y = x0 + i * step, feet - w.h
            r = w.rect
            # suolo pieno sotto tutto il corpo (per il verme, sotto tutto il cumulo di terra)
            half = r.w // 2 + (WORM_MOUND if kind.startswith("worm") else -6)
            support = all(self.lv.solid(r.centerx + dx, r.bottom + 2) for dx in (-half, 0, half))
            if kind.startswith("worm"):
                support = support and self.flat_ground(r.centerx, r.bottom)
            if support and not any(self.lv.solid(px, py) for px in (r.left + 2, r.centerx, r.right - 3)
                                   for py in (r.top + 2, r.centery, r.bottom - 3)):
                w.on_ground = True
                return w
        if kind.startswith("worm"):
            return None                       # niente terreno in piano li' vicino: niente verme
        w.x = x0
        feet = self.lv.floor_near(w.rect.centerx, feet_y, 20)
        if feet is not None:
            w.y = feet - w.h
        return w

    def start_round(self):
        self.player = Player(3 * TILE, GROUND * TILE - Entity.h)
        self.player.on_ground = True
        self.player.albedo = self.luce          # la Luce arriva intatta al duello
        self.player.weapon = levels.weapon_cfg(self.weapon_i)
        self.player.gravity_scale = self.cfg["gravity_scale"]
        self.effects = []
        self.boss = knights.GoldKnight(self.lv.w - 10 * TILE, knights.knight_cfg(self.ci), self.gfx)
        self.boss.arena_w = self.lv.w
        self.balls = []
        self.intro = 150
        self.jb.fx("round")
        self.ko_wait = 0

    def next_part(self):
        if self.state == "victory":
            return
        # Titano e' un unico percorso (ondate, poi traversata) e poi il duello.
        if self.part == "surface":
            self.start_part("arena")
        else:
            self.state = "victory"
            self.card_t = 260
            self.jb.play("victory")
            self.save_progress(clear=True)

    def after_victory(self):
        # Per ora il viaggio si ferma a Titano: gli altri satelliti arriveranno.
        self.state = "end"
        self.hi = max(self.hi, self.score)
        self.jb.stop()
        self.save_progress(clear=True)

    # ---- danni
    def burst_sparks(self, x, y, n, color=(255, 214, 150)):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(2, 9)
            self.sparks.append([x, y, math.cos(a) * v, math.sin(a) * v - 2, random.randint(14, 28), color])

    def hurt_player(self, dmg, from_x):
        p = self.player
        if (p.invuln or self.state != "play"
                or (self.boss and self.boss.hp <= 0)):
            return
        p.invuln = 80
        p.hurt_t = HURT_FRAMES
        p.vy = -9
        p.vx = 6 if p.x > from_x else -6
        p.attack = None
        p.climbing = False
        p.coyote = p.jump_buffer = 0
        self.jb.fx("hurt")
        # NightKnight non perde mai l'armatura: un colpo toglie solo vita.
        p.hp = max(0, p.hp - dmg)
        self.shake = 14
        self.burst_sparks(p.rect.centerx, p.rect.centery, 14, (255, 140, 100))
        if p.hp == 0:
            self.die()

    def sword_feedback(self):
        """Ogni fendente, anche quelli della combo partiti da soli: suono e medusa staccata."""
        p = self.player
        if p.new_slash:
            p.new_slash = False
            self.jb.fx("sword")
            self.shake_off(1)

    def shake_off(self, n):
        """Un fendente o un calcio stacca una medusa di dosso; il calcio girato tutte."""
        for c in [c for c in self.crows if c.alive and getattr(c, "stuck", None) is not None][:n]:
            self.hit_enemy(c, 999, pts=c.spec.get("pts", 150))

    def luce_burst(self):
        """V: Bianca spende un'unita' di Luce e va in incursione su volanti e nemici
        di terra, uno alla volta, fino a BIANCA_SORTIE; al Guardiano toglie il 5%."""
        p = self.player
        if p.albedo < LUCE_UNIT or not self.bianca:
            return False
        p.albedo -= LUCE_UNIT
        self.bianca.burst = BURST_FRAMES
        self.bianca.sortie, self.bianca.flyers_only = BIANCA_SORTIE, False
        self.jb.fx("luce")
        if self.boss and self.boss.hp > 0:
            self.boss.hp = max(0, self.boss.hp - max(1, round(self.boss.max_hp * 0.05)))
            self.boss.flash = 20
        return True

    @property
    def nova_ready(self):
        freed = sum(1 for f in self.freed if f[0] == self.ci)
        return not self.nova_used and freed >= NOVA_PRISONERS

    def start_nova(self):
        """B: 9T9T scarica il nucleo della tuta ricaricato dai coloni liberati."""
        p = self.player
        if not self.nova_ready or self.nova_t or self.state != "play" or (self.cable and self.cable.attached):
            return False
        self.nova_used, self.nova_t = True, 1
        self.nova_base = p.y
        p.climbing, p.attack, p.vx, p.vy = False, None, 0, 0
        self.jb.fx("nova_rise")
        return True

    def update_nova(self):
        """La sequenza di Nova: il mondo si ferma, 9T9T sale da solo facendo il
        calcio girato, due bagliori, un'onda d'urto, e non resta nessuno."""
        p, t = self.player, self.nova_t
        self.nova_t += 1
        rise = min(1.0, t / 28) if t < 70 else max(0.0, 1 - (t - 70) / (NOVA_FRAMES - 70))
        p.y = self.nova_base - NOVA_HEIGHT * math.sin(rise * math.pi / 2)
        p.on_ground, p.vx, p.vy, p.hanging = False, 0, 0, None
        p.attack = ("spin", (t * 2) % SPIN_FRAMES) if 12 <= t < 76 else None
        if 12 <= t < 76:
            p.facing = 1 if (t // 6) % 2 else -1          # gira su se stesso
        if t in (NOVA_FLASH, NOVA_BLAST):
            self.jb.fx("nova")
            self.shake = 18 if t == NOVA_FLASH else 34
            self.burst_sparks(p.rect.centerx, p.rect.centery, 60, (255, 240, 200))
        if t == NOVA_BLAST:
            for e in self.skels + self.crows:
                if e.alive and self.on_screen(e):
                    self.hit_enemy(e, 999, pts=getattr(e, "spec", {}).get("pts", 150))
                    self.burst_sparks(e.rect.centerx, e.rect.centery, 30, (255, 226, 160))
            if self.boss and self.boss.hp > 0:
                self.boss.hp = max(1, self.boss.hp - round(self.boss.max_hp * NOVA_BOSS))
                self.boss.flash = 30
        for sp in self.sparks:
            sp[0] += sp[2]; sp[1] += sp[3]; sp[3] += 0.4; sp[4] -= 1
        self.sparks = [sp for sp in self.sparks if sp[4] > 0]
        self.shake = max(0, self.shake - 1)
        self.skels = [k for k in self.skels if k.alive]
        self.crows = [c for c in self.crows if c.alive]
        if t >= NOVA_FRAMES:
            p.y, p.attack, p.on_ground = self.nova_base, None, True
            p.invuln = 60
            self.nova_t = 0

    def draw_nova(self, s):
        """Buio attorno, colonna di luce su 9T9T, due bagliori e l'onda d'urto."""
        t = self.nova_t
        if not t:
            return
        p = self.player
        vx, vy, cw, ch = self.view_rect()
        k = W / cw
        sx = int((p.rect.centerx - self.cam - vx) * k)
        sy = int((p.rect.centery - int(self.camy) - vy) * k)
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((8, 4, 2, int(150 * min(1, t / 20)) if t < NOVA_BLAST else max(0, 150 - (t - NOVA_BLAST) * 8)))
        s.blit(dim, (0, 0))
        # alone dorato attorno a lui: la luce della visiera rovesciata, chiara al centro
        size = int(self.gfx.visor_light.get_width() * (0.4 + 0.6 * min(1, t / 40)))
        edge = pygame.transform.smoothscale(self.gfx.visor_light, (size, size))
        halo = pygame.Surface((size, size), pygame.SRCALPHA)
        halo.fill((255, 220, 140, 180))
        halo.blit(edge, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        s.blit(halo, (sx - size // 2, sy - size // 2), special_flags=pygame.BLEND_RGBA_ADD)
        if NOVA_FLASH - 14 < t < NOVA_BLAST + 10 and sy > 0:
            # la colonna di luce che scende dal cielo su di lui, sfumata ai lati
            k = 1 - abs(t - (NOVA_FLASH + NOVA_BLAST) / 2) / ((NOVA_BLAST - NOVA_FLASH) / 2 + 14)
            s.blit(self.gfx.nova_beam(sy), (sx - NOVA_BEAM // 2, 0), special_flags=pygame.BLEND_RGBA_ADD)

        for at in (NOVA_FLASH, NOVA_BLAST):            # i due bagliori
            if at <= t < at + 16:
                flash = pygame.Surface((W, H), pygame.SRCALPHA)
                flash.fill((255, 244, 214, int(255 * (1 - (t - at) / 16))))
                s.blit(flash, (0, 0))
        if t >= NOVA_BLAST:                            # l'onda d'urto che spazza la scena
            r = (t - NOVA_BLAST) * 70
            alpha = max(0, 255 - (t - NOVA_BLAST) * 7)
            ring = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 236, 190, alpha), (sx, sy), r, 18)
            pygame.draw.circle(ring, (255, 160, 80, alpha // 2), (sx, sy), max(1, r - 30), 10)
            s.blit(ring, (0, 0))

    def on_screen(self, e):
        """Nella scena: dentro la vista piu' larga che la telecamera puo' avere."""
        p = self.player.rect
        return abs(e.rect.centerx - p.centerx) < DW // 2 and abs(e.rect.centery - p.centery) < DH * 0.7

    def bianca_sortie(self):
        """Bianca in incursione. Da sola parte quando ci sono piu' di BIANCA_CROWD
        volanti sullo schermo, e prende solo volanti; con V prende chiunque."""
        b = self.bianca
        if not b:
            return
        b.rest = max(0, b.rest - 1)
        flying = [c for c in self.crows if c.alive and getattr(c, "stuck", None) is None and self.on_screen(c)]
        if not b.sortie and not b.rest and len(flying) > BIANCA_CROWD:
            b.sortie, b.flyers_only = BIANCA_SORTIE, True
        boss = self.boss
        if b.target is not None and b.target is boss:
            if boss.hp <= 0 or getattr(boss, "hidden", False):
                b.target = None
            elif pygame.Vector2(boss.rect.center).distance_to((b.x, b.y)) < 60:
                boss.hp = max(1, boss.hp - max(1, round(boss.max_hp * BIANCA_BOSS_HIT)))
                boss.flash = 12
                self.burst_sparks(b.x, b.y, 18, (255, 240, 200))
                self.jb.fx("boss_hit")
                b.target, b.rest = None, BIANCA_BOSS_REST
            return
        if (boss and boss.hp > 0 and not self.intro and b.target is None and not b.sortie
                and not b.rest and not getattr(boss, "hidden", False)):
            b.target = boss                      # nel duello: picchiata sul Guardiano
            return
        if b.target is not None:
            if not b.target.alive:
                b.target = None
            elif pygame.Vector2(b.target.rect.center).distance_to((b.x, b.y)) < 50:
                self.hit_enemy(b.target, 999, pts=getattr(b.target, "spec", {}).get("pts", 150))
                self.burst_sparks(b.x, b.y, 18, (255, 240, 200))
                self.jb.fx("caw")
                b.target = None
            return
        if not b.sortie:
            return
        pool = flying + ([] if b.flyers_only else
                         [k for k in self.skels if k.alive and not getattr(k, "hidden", False) and self.on_screen(k)])
        if not pool:
            b.sortie = 0
            b.rest = BIANCA_REST if b.flyers_only else b.rest
            return
        b.target = min(pool, key=lambda e: pygame.Vector2(e.rect.center).distance_to(self.player.rect.center))
        b.sortie -= 1
        if not b.sortie and b.flyers_only:
            b.rest = BIANCA_REST

    def boss_spawn(self, projectile):
        self.balls.append(projectile)
        if projectile.kind == "hook":
            self.jb.fx("hook")

    def follow_y(self, p):
        """Telecamera verticale: a terra, sulla scala o al cavo si porta i piedi
        all'altezza di sempre; in salto si muove solo se NightKnight esce dai margini."""
        r = p.rect
        steady = p.on_ground or p.climbing or (self.cable and self.cable.attached)
        if steady:
            self.camy_target = r.bottom - FEET_IN_VIEW
            if self.cable and self.cable.attached:
                # appesi al cavo, con la vista larga: lui in alto, il lago sotto in quadro
                k = ZOOM / (self.looking_down(p) or ZOOM_OUT)
                rope = self.cable.current.rope              # tutto l'arco dell'oscillazione
                top = rope.anchor.y + rope.length * 0.6 - 45 - 110
                self.camy_target = (top - r.bottom * (1 - k)) / k
            if p.on_ground and self.part != "arena":
                # su un rilievo: il suolo piu' basso li' davanti deve restare in quadro
                low = max((f for f in (self.lv.floor_near(r.centerx + d * TILE, r.bottom + 4 * TILE, 5)
                                       for d in range(-2, 6) for d in (d * p.facing,)) if f is not None
                           and r.bottom < f <= r.bottom + 5 * TILE), default=None)
                if low is not None:
                    self.camy_target = max(self.camy_target, low + LOW_MARGIN - VH)
            if p.climbing:
                # sulla scala si guarda dove si va: in cima c'e' la prossima cengia
                self.camy_target -= LADDER_LOOK
        elif r.top < self.camy_target + CAM_TOP:
            self.camy_target = r.top - CAM_TOP
        elif r.bottom > self.camy_target + VH - CAM_BOTTOM:
            self.camy_target = r.bottom - VH + CAM_BOTTOM
        self.camy_target = max(0, min(self.camy_target, self.lv.h - VH))
        self.camy += (self.camy_target - self.camy) * (0.2 if p.vy > 8 else 0.1)
        if abs(self.camy - self.camy_target) < 0.5:
            self.camy = self.camy_target

    def update_zoom(self, p):
        """Si avvicina in circa mezzo secondo e si allontana piu' piano, inquadrando
        NightKnight insieme ai nemici che ha addosso."""
        r = p.rect
        near = [e.rect.center for e in self.skels + self.crows
                if e.alive and getattr(e, "state", "") not in ("away", "wait") and not getattr(e, "hidden", False)
                and abs(e.rect.centerx - r.centerx) < FIGHT_RANGE[0]
                and abs(e.rect.centery - r.centery) < FIGHT_RANGE[1]]
        if self.part == "arena":
            target = ZOOM_DUEL
            if self.boss:
                near = [self.boss.rect.center]
        else:
            target = ZOOM_FIGHT if 0 < len(near) <= CROWD else ZOOM
        if near:
            # mai cosi' vicina da lasciare fuori qualcuno che ti sta addosso
            xs = [x for x, _ in near] + [r.centerx]
            margin = 760 if self.part == "arena" else 420      # il Guardiano e' grande il doppio
            fit = VW * ZOOM / (max(xs) - min(xs) + margin)
            # nel duello ci si allontana quanto serve a tenere in quadro anche il Guardiano
            target = max(ZOOM_WIDEST if self.part == "arena" else ZOOM, min(target, fit))
        wide = self.looking_down(p) if self.part != "arena" else None
        if wide == ZOOM_STEP and near:
            wide = None                    # in combattimento conta chi ti sta addosso
        self.peering = bool(wide) and not (self.cable and self.cable.attached)   # si guarda giu' 
        if wide:
            target = min(target, wide)
        self.zoom += (target - self.zoom) * (0.08 if target > self.zoom else (0.06 if wide else 0.035))
        if abs(self.zoom - target) < 0.002:
            self.zoom = target
        fx = r.centerx
        if near:
            fx += (sum(x for x, _ in near) / len(near) - r.centerx) * 0.5
            half = W / self.zoom / 2 - 220            # NightKnight resta sempre in quadro
            fx = max(r.centerx - half, min(r.centerx + half, fx))
        self.focus_x = fx if self.focus_x is None else self.focus_x + (fx - self.focus_x) * 0.1

    def drop_ahead(self, p):
        """Di quante tessere scende il suolo davanti a NightKnight (fino a EDGE_LOOK
        tessere avanti); 99 se sotto c'e' solo vuoto o metano."""
        r = p.rect
        drop = 0
        for ahead in range(1, EDGE_LOOK + 1):
            x = r.centerx + p.facing * ahead * TILE
            floor = self.lv.floor_near(x, r.bottom + 6 * TILE, 7, liquid=True)
            if floor is None:
                return 99
            drop = max(drop, (floor - r.bottom) // TILE)
        return drop

    def looking_down(self, p):
        """Quanto allontanare la telecamera: cadendo, appesi al cavo, o sul bordo di
        un vuoto del tutto; sul bordo di un gradino alto un poco. None se no."""
        if self.cable and self.cable.attached:
            # abbastanza larga da tenere l'arco del cavo e il lago sotto
            rope = self.cable.current.rope
            top = rope.anchor.y + rope.length * 0.6 - 45 - 110
            need = (GROUND * TILE + LOW_MARGIN - top) / VH
            return max(ZOOM_WIDEST, min(ZOOM_OUT, ZOOM / need))
        if not p.on_ground and not p.climbing and p.vy > 9:
            return ZOOM_OUT
        if p.on_ground:
            drop = self.drop_ahead(p)
            if drop >= EDGE_DROP:
                return ZOOM_OUT
            if drop >= STEP_DROP:
                return ZOOM_STEP
        return None

    def die(self):
        self.state, self.state_t = "dead", 0
        self.jb.fx("death")

    def hit_enemy(self, e, hits, pts=100, weapon=False):
        """La vita dei nemici si conta in colpi. Il fendente con l'arma non affine
        alla fauna del satellite vale mezzo colpo: i nemici diventano piu' resistenti."""
        if not e.alive:
            return
        if weapon and self.player.weapon["affinity"] != self.cfg["affinity"]:
            hits *= 0.5
        e.flash = 6
        if hasattr(e, "rect"):
            self.burst_sparks(e.rect.centerx, e.rect.centery, 10)
        e.hp -= hits
        bony = isinstance(e, Skeleton) and getattr(e, "kind", "skeleton").startswith("skeleton")
        self.jb.fx("hit" if bony else "flesh_hit")
        if e.hp <= 0:
            e.alive = False
            self.score += pts
            if hasattr(e, "rect"):
                self.shake = max(self.shake, 6 if e.rect.h > 300 else 3)
                self.burst_sparks(e.rect.centerx, e.rect.centery, 22)
            if bony:
                self.jb.fx("bones")

    # ---- aggiornamento
    def update(self):
        if self.paused:
            return
        self.frame += 1
        if self.state == "card":
            self.card_t -= 1
            if self.card_t <= 0:
                self.state = "play"
            return
        if self.state == "victory":
            self.card_t -= 1
            if self.card_t <= 0:
                self.after_victory()
            return
        if self.state == "dead":
            self.state_t += 1
            if self.state_t > 110:
                self.lose_life()
            return
        if self.state != "play":
            return
        p = self.player
        if self.nova_t:
            self.update_nova()
            return
        if self.msg:
            t, n, col = self.msg
            self.msg = (t, n - 1, col) if n > 1 else None
        if self.part == "arena" and self.intro:
            self.intro -= 1
            if self.intro == 70:
                self.msg = ("FIGHT!", 60, (230, 40, 40))
            if self.intro > 70:
                return
        keys = pygame.key.get_pressed()
        if self.cable:
            self.cable.update_player(p, keys, self.lv)
        else:
            p.update(keys, self.lv)
        if self.bianca:
            self.bianca.update(p, self.cam, self.camy)
            self.bianca_sortie()
        self.luce = p.albedo
        if p.jumped:
            self.jb.fx("jump")
        self.sword_feedback()
        for e in self.effects:
            e.update()
        self.effects = [e for e in self.effects if e.alive]
        for sp in self.sparks:
            sp[0] += sp[2]; sp[1] += sp[3]; sp[3] += 0.4; sp[4] -= 1
        self.sparks = [sp for sp in self.sparks if sp[4] > 0]
        self.shake = max(0, self.shake - 1)
        target = p.rect.centerx - DW // 2
        self.cam = int(max(0, min(target, self.lv.w - DW)))
        lock = self.waves.lock() if self.waves else None
        if lock:
            # porte stagne chiuse: si resta nell'arena finche' l'ondata non e' finita
            p.x = max(lock[0] + 30, min(p.x, lock[1] - 30 - p.w))
            self.cam = int(max(lock[0], min(target, lock[1] - DW)))
        self.follow_y(p)
        self.update_zoom(p)
        # scendendo nelle gallerie la luce se ne va piano
        depth = (p.rect.bottom / TILE - levels.CAVE_TOP) / 3
        self.dark += (max(0.0, min(1.0, depth)) - self.dark) * 0.05
        if self.lv.drowned(p.rect):
            self.die(); return
        r = p.rect
        for geyser in self.geysers:
            if geyser.update(p):
                hit = not p.invuln
                self.hurt_player(25, geyser.x)
                if hit:
                    p.vx = GEYSER_LAUNCH[0] * (1 if p.rect.centerx > geyser.x else -1)
                    p.vy = GEYSER_LAUNCH[1]
            if geyser.phase != geyser.previous_phase and abs(geyser.x - p.x) < W:
                self.jb.fx({"warning": "geyser_warn", "eruption": "geyser"}.get(geyser.phase, "none"))
            if self.state != "play":
                return
        for spento in self.spenti:
            if spento.update(p):
                p.albedo = min(LUCE_MAX, p.albedo + LUCE_PER_PRISONER)
                self.freed.add((self.ci, self.part, int(spento.x)))
                self.jb.fx("prisoner")
        # Ossigeno: scende all'aperto, risale vicino alle stazioni della colonia
        breathing = any(st.near(p) for st in self.stations) or self.part == "arena"
        if breathing:
            if p.oxygen < OXYGEN_MAX and self.frame % 30 == 0:
                self.jb.fx("air")
            p.oxygen = min(OXYGEN_MAX, p.oxygen + OXYGEN_REFILL)
        else:
            p.oxygen = max(0, p.oxygen - OXYGEN_DRAIN * (SPRINT_O2 if p.sprinting else 1))
            if p.oxygen == 0 and self.frame % 90 == 0:
                self.jb.fx("pant")                  # senz'aria: si ansima, non si muore
        for vent in self.vents:
            if vent.update(p):
                if not p.chill:
                    self.jb.fx("freeze")
                p.chill = CHILL_FRAMES              # il gas gela: si rallenta per un momento
                p.vx += vent.facing * VENT_PUSH     # e il getto spinge indietro
        if self.state != "play":
            return
        # uscita
        ec, er = self.lv.exit
        door = pygame.Rect(ec * TILE, (er - 1) * TILE, TILE, TILE * 2)
        if self.part != "arena" and r.colliderect(door):
            self.jb.fx("door")
            self.next_part()
            return
        if self.part == "surface":
            stages = levels.TITAN_STAGES
            moved = False
            while self.stage + 1 < len(stages) and p.rect.centerx > stages[self.stage + 1][0] * TILE:
                self.stage += 1                     # nuova tappa: da qui si riparte
                moved = True
            if not self.reached_pass and p.x > levels.TITAN_PASS_START * TILE:
                self.reached_pass = True
                self.jb.play("trials")
            if moved:
                self.save_progress(checkpoint=True)
        if self.waves:
            event = self.waves.update(p, self.skels, self.crows)
            if event:
                kind, wave = event
                self.jb.fx("door")
                if kind == "clear":
                    self.score += 1000 * wave.total // 10
        for k in self.skels:
            k.update(self.lv, p)
            if getattr(k, "rumble", 0) and abs(k.x - p.x) < 300:
                self.shake = max(self.shake, 3)          # il suolo trema sotto i piedi
        for cr in self.crows:
            cr.update(self.lv, p)
            if getattr(cr, "cawed", False):
                cr.cawed = False
                self.jb.fx("caw")
        for b in self.balls:
            b.update(self.lv, self.cam)
        # meduse addosso: tolgono vita a poco a poco
        stuck = [c for c in self.crows if c.alive and getattr(c, "stuck", None) is not None]
        p.jellies = len(stuck)
        if stuck and self.frame % JELLY_EVERY == 0:
            p.hp = max(0, p.hp - JELLY_DRAIN * len(stuck))
            self.burst_sparks(p.rect.centerx, p.rect.centery, 4, (180, 220, 255))
            if p.hp == 0:
                self.die(); return
        # lancio della lancia / hadouken / albedo
        # colpi del giocatore sui nemici
        enemies = [(k, k.spec["pts"]) for k in self.skels] + [(c, c.spec.get("pts", 150)) for c in self.crows]
        for e, pts in enemies:
            if not e.alive:
                continue
            abox, adm = p.attack_box()
            er = e.rect
            if abox and abox.colliderect(er) and getattr(e, "swing", None) != p.swing:
                e.swing = p.swing
                self.hit_enemy(e, p.power(SWORD_HIT if p.attack[0] in ("throw", "spin") else STONE_HIT),
                               pts=pts, weapon=p.attack[0] == "throw" and not p.breathless)
                continue
            if not e.alive:
                continue
            if getattr(e, "stuck", None) is not None or getattr(e, "hidden", False):
                continue
            if p.hurtbox().colliderect(er):
                if getattr(e, "spec", {}).get("drift") and not self.intro:
                    if p.jellies < JELLY_MAX:
                        e.stuck = (random.randint(-40, 40), random.randint(10, 90))
                        p.jellies += 1
                        self.jb.fx("hurt")
                    continue
                if isinstance(e, Crow) and getattr(e, "harmless", True):
                    # il corvo disturba: spinge, fa sbagliare il colpo, ma non toglie vita
                    if not p.invuln:
                        p.vx = 3 * e.facing
                        p.attack = None
                        p.invuln = 20
                elif p.vy > 0 and r.bottom - er.top < 40:
                    self.hit_enemy(e, p.power(1), pts=pts)
                    p.vy = -14
                    self.jb.fx("stomp")
                elif not getattr(e, "frozen", 0):
                    self.hurt_player(getattr(e, "dmg", 25) or 25, e.x)
            sb = e.attack_box() if isinstance(e, Skeleton) else None
            if sb and sb.colliderect(p.hurtbox()):
                self.hurt_player(getattr(e, "dmg", 30), e.x)
            if self.state != "play":
                return
        for b in self.balls:
            if b.owner == "player" and b.alive:
                for e, pts in enemies:
                    if e.alive and not getattr(e, "hidden", False) and getattr(b, "hit_rect", b.rect).colliderect(e.rect):
                        self.hit_enemy(e, p.power(b.dmg), pts=pts)
                        b.alive = False
                        break
                if self.boss and b.alive and b.rect.colliderect(self.boss.rect):
                    if self.boss.hit(getattr(b, "boss_dmg", b.dmg)):
                        self.score += 50
                        self.shake = max(self.shake, 5)
                        self.jb.fx("boss_hit")
                    b.alive = False
            if b.owner == "boss" and b.alive and b.rect.colliderect(p.hurtbox()):
                b.alive = False
                self.hurt_player(b.dmg, b.x)
                if self.state != "play":
                    return
        # boss
        bs = self.boss
        if bs:
            if bs.hp <= 0:
                self.ko_wait += 1
                if self.ko_wait == 1:
                    self.balls = []
                    self.msg = ("K.O.", 120, (250, 210, 60))
                    self.jb.fx("ko")
                    self.score += 5000 * self.cfg["num"]
                bs.update(self.lv, p, self.boss_spawn)
                if self.ko_wait > 130:          # un solo round: il Guardiano e' caduto
                    self.next_part()
                    return
            else:
                bs.update(self.lv, p, self.boss_spawn)
                gap = p.rect.centerx - bs.rect.centerx
                if abs(gap) > BOSS_FAR and not bs.hidden:
                    # mai fuori scena a colpire da dove non si vede: se e' lontano avanza
                    bs.x += BOSS_STRIDE * (1 if gap > 0 else -1)
                    bs.facing = 1 if gap > 0 else -1
                br = bs.rect
                abox, adm = p.attack_box()
                if abox and abox.colliderect(br) and bs.hit(adm):
                    self.score += 50; self.shake = max(self.shake, 5); self.jb.fx("boss_hit")
                if not bs.hidden and p.hurtbox().colliderect(br):
                    if p.vy > 0 and r.bottom - br.top < 50:
                        p.vy = -14
                        if bs.hit(8):
                            self.score += 50
                    else:
                        push = 1 if p.x < bs.x else -1
                        p.x -= push * 5
                        bs.x += push * 2
                bb = bs.attack_box()
                if bb and bb.colliderect(p.hurtbox()):
                    self.hurt_player(bs.move_dmg(), bs.x)
        self.skels = [k for k in self.skels if k.alive]
        self.crows = [c for c in self.crows if c.alive]
        self.balls = [b for b in self.balls if b.alive]

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state = "gameover"
            self.menu_index = 0
            self.hi = max(self.hi, self.score)
            self.jb.stop()
            # si puo' continuare dall'ultima tappa con tre vite, ma il punteggio
            # riparte da zero: questo e' il salvataggio che "Continua" riprende
            lives, score = self.lives, self.score
            self.lives, self.score = 3, 0
            self.save_progress(checkpoint=True)
            self.lives, self.score = lives, score
        else:
            self.rounds = [0, 0]
            self.spawn()
            self.state = "play"
            self.save_progress(checkpoint=True)

    # ---- tasti
    def key(self, k):
        p = self.player
        if k == pygame.K_m:
            self.jb.toggle_mute()
            return
        if k in (pygame.K_ESCAPE, pygame.K_p):
            if self.state not in ("title", "end", "gameover"):
                self.set_paused(not self.paused)
            elif k == pygame.K_ESCAPE:
                if self.state == "title":
                    self.running = False
                else:
                    self.state = "title"
                    self.menu_index = 0
            return
        if self.paused:
            self.menu_key(k)
            return
        if self.state == "title":
            self.menu_key(k)
            return
        if self.state == "weapon_select":
            if k in (pygame.K_LEFT, pygame.K_a, pygame.K_UP, pygame.K_w):
                self.weapon_i = (self.weapon_i - 1) % len(levels.WEAPONS)
            elif k in (pygame.K_RIGHT, pygame.K_d, pygame.K_DOWN, pygame.K_s):
                self.weapon_i = (self.weapon_i + 1) % len(levels.WEAPONS)
            elif k == pygame.K_RETURN:
                self.new_game()
            elif k == pygame.K_ESCAPE:
                self.state = "title"
            return
        if self.state == "gameover":
            self.menu_key(k)                  # CONTINUA dall'ultima tappa, o NUOVA PARTITA
            return
        if self.state == "end":
            if k == pygame.K_RETURN:
                self.state = "title"
                self.menu_index = 0
            return
        if self.state in ("card", "victory"):
            if k == pygame.K_RETURN:
                self.card_t = 0
            return
        if self.state != "play" or (self.part == "arena" and (self.intro > 70 or self.boss.hp <= 0)):
            return
        if self.cable and k == pygame.K_e:
            self.cable.interact(p, self.lv)
            return
        if self.cable and self.cable.attached:
            if k == pygame.K_SPACE:
                self.cable.release(p)
                self.jb.fx("jump")
            elif k == pygame.K_z:
                p.slash()                          # appesi al cavo si puo' menare la spada
                self.sword_feedback()
            return
        side = 1 if k in (pygame.K_RIGHT, pygame.K_d) else (-1 if k in (pygame.K_LEFT, pygame.K_a) else 0)
        if side:
            if p.tap_dir == side and self.frame - p.last_tap <= DOUBLE_TAP:
                p.running = side                    # doppio tocco: si corre
            p.last_tap, p.tap_dir = self.frame, side
        if k == pygame.K_b:
            self.start_nova()
            return
        fwd = (pygame.K_RIGHT, pygame.K_d) if p.facing > 0 else (pygame.K_LEFT, pygame.K_a)
        if k in (pygame.K_DOWN, pygame.K_s):
            p.last_down = self.frame
        elif k in fwd:
            p.last_fwd = self.frame
        if k in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
            r = p.rect
            near_ladder = self.lv.tile_at(r.centerx, r.centery) == "H" or self.lv.tile_at(r.centerx, r.top - 4) == "H"
            if k == pygame.K_SPACE or not near_ladder:
                if p.do_jump():
                    self.jb.fx("jump")
        elif k == pygame.K_z:
            p.slash()
            self.sword_feedback()
        elif k == pygame.K_x:
            if p.start_attack("punch"):
                self.balls.append(Stone(p))
                self.jb.fx("throw")
        elif k == pygame.K_c:
            # in salto, muovendosi, il calcio diventa il calcio volante girato;
            # da un salto da fermo resta il calcio volante semplice
            spin = not p.on_ground and abs(p.vx) > SPIN_MIN_SPEED
            if p.start_attack("spin" if spin else "kick"):
                self.jb.fx("sword" if spin else "swing")
                self.shake_off(JELLY_MAX if spin else 1)
        elif k == pygame.K_v:
            self.luce_burst()

    # ---- disegno
    def bar(self, x, y, w, frac, color, right=False):
        s = self.screen
        pygame.draw.rect(s, (105, 112, 115), (x - 2, y - 2, w + 4, 18), border_radius=3)
        pygame.draw.rect(s, (15, 19, 22), (x, y, w, 14), border_radius=2)
        fw = int(w * max(0, min(1, frac)))
        if fw:
            left = x + w - fw if right else x
            pygame.draw.rect(s, color, (left, y, fw, 14), border_radius=2)
            highlight = tuple(min(255, int(v * 1.2 + 15)) for v in color)
            pygame.draw.line(s, highlight, (left, y + 2), (left + fw - 1, y + 2))

    def pill(self, x, y, w, h, frac, color, back=(18, 14, 12, 150)):
        """Barra sottile e arrotondata, con un filo di luce sul riempimento."""
        s = self.screen
        bg = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        pygame.draw.rect(bg, back, bg.get_rect(), border_radius=(h + 4) // 2)
        s.blit(bg, (x - 2, y - 2))
        fw = int(w * max(0, min(1, frac)))
        if fw > h // 2:
            pygame.draw.rect(s, color, (x, y, fw, h), border_radius=h // 2)
            hi = tuple(min(255, v + 45) for v in color)
            pygame.draw.line(s, hi, (x + h // 2, y + 2), (x + fw - h // 2, y + 2), 2)

    def draw_hud(self):
        """HUD essenziale: vita e Luce in alto a sinistra, punti piccoli a destra;
        la vita del Guardiano in basso, solo durante il duello."""
        s, p = self.screen, self.player
        if not hasattr(self, "hud_icon"):
            self.hud_icon = assets.load("emblema", 64, 64, by_height=True) if assets.has("emblema") else None
        x0, y0 = 48, 40
        if self.hud_icon:
            s.blit(self.hud_icon, (x0, y0 - 6))
            x0 += self.hud_icon.get_width() + 18
        hurt = p.hp <= 30
        self.pill(x0, y0, 360, 14, p.hp / PLAYER_HP, (205, 92, 72) if hurt else (238, 226, 204))
        # Luce: quattro tacche, una per unita' di raffica di Bianca
        for i in range(LUCE_MAX // LUCE_UNIT):
            fill = max(0, min(1, (p.albedo - i * LUCE_UNIT) / LUCE_UNIT))
            glow = (255, 214, 120) if fill >= 1 else (186, 150, 92)
            self.pill(x0 + i * 92, y0 + 28, 80, 10, fill, glow)
        # ossigeno: sottile, azzurro, diventa rosso quando sta finendo
        o2 = p.oxygen / OXYGEN_MAX
        self.pill(x0, y0 + 50, 360, 6, o2, (120, 200, 220) if o2 > 0.25 else (220, 90, 70))
        for i in range(self.lives):
            pygame.draw.circle(s, (238, 226, 204), (x0 + 380 + i * 22, y0 + 7), 6)
        if self.nova_ready:
            # Nova pronta: una stella che pulsa accanto alla Luce
            cx, cy = x0 + 392, y0 + 34
            pulse = 1 + 0.25 * math.sin(self.frame / 7)
            for a in range(8):
                ang = a * math.pi / 4 + self.frame / 40
                pygame.draw.line(s, (255, 214, 120), (cx, cy), (cx + math.cos(ang) * 16 * pulse, cy + math.sin(ang) * 16 * pulse), 3)
            pygame.draw.circle(s, (255, 244, 214), (cx, cy), int(7 * pulse))
        sc = f"{self.score}"
        fonts.draw_text(s, sc, W - 48 - fonts.text_width(sc, 4), y0 - 6, (238, 226, 204), scale=4)
        if self.boss:
            name = self.cfg["boss"].upper()
            bx, by, bw = W // 2 - 420, H - 70, 840
            fonts.draw_text(s, name, W // 2 - fonts.text_width(name, 3) // 2, by - 34, (238, 226, 204), scale=3)
            self.pill(bx, by, bw, 12, self.boss.hp / self.boss.max_hp, (196, 84, 60))
        if self.msg:
            t, n, col = self.msg
            fonts.draw_text(s, t, W // 2 - fonts.text_width(t, 12) // 2, 380, col, scale=12)

    def draw_world(self):
        """Cielo e fondali, a piena risoluzione dietro la vista del mondo: dal piu'
        lontano al piu' vicino, ognuno scorre piu' in fretta del precedente e fra
        l'uno e l'altro la foschia di Titano schiarisce le distanze."""
        s, cam, lv = self.screen, self.cam, self.lv
        # In verticale i piani lontani si spostano meno di quelli vicini.
        lift = (VIEW_Y - self.camy) * ZOOM
        s.fill((34, 16, 8))
        # Il cielo non si ripete: e' appena piu' largo dello schermo e scorre
        # pochissimo, cosi' Saturno resta uno solo.
        fogs = tuple(fog for *_, fog in PARALLAX)
        sky = self.gfx.wide_sky(1, SKY_PAN)
        sky = self.gfx.fogged(sky, fogs, H - sky.get_height())
        off = -min(SKY_PAN, int(cam * SKY_PAN / max(1, lv.cols * TILE - W, W)))
        s.blit(sky, (off, H - sky.get_height() + int(lift * 0.04)))
        # Ogni piano si ripete alternando una copia specchiata: niente cuciture.
        for i, (name, speed, dy, _) in enumerate(PARALLAX):
            layer = self.gfx.mirrored(self.gfx.fogged(self.gfx.layer(name), fogs[i:], dy))
            off = -(int(cam * speed) % layer.get_width())
            for x in range(off, W, layer.get_width()):
                s.blit(layer, (x, dy + int(lift * speed)))
        # Sotto la crosta non c'e' cielo: dietro le gallerie si vede la caverna.
        vx, vy, cw, ch = self.view_rect()
        ground = int((GROUND * TILE + TILE - self.camy - vy) * H / ch)
        if ground < H:
            cave = self.gfx.mirrored(self.gfx.layer("cave_bg"))
            off = -(int(cam * 0.3) % cave.get_width())
            clip = s.get_clip()
            s.set_clip((0, max(0, ground), W, H))
            for x in range(off, W, cave.get_width()):
                s.blit(cave, (x, ground - H // 3))
            s.set_clip(clip)

    def draw_foreground(self, s):
        """Il piano piu' vicino, davanti a tutto: sagome scure che passano veloci.
        Sono rocce della superficie: scendendo sottoterra svaniscono."""
        fade = 1 - (self.camy - VIEW_Y) / (3 * TILE)
        if fade <= 0:
            return
        fg = self.gfx.mirrored(self.gfx.foreground_low)
        fg.set_alpha(int(255 * min(1, fade)))
        lift = (VIEW_Y - self.camy) * ZOOM
        off = -(int(self.cam * ZOOM * FOREGROUND_SPEED) % fg.get_width())
        y = H - fg.get_height() + FOREGROUND_SINK + int(lift * FOREGROUND_SPEED)
        for x in range(off, W, fg.get_width()):
            s.blit(fg, (x, y))

    def draw_darkness(self, s):
        """Nelle gallerie non arriva luce: resta solo il cono della visiera."""
        p = self.player
        if self.dark < 0.02:
            return
        vx, vy, cw, ch = self.view_rect()
        k = W / cw
        cx = (p.rect.centerx + p.facing * 40 - self.cam - vx) * k
        cy = (p.rect.top + 40 - self.camy - vy) * k
        shade = self.gfx.darkness
        shade.fill((6, 3, 2, int(DARKNESS * self.dark)))
        light = self.gfx.visor_light
        shade.blit(light, (cx - light.get_width() // 2, cy - light.get_height() // 2),
                   special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(shade, (0, 0))

    def view_rect(self):
        """La parte della vista del mondo che finisce sullo schermo: con lo zoom
        e' piu' piccola, ancorata ai piedi di NightKnight e ai nemici che ha addosso."""
        p = self.player
        k = ZOOM / self.zoom
        cw, ch = int(VW * k), int(VH * k)
        camy = int(self.camy)
        fx = max(0, min(DW, (self.focus_x if self.focus_x is not None else p.rect.centerx) - self.cam))
        fy = max(0, min(VH, p.rect.bottom - camy))
        vx = max(0, min(DW - cw, int(fx - VW / 2 * k)))
        # avvicinandosi i piedi restano dove sono; allontanandosi la vista scende
        bias = DROP_BIAS if getattr(self, "peering", False) else 0
        vy = int(fy * (1 - k) + max(0, k - 1) * VH * bias)
        vy = max(-camy, min(self.lv.h - ch - camy, vy))
        return vx, vy, cw, ch

    def draw_tiles(self):
        """Terreno, laghi di metano, scale e portello: disegnati nella vista del mondo."""
        s, cam, lv = self.screen, self.cam, self.lv
        c0 = max(0, cam // TILE)
        cols = range(c0, min(lv.cols, c0 + DW // TILE + 3))
        _, vy, _, ch = self.view_rect()
        r0 = max(0, (int(self.camy) + vy) // TILE)
        rows = range(r0, min(lv.rows, r0 + ch // TILE + 2))
        for c in cols:
            for r in range(max(0, r0 - levels.LAKE_DEPTH), rows.stop):
                if lv.g[r][c] != "~" or lv.at(c, r - 1) == "~":
                    continue
                s.blit(self.gfx.titan_lake, (c * TILE - cam, r * TILE))
                # riflessi che scorrono piano sulla superficie del metano
                y = r * TILE + LAKE_LEVEL
                for i in range(3):
                    ph = (self.frame * (0.6 + i * 0.25) + c * 37 + i * 90) % 140
                    if ph < TILE:
                        pygame.draw.line(s, (236, 168, 96), (c * TILE - cam + ph, y + 3 + i * 7),
                                         (c * TILE - cam + min(TILE, ph + 22 - i * 6), y + 3 + i * 7), 2)
        s.blit(self.gfx.haze, (0, GROUND * TILE - 75))
        self.draw_cave_props(s, cam, lv)
        for c in cols:
            x = c * TILE - cam
            for r in rows:
                ch = lv.g[r][c]
                y = r * TILE
                if ch in self.gfx.tiles:
                    part = 0
                    while ch == "H" and part < LADDER_W and lv.at(c - part - 1, r) == "H":
                        part += 1
                    s.blit(self.gfx.titan_tile(ch, c, r, part), (x, y))
                    if ch in "#D":
                        self.rock_edges(s, lv, c, r, x, y)
                elif ch in "EP":
                    img = self.gfx.airlock if ch == "E" else self.gfx.capsule
                    titan.ground_shadow(s, x + TILE // 2, y + TILE, img.get_width() * 0.9)
                    s.blit(img, (x + TILE // 2 - img.get_width() // 2, y + TILE - img.get_height() + titan.SINK))

    def draw_cave_props(self, s, cam, lv):
        """Stalattiti, stalagmiti, puntelli e rottami della colonia nelle gallerie."""
        if lv.kind != "surface":
            return
        x0 = levels.TITAN_PASS_START * TILE - cam
        mouth = self.gfx.cave_mouth
        if mouth:
            x = x0 + levels.CAVE_MOUTH * TILE
            if -mouth.get_width() < x < DW + mouth.get_width():
                s.blit(mouth, (x - mouth.get_width() // 2, levels.CAVE_FLOOR * TILE - mouth.get_height() + 12))
        for col, kind in levels.CAVE_PROPS:
            if kind >= len(self.gfx.cave_props):
                continue
            img = self.gfx.cave_props[kind]
            x = x0 + col * TILE + TILE // 2 - img.get_width() // 2
            if not -img.get_width() < x < DW:
                continue
            if kind == 0:              # appesa al soffitto
                s.blit(img, (x, levels.CAVE_TOP * TILE - 10))
            else:
                s.blit(img, (x, levels.CAVE_FLOOR * TILE - img.get_height() + 6))

    def draw_drizzle(self, s):
        """Pioviggine di metano: gocce lente e pesanti, in diagonale, davanti a tutto."""
        if not hasattr(self, "drops"):
            rnd = random.Random(7)
            self.drops = [(rnd.randrange(W), rnd.randrange(H), rnd.uniform(3, 6)) for _ in range(140)]
        t = self.frame
        # sottoterra non piove: le gocce diradano mentre si scende
        for x0, y0, v in self.drops[:int(len(self.drops) * (1 - self.dark))]:
            y = (y0 + t * v) % H
            x = (x0 - t * v * 0.35 - self.cam * 0.6) % W
            pygame.draw.line(s, (255, 208, 160), (x, y), (x - 4, y + 16), 1)

    def rock_edges(self, s, lv, c, r, x, y):
        """Contorno e ombra dove la roccia incontra l'aria: le pareti hanno un
        volume invece di sembrare blocchi di texture."""
        air = lambda cc, rr: lv.at(cc, rr) not in SOLID
        if air(c - 1, r):
            s.blit(self.gfx.rock_shade, (x, y))
            pygame.draw.line(s, (24, 14, 10), (x, y), (x, y + TILE), 4)
        if air(c + 1, r):
            s.blit(self.gfx.rock_shade_r, (x + TILE - self.gfx.rock_shade_r.get_width(), y))
            pygame.draw.line(s, (24, 14, 10), (x + TILE - 2, y), (x + TILE - 2, y + TILE), 4)
        if air(c, r - 1) and r < GROUND:
            # il bordo su cui si cammina: contorno scuro e un filo di luce, si
            # legge contro i fondali dello stesso colore
            pygame.draw.line(s, (24, 14, 10), (x, y), (x + TILE, y), 5)
            pygame.draw.line(s, (255, 214, 150), (x, y + 4), (x + TILE, y + 4), 3)
        if air(c, r + 1) and r < GROUND:
            # sotto una cengia sospesa: contorno e ombra portata
            pygame.draw.line(s, (24, 14, 10), (x, y + TILE - 2), (x + TILE, y + TILE - 2), 5)
            s.blit(self.gfx.ledge_shadow, (x, y + TILE))

    def draw_center(self, text, y, color=(245, 245, 245), scale=8):
        fonts.draw_text(self.screen, text, W // 2 - fonts.text_width(text, scale) // 2, y, color, scale)

    def draw_menu(self, y):
        for i, label in enumerate(self.menu_items()):
            color = (222, 201, 150) if i == self.menu_index else (190, 195, 210)
            self.draw_center(label, y + i * 64, color, 6)
            if i == self.menu_index:
                x = W // 2 - fonts.text_width(label, 6) // 2 - 36
                cy = y + i * 64 + 14
                pygame.draw.polygon(self.screen, color, [(x, cy - 10), (x + 14, cy), (x, cy + 10)])

    def draw_save_status(self):
        if self.save_error:
            self.draw_center("SALVATAGGIO NON DISPONIBILE", H - 40, (255, 120, 120), 4)

    def draw(self):
        s = self.screen
        if self.state == "title":
            s.blit(self.gfx.title_backdrop(), (0, 0))
            self.draw_center("NIGHTKNIGHT", 40, (238, 222, 190), 16)
            self.draw_center("DODICI SATELLITI, UN CAVALIERE", 205, (230, 205, 170), 4)
            self.draw_menu(760)
            self.draw_center(f"RECORD {self.hi:08d}", 965, (220, 205, 180), 3)
            self.draw_center("FRECCE MUOVI   SPAZIO SALTA   Z SPADA   X SASSO   C CALCIO   V BIANCA", 1010, (225, 210, 185), 3)
            self.draw_save_status()
            pygame.display.flip()
            return
        if self.state == "weapon_select":
            s.blit(self.gfx.title_backdrop(), (0, 0))
            shade = pygame.Surface((W, H), pygame.SRCALPHA); shade.fill((12, 6, 3, 150)); s.blit(shade, (0, 0))
            weapon = levels.weapon_cfg(self.weapon_i)
            titan = levels.cfg(0)
            self.draw_center("SCEGLI LA TUA ARMA", 150, (238, 222, 190), 9)
            self.draw_center(f"{self.weapon_i + 1} / 12", 290, (220, 205, 180), 4)
            self.draw_center(weapon["name"].upper(), 380, (250, 240, 225), 9)
            self.draw_center(weapon["description"].upper(), 490, (225, 210, 185), 4)
            self.draw_center("TITANO", 640, (238, 222, 190), 6)
            self.draw_center(f"GRAVITA {titan['gravity'].upper()}   ARIA {titan['air'].upper()}", 720, (225, 210, 185), 3)
            self.draw_center(titan["climate"].upper(), 760, (225, 210, 185), 3)
            self.draw_center("FRECCE SCEGLI   INVIO PARTE   ESC INDIETRO", 960, (225, 210, 185), 3)
            pygame.display.flip()
            return
        if self.state == "end":
            s.blit(self.gfx.title_backdrop(), (0, 0))
            shade = pygame.Surface((W, H), pygame.SRCALPHA); shade.fill((12, 6, 3, 150)); s.blit(shade, (0, 0))
            self.draw_center("TITANO E' LIBERO", 300, (238, 222, 190), 12)
            self.draw_center(f"{self.score}", 470, (250, 240, 225), 7)
            self.draw_center("GLI ALTRI UNDICI SATELLITI TI ASPETTANO", 620, (225, 210, 185), 4)
            self.draw_center("INVIO", 820, (225, 210, 185), 4)
            pygame.display.flip()
            return
        self.draw_world()
        screen = self.screen
        camy = int(self.camy)
        if getattr(self, "world_surf", None) is None or self.world_surf.get_height() != self.lv.h:
            self.world_surf = pygame.Surface((DW, self.lv.h), pygame.SRCALPHA)
        _, vy, _, ch = self.view_rect()
        self.world_surf.fill((0, 0, 0, 0), (0, camy + vy, DW, ch))
        self.screen = s = self.world_surf
        if self.cable:
            self.cable.draw_portals(s, self.cam)
        self.draw_tiles()
        cam = self.cam
        for spento in self.spenti:
            spento.draw(s, cam, self.gfx.spento_sleeping, self.gfx.spento_awake)
        for geyser in self.geysers:
            geyser.draw(s, cam)
        for st in self.stations:
            st.draw(s, cam, st.near(self.player), self.gfx.station)
        for vent in self.vents:
            vent.draw(s, cam)
        if self.cable:
            self.cable.draw(s, cam)
        if self.bianca:
            self.bianca.draw(s, self.gfx, cam)
        for k in self.skels:
            k.draw(s, self.gfx, cam)
        for cr in self.crows:
            if getattr(cr, "stuck", None) is None:
                cr.draw(s, self.gfx, cam)
        if self.boss:
            self.boss.draw(s, cam)
        for b in self.balls:
            b.draw(s, self.gfx, cam)
        p = self.player
        if self.state == "dead":
            # NightKnight a terra: la posa ferma distesa sul suolo
            if not self.lv.drowned(p.rect):
                if "death" in self.gfx.sheets:
                    fr = self.gfx.sheets["death"][0 if p.facing > 0 else 1]
                    p.draw_img(s, fr[min(len(fr) - 1, self.state_t // 9)], cam)
                else:
                    fallen = pygame.transform.rotate(self.gfx.player["idle"][0], 90 * p.facing)
                    s.blit(fallen, (p.rect.centerx - fallen.get_width() // 2 - cam, p.rect.bottom - fallen.get_height() + 10))
        else:
            p.draw(s, self.gfx, cam)
        for cr in self.crows:            # le meduse attaccate stanno sopra la tuta
            if getattr(cr, "stuck", None) is not None:
                cr.draw(s, self.gfx, cam)
        for e in self.effects:
            fonts.draw_text(s, e.text, int(e.x) - cam, int(e.y), e.color, 4)
        for x, y, vx, vy, life, color in self.sparks:
            pygame.draw.line(s, color, (int(x) - cam, int(y)), (int(x - vx * 1.5) - cam, int(y - vy * 1.5)), 3)
        # la vista del mondo si ingrandisce sopra cielo e fondali
        self.screen = s = screen
        vx, vy, cw, ch = self.view_rect()
        view = self.world_surf.subsurface((vx, camy + vy, cw, ch))
        jolt = (random.randint(-self.shake, self.shake), random.randint(-self.shake, self.shake)) if self.shake else (0, 0)
        s.blit(pygame.transform.smoothscale(view, (W, H)), jolt)
        self.draw_foreground(s)
        self.draw_darkness(s)
        self.draw_nova(s)
        self.draw_drizzle(s)
        s.blit(self.gfx.vignette, (0, 0))
        self.draw_hud()
        if self.state == "card":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((12, 6, 3, 160)); s.blit(ov, (0, 0))
            if self.part == "arena":
                self.draw_center(self.cfg["boss"].upper(), 440, (238, 222, 190), 10)
            else:
                self.draw_center(self.cfg["name"].upper(), 400, (238, 222, 190), 14)
                self.draw_center(f"GRAVITA {self.cfg['gravity'].upper()}   ARIA {self.cfg['air'].upper()}", 590, (225, 210, 185), 3)
        elif self.state == "victory":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 190)); s.blit(ov, (0, 0))
            self.draw_center("VITTORIA", 260, (250, 210, 60), 14)
            self.draw_center(f"{self.cfg['boss'].upper()} E' CADUTO", 460, self.cfg["color"], 7)
            self.draw_center("PREMI INVIO", 820, (150, 160, 190), 5)
        elif self.state == "gameover":
            ov = pygame.Surface((W, H), pygame.SRCALPHA); ov.fill((0, 0, 0, 170)); s.blit(ov, (0, 0))
            self.draw_center("GAME OVER", 380, (230, 40, 40), 16)
            self.draw_menu(600)
        if self.paused:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 195))
            s.blit(ov, (0, 0))
            self.draw_center("PAUSA", 300, (250, 210, 60), 14)
            self.draw_menu(520)
        self.draw_save_status()
        pygame.display.flip()

    def run(self):
        while self.running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                if e.type == pygame.WINDOWFOCUSLOST and self.state not in ("title", "end", "gameover"):
                    self.set_paused(True)
                if e.type == pygame.KEYDOWN:
                    self.key(e.key)
            if not self.running:
                break
            self.update()
            self.draw()
            self.clock.tick(FPS)
        self.save_progress()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--windowed", action="store_true", help="Avvia in finestra")
    args = parser.parse_args()
    try:
        Game(windowed=args.windowed).run()
    finally:
        pygame.quit()
