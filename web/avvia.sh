#!/bin/sh
# NightKnight: la prima volta prepara Python e le librerie del gioco, poi lo avvia.
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "Prima volta: installo le librerie del gioco, ci vuole qualche minuto..."
  python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt || exit 1
fi
exec .venv/bin/python goblin.py "$@"
