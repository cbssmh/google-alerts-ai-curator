from __future__ import annotations

import json

from src.models import Article, CuratedArticle

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


TARGET_INTERESTS = [
    "AI infrastructure",
    "Enterprise AI",
    "semiconductor trends",
    "quant / systematic investing",
    "cybersecurity",
    "global tech career trends",
    "Germany-related IT career opportunities if relevant",
]


def build_curator_prompt(articles: list[Article]) -> str:
    article_lines = []
    for index, article in enumerate(articles, start=1):
        article_lines.append(
            "\n".join(
                [
                    f"{index}. title: {article.title}",
                    f"   source: {article.source}",
                    f"   url: {article.url}",
                    f"   snippet: {article.snippet}",
                ]
            )
        )

    return f"""You are curating Google Alerts articles for personal relevance.

Target interests:
- {TARGET_INTERESTS[0]}
- {TARGET_INTERESTS[1]}
- {TARGET_INTERESTS[2]}
- {TARGET_INTERESTS[3]}
- {TARGET_INTERESTS[4]}
- {TARGET_INTERESTS[5]}
- {TARGET_INTERESTS[6]}

Select maximum 3 articles.
Skip all articles if quality is low.
Assign relevance_score from 0 to 10.
Only select articles with relevance_score >= 8.
Preserve the original title exactly.
Write korean_summary, why_selected, and career_market_insight in Korean.
Output strict JSON only, with this schema:
{{
  "articles": [
    {{
      "title": "...",
      "source": "...",
      "url": "...",
      "relevance_score": 9,
      "why_selected": "...",
      "korean_summary": "...",
      "career_market_insight": "..."
    }}
  ]
}}

Articles:
{chr(10).join(article_lines)}
"""


def parse_curator_response(response_text: str) -> list[CuratedArticle]:
    if not response_text:
        return []

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        return []

    raw_articles = data.get("articles") if isinstance(data, dict) else None
    if not isinstance(raw_articles, list):
        return []

    curated_articles: list[CuratedArticle] = []
    for raw_article in raw_articles:
        if not isinstance(raw_article, dict):
            continue

        relevance_score = raw_article.get("relevance_score", 0)
        if not isinstance(relevance_score, int) or relevance_score < 8:
            continue

        curated_articles.append(
            CuratedArticle(
                title=str(raw_article.get("title", "")),
                source=str(raw_article.get("source", "")),
                url=str(raw_article.get("url", "")),
                snippet="",
                relevance_score=relevance_score,
                why_selected=str(raw_article.get("why_selected", "")),
                korean_summary=str(raw_article.get("korean_summary", "")),
                career_market_insight=str(
                    raw_article.get("career_market_insight", "")
                ),
            )
        )

        if len(curated_articles) == 3:
            break

    return curated_articles


def curate_articles(
    articles: list[Article],
    api_key: str,
    model: str = "gpt-4.1-mini",
    base_url: str | None = None,
) -> list[CuratedArticle]:
    if not articles or OpenAI is None:
        return []

    prompt = build_curator_prompt(articles)

    try:
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.choices[0].message.content
    except Exception:
        return []

    return parse_curator_response(response_text)
