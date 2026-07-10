from dataclasses import dataclass, field


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
    recommendation_reasons: list[str] = field(default_factory=list)
    korean_title: str = ""
    preview: str = ""
    enhanced_why_selected: str = ""
    confidence: str = ""
    evidence: list[str] = field(default_factory=list)
