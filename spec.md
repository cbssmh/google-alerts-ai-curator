# Google Alerts AI Curator — Specification

## 1. Project Goal
Google Alerts 이메일을 최근 24시간 기준으로 수집하고, 중복 제거 후 LLM이 고신호 기사만 선별하여 Telegram으로 한국어 요약을 전송한다.

## 2. Input
- Gmail IMAP
- 최근 24시간 Google Alerts 이메일
- HTML email body

## 3. Output
Telegram 메시지:
- 원문 제목
- 출처
- 링크
- 선정 이유
- 한국어 요약
- 커리어 / 시장 인사이트

## 4. Selection Policy
- 최대 3개 기사 전송
- 품질 낮으면 0개 전송 가능
- relevance score 8 이상만 전송 후보

## 5. Deduplication
- `data/processed_urls.json` 사용
- URL normalize 후 sha256 hash 저장
- 이미 처리한 URL은 재전송하지 않음

## 6. Main Components
- Gmail fetcher
- Google Alerts parser
- URL normalizer
- Dedup store
- LLM curator
- Telegram sender
- GitHub Actions workflow

## 7. Constraints
- GitHub Actions only
- No local PC
- No personal server
- Secrets must not be logged
- Parser must tolerate HTML changes

## 8. Failure Handling
- Gmail fetch 실패 시 로그만 남기고 종료
- 기사 0개면 Telegram 전송 생략
- LLM 실패 시 Telegram 전송하지 않음
- Dedup 저장 실패 시 다음 실행에서 재전송 가능성 있음

## 9. Test Strategy
- Google Alerts HTML fixture parser test
- URL normalization test
- Dedup test
- Telegram message format test
- LLM prompt structure test