from __future__ import annotations

import hashlib
import json
from pathlib import Path

from src.models import Article
from src.url_normalizer import normalize_url


DEFAULT_STATE_FILE = Path("data/processed_urls.json")


class DedupStore:
    def __init__(self, path: str | Path = DEFAULT_STATE_FILE):
        self.path = Path(path)
        self.processed_hashes = self._load()

    def is_processed(self, url: str) -> bool:
        return self._hash_url(url) in self.processed_hashes

    def mark_processed(self, url: str) -> None:
        self.processed_hashes.add(self._hash_url(url))

    def filter_new_articles(self, articles: list[Article]) -> list[Article]:
        return [article for article in articles if not self.is_processed(article.url)]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(sorted(self.processed_hashes), indent=2),
            encoding="utf-8",
        )

    def _load(self) -> set[str]:
        if not self.path.exists():
            return set()

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return set()

        if not isinstance(data, list):
            return set()

        return {item for item in data if isinstance(item, str)}

    def _hash_url(self, url: str) -> str:
        normalized_url = normalize_url(url)
        return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()
