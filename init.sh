#!/usr/bin/env bash
set -euo pipefail

# init.sh
# Purpose: start or restart the dev environment reliably.
# The initializer agent should update this file to match your stack.

# Set up Python virtual environment and install dependencies
# Assumes Python is available (e.g., via nix develop)
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Dev environment ready!"
