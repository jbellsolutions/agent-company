# Slack App Setup

5-minute walkthrough to create the Slack app the bot uses. You'll end up with three tokens that go in `.env`.

---

## Step 1 — Create the app

1. Go to **[api.slack.com/apps](https://api.slack.com/apps)**
2. Click **Create New App** → **From scratch**
3. App name: `Agent Company` (or whatever you want)
4. Pick your workspace → **Create App**

---

## Step 2 — Enable Socket Mode (no public URL needed)

Socket Mode lets the bot talk to Slack via a persistent WebSocket. You don't need to expose a public URL or run a webhook — perfect for local + Railway.

1. Left sidebar → **Socket Mode**
2. Toggle **Enable Socket Mode** ON
3. It'll prompt for an **App-Level Token name** — name it `socket-token` and add scope `connections:write`
4. Click **Generate** → copy the token (starts with `xapp-`)

→ This is your **`SLACK_APP_TOKEN`**.

---

## Step 3 — Add bot scopes

1. Left sidebar → **OAuth & Permissions**
2. Scroll to **Bot Token Scopes** → **Add an OAuth Scope**
3. Add each of these:
   - `app_mentions:read` — see when someone @mentions the bot
   - `chat:write` — post messages
   - `im:history` — read DMs sent to the bot
   - `im:read` — see DM channel info
   - `im:write` — start DMs

---

## Step 4 — Subscribe to events

1. Left sidebar → **Event Subscriptions**
2. Toggle **Enable Events** ON
3. Under **Subscribe to bot events**, add:
   - `message.im` — fires when you DM the bot
   - `app_mention` — fires when someone @mentions the bot in a channel
4. Click **Save Changes** at the bottom

---

## Step 5 — Install the app to your workspace

1. Left sidebar → **Install App** → **Install to Workspace**
2. Click **Allow** on the permissions screen
3. You'll be redirected back. Copy the **Bot User OAuth Token** (starts with `xoxb-`).

→ This is your **`SLACK_BOT_TOKEN`**.

---

## Step 6 — Grab the signing secret

1. Left sidebar → **Basic Information**
2. Scroll to **App Credentials**
3. Click **Show** next to **Signing Secret** → copy.

→ This is your **`SLACK_SIGNING_SECRET`**.

---

## Step 7 — Drop them into `.env`

```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...
```

---

## Step 8 — Run the bot

```bash
python interfaces/slack_bot.py
```

You should see:
```
INFO:__main__:Starting Slack bot in Socket Mode...
INFO:slack_bolt.App:⚡️ Bolt app is running!
```

The bot will now appear in your Slack sidebar under **Apps**. Click it → DM something. It'll reply.

---

## Troubleshooting

**Bot doesn't reply when you DM it.**
- Check the terminal for errors. Most common: missing event subscription (Step 4) or scope (Step 3).
- After adding scopes or events, you have to **reinstall the app** (Step 5).

**`socket_mode` connection error.**
- Wrong `SLACK_APP_TOKEN`. Regenerate in **Basic Information** → **App-Level Tokens**.

**Bot replies in channels but not DMs.**
- Missing `im:history`, `im:read`, or `message.im` event.

**Connection drops after 30 minutes.**
- Slack-side issue, very rare. The bot auto-reconnects via Socket Mode.

---

## Production: HTTP mode instead of Socket Mode

If you deploy to Railway/Render/Fly.io and want HTTP webhooks instead of Socket Mode:

1. Disable Socket Mode in your app settings.
2. Set `SLACK_APP_TOKEN=` (empty) in your env.
3. The bot will start in HTTP mode on port 3000.
4. Configure your Slack app's **Event Subscriptions** → **Request URL** to point at `https://your-app.railway.app/slack/events`.

But honestly: Socket Mode works on Railway too. Less setup, fewer moving parts.
