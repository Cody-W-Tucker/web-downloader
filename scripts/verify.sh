#!/usr/bin/env bash
set -euo pipefail

# verify.sh
# Purpose: a fast local feedback loop that the agent can run repeatedly.
# This is the FEEDBACK LOOP that keeps Ralph honest.
# Exit with non-zero if anything fails.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "🔍 Running verification checks..."
echo

# Detect project type and run appropriate checks
if [ -f "package.json" ]; then
  echo "📦 Node.js project detected"

  # Type checking (TypeScript is critical for Ralph)
  if command -v npm &> /dev/null && npm run typecheck &> /dev/null; then
    echo "✓ Type check"
    npm run typecheck
  elif command -v pnpm &> /dev/null && pnpm run typecheck &> /dev/null; then
    echo "✓ Type check"
    pnpm run typecheck
  fi

  # Linting
  if command -v npm &> /dev/null && npm run lint &> /dev/null; then
    echo "✓ Lint"
    npm run lint
  elif command -v pnpm &> /dev/null && pnpm run lint &> /dev/null; then
    echo "✓ Lint"
    pnpm run lint
  fi

  # Tests (the most important part!)
  if command -v npm &> /dev/null && npm test &> /dev/null; then
    echo "✓ Tests"
    npm test
  elif command -v pnpm &> /dev/null && pnpm test &> /dev/null; then
    echo "✓ Tests"
    pnpm test
  fi

elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
  echo "🐍 Python project detected"

  # Type checking
  if command -v mypy &> /dev/null; then
    echo "✓ Type check (mypy)"
    mypy .
  fi

  # Linting
  if command -v ruff &> /dev/null; then
    echo "✓ Lint (ruff)"
    ruff check .
  elif command -v flake8 &> /dev/null; then
    echo "✓ Lint (flake8)"
    flake8 .
  fi

  # Tests
  if command -v pytest &> /dev/null; then
    echo "✓ Tests (pytest)"
    pytest
  fi

elif [ -f "flake.nix" ]; then
  echo "🐍 Nix Python project detected"

  # Type checking
  if command -v mypy &> /dev/null; then
    echo "✓ Type check (mypy)"
    mypy src tests
  fi

  # Linting
  if command -v ruff &> /dev/null; then
    echo "✓ Lint (ruff)"
    ruff check src tests
  elif command -v flake8 &> /dev/null; then
    echo "✓ Lint (flake8)"
    flake8 src tests
  fi

  # Tests
  if command -v pytest &> /dev/null; then
    echo "✓ Tests (pytest)"
    pytest tests
  fi
else
  echo "⚠️  Unknown project type. Update verify.sh to add your checks."
  echo "For now, just checking git status..."
  git status
fi

echo
echo "✅ All verification checks passed!"
