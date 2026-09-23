"""Musica (solo basso e percussioni leggere) ed effetti, sintetizzati localmente."""
import numpy as np
import pygame

SR = 22050
_cache = {}


def _env(n, a=0.01, d=0.05, s=0.6, r=0.05):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    e = np.ones(n)
    a = min(a, n); e[:a] = np.linspace(0, 1, a)
    d = min(d, n - a); e[a:a + d] = np.linspace(1, s, d)
    e[a + d:] = s
    r = min(r, n); e[n - r:] *= np.linspace(1, 0, r)
    return e


def _osc(freq, n, kind):
    t = np.arange(n) / SR
    if kind == "square":
        vib = 1 + 0.004 * np.sin(2 * np.pi * 6 * t)
        return np.sign(np.sin(2 * np.pi * freq * vib * t)) * 0.5 + 0.25 * np.sign(np.sin(2 * np.pi * freq * 2 * t + 1))
    if kind == "saw":
        return 2 * ((freq * t) % 1) - 1
    if kind == "tri":
        return 2 * np.abs(2 * ((freq * t) % 1) - 1) - 1
    return np.sin(2 * np.pi * freq * t)


def _midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def _lowpass(x, k):
    """Filtro passa-basso a un polo: k piccolo = suono piu' scuro."""
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        y[i] = acc
    return y


def _noise(n, seed):
    return np.random.default_rng(seed).uniform(-1, 1, n)


def _bass_note(freq, n, grit):
    """Basso elettrico sintetico: fondamentale piena, un po' di sega filtrata e saturazione."""
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * 2 * t)
    saw = _lowpass(2 * ((freq * t) % 1) - 1, 0.08)
    wave = np.tanh((body + grit * saw) * 1.6)
    pluck = 1 - np.exp(-t * 400)
    return wave * pluck * np.exp(-t * 1.6)


def _perc(kind, n):
    t = np.arange(n) / SR
    if kind == "kick":       # cassa morbida, piu' tonfo che colpo
        return np.sin(2 * np.pi * (46 * t + 2.2 * (1 - np.exp(-t * 20)))) * np.exp(-t * 11) * (1 - np.exp(-t * 300))
    if kind == "rim":        # colpo di bordo secco, al posto del rullante
        return (np.sin(2 * np.pi * 830 * t) * 0.5 + _lowpass(_noise(n, 5), 0.5) * 0.6) * np.exp(-t * 60)
    if kind == "brush":      # spazzola sul rullante
        return _lowpass(_noise(n, 6), 0.35) * np.exp(-t * 14) * (1 - np.exp(-t * 80))
    # "hat": charleston chiuso, appena accennato
    hp = _noise(n, 7) - _lowpass(_noise(n, 7), 0.3)
    return hp * np.exp(-t * 90)


# Tracce: solo basso e percussioni leggere. Un riff di due battute in re minore
# (semitoni dalla tonica, durata in ottavi); in esplorazione il basso e' suonato
# al contrario, quando arriva il Guardiano torna dritto.
TRACKS = {
    #            bpm  tonica  riff                                                 percussioni           al contrario
    "surface":  (78,  38, [(0, 3), (0, 1), (3, 2), (5, 2), (7, 3), (5, 1), (3, 2), (-2, 2)], "sparse", True),
    "crypt":    (66,  38, [(0, 4), (1, 2), (0, 2), (-2, 4), (-4, 4)],                          "sparse", True),
    "trials":   (92,  38, [(0, 2), (0, 1), (12, 1), (0, 2), (3, 2), (5, 2), (3, 2), (0, 4)],   "steady", False),
    "arena":    (104, 38, [(0, 1), (0, 1), (0, 1), (12, 1), (0, 2), (3, 2), (5, 1), (6, 1), (5, 1), (3, 1), (0, 4)], "drive", False),
    "victory":  (70,  38, [(0, 4), (7, 4), (3, 4), (0, 4)],                                    "none", True),
}


def track(name):
    if name in _cache:
        return _cache[name]
    bpm, root, riff, groove, backwards = TRACKS.get(name, TRACKS["surface"])
    eighth = 60 / bpm / 2
    bars = 8                                   # il riff dura due battute: si ripete 4 volte
    total = int(bars * 8 * eighth * SR)
    out = np.zeros((total, 2))

    def add(start, wave, gain, pan=0.0):
        # Le code attraversano il punto di loop senza un taglio improvviso.
        pos = int(start * SR) % total
        stereo = wave[:, None] * gain * np.array([1 - pan * 0.4, 1 + pan * 0.4])
        n = min(len(wave), total - pos)
        out[pos:pos + n] += stereo[:n]
        if n < len(wave):
            out[:len(wave) - n] += stereo[n:]

    riff_len = sum(d for _, d in riff)
    for rep in range(bars * 8 // riff_len):
        pos = rep * riff_len
        for i, (semi, dur) in enumerate(riff):
            n = int(dur * eighth * SR * 0.95)
            # ogni quarta ripetizione il riff scende di una quarta, come un giro
            shift = -5 if rep % 4 == 3 else 0
            note = _bass_note(_midi(root + semi + shift), n, 0.5 if groove == "drive" else 0.3)
            if backwards:
                note = note[::-1] * (1 - np.exp(-np.arange(n) / SR * 200))[::-1]
            add(pos * eighth, note, 0.42)
            pos += dur

    beats = bars * 4
    for b in range(beats):
        at = b * 2 * eighth
        if groove == "none":
            continue
        if groove == "sparse":
            if b % 4 == 0:
                add(at, _perc("kick", int(0.5 * SR)), 0.30)
            if b % 4 == 3:
                add(at, _perc("rim", int(0.2 * SR)), 0.06, 0.3)
            add(at + eighth, _perc("hat", int(0.08 * SR)), 0.035, -0.4)
        else:
            if b % 2 == 0 or groove == "drive":
                add(at, _perc("kick", int(0.5 * SR)), 0.34 if b % 2 == 0 else 0.2)
            if b % 2 == 1:
                add(at, _perc("brush" if groove == "steady" else "rim", int(0.3 * SR)), 0.10 if groove == "steady" else 0.08)
            for h in (0, 1):
                add(at + h * eighth, _perc("hat", int(0.06 * SR)), 0.04 if h else 0.025, -0.4)
    snd = pygame.sndarray.make_sound((np.tanh(out * 1.2) * 22000).astype(np.int16))
    _cache[name] = snd
    return snd


def _tone(f0, f1, n, kind="sine"):
    """Nota che scivola da f0 a f1."""
    t = np.arange(n) / SR
    phase = 2 * np.pi * np.cumsum(np.linspace(f0, f1, n)) / SR
    if kind == "square":
        return np.sign(np.sin(phase))
    return np.sin(phase)


def _whoosh(n, seed, bright):
    t = np.arange(n) / SR
    env = np.sin(np.pi * np.minimum(1, t / (n / SR))) ** 2
    return _lowpass(_noise(n, seed), bright) * env


def sfx(name):
    key = "fx:" + name
    if key in _cache:
        return _cache[key]
    L = lambda sec: int(sec * SR)
    if name == "jump":            # spinta: soffio corto verso l'alto
        n = L(0.18); t = np.arange(n) / SR
        w = _whoosh(n, 1, 0.25) * 0.5 + _tone(90, 160, n) * np.exp(-t * 30) * 0.3
    elif name == "stomp":         # atterrare sulla testa di un nemico
        n = L(0.2); t = np.arange(n) / SR
        w = _tone(160, 50, n) * np.exp(-t * 25) * 0.7 + _lowpass(_noise(n, 2), 0.4) * np.exp(-t * 40) * 0.4
    elif name == "sword":         # fendente: sibilo metallico
        n = L(0.22); t = np.arange(n) / SR
        w = _whoosh(n, 3, 0.6) * 0.45 + _tone(1800, 900, n) * np.exp(-t * 18) * 0.08
    elif name == "swing":         # calcio: spostamento d'aria pieno
        n = L(0.2)
        w = _whoosh(n, 4, 0.15) * 0.6
    elif name == "throw":         # sasso lanciato
        n = L(0.14)
        w = _whoosh(n, 5, 0.45) * 0.45
    elif name == "hit":           # colpo su ossa e metallo
        n = L(0.16); t = np.arange(n) / SR
        w = (_tone(420, 300, n) * 0.4 + _tone(1270, 1180, n) * 0.2) * np.exp(-t * 30) + _noise(n, 8) * np.exp(-t * 60) * 0.35
    elif name == "flesh_hit":     # colpo su una creatura
        n = L(0.18); t = np.arange(n) / SR
        w = _tone(110, 60, n) * np.exp(-t * 28) * 0.7 + _lowpass(_noise(n, 12), 0.2) * np.exp(-t * 24) * 0.55
    elif name == "bones":         # scheletro che crolla: ossa che cadono
        n = L(0.5); t = np.arange(n) / SR
        w = np.zeros(n)
        rng = np.random.default_rng(9)
        for k in range(7):
            at = int(rng.uniform(0, 0.35) * SR); m = L(0.06)
            f = rng.uniform(700, 1400)
            click = np.sin(2 * np.pi * f * np.arange(m) / SR) * np.exp(-np.arange(m) / SR * 80)
            w[at:at + m] += click[:n - at] * 0.35
    elif name == "hurt":          # NightKnight colpito: clangore sull'armatura
        n = L(0.35); t = np.arange(n) / SR
        w = (_tone(230, 200, n) * 0.5 + _tone(612, 590, n) * 0.3 + _tone(1480, 1450, n) * 0.15) * np.exp(-t * 12) \
            + _noise(n, 10) * np.exp(-t * 50) * 0.3
    elif name == "boss_hit":      # colpo sul Guardiano: armatura pesante
        n = L(0.45); t = np.arange(n) / SR
        w = (_tone(140, 120, n) * 0.6 + _tone(395, 380, n) * 0.35 + _tone(955, 940, n) * 0.18) * np.exp(-t * 8) \
            + _noise(n, 11) * np.exp(-t * 40) * 0.3
    elif name == "prisoner":      # prigioniero liberato: luce che sale
        n = L(0.9); t = np.arange(n) / SR
        w = np.zeros(n)
        for k, f in enumerate((587, 880, 1175, 1760)):
            at = L(0.09 * k); m = n - at; tt = np.arange(m) / SR
            w[at:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 4) * (1 - np.exp(-tt * 200)) * 0.18
    elif name == "door":          # uscita: portello stagno che si apre
        n = L(0.9); t = np.arange(n) / SR
        w = _lowpass(_noise(n, 13), 0.5) * np.exp(-t * 3) * 0.35 + _tone(70, 55, n) * np.exp(-t * 6) * 0.4
    elif name == "target":        # bersaglio delle prove
        n = L(0.4); t = np.arange(n) / SR
        w = (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t)) * np.exp(-t * 9) * 0.25
    elif name == "geyser_warn":   # sfiato prima del getto
        n = L(1.2); t = np.arange(n) / SR
        w = _lowpass(_noise(n, 14), 0.6) * np.minimum(1, t * 2) * np.exp(-t * 1.5) * 0.25
    elif name == "geyser":        # eruzione
        n = L(1.5); t = np.arange(n) / SR
        w = (_lowpass(_noise(n, 15), 0.25) * 0.8 + _tone(55, 40, n) * 0.5) * (1 - np.exp(-t * 30)) * np.exp(-t * 1.8) * 0.6
    elif name == "caw":           # corvo in picchiata
        n = L(0.25); t = np.arange(n) / SR
        w = np.tanh(_tone(900, 600, n, "square") * 0.6 * (1 + np.sin(2 * np.pi * 30 * t))) * np.exp(-t * 10) * 0.18
    elif name == "hook":          # gancio del Guardiano: catena che corre
        n = L(0.6); t = np.arange(n) / SR
        chain = (np.sin(2 * np.pi * 45 * t) > 0.7).astype(float) * _noise(n, 16)
        w = _lowpass(chain, 0.7) * np.exp(-t * 3) * 0.4 + _whoosh(n, 17, 0.3) * 0.3
    elif name == "luce":          # raffica di Bianca
        n = L(1.1); t = np.arange(n) / SR
        w = (_tone(300, 1500, n) * 0.25 + _tone(600, 3000, n) * 0.12) * np.exp(-t * 2.5) + _whoosh(n, 18, 0.5) * 0.4
    elif name == "air":           # stazione d'ossigeno: soffio d'aria
        n = L(0.35); t = np.arange(n) / SR
        w = _lowpass(_noise(n, 20), 0.55) * np.sin(np.pi * t / (n / SR)) * 0.18
    elif name == "albedo":        # vecchio nome della raffica
        return sfx("luce")
    elif name == "pickup":
        return sfx("prisoner")
    elif name == "round":         # inizio round: colpo di cassa profondo
        n = L(1.4); t = np.arange(n) / SR
        w = _tone(80, 38, n) * np.exp(-t * 3.5) * 0.8
    elif name == "ko":            # K.O.: rintocco basso che si spegne
        n = L(2.0); t = np.arange(n) / SR
        w = (_tone(73, 70, n) * 0.6 + _tone(110, 108, n) * 0.3 + _tone(220, 218, n) * 0.12) * np.exp(-t * 1.6)
    elif name == "death":         # NightKnight cade
        n = L(1.4); t = np.arange(n) / SR
        w = _tone(196, 49, n) * np.exp(-t * 2) * 0.5 + _lowpass(_noise(n, 19), 0.2) * np.exp(-t * 4) * 0.3
    else:
        n = L(0.1); w = np.zeros(n)
    w = np.tanh(w * 1.2)
    stereo = np.stack([w, w], axis=1)
    snd = pygame.sndarray.make_sound((np.clip(stereo, -1, 1) * 30000).astype(np.int16))
    _cache[key] = snd
    return snd


class Jukebox:
    def __init__(self):
        self.on = True
        self.current = None
        self.chan = None
        self.muted = False
        try:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=SR, size=-16, channels=2, buffer=1024)
            self.chan = pygame.mixer.Channel(0)
            pygame.mixer.set_reserved(1)
            self.chan.set_volume(0.55)
        except pygame.error:
            self.on = False

    def play(self, name):
        if not self.on or name == self.current:
            return
        self.current = name
        self.chan.play(track(name), loops=-1, fade_ms=300)

    def stop(self):
        if self.on:
            self.current = None
            self.chan.fadeout(300)

    def toggle_mute(self):
        self.muted = not self.muted
        if self.on:
            self.chan.set_volume(0 if self.muted else 0.55)

    def fx(self, name):
        if self.on:
            sfx(name).play()
