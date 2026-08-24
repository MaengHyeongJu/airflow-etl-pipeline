"""Genre classification via the Aladin(알라딘) Open API.

Naver's book-search API was fully discontinued 2026-07-31 with no
replacement, and Kakao's book-search API is dropping its `category` field
when v3 replaces v2 (v2 shuts down 2026-12-31) — neither is viable for
genre detection going forward. Aladin's `ItemLookUp` (ISBN lookup) still
returns a full category breadcrumb per item via `OptResult=categoryIdList`,
e.g. "국내도서>소설/시/희곡>한국소설>추리/미스터리/스릴러", which is what
we match SF/추리 keywords against instead of guessing from free text.

Requires a free TTBKey (가입 후 나의계정 > TTB/API 발급, 승인까지 1~2일).
Free tier is 5,000 calls/day — comfortably enough for a daily new-arrivals
scan.

NOTE: the exact nesting of `categoryIdList` in the JSON response is not
fully documented publicly (dict vs list of category entries). `extract_category_paths`
handles both shapes defensively, but this should be re-checked against a
live response the first time a real TTBKey is available.
"""
from __future__ import annotations

import logging
import time

import requests

from .models import GENRE_KEYWORDS, GenreMatch, NewArrivalBook

logger = logging.getLogger(__name__)

BASE_URL = "http://www.aladin.co.kr/ttb/api/ItemLookUp.aspx"


def lookup_by_isbn(isbn: str, ttbkey: str, session: requests.Session | None = None) -> dict | None:
    session = session or requests.Session()
    params = {
        "ttbkey": ttbkey,
        "itemIdType": "ISBN13" if len(isbn) == 13 else "ISBN",
        "ItemId": isbn,
        "output": "js",
        "Version": "20131101",
        "OptResult": "categoryIdList",
    }
    resp = session.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("errorCode"):
        logger.warning("aladin lookup error isbn=%s code=%s msg=%s", isbn, data.get("errorCode"), data.get("errorMessage"))
        return None

    items = data.get("item") or []
    return items[0] if items else None


def extract_category_paths(item: dict) -> list[str]:
    paths: list[str] = []
    cat_list = (item or {}).get("categoryIdList")
    infos = cat_list.get("categoryInfo") if isinstance(cat_list, dict) else cat_list
    if isinstance(infos, dict):
        infos = [infos]
    for info in infos or []:
        name = info.get("categoryName")
        if name:
            paths.append(name)
    if item and item.get("categoryName"):
        paths.append(item["categoryName"])
    return paths


def classify_genre(item: dict) -> tuple[str, str] | None:
    """Return (genre, matched_category_path) if the item's category paths
    contain an SF/추리 keyword, else None."""
    for path in extract_category_paths(item):
        for genre, keywords in GENRE_KEYWORDS.items():
            if any(kw in path for kw in keywords):
                return genre, path
    return None


def find_genre_matches(
    books: list[NewArrivalBook],
    ttbkey: str,
    delay_seconds: float = 0.3,
    session: requests.Session | None = None,
) -> list[GenreMatch]:
    session = session or requests.Session()
    matches: list[GenreMatch] = []

    for book in books:
        if not book.isbn:
            continue
        item = lookup_by_isbn(book.isbn, ttbkey, session=session)
        if item:
            result = classify_genre(item)
            if result:
                genre, path = result
                matches.append(GenreMatch(book=book, matched_genre=genre, category_path=path))
        time.sleep(delay_seconds)

    return matches
