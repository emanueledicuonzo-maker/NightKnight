@echo off
rem NightKnight: la prima volta prepara Python e le librerie del gioco, poi lo avvia.
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Prima volta: installo le librerie del gioco, ci vuole qualche minuto...
  py -3 -m venv .venv 2>nul || python -m venv .venv
  .venv\Scripts\python -m pip install -r requirements.txt
)
.venv\Scripts\python goblin.py %*
if errorlevel 1 pause
