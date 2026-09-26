#!/usr/bin/env bash
# Start Bid Remote (run the setup steps in README.md first).
cd "$(dirname "$0")"
source .venv/bin/activate
exec python app.py
