"""Salvataggio atomico del checkpoint di sezione e del record locale."""
import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent / "savegame.json"


def load(path=DEFAULT_PATH):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"high_score": 0, "checkpoint": None}
    if not isinstance(data, dict):
        return {"high_score": 0, "checkpoint": None}
    hi = data.get("high_score", 0)
    if type(hi) is not int or hi < 0:
        hi = 0
    cp = data.get("checkpoint")
    if not (isinstance(cp, dict)
            and cp.get("cemetery") == 0
            and cp.get("part") in ("surface", "arena")
            and type(cp.get("lives")) is int and 1 <= cp["lives"] <= 3
            and type(cp.get("score")) is int and cp["score"] >= 0):
        cp = None
    return {"high_score": hi, "checkpoint": cp}


def save(data, path=DEFAULT_PATH):
    path = Path(path)
    temp = path.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
    except OSError as exc:
        # Un disco non scrivibile non deve interrompere la partita.
        return str(exc)
    return None
