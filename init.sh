#!/usr/bin/env bash
set -euo pipefail

# init.sh
# Purpose: Enter the Nix-managed development environment

echo "Entering Nix development shell..."
exec nix develop
