from dataclasses import dataclass


@dataclass
class Article:
    title: str
    source: str
    url: str
    snippet: str


@dataclass
class CuratedArticle:
    title: str
    source: str
    url: str
    snippet: str
    relevance_score: int
    why_selected: str
    korean_summary: str
    career_market_insight: str
