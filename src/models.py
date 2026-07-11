from dataclasses import dataclass, field


@dataclass
class Article:
    title: str
    source: str
    url: str
    snippet: str


@dataclass
class TrendTheme:
    label: str
    article_indices: list[int] = field(default_factory=list)
    summary: str = ""


@dataclass
class DailyLandscape:
    headline: str = ""
    themes: list[TrendTheme] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return (
            not self.headline
            and not self.themes
            and not self.keywords
            and not self.entities
        )


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
