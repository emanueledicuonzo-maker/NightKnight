"""Colonna sonora ambient dark fantasy ed effetti sintetizzati localmente."""
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


def _drum(kind, n):
    t = np.arange(n) / SR
    if kind == "kick":
        return np.sin(2 * np.pi * (120 * np.exp(-t * 30) + 40) * t) * np.exp(-t * 18)
    if kind == "snare":
        rng = np.random.default_rng(1)
        return (rng.uniform(-1, 1, n) * 0.7 + 0.3 * np.sin(2 * np.pi * 180 * t)) * np.exp(-t * 25)
    rng = np.random.default_rng(2)
    return rng.uniform(-1, 1, n) * np.exp(-t * 90) * 0.5


def _render(bpm, bars, chords, bass_riff, lead_bars, key=40, drums=True, lead_kind="square"):
    """chords: lista di semitoni per barra (12-bar). bass_riff: 8 semitoni (shuffle). lead_bars: lista di frasi,
    ogni frase = lista di (step, semitono relativo alla tonica, durata in step); 12 step per barra (4 beat x 3)."""
    step = 60 / bpm / 3
    n_bar = int(12 * step * SR)
    total = n_bar * bars
    out = np.zeros(total)

    def add(pos, wave):
        end = min(total, pos + len(wave))
        out[pos:end] += wave[:end - pos]

    for b in range(bars):
        root = key + chords[b % len(chords)]
        base = b * n_bar
        # basso boogie
        for i, semi in enumerate(bass_riff):
            pos = base + int((i * 1.5) * step * SR)
            n = int(1.2 * step * SR)
            f = _midi(root + semi - 12)
            wave = 0.8 * _osc(f, n, "sine") + 0.2 * _osc(f, n, "tri")
            add(pos, wave * _env(n, 0.01, 0.08, 0.6, 0.06) * 0.6)
        # solo il basso (niente melodia, niente batteria)
    out = np.tanh(out * 1.1) * 0.7
    stereo = np.stack([out, out], axis=1)
    return pygame.sndarray.make_sound((stereo * 32000).astype(np.int16))


TWELVE = [0, 0, 0, 0, 5, 5, 0, 0, 7, 5, 0, 7]
BOOGIE = [0, 0, 7, 7, 9, 9, 10, 10]
PENTA_A = [(0, 12, 2), (3, 10, 2), (6, 7, 1), (7, 5, 1), (9, 7, 2)]
PENTA_B = [(0, 7, 1), (1, 10, 1), (3, 12, 2), (6, 15, 1), (7, 12, 1), (9, 10, 3)]
PENTA_C = [(0, 12, 1), (2, 12, 1), (3, 15, 2), (6, 12, 1), (7, 10, 1), (9, 7, 1), (10, 3, 2)]
REST = [(0, None, 0)]
TURN = [(0, 0, 1), (3, 3, 1), (6, 4, 1), (9, 5, 3)]


def track(name):
    if name in _cache:
        return _cache[name]
    bpm, root = {"surface": (72, 38), "crypt": (56, 33), "arena": (96, 38),
                 "victory": (76, 50)}.get(name, (72, 38))
    beat = 60 / bpm
    total = int(32 * beat * SR)
    out = np.zeros((total, 2), dtype=np.float64)

    def add(start, wave, gain, pan=0.0):
        # Le code attraversano il punto di loop senza un taglio improvviso.
        pos = int(start * SR) % total
        stereo = wave[:, None] * gain * np.array([1 - pan * 0.45, 1 + pan * 0.45])
        n = min(len(wave), total - pos)
        out[pos:pos+n] += stereo[:n]
        if n < len(wave):
            out[:len(wave)-n] += stereo[n:]

    chords = [(0, 3, 7), (-5, 0, 3), (-2, 2, 5), (-7, -2, 2)]
    if name == "victory":
        chords = [(0, 4, 7), (5, 9, 12), (7, 11, 14), (0, 4, 7)]
    for bar in range(8):
        chord = chords[bar % 4]
        n = int(beat * 5 * SR)
        t = np.arange(n) / SR
        envelope = np.sin(np.pi * np.arange(n) / n) ** 2
        for j, semitone in enumerate(chord):
            freq = _midi(root + semitone)
            wave = (np.sin(2*np.pi*freq*t) + 0.35*np.sin(2*np.pi*freq*2.002*t)
                    + 0.14*np.sin(2*np.pi*freq*3*t)) * envelope
            add(bar * 4 * beat, wave, 0.075, (j - 1) * 0.65)
        for step in (0, 2.5):
            n = int(beat * 3 * SR)
            t = np.arange(n) / SR
            freq = _midi(root + chord[(bar + int(step)) % 3] + 24)
            wave = (np.sin(2*np.pi*freq*t) + 0.22*np.sin(2*np.pi*freq*2.76*t))
            wave *= (1 - np.exp(-t * 35)) * np.exp(-t * 2.2)
            add((bar * 4 + step) * beat, wave, 0.055, (-1 if bar % 2 else 1) * 0.6)
            add((bar * 4 + step + 0.75) * beat, wave, 0.018, 0.0)
        if name == "arena":
            for step in (0, 1.5, 2, 3.5):
                n = int(0.6 * SR)
                t = np.arange(n) / SR
                drum = np.sin(2*np.pi*(48*t + 1.4*(1-np.exp(-t*16)))) * np.exp(-t*9)
                drum *= 1 - np.exp(-t*150)
                add((bar * 4 + step) * beat, drum, 0.13)
    snd = pygame.sndarray.make_sound((np.tanh(out) * 24000).astype(np.int16))
    _cache[name] = snd
    return snd


def sfx(name):
    if name in _cache:
        return _cache[name]
    t = None
    if name == "jump":
        n = int(0.15 * SR); t = np.arange(n) / SR
        w = np.sign(np.sin(2 * np.pi * (300 + 900 * t) * t)) * np.exp(-t * 12) * 0.3
    elif name == "throw":
        n = int(0.12 * SR); t = np.arange(n) / SR
        w = np.random.default_rng(3).uniform(-1, 1, n) * np.exp(-t * 40) * 0.35
    elif name == "flesh_hit":
        n = int(0.18 * SR); t = np.arange(n) / SR
        noise = np.random.default_rng(12).uniform(-1, 1, n)
        noise = np.convolve(noise, np.ones(18) / 18, mode="same")
        w = (0.7*np.sin(2*np.pi*(70*t + 0.4*(1-np.exp(-t*30))))*np.exp(-t*32)
             + 0.55*noise*np.exp(-t*24)) * (1-np.exp(-t*400)) * 0.65
    elif name == "hit":
        n = int(0.15 * SR); t = np.arange(n) / SR
        w = (np.sign(np.sin(2 * np.pi * 110 * t)) + np.random.default_rng(4).uniform(-1, 1, n)) * np.exp(-t * 25) * 0.3
    elif name == "hurt":
        n = int(0.35 * SR); t = np.arange(n) / SR
        w = np.sign(np.sin(2 * np.pi * (500 - 400 * t) * t)) * np.exp(-t * 6) * 0.3
    elif name == "pickup":
        n = int(0.3 * SR); t = np.arange(n) / SR
        f = np.where(t < 0.1, 660, np.where(t < 0.2, 880, 1320))
        w = np.sign(np.sin(2 * np.pi * f * t)) * 0.25 * _env(n, 0.005, 0.02, 0.8, 0.1)
    elif name == "cosmo":
        n = int(0.8 * SR); t = np.arange(n) / SR
        w = (np.sin(2 * np.pi * (200 + 1500 * t) * t) + 0.5 * np.sign(np.sin(2 * np.pi * (100 + 700 * t) * t))) * np.exp(-t * 2) * 0.35
    elif name == "ko":
        n = int(1.2 * SR); t = np.arange(n) / SR
        w = np.sign(np.sin(2 * np.pi * (220 * np.exp(-t * 2)) * t)) * np.exp(-t * 2.5) * 0.4
    else:
        n = int(0.1 * SR); w = np.zeros(n)
    stereo = np.stack([w, w], axis=1)
    snd = pygame.sndarray.make_sound((np.clip(stereo, -1, 1) * 32000).astype(np.int16))
    _cache[name] = snd
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
