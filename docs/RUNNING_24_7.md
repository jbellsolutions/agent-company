# Running 24/7

The bot only works when its process is running. Here are the four sane ways to keep it alive.

---

## TL;DR

| You want… | Use this |
|---|---|
| Quick hack while testing | `nohup` (5 minutes) |
| Local Mac, survives reboots | **launchd plist** (Recommended for laptop) |
| Linux server / VPS | systemd unit |
| Cloud, no machine to manage | Railway (Recommended for production) |

---

## Option 1 — `nohup` (testing only)

```bash
cd ~/Desktop/agent-company
nohup python3 interfaces/slack_bot.py > bot.log 2>&1 &
echo $! > bot.pid
```

The bot keeps running after you close the terminal. To stop:
```bash
kill $(cat bot.pid)
```

**Won't survive a reboot.** Fine for a few hours of testing; not real production.

---

## Option 2 — launchd plist (Mac, recommended for laptop / Mac mini)

Create `~/Library/LaunchAgents/com.usingaitoscale.agentcompany.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.usingaitoscale.agentcompany</string>

  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/justinbellware/Desktop/agent-company/interfaces/slack_bot.py</string>
  </array>

  <key>WorkingDirectory</key>
  <string>/Users/justinbellware/Desktop/agent-company</string>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>/Users/justinbellware/Desktop/agent-company/bot.log</string>

  <key>StandardErrorPath</key>
  <string>/Users/justinbellware/Desktop/agent-company/bot.err.log</string>
</dict>
</plist>
```

Load and start:
```bash
launchctl load -w ~/Library/LaunchAgents/com.usingaitoscale.agentcompany.plist
```

To stop:
```bash
launchctl unload ~/Library/LaunchAgents/com.usingaitoscale.agentcompany.plist
```

To restart (e.g., after pulling a code update):
```bash
launchctl unload ~/Library/LaunchAgents/com.usingaitoscale.agentcompany.plist
launchctl load -w ~/Library/LaunchAgents/com.usingaitoscale.agentcompany.plist
```

The bot now starts on login, restarts if it crashes, and survives reboots.

**Caveat:** if your Mac sleeps, the bot pauses too. For a laptop you close at night, the bot only runs while open. For 24/7, run on a Mac mini you leave plugged in (and uncheck "Put hard disks to sleep" in System Settings → Battery / Energy Saver), or use Railway.

---

## Option 3 — systemd (Linux VPS, e.g., DigitalOcean)

SSH into your VPS, clone the repo, fill in `.env`, run `./setup.sh`. Then:

`/etc/systemd/system/agentcompany.service`:
```ini
[Unit]
Description=Agent Company Slack bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/agent-company
ExecStart=/usr/bin/python3 /home/youruser/agent-company/interfaces/slack_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/agentcompany.log
StandardError=append:/var/log/agentcompany.err.log

# Load env vars from .env
EnvironmentFile=/home/youruser/agent-company/.env

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable agentcompany
sudo systemctl start agentcompany
```

Check status:
```bash
sudo systemctl status agentcompany
sudo journalctl -u agentcompany -f   # live logs
```

Restart after code update:
```bash
cd ~/agent-company && git pull && sudo systemctl restart agentcompany
```

---

## Option 4 — Railway (cloud, recommended for production)

Easiest cloud option. The repo includes `infra/Dockerfile` and `infra/railway.toml`.

### One-time setup
1. Sign up at [railway.app](https://railway.app) (you mentioned you already have a paid plan)
2. Install the CLI:
   ```bash
   npm install -g @railway/cli
   railway login
   ```
3. Link the repo:
   ```bash
   cd ~/Desktop/agent-company
   railway init    # creates a Railway project
   ```
4. Set env vars (Railway needs them set explicitly — your local `.env` doesn't auto-sync):
   ```bash
   railway variables set ANTHROPIC_API_KEY="sk-ant-..."
   railway variables set OPENROUTER_API_KEY="sk-or-..."
   railway variables set COMPOSIO_API_KEY="ak_..."
   railway variables set SLACK_BOT_TOKEN="xoxb-..."
   railway variables set SLACK_SIGNING_SECRET="..."
   railway variables set SLACK_APP_TOKEN="xapp-..."
   railway variables set DB_PATH="/data/agentcompany.db"
   ```
5. Add a persistent volume (so your SQLite DB survives deploys):
   - Railway dashboard → your service → **Volumes** → **+ New Volume**
   - Mount path: `/data`
6. Deploy:
   ```bash
   railway up
   ```

### Updating
After pushing changes to GitHub:
```bash
railway up
```

Or set up GitHub auto-deploy in the Railway dashboard so every commit to `main` triggers a deploy.

### Logs
```bash
railway logs --tail
```

Or in the Railway dashboard → service → **Deployments** → click any deploy → **Logs**.

### Cost
Railway charges based on usage. A bot like this uses:
- ~256 MB RAM
- minimal CPU (only spikes when handling DMs)
- a tiny volume for SQLite

Expect ~$5-10/month for the bot itself. LLM costs (Anthropic + OpenRouter) are separate and usage-based.

---

## Hybrid: SQLite locally, Postgres on Railway

If you outgrow SQLite (multiple parallel workers, contention), switch the prod DB to a hosted Postgres (Neon's free tier is excellent).

1. Create a Postgres on [neon.tech](https://neon.tech)
2. Copy the connection string
3. In Railway: `railway variables set DATABASE_URL="postgres://..."`
4. Update `company/ceo/memory.py` to detect: if `DATABASE_URL` starts with `postgres://`, use psycopg2; else SQLite. (~30 lines.)
5. Re-add `psycopg2-binary` to `requirements.txt`.

Local dev stays on SQLite (zero setup); prod uses Postgres (concurrent-safe).

---

## What about Docker?

The repo ships an `infra/Dockerfile` for cloud platforms that require it (Railway uses it). For local dev, **don't bother** — Docker eats laptop resources. SQLite + native Python is faster and simpler.

If you do want Docker locally:
```bash
docker build -f infra/Dockerfile -t agent-company .
docker run --env-file .env -v $(pwd):/app agent-company
```

But again — the whole point of the SQLite redesign was to skip this.

---

## Monitoring

Once 24/7, watch for:

1. **The bot is alive**: write a tiny health-check script that DMs the bot and verifies a reply. Run it via cron every 15 minutes; alert if no reply.
2. **API quotas**: console.anthropic.com → set $X/day alert. openrouter.ai → spend cap.
3. **Disk space** (if SQLite): `du -h agentcompany.db` — should grow slowly. If it explodes, check for a runaway loop.
4. **Logs**: rotate them. `bot.log` will grow forever otherwise.

For real production, wire up:
- **Sentry** for exception tracking (3 lines of code)
- **Better Stack / Datadog** for log aggregation
- **A simple uptime ping** (UptimeRobot, free) hitting a `/health` endpoint you add to the bot

But for solo / small-team use, just `tail -f bot.log` is enough.
