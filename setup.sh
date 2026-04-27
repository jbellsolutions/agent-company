#!/usr/bin/env bash
set -euo pipefail

echo "=== agent-company setup ==="

# ── Prerequisites ──────────────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || { echo "Python 3 required"; exit 1; }
command -v pip >/dev/null 2>&1    || { echo "pip required"; exit 1; }

# ── Validate .env ──────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  echo "ERROR: .env not found. Run: cp .env.example .env and fill in your keys."
  exit 1
fi

required_keys=(
  ANTHROPIC_API_KEY
  OPENROUTER_API_KEY
  COMPOSIO_API_KEY
  SLACK_BOT_TOKEN
  SLACK_SIGNING_SECRET
)

missing=()
for key in "${required_keys[@]}"; do
  val=$(grep "^${key}=" .env | cut -d= -f2 | tr -d ' ')
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

# ── Python deps ────────────────────────────────────────────────────────────────
echo "Installing Python dependencies..."
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# ── Database setup ─────────────────────────────────────────────────────────────
source .env
if [ -n "${DATABASE_URL:-}" ]; then
  echo "Running database migrations..."
  python -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
with open('memory/schema.sql') as f:
    conn.cursor().execute(f.read())
conn.commit()
conn.close()
print('✓ Database schema applied')
"
else
  echo "⚠ DATABASE_URL not set — skipping DB setup (required for production)"
fi

# ── Railway deploy (optional) ─────────────────────────────────────────────────
if command -v railway >/dev/null 2>&1; then
  echo ""
  read -p "Deploy to Railway now? [y/N] " deploy
  if [[ "$deploy" =~ ^[Yy]$ ]]; then
    railway up
    echo "✓ Deployed to Railway"
    echo ""
    echo "Set your env vars in Railway dashboard, then:"
    echo "  railway variables set ANTHROPIC_API_KEY=... OPENROUTER_API_KEY=... etc."
  fi
else
  echo "ℹ Railway CLI not found. To deploy: npm install -g @railway/cli && railway up"
fi

echo ""
echo "=== Setup complete ==="
echo "Local: docker-compose up"
echo "CLI:   python interfaces/cli.py \"set up SDR fleet\""
echo "Slack: DM your bot to get started"
