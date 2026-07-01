# Google Alerts AI Curator v1

## Vision

Google Alerts AI Curator v1 is not an AI summarizer.

Its purpose is to reduce decision time, not reading time. Google Alerts discovers relevant AI and technology articles. The selector determines which articles deserve attention, then Telegram presents a compact decision-focused digest.

The reader should be able to scan the message quickly and decide what to open.

## Major Changes

Earlier versions were closer to a verbose explanation layer:

- generic rule explanations
- Google Alerts snippets in the message
- `Why it Matters` blocks
- long Telegram cards

Version 1 moves to a cleaner no-LLM baseline:

- deterministic event-based selector
- reader-facing recommendation evidence
- compact Telegram cards
- decision-focused UX
- HTML `Read` links
- free-first operation
- no-LLM baseline when `OPENAI_API_KEY` is not configured

## Engineering Decisions

### Leverage Before Expansion

The project uses the information Google Alerts already provides before adding heavier systems. Title, source, URL, and snippet are enough to make useful first-pass ranking decisions.

### Event-Type Detection

The selector favors concrete news structures over broad AI buzzwords. Examples include pricing changes, semiconductor supply-chain signals, government or regulatory events, security incidents, enterprise adoption, infrastructure investment, and investment or IPO activity.

### Recommendation Evidence

The selector records reader-facing recommendation reasons separately from internal scoring math. Telegram shows compact `Key Signals` instead of exposing score formulas or developer-facing labels.

### Structural Signals

The scoring model prioritizes trusted sources and structural cues that help identify articles worth opening. Low-value patterns such as listicles, vague stock-pumping language, rumor framing, and clickbait-style wording are penalized internally.

### Minimal-Diff Philosophy

The release keeps the architecture small and testable. Improvements are made in narrow layers: parsing, selection, message building, and sending remain separate.

## Current Constraints

The no-LLM baseline uses only:

- article title
- source
- URL
- Google Alerts snippet

It does not read the full article body.

It does not require an LLM.

Because the selector only sees limited metadata, the Telegram message does not pretend to summarize or interpret the full article.

## Future Roadmap

Potential future improvements:

- URL-derived display date when reliably available
- better structural signal coverage
- stronger selector tuning from fixture reviews
- optional LLM layer for richer interpretation
- better title translation as an optional presentation layer

The default path should remain deterministic, free-first, and useful without external paid APIs.
