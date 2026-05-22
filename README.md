# Google Alerts AI Curator

Google Alerts AI Curator fetches recent Google Alerts emails from Gmail, parses article links, removes URLs that were already processed, asks an OpenAI model to select high-signal articles, and sends a concise plain-text digest to Telegram.

## Pipeline Flow

1. Fetch recent Google Alerts HTML emails from Gmail IMAP.
2. Parse candidate article links from each email.
3. Normalize URLs and remove duplicates.
4. Filter already processed URLs with the deduplication store.
5. Curate new articles with OpenAI.
6. Build a Telegram message for selected high-signal articles.
7. Send the message to Telegram.
8. Mark URLs as processed only after a successful Telegram send.
9. Save deduplication state.

## Local Setup

Create and activate a Python environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Set the required environment variables before running locally:

```bash
export GMAIL_EMAIL="your-email@gmail.com"
export GMAIL_APP_PASSWORD="your-gmail-app-password"
export OPENAI_API_KEY="your-openai-api-key"
export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
export TELEGRAM_CHAT_ID="your-telegram-chat-id"
```

Run the app:

```bash
python -m src.main
```

## Required GitHub Secrets

Configure these repository secrets in GitHub Actions:

- `GMAIL_EMAIL`
- `GMAIL_APP_PASSWORD`
- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Gmail IMAP Requirements

The Gmail account used by the workflow must have:

- IMAP enabled
- 2-Step Verification enabled
- A Gmail App Password created for this app

Use the app password as `GMAIL_APP_PASSWORD`; do not use your normal Gmail password.

## GitHub Actions Schedule

The workflow runs on this cron schedule:

```yaml
0 0 * * *
```

This is 09:00 KST.

## Manual Run

To run manually in GitHub:

1. Open the repository on GitHub.
2. Go to the **Actions** tab.
3. Select **Google Alerts AI Curator**.
4. Click **Run workflow**.

To run manually locally, set the environment variables and run:

```bash
python -m src.main
```

## Testing

Run the test suite with:

```bash
python -m pytest
```

## Security Notes

- Never commit secrets, tokens, app passwords, or API keys.
- Do not log credentials.
- The app prints only minimal operational status messages.
- GitHub Actions reads credentials from repository secrets.

## Deduplication Behavior

Processed URLs are stored in:

```text
data/processed_urls.json
```

The store saves SHA256 hashes of normalized URLs, not raw URLs. URLs are marked as processed only after a successful Telegram send, so failed sends do not suppress articles from a future run.
