# Google Alerts AI Curator — Project Standard

## 1. Project Intent

Google Alerts AI Curator is a personal, free-first technology news curation system.

The purpose of this project is **not** to summarize every article delivered by Google Alerts.

The purpose is to reduce noise and deliver only the highest-signal technology articles through Telegram.

The question this project should answer every day is:

> Which articles are actually worth reading today, and why?

This project should behave as a lightweight personal technology curator rather than a generic news notifier.

---

## 2. Current Product Direction

The project follows three guiding principles.

### Free-first

The baseline version must work without paid services.

### Stability-first

The current pipeline already works in production.

Do not redesign stable components unless there is a strong technical reason.

### Minimal-diff

Improve message quality with the smallest possible change.

Architecture rewrites are not the current goal.

---

## Leverage Before Expansion

Before introducing a new service, dependency, API, scraper, database, or LLM step, first check whether the required signal already exists inside the current pipeline.

The project should prefer:

- using existing Google Alerts email data
- improving parser quality
- improving deterministic selection
- improving message structure
- adding tests around existing flows

before expanding to:

- full article scraping
- paid LLM APIs
- external automation platforms
- databases
- SaaS tools
- new infrastructure

Good engineering is not adding more tools by default.

Good engineering is extracting more value from existing constraints.

The practical analogy is simple: improve the outfit using the clothes already in the closet before buying expensive new clothes. In engineering terms, current inputs should be fully inspected, parsed, tested, and proven insufficient before the project expands its toolchain.

Constraints should produce clarity, not excuses.

Expansion should happen only after the current pipeline has been fully used and still cannot meet the product need.

---

## 3. Core User Need

The user does **not** need more notifications.

The user needs **better notifications.**

A successful Telegram message should make the user think:

> "I'm glad I opened this."

A failed message is one that only says things like:

- AI Infrastructure signal exists
- Platform Shift signal exists
- This may change the market

Those statements provide little value.

---

## 4. Constraints

### 4.1 Free-first Constraint

The current version must use only free services.

Allowed services:

- Google Alerts
- Gmail
- GitHub Actions
- GitHub Secrets
- Telegram Bot API
- Local JSON files
- Python open-source libraries

Not required:

- Paid LLM APIs
- Paid databases
- Paid hosting
- Paid scraping services

LLMs may become an optional feature later.

However, the baseline system must work without them.

---

### 4.2 Stability-first Constraint

The existing production pipeline should remain unchanged whenever possible.

The following components should be preserved:

- Gmail IMAP fetching
- Google Alerts email input
- URL normalization
- Deduplication
- Telegram sender
- GitHub Actions workflow
- Secret management
- Main orchestration flow

Message quality should improve without redesigning these components.

---

### 4.3 Minimal-diff Constraint

Changes should be:

- small
- reviewable
- easy to rollback
- easy to test

Avoid:

- architecture rewrites
- new infrastructure
- new databases
- new schedulers
- full article scraping
- mandatory LLM usage

Prefer:

- parser improvements
- scoring improvements
- message formatting improvements
- better tests

---

## 5. Current Architecture

Current production flow:

~~~text
Google Alerts
  ↓
Gmail
  ↓
GitHub Actions
  ↓
Python Pipeline
  ↓
HTML Parsing
  ↓
URL Normalization
  ↓
Deduplication
  ↓
Rule-based Selection
  ↓
Telegram Formatting
  ↓
Telegram Delivery
  ↓
State Update
~~~

The rule-based path is the required baseline.

The LLM path is optional.

---

## 6. Service Decisions

### Google Alerts

Purpose:

- Free article discovery
- No crawler maintenance
- Structured email delivery

Limitations:

- Noisy
- Duplicate articles
- SEO-heavy results
- Limited snippets

---

### Gmail

Purpose:

- Receive Google Alerts
- IMAP access
- Compatible with GitHub Actions

Limitations:

- Requires App Password
- Depends on Gmail search behavior

---

### GitHub Actions

Purpose:

- Scheduled execution
- No server required
- Easy secret management

Limitations:

- Ephemeral runtime
- UTC cron
- Local files do not persist automatically

---

### Telegram

Purpose:

- Daily delivery
- Mobile-friendly
- Free HTTP API

Limitations:

- Message length
- Mobile readability

---

### Local JSON State

Purpose:

- Processed URL tracking
- No database required

Limitations:

- State persistence requires care on GitHub Actions

---

### LLM

Current baseline:

- Not required

Future:

- Optional enhancement only

The system must remain useful without any LLM.

---

## 7. Current Problem

The infrastructure is not the problem.

The message quality is.

Current messages include fields such as:

- Selection Reason
- Career / Market Insight

However, they often feel generic.

Current inspection shows why.

Rule-based selection already supports:

- title
- source
- snippet

Earlier versions discarded Google Alerts snippets even though they already existed inside the email HTML.

The parser now extracts those snippets.

This confirmed an important project lesson: before adding article scraping, LLM usage, or new infrastructure, first extract more value from the data already moving through the pipeline.

Remaining message-quality work should build on:

- title
- source
- Google Alerts snippet
- deterministic rule-based reasoning

---

## 8. Improvement Priority

### Phase 1 — Documentation

Define:

- project intent
- constraints
- engineering principles

before changing code.

---

### Phase 2 — Validate the no-LLM production path

Current flow:

~~~text
Fixture Email
  ↓
Parser
  ↓
Rule Selector
  ↓
Message Builder
~~~

Create a reliable baseline.

---

### Phase 3 — Use existing Google Alerts snippets

Use existing email data.

Do **not** fetch article bodies.

Do **not** add network requests.

This was the preferred first improvement because the snippets already existed in the current pipeline.

---

### Phase 4 — Improve rule-based reasoning

Focus on:

- explanation
- signal interpretation
- article-specific evidence
- primary signal selection

using:

- title
- source
- snippet

---

### Phase 5 — Decide message format

Once reasoning has enough evidence, decide how the Telegram message should present:

- selection reason
- evidence
- market / technology insight
- score visibility
- optional summaries

---

### Phase 6 — Tune scoring

Tune scoring only after the message format is stable.

Examples:

- keyword weights
- source weights
- clickbait penalties
- selection thresholds

---

### Phase 7 — Evaluate article body extraction

Only consider this if snippet-based improvements are still insufficient.

If implemented later, it must be:

- optional
- timeout-controlled
- limited to top candidates
- failure-safe
- free

---

### Phase 8 — Consider optional LLM enhancement

LLMs may be useful later for summarization or richer interpretation.

They must remain optional.

The no-LLM rule-based path remains the required baseline.

Do not make paid LLM usage mandatory for the daily production workflow.

---

## 9. Non-Goals

This project is not intended to become:

- a news crawler
- a scraping platform
- a paid LLM summarizer
- a newsletter SaaS
- a stock recommendation engine
- a real-time monitoring platform
- a multi-user service

---

## 10. Message Quality Standard

A useful message should explain:

- what happened
- why it matters
- what signal it represents
- why the reader should care
- whether the article is worth opening

Avoid generic statements.

Weak:

~~~text
Selection Reason:
AI Infrastructure signal exists.
~~~

Better:

~~~text
Why It Matters

Companies are beginning to prioritize AI cost efficiency over maximum model performance.

Evidence

Google Alerts summary mentions increasing AI operating costs and adoption of lower-cost models.

Perspective

Engineers working on AI systems should pay increasing attention to model routing, caching, and inference cost optimization.
~~~

---

## 11. Engineering Rules

Prefer:

- small changes
- explicit logic
- tests
- readable code
- rule-based baseline
- graceful fallback

Avoid:

- speculative redesign
- large refactors
- unnecessary dependencies
- mandatory LLM logic
- network-heavy scraping

---

## 12. Review Checklist

Before implementing any change, ask:

1. Does this preserve the free-first baseline?
2. Does this preserve the stable pipeline?
3. Is the diff small?
4. Can it be tested with fixtures?
5. Does it improve the no-LLM path?
6. Does failure fall back safely?
7. Does it avoid unnecessary services?

If not, reconsider the implementation.

---

## 13. Current Recommended Next Step

The next implementation should be:

> Validate and refine the no-LLM Telegram message format using title, source, and Google Alerts snippets.

Reason:

- Snippet extraction is already available.
- Rule-based reasoning now has more evidence.
- The no-LLM baseline remains the required production path.
- No network requests are required.
- No paid services are required.
- No LLM is required.
- The change is small.
- The change is easy to test.
- The change is easy to rollback.
