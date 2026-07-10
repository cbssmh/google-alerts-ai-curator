from __future__ import annotations

import json
from dataclasses import replace

from src.models import CuratedArticle

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


CONFIDENCE_LEVELS = {"high", "medium", "low"}
FORBIDDEN_PREVIEW_TERMS = (
    "투자 조언",
    "매수",
    "매도",
    "추천 종목",
    "커리어",
    "개발자",
    "해야 합니다",
)


def build_message_enhancement_prompt(articles: list[CuratedArticle]) -> str:
    article_blocks = []
    for index, article in enumerate(articles):
        article_blocks.append(
            "\n".join(
                [
                    f"index: {index}",
                    f"title: {article.title}",
                    f"source: {article.source}",
                    f"snippet: {article.snippet}",
                    "rule_based_reasons: "
                    + ", ".join(article.recommendation_reasons),
                ]
            )
        )

    return f"""You enhance a Telegram decision card for Google Alerts articles.

Core philosophy:
- Rule-based selection already decided which articles are worth showing.
- You do not select new articles.
- You may only make the message easier to understand.

Grounding rules:
- Do not assume you read the full article body.
- Use only title, source, snippet, and rule_based_reasons.
- If there is not enough evidence, return an empty string for preview.
- Do not force a preview.
- Do not infer company intent.
- Do not invent numbers, facts, causes, or outcomes.
- Do not write market forecasts.
- Do not write investment advice.
- Do not write developer career advice or career insight.
- Do not write "Why it Matters".
- Do not write a full summary.
- Evidence must contain only words that appear in the original title or snippet.

Output rules:
- Output strict JSON only.
- Write korean_title, preview, why_selected, and daily_trends in Korean.
- Keep the original article title unchanged by referring to articles by index.
- korean_title must be short, natural, and grounded in the title/snippet.
- korean_title should be 20 to 45 Korean characters when possible.
- preview must be 25 to 70 Korean characters.
- preview must be one sentence.
- preview must not include future outlook, investment advice, or career advice.
- why_selected should explain the rule-based signal in one reader-friendly Korean sentence.
- confidence must be one of: high, medium, low.
- If confidence is low, preview must be an empty string.
- daily_trends should contain only common trends across multiple final articles.
- If there is only one final article, daily_trends must be an empty array.
- Include only trends directly supported by at least two final articles.
- Return at most two daily_trends items.
- If there is no clear common trend, daily_trends must be an empty array.

Semantic deduplication is disabled for this release.
- Do not remove, merge, hide, or reorder articles.
- Return every article index exactly once.
- Leave duplicate handling to the existing URL and rule-based steps.

JSON schema:
{{
  "articles": [
    {{
      "index": 0,
      "korean_title": "",
      "preview": "",
      "why_selected": "",
      "confidence": "high",
      "evidence": []
    }}
  ],
  "daily_trends": []
}}

Articles:
{chr(10).join(article_blocks)}
"""


def enhance_message_with_llm(
    articles: list[CuratedArticle],
    api_key: str,
    model: str,
    base_url: str | None = None,
    timeout_seconds: float | None = None,
) -> tuple[list[CuratedArticle], list[str]]:
    if not articles or OpenAI is None:
        return articles, []

    prompt = build_message_enhancement_prompt(articles)

    try:
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        if timeout_seconds is not None:
            client_kwargs["timeout"] = timeout_seconds

        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.choices[0].message.content
    except Exception:
        return articles, []

    enhanced_articles, daily_trends = parse_message_enhancement_response(
        response_text,
        articles,
    )
    if not enhanced_articles:
        return articles, []

    return enhanced_articles, daily_trends


def parse_message_enhancement_response(
    response_text: str,
    articles: list[CuratedArticle],
) -> tuple[list[CuratedArticle], list[str]]:
    if not response_text:
        return [], []

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        return [], []

    if not isinstance(data, dict):
        return [], []

    raw_articles = data.get("articles")
    if not isinstance(raw_articles, list):
        return [], []

    enhanced_by_index: dict[int, CuratedArticle] = {}
    seen_indices: set[int] = set()
    for raw_article in raw_articles:
        if not isinstance(raw_article, dict):
            continue

        index = raw_article.get("index")
        if not isinstance(index, int):
            continue

        if index < 0 or index >= len(articles) or index in seen_indices:
            continue

        seen_indices.add(index)
        original = articles[index]
        enhanced_by_index[index] = (
            replace(
                original,
                korean_title=_clean_korean_title(
                    raw_article.get("korean_title", "")
                ),
                preview=_clean_preview(
                    raw_article.get("preview", ""),
                    raw_article.get("confidence", ""),
                    raw_article.get("evidence", []),
                    original,
                ),
                enhanced_why_selected=_clean_sentence(
                    raw_article.get("why_selected", ""),
                    max_length=120,
                ),
                confidence=_clean_confidence(raw_article.get("confidence", "")),
                evidence=_filter_grounded_evidence(
                    raw_article.get("evidence", []),
                    original,
                ),
            )
        )

    enhanced_articles = [
        enhanced_by_index.get(index, article)
        for index, article in enumerate(articles)
    ]

    return enhanced_articles, _clean_daily_trends(
        data.get("daily_trends", []),
        article_count=len(enhanced_articles),
    )


def _clean_korean_title(value) -> str:
    title = _clean_sentence(value, max_length=45)
    if len(title) > 45:
        return ""
    return title


def _clean_preview(
    value,
    confidence_value,
    evidence_value,
    article: CuratedArticle,
) -> str:
    confidence = _clean_confidence(confidence_value)
    if confidence == "low":
        return ""

    evidence = _filter_grounded_evidence(evidence_value, article)
    if not evidence:
        return ""

    preview = _clean_sentence(value, max_length=90)
    if not preview:
        return ""

    if any(term in preview for term in FORBIDDEN_PREVIEW_TERMS):
        return ""

    return preview


def _clean_confidence(value) -> str:
    confidence = str(value or "").strip().lower()
    if confidence in CONFIDENCE_LEVELS:
        return confidence
    return "low"


def _filter_grounded_evidence(value, article: CuratedArticle) -> list[str]:
    if not isinstance(value, list):
        return []

    source_text = " ".join([article.title, article.snippet]).lower()
    grounded = []
    for item in value:
        evidence = _clean_sentence(item, max_length=40)
        if not evidence:
            continue

        if evidence.lower() not in source_text:
            continue

        if evidence not in grounded:
            grounded.append(evidence)

        if len(grounded) == 5:
            break

    return grounded


def _clean_daily_trends(value, article_count: int) -> list[str]:
    if article_count < 2 or not isinstance(value, list):
        return []

    trends = []
    for item in value:
        trend = _clean_sentence(item, max_length=60)
        if not trend:
            continue

        if trend not in trends:
            trends.append(trend)

        if len(trends) == 2:
            break

    return trends


def _clean_sentence(value, max_length: int) -> str:
    if not isinstance(value, str):
        return ""

    cleaned = " ".join(value.split())
    if len(cleaned) > max_length:
        return ""

    return cleaned
