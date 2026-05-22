# Google Alerts AI Curator — Implementation Plan

## Phase 0 — Project Setup
- [ ] Create project folder
- [ ] Add `src/`, `tests/`, `data/`
- [ ] Add `requirements.txt`
- [ ] Add `.env.example`
- [ ] Add `.github/workflows/google-alerts-curator.yml`

## Phase 1 — Core Data Model
- [ ] Define `Article` model
- [ ] Define `CuratedArticle` model
- [ ] Decide required fields:
  - title
  - source
  - url
  - snippet
  - relevance_score
  - why_selected
  - korean_summary
  - career_market_insight

## Phase 2 — Gmail Fetcher
- [ ] Connect to Gmail IMAP
- [ ] Search Google Alerts emails from last 24 hours
- [ ] Extract HTML body
- [ ] Return list of raw email HTML strings
- [ ] Add safe logging without secrets

## Phase 3 — Google Alerts Parser
- [ ] Parse HTML with BeautifulSoup
- [ ] Extract article candidates
- [ ] Extract title, source, link, snippet
- [ ] Tolerate missing fields
- [ ] Add fixture-based parser tests

## Phase 4 — URL Normalization
- [ ] Normalize Google redirect URLs
- [ ] Remove tracking parameters
- [ ] Canonicalize URLs for deduplication
- [ ] Add URL normalization tests

## Phase 5 — Deduplication
- [ ] Use `data/processed_urls.json`
- [ ] Store SHA256 hash of normalized URLs
- [ ] Filter already processed articles
- [ ] Update state only after successful Telegram delivery
- [ ] Add dedup tests

## Phase 6 — LLM Curator
- [ ] Build relevance scoring prompt
- [ ] Score articles against personal interests
- [ ] Select only score >= 8
- [ ] Select maximum 3 articles
- [ ] Generate Korean summary and insight
- [ ] Add prompt structure tests

## Phase 7 — Telegram Message Builder
- [ ] Format daily digest
- [ ] Keep original article title
- [ ] Use Korean for summary, why selected, and insight
- [ ] Skip message if no high-signal articles
- [ ] Add formatting tests

## Phase 8 — Telegram Sender
- [ ] Send message through Telegram Bot API
- [ ] Handle API failure safely
- [ ] Avoid logging token or chat ID

## Phase 9 — GitHub Actions
- [ ] Add daily cron: `0 0 * * *`
- [ ] Add manual trigger
- [ ] Load secrets:
  - GMAIL_EMAIL
  - GMAIL_APP_PASSWORD
  - OPENAI_API_KEY
  - TELEGRAM_BOT_TOKEN
  - TELEGRAM_CHAT_ID
- [ ] Install dependencies
- [ ] Run tests before execution
- [ ] Run curator script

## Phase 10 — End-to-End Dry Run
- [ ] Run locally with test HTML fixture
- [ ] Run GitHub Actions manually
- [ ] Confirm Telegram output
- [ ] Confirm dedup state updates
- [ ] Confirm repeated run does not resend same articles