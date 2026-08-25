"""Data structures shared across the scraper and genre classifier."""
from __future__ import annotations

from dataclasses import dataclass, field

# 목록 페이지에 나오는 대출상태 문구는 이 4가지뿐이며, "대출가능"으로 시작하는 것만 대출 가능한 상태다.
AVAILABLE_STATUS_PREFIX = "대출가능"


@dataclass
class NewArrivalBook:
    rec_key: str
    book_key: str
    title: str
    author: str | None
    publisher: str | None
    pub_year: str | None
    call_number: str | None
    isbn: str | None
    library: str
    room: str | None
    status_text: str
    cover_image_url: str | None = None

    @property
    def is_available(self) -> bool:
        return self.status_text.startswith(AVAILABLE_STATUS_PREFIX)

    @property
    def detail_key(self) -> str:
        """Unique key for a physical copy (matches the site's checkbox value)."""
        return f"{self.rec_key}^{self.book_key}"


@dataclass
class GenreMatch:
    book: NewArrivalBook
    matched_genre: str  # "SF" | "MYSTERY"
    category_path: str
    description: str | None = None  # 알라딘 상품설명(줄거리) 요약
    source: str = "aladin"


GENRE_KEYWORDS: dict[str, list[str]] = {
    "SF": ["SF", "공상과학"],
    "MYSTERY": ["추리", "미스터리", "스릴러"],
}
