#!/bin/bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm --prefix frontend ci --no-audit --no-fund
npm --prefix frontend run build
chmod +x Run_Clip_Assassin.command
echo "Installation complete. Launch Run_Clip_Assassin.command."
