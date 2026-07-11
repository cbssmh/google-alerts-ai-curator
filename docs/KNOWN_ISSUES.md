# Known Issues

This document tracks non-blocking product quality issues that should inform
future releases without changing the current release boundary.

## Korean Supporting Title May Be Omitted for Person/Company/Event-Style Headlines

Severity: Low / P3

Target: v2.1

### Summary

For some English headline shapes, `korean_title` may remain empty and the
Telegram article card may omit the Korean supporting title.

Observed example:

```text
Andrew Feldman, Cerebras Systems | RAISE Summit 2026
```

Observed result:

- Original title is rendered.
- Preview is rendered.
- Article-to-landscape explanation is rendered.
- Only the Korean supporting title is omitted.

### Impact

- System execution is not affected.
- Telegram delivery succeeds.
- Daily Landscape generation succeeds.
- The Reading Decision flow remains usable.
- Korean readability is reduced for the affected article card only.

### Current Evidence

Confirmed facts:

- The same article reproduced the behavior before and after the message UX
  tuning.
- The message builder renders a non-empty `korean_title` normally.
- The raw LLM JSON from the observed run was not retained, so it is not yet
  confirmed whether the value was empty in the LLM response or removed during
  validation.
- Current validation removes non-string, whitespace-only, and over-45-character
  `korean_title` values.
- The production workflow and tests passed.

GitHub Actions evidence:

- 181 tests passed.
- Sent 3 curated articles.

Uploaded PDF evidence is not stored in this repository.

### Likely Scope

This may affect headlines centered on:

- Person names.
- Company names.
- Event names.

This is a hypothesis, not a confirmed root cause. The issue may be model output,
validation behavior, or the interaction between the prompt and this headline
shape.

### Deferred Rationale

This is not a 2.0 release blocker because:

- The core 2.0 value is Daily Landscape plus Reading Decision.
- Original title, preview, article explanation, and link are all present.
- The observed impact is limited to one article-card readability field.
- Keeping one-off diagnostic code in production paths has higher maintenance
  cost than the current impact justifies.
- More operational samples are needed before choosing a v2.1 fix.

### v2.1 Investigation Plan

1. Collect at least three samples with the same headline style.
2. Compare raw LLM output in a safe diagnostic environment.
3. Determine whether the missing title is caused by raw empty output or
   validation removal.
4. Review whether prompt guidance should be strengthened.
5. Review whether the 45-character hard cutoff is too strict.
6. Add regression fixtures for person/company/event-style titles.
7. Review neutral fallback wording that does not add unsupported claims.

Safe fallback example:

```text
앤드루 펠드먼·Cerebras Systems, RAISE Summit 2026
```

Unsupported fallback wording must not add roles or events absent from the source
title or snippet, such as:

- CEO
- 발표
- 전략
- 인터뷰

If a role or event is not grounded in the title or snippet, it must not be added.

## GitHub Issue Draft

Title:

```text
Korean supporting title may be omitted for person/company/event headlines
```

Labels:

```text
bug, quality, llm, v2.1
```

Body:

```markdown
## Observed behavior

In one production Telegram run, the article:

Andrew Feldman, Cerebras Systems | RAISE Summit 2026

rendered the original title, preview, article-to-landscape explanation, and link,
but did not render a Korean supporting title.

## Expected behavior

Person/company/event-style headlines should receive a grounded Korean supporting
title when the source title/snippet provide enough information.

## Impact

- Severity: Low / P3
- Telegram delivery succeeded.
- Daily Landscape succeeded.
- Reading Decision remained usable.
- Only one article card had reduced Korean readability.

## Known evidence

- The behavior appeared before and after the message UX tuning.
- The builder renders non-empty `korean_title` values normally.
- Current validation removes non-string, whitespace-only, and over-45-character
  `korean_title` values.
- The raw LLM JSON from the observed run was not retained.
- Production workflow passed with 181 tests and sent 3 curated articles.

## Unknowns

- Whether the raw LLM response used an empty `korean_title`.
- Whether validation removed a generated title.
- Whether this is specific to person/company/event-style headlines.
- Whether prompt guidance or validation constraints should be adjusted.

## Acceptance criteria

- Confirm whether the root cause is raw LLM output or validation removal.
- Generate grounded `korean_title` values for person/company/event-style titles.
- Do not add unsupported roles or events absent from the title/snippet.
- Keep existing title validation and builder regressions passing.
- Full test suite passes.
```
