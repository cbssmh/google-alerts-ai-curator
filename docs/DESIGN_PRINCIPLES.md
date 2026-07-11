# Google Alerts AI Curator 2.0 Design Principles

## Vision

Google Alerts AI Curator exists to turn a noisy batch of Google Alerts into a
small, grounded briefing that helps the user decide what to read.

The product is not trying to summarize the AI industry. It is trying to make one
daily news intake moment clearer. The useful output is a compact view of what
appeared repeatedly in the selected Google Alerts batch, followed by the
individual articles that are most likely to be worth opening.

## Core Problem

Google Alerts is useful because it is broad, free, and already integrated with
email. It is also noisy. A single run can contain duplicates, SEO-heavy posts,
thin announcements, vague commentary, and unrelated articles that happen to
match the alert terms.

The user does not need more article notifications. The user needs a quick answer
to three questions:

1. What patterns are visible in today's selected alerts?
2. Which articles are worth reading?
3. Why were those articles selected?

The system must answer these questions using only the evidence it actually has:
Google Alerts title, source, snippet, rule-based reasons, and deterministic
selection metadata.

## Product Definition

Google Alerts AI Curator is a grounded reading-decision briefing that identifies
observable patterns in today's selected Google Alerts batch and helps the user
choose which AI news articles to read.

## Product Philosophy

### Why Google Alerts

Google Alerts provides broad, low-maintenance discovery without running a crawler
or maintaining source integrations. It is a pragmatic input source: imperfect,
but cheap, stable, and available through email.

That constraint is intentional. The product should extract value from the
existing alert stream before adding scraping, paid data sources, embeddings, or
external search.

### Why Not a News Summarizer

The system does not read full article bodies. A generic news summarizer would
imply access to article content, author nuance, source context, and the complete
argument of each piece. This project does not have that evidence.

The product therefore must not produce full article summaries, hidden-company
intent, broad market analysis, or conclusions that require reading the full
article.

### Why Reading Decision

The primary job is to reduce the cost of deciding what to read. A useful message
does not need to explain everything. It needs to show enough signal for the user
to decide whether a link deserves attention.

This is why the product keeps article cards short, keeps source links visible,
and treats rule-based selection as the authority for article inclusion.

### Why Today's AI Landscape

"Today's AI Landscape" means the observable repeated patterns inside today's
selected Google Alerts articles.

It is not a claim about the entire AI market. It is not a forecast. It is not a
macro research note. It is a batch-level orientation layer that helps the user
scan what the current run appears to contain.

## Design Principles

### 1. Reading Decision First

The product should help the user decide what to read, not make the message feel
complete for its own sake.

Implementation implications:

- Keep article cards compact.
- Preserve source links as the final action.
- Avoid fields that do not improve the read-or-skip decision.

### 2. Patterns Before Articles

When multiple selected articles share an observable pattern, the message should
surface that pattern before listing individual links.

Implementation implications:

- Put Daily Landscape above article cards when it has content.
- Group repeated themes before showing per-article detail.
- Hide the landscape section when no reliable pattern exists.

### 3. Observable, Not Predictive

The system describes what is present in the selected alerts. It does not predict
what will happen next.

Implementation implications:

- Prefer language such as "related reports appeared together".
- Reject market forecasts, investment implications, and claims about future
  competition.
- Remove unsupported headline, theme, keyword, or entity output.

### 4. Respect the Source

The system should never imply that it has more source access than it actually
has.

Implementation implications:

- Use only title, source, snippet, and rule-based reasons in the LLM prompt.
- Do not claim to have read full article bodies.
- Keep original article titles and source links visible.

### 5. Rule-based Decides

Deterministic logic decides which articles enter the message. The LLM explains
and synthesizes; it does not replace the selector.

Implementation implications:

- URL deduplication remains before selection.
- Rule-based scoring and limits remain the inclusion authority.
- LLM output must not remove, merge, hide, or reorder selected articles.

### 6. Adaptive Intelligence

The product should use the minimum intelligence needed for the current batch. It
should not call or display LLM output just because an LLM is available.

Implementation implications:

- The rule-based path must remain useful without any provider configured.
- Landscape output should appear only when the selected articles support it.
- LLM enhancement should add value through grounded synthesis, not decoration.

### 7. Progressive Enhancement

LLM output is an enhancement layer on top of a stable deterministic product.

Implementation implications:

- If LLM configuration is missing, use the rule-based Telegram message.
- If the LLM fails, falls back to rule-based article cards.
- If only part of the enhancement validates, keep the valid fields and hide the
  invalid ones.

### 8. Grounded Generation

Generated text must be constrained by available evidence.

Implementation implications:

- Evidence must come from title or snippet.
- Keywords and entities must appear in the source title or snippet.
- Empty strings and empty arrays are better than invented detail.

### 9. One LLM Call

The selected batch should be enhanced in one LLM request.

Implementation implications:

- Generate landscape and article enhancement together.
- Do not split trend generation from article card enhancement unless there is a
  measured need.
- Keep the prompt focused on fields that are actually rendered or validated.

### 10. Cost is a Product Feature

Low operating cost is part of the product design, not only an infrastructure
detail.

Implementation implications:

- Preserve the free-first baseline.
- Avoid additional providers, retries, or calls unless they improve the user
  outcome enough to justify the cost.
- Treat token usage, runtime, and provider reliability as product constraints.

### 11. Graceful Degradation

The product should fail toward a useful deterministic message.

Implementation implications:

- API errors, malformed JSON, empty choices, and unusable enhancement output
  should not block delivery of selected articles.
- Strict diagnostics may fail smoke tests, but production should fall back.
- Telegram delivery and dedup state updates remain separate safety boundaries.

### 12. Honest Scope

The product must communicate only what this pipeline can know.

Implementation implications:

- Do not describe the output as a complete AI market view.
- Do not infer author intent, company strategy, investment signals, or career
  advice.
- State product behavior in terms of selected alerts, not all available news.

### 13. Evidence over Fluency

Clear but unsupported text is worse than plain grounded text.

Implementation implications:

- Validate model output after parsing.
- Prefer conservative removal over automatic repair.
- Keep forbidden phrases and low-confidence preview handling.

### 14. Every Section Must Earn Its Place

Sections should appear only when they add distinct information.

Implementation implications:

- Hide headline, themes, keywords, entities, and previews when empty or invalid.
- Do not show internal confidence or evidence fields in Telegram.
- Avoid repeating article titles inside theme sections.

### 15. Design for Scanability

The message should be understandable in a short Telegram glance.

Implementation implications:

- Use a stable order: landscape, themes, keywords, companies, articles.
- Keep labels short and specific.
- Prefer compact lists over paragraph-heavy explanations.

## Adaptive Intelligence

Adaptive Intelligence is the operating principle that the system should adjust
how much intelligence it applies based on the value available in the current
batch.

The presence of an LLM provider does not mean every run deserves a visible
landscape section. A batch with one selected article may benefit from a Korean
title and grounded preview, but it usually cannot support a daily pattern. A
batch with several selected articles may support themes, keywords, and entities
if those fields are directly grounded in the alert metadata.

| Condition | Expected behavior | Reason |
| --- | --- | --- |
| No selected articles | Send nothing | There is no reading decision to support. |
| Selected articles, no LLM provider | Build rule-based Telegram cards | The deterministic baseline remains the product. |
| LLM provider configured, API fails | Fall back to rule-based cards | Delivery should not depend on generation. |
| One selected article | Enhance article fields only when grounded | One article cannot establish a daily pattern. |
| Multiple selected articles, no shared pattern | Hide landscape sections | Empty output is more honest than forced synthesis. |
| Multiple selected articles with repeated evidence | Show headline, themes, keywords, or entities as available | Repeated observable patterns help the user orient quickly. |
| Model returns unsupported terms | Remove invalid fields | Validation protects the product boundary. |

Example behavior:

- If three selected articles mention GPU capacity, HBM, and data center
  investment, the landscape may show an infrastructure theme and grounded
  keywords.
- If three selected articles are unrelated, the message should skip the
  landscape and show only the article cards.
- If the model returns a fluent forecast that is not supported by snippets, the
  forecast should be discarded.

This principle keeps the system from becoming an "LLM because we can" product.
The LLM is used when it creates grounded reader value; otherwise, the stable
rule-based path is enough.

## Today's AI Landscape

Today's AI Landscape is the optional top-level orientation layer in the Telegram
message.

Definition:

> The observable repeated patterns in today's selected Google Alerts articles.

Allowed content:

- A short headline supported by at least two selected articles.
- Two to four specific themes when repeated patterns exist.
- Up to six grounded keywords that appear in source titles or snippets.
- Up to five grounded companies, institutions, products, or model names that
  appear in source titles or snippets.

Disallowed content:

- Claims about the whole AI market.
- Forecasts or predictions.
- Investment advice.
- Career advice.
- Full article summaries.
- Entities, keywords, causes, or outcomes not present in the source metadata.

The landscape is a lens for the current batch. It is not a market report.

## Non-goals

The project does not do the following:

- Full article body summaries.
- Market predictions.
- Investment advice.
- "Why it Matters" commentary.
- Career advice.
- Whole AI market analysis.
- Embedding-based semantic analysis.
- External-search-based analysis.
- Browser automation or paywall handling.
- Long-term trend analysis across weeks or months.

These may sound adjacent to news intelligence, but they require evidence and
systems that this product intentionally does not use.

## Information Hierarchy

The Telegram message should be read in this order:

1. Landscape
2. Theme
3. Keywords
4. Companies
5. Articles

This order moves from orientation to action.

Landscape gives the user the batch-level shape. Themes explain the repeated
areas of attention. Keywords provide quick recognition anchors. Companies and
institutions identify the actors involved. Article cards then support the final
reading decision with titles, grounded previews, selection reasons, and links.

The order is intentionally not source-first. The user first needs to know what
kind of news batch they are looking at, then which links deserve attention.

## Architecture Alignment

The product philosophy maps directly to the current architecture.

### Rule-based Selection

Rule-based selection filters noisy Google Alerts into a small set of candidates.
It uses deterministic scoring, source signals, event categories, low-value
patterns, and a fixed limit. This keeps article inclusion explainable and cheap.

### LLM Enhancement

The LLM receives only selected articles and metadata. It produces optional
article fields and optional Daily Landscape fields in one request. It must keep
article count and order stable.

The parser and validators are part of the product, not just defensive code. They
enforce scope by removing ungrounded fields and falling back when the response is
not usable.

### Telegram Delivery

Telegram is the reading-decision surface. It should show the smallest useful
message: landscape when earned, then article cards. It should not expose internal
confidence, evidence arrays, prompt diagnostics, or implementation details.

### State Update

Dedup state should be saved only after successful delivery. This keeps failed
runs from losing articles before the user receives them.

## Future Direction

### 2.x

2.x work should improve the current batch-level briefing without changing the
core evidence boundary.

Possible directions:

- Better deterministic keyword and entity validation.
- Better theme validation using only selected titles and snippets.
- More precise Telegram scanability limits.
- Smoke tests that verify landscape counts without exposing prompt or secret
  content.
- Documentation alignment across README, prompt, and workflow notes.

### 3.x

3.x may expand the evidence boundary only if the product need clearly requires
it.

Possible directions:

- Optional article-body fetching with explicit source and paywall constraints.
- Historical trend comparison across saved runs.
- User feedback on read-worthiness.
- More advanced deduplication if URL-based dedup is proven insufficient.

Any 3.x expansion must preserve the core rule: the system may only claim what
its evidence can support.

## Decision Standard

Future README updates, prompt changes, architecture changes, and new features
should be checked against these questions:

1. Does this improve the user's reading decision?
2. Is the output grounded in evidence the system actually has?
3. Does rule-based selection remain the authority for article inclusion?
4. Does this keep cost and operational complexity proportional to value?
5. Does the message remain scannable in Telegram?
6. Can the system degrade gracefully when the enhancement layer fails?

If the answer is unclear, the change should be treated as a product design
question before it becomes an implementation task.
