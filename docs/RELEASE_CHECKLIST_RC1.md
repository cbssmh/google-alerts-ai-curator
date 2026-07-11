# Google Alerts AI Curator 2.0 RC1 Checklist

## Release Candidate Scope

RC1 prepares the existing 2.0 pipeline for production operation with NVIDIA
Mistral enhancement.

Target runtime flow:

```text
Google Alerts email
-> Gmail IMAP
-> parser
-> URL dedup
-> rule-based selector
-> Mistral enhancement
-> Daily Landscape and article cards
-> Telegram
-> processed URL save after successful send
```

This release candidate does not add new product features. It verifies the
implemented 2.0 architecture and switches the production workflow to the same
variable-driven NVIDIA provider configuration used by the smoke workflow.

## Required GitHub Configuration

Repository Variables:

| Name | RC1 value |
| --- | --- |
| `LLM_PROVIDER` | `nvidia` |
| `NVIDIA_MODEL` | `mistralai/mistral-medium-3.5-128b` |
| `NVIDIA_TIMEOUT_SECONDS` | `60` or higher if production runs need more margin |
| `NVIDIA_BASE_URL` | Optional; leave empty to use `https://integrate.api.nvidia.com/v1` |
| `OPENAI_MODEL` | Optional fallback setting for OpenAI provider |

Repository Secrets:

| Name | Purpose |
| --- | --- |
| `GMAIL_EMAIL` | Gmail account used for Google Alerts ingestion |
| `GMAIL_APP_PASSWORD` | Gmail app password for IMAP |
| `NVIDIA_API_KEY` | NVIDIA Build NIM API key |
| `OPENAI_API_KEY` | Optional OpenAI fallback key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram target chat |

## Operational Workflow Status

- [x] Main workflow runs on schedule and `workflow_dispatch`.
- [x] Main workflow runs tests before production execution.
- [x] Main workflow uses repository variables for provider/model/timeout.
- [x] NVIDIA API key remains a secret.
- [x] Gmail and Telegram credentials remain secrets.
- [x] No formatter debug step is present.
- [x] No temporary runtime debug step is present.
- [x] Smoke workflow remains manual and fixture-based.
- [x] Smoke workflow does not access Gmail.
- [x] Smoke workflow does not use dedup state.

## Runtime Checklist

- [x] Gmail fetch uses IMAP over SSL.
- [x] Google Alerts HTML is parsed into title, source, URL, and snippet.
- [x] Google redirect URLs are normalized.
- [x] Tracking parameters are removed from URLs.
- [x] Email-level URL dedup is deterministic.
- [x] Processed URL dedup uses normalized URL hashes.
- [x] Rule-based selector runs before LLM enhancement.
- [x] Selector remains the article decision owner.
- [x] LLM remains the explanation and synthesis owner.
- [x] Semantic deduplication remains disabled.
- [x] Telegram send success is required before processed URL save.

## Provider Checklist

- [x] OpenAI provider remains supported.
- [x] NVIDIA provider remains supported.
- [x] Main workflow can run with `LLM_PROVIDER=nvidia`.
- [x] Main workflow can use `NVIDIA_MODEL=mistralai/mistral-medium-3.5-128b`.
- [x] NVIDIA timeout is passed through `NVIDIA_TIMEOUT_SECONDS`.
- [x] NVIDIA common completion kwargs are used for Mistral.
- [x] MiniMax-only `thinking_mode=disabled` is not sent to Mistral.
- [x] MiniMax-specific compatibility remains in code.

## Message and Guardrail Checklist

- [x] Daily Landscape is optional.
- [x] Empty Landscape collapses to article cards.
- [x] Theme labels are hidden when invalid or unsupported.
- [x] Keywords must appear in source title or snippet.
- [x] Entities must appear in source title or snippet.
- [x] Broad landscape terms are filtered.
- [x] Preview requires grounded evidence.
- [x] Low-confidence preview is hidden.
- [x] Confidence is not rendered in Telegram.
- [x] Evidence arrays are not rendered in Telegram.
- [x] Source links remain visible.
- [x] HTML escaping is applied in message builder.

## Prompt and Parser Checklist

- [x] Prompt states that only Google Alerts metadata is visible.
- [x] Prompt forbids claiming full article access.
- [x] Prompt forbids market forecasts.
- [x] Prompt forbids investment advice.
- [x] Prompt forbids career advice.
- [x] Prompt keeps semantic dedup disabled.
- [x] Prompt requires every article index exactly once.
- [x] Parser accepts strict JSON.
- [x] Parser accepts full-response Markdown JSON fences.
- [x] Parser does not perform broad JSON repair.
- [x] Strict diagnostics remain available for smoke tests.

## Documentation Checklist

- [x] Design Principles exist.
- [x] Message Specification exists.
- [x] Architecture document exists.
- [x] README large rewrite is deferred.
- [x] RC1 operational checklist exists.

## Example Telegram Message

The following example is based on parsed Google Alerts fixture emails in
`tests/google_alerts/`. The selected articles come from the current rule-based
selector. The landscape and enhanced wording represent the validated 2.0 message
shape expected from Mistral enhancement; it does not claim full article-body
access.

```text
📰 오늘의 AI Landscape

Google AI 제품과 검색 변화 관련 소식이 함께 나타났습니다.

주요 흐름
• Google AI 제품·검색 변화
• AI 인프라와 반도체 언급

주요 키워드
Google · AI Search · AI infrastructure · chips

주요 기업·기관
Google · OpenAI · White House

━━━━━━━━━━━━━━

🏆 ESSENTIAL
AI & Tech Brief: Exclusive | White House AI order expected

🇰🇷 백악관 AI 명령과 Google AI 전략

Google I/O 제품 발표와 White House AI order가 함께 언급됐습니다.

✓ Why selected
신뢰도 높은 출처와 정부·플랫폼 전략 신호가 함께 잡혔습니다.

🔗 Read →

━━━━━━━━━━━━━━

🏆 ESSENTIAL
Google Shifts to AI Search, Heralding Major Change in How People Use the Internet

🇰🇷 Google AI 검색 전환과 인프라 언급

AI Search와 AI infrastructure, chips가 제목과 snippet에 나타났습니다.

✓ Why selected
AI 검색 변화와 인프라·반도체 신호가 함께 있는 기사입니다.

🔗 Read →

━━━━━━━━━━━━━━

✅ RECOMMENDED
Google is dethroning OpenAI as the king of consumer AI

🇰🇷 Google과 OpenAI 소비자 AI 경쟁

Google과 OpenAI가 소비자 AI 맥락에서 함께 언급됐습니다.

✓ Why selected
신뢰도 높은 출처에서 Google과 OpenAI 경쟁 구도를 다룹니다.

🔗 Read →
```

## RC1 Decision

RC1 is ready when:

- Local tests pass.
- Diff check passes.
- Smoke-test unit coverage passes.
- Production workflow points to repository variables for NVIDIA provider config.
- GitHub repository variables are set to the Mistral model.
- GitHub secrets remain configured for Gmail, NVIDIA, and Telegram.

Live production delivery still depends on external systems: Gmail IMAP, NVIDIA
Build NIM, Telegram Bot API, and GitHub Actions availability.
