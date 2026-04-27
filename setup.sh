#!/usr/bin/env bash
set -euo pipefail

echo "=== agent-company setup (no Docker, SQLite local) ==="

command -v python3 >/dev/null 2>&1 || { echo "Python 3 required"; exit 1; }
command -v pip >/dev/null 2>&1    || { echo "pip required"; exit 1; }

if [ ! -f .env ]; then
  echo "ERROR: .env not found. Run: cp .env.example .env and fill in your keys."
  exit 1
fi

required_keys=(
  ANTHROPIC_API_KEY
  OPENROUTER_API_KEY
  SLACK_BOT_TOKEN
  SLACK_SIGNING_SECRET
)

missing=()
for key in "${required_keys[@]}"; do
  val=$(grep "^${key}=" .env | cut -d= -f2- | tr -d ' ')
  if [ -z "$val" ]; then
    missing+=("$key")
  fi
done

if [ ${#missing[@]} -gt 0 ]; then
  echo "ERROR: Missing required keys in .env:"
  printf '  %s\n' "${missing[@]}"
  exit 1
fi

echo "✓ .env validated"

echo "Installing Python dependencies..."
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# ── SQLite setup ───────────────────────────────────────────────────────────────
DB_PATH=$(grep "^DB_PATH=" .env | cut -d= -f2- | tr -d ' ')
DB_PATH=${DB_PATH:-./agentcompany.db}

echo "Initializing SQLite DB at $DB_PATH..."
python3 -c "
import os
os.environ.setdefault('DB_PATH', '$DB_PATH')
from company.ceo.memory import init_schema
init_schema('memory/schema.sql')
print('✓ Schema applied')
"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Start the Slack bot:"
echo "  python interfaces/slack_bot.py"
echo ""
echo "Or use the CLI:"
echo "  python interfaces/cli.py --interactive"
