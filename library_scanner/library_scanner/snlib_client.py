"""Scraper for 성남도서관(snlib.go.kr) new-arrivals search.

The page is server-rendered (confirmed by inspection), so this parses the
HTML directly rather than driving a browser. `robots.txt` disallows
automated access site-wide, so this client is deliberately low-volume:
one request per page, a descriptive User-Agent, and a delay between
requests. Use it for personal, low-frequency checks only.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

import requests

from .models import NewArrivalBook

logger = logging.getLogger(__name__)

BASE_URL = "https://snlib.go.kr"
SEARCH_PATH = "/intro/menu/10037/program/30005/plusSearchNewList.do"

USER_AGENT = (
    "library-scanner/0.1 (personal reading-list checker; "
    "low-frequency, non-commercial; contact: see project README)"
)

# 참고용 전체 코드 (사이트 검색폼의 <option value=...>에서 추출)
LIBRARY_CODES = {
    "ALL": "전체도서관",
    "MA": "중앙도서관",
    "MH": "해오름도서관",
    "MB": "분당도서관",
    "MO": "수내도서관",
    "MS": "수정도서관",
    # ... 그 외 지점은 필요 시 추가
}
KDC_CODES = {
    "ALL": "전체주제",
    "0": "총류",
    "1": "철학",
    "2": "종교",
    "3": "사회과학",
    "4": "자연과학",
    "5": "기술과학",
    "6": "예술",
    "7": "언어",
    "8": "문학",
    "9": "역사",
}
PERIODS = {"3M": "3달 이내", "1M": "1달 이내", "3W": "3주 이내", "2W": "2주 이내", "1W": "1주 이내"}
BOOK_CLASSES = {"ALL": "전체도서", "GENERAL": "일반도서", "CHILD": "아동도서"}

_TOTAL_COUNT_RE = re.compile(r"총\s*<strong[^>]*>([\d,]+)건</strong>")
_ITEM_SPLIT_RE = re.compile(r"<li>")
_DETAIL_TITLE_RE = re.compile(
    r"fnSearchResultDetail\((\d+),\s*(\d+),\s*'([A-Z]+)'\);\s*return false;\">\s*([^<]+?)\s*</a>"
)
_AUTHOR_RE = re.compile(r"저자\s*:\s*([^<]+)</span>")
_PUBLISHER_RE = re.compile(r"발행자:\s*([^<]+)</span>")
_PUBYEAR_RE = re.compile(r"발행연도:\s*([^<]+)</span>")
_CALLNO_RE = re.compile(r"청구기호:\s*([^\n<]+?)\s*(?:<|$)")
_ISBN_RE = re.compile(r"ISBN:\s*([0-9Xx]+)</span>")
_LIBRARY_RE = re.compile(r"도서관:\s*([^<]+)</span>")
_ROOM_RE = re.compile(r"자료실:\s*([^<]+)</span>")
_STATUS_RE = re.compile(r'<b class="emp\d+">\s*([^<]+?)\s*</b>')
_COVER_RE = re.compile(r'class="bookCoverImg" src="([^"]+)"')


@dataclass
class SearchFilters:
    library: str = "MH"
    kdc: str = "8"
    period: str = "3M"
    book_class: str = "GENERAL"
    page_size: int = 50


def _build_payload(filters: SearchFilters, page: int) -> dict:
    return {
        "searchType": "NEW",
        "searchCategory": "ALL",
        "currentPageNo": page,
        "viewStatus": "IMAGE",
        "searchLibrary": filters.library,
        "searchKdc": filters.kdc,
        "searchPeriod": filters.period,
        "searchSort": "KEY",
        "searchOrder": "DESC",
        "searchRecordCount": filters.page_size,
        "searchBookClass": filters.book_class,
    }


def fetch_page_html(session: requests.Session, filters: SearchFilters, page: int) -> str:
    resp = session.post(
        BASE_URL + SEARCH_PATH,
        data=_build_payload(filters, page),
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    resp.raise_for_status()
    resp.encoding = "utf-8"
    return resp.text


def parse_total_count(html: str) -> int:
    m = _TOTAL_COUNT_RE.search(html)
    return int(m.group(1).replace(",", "")) if m else 0


def parse_items(html: str) -> list[NewArrivalBook]:
    books = []
    for block in _ITEM_SPLIT_RE.split(html)[1:]:
        title_m = _DETAIL_TITLE_RE.search(block)
        if not title_m:
            continue  # 결과 항목이 아닌 다른 <li> (탭메뉴 등)
        rec_key, book_key, _publish_form, title = title_m.groups()

        def _opt(pattern: re.Pattern) -> str | None:
            m = pattern.search(block)
            return m.group(1).strip() if m else None

        status_text = _opt(_STATUS_RE) or ""
        library = _opt(_LIBRARY_RE) or ""

        books.append(
            NewArrivalBook(
                rec_key=rec_key,
                book_key=book_key,
                title=title,
                author=_opt(_AUTHOR_RE),
                publisher=_opt(_PUBLISHER_RE),
                pub_year=_opt(_PUBYEAR_RE),
                call_number=_opt(_CALLNO_RE),
                isbn=_opt(_ISBN_RE),
                library=library,
                room=_opt(_ROOM_RE),
                status_text=status_text,
                cover_image_url=_opt(_COVER_RE),
            )
        )
    return books


def fetch_all_new_arrivals(
    filters: SearchFilters | None = None,
    delay_seconds: float = 1.5,
    session: requests.Session | None = None,
) -> list[NewArrivalBook]:
    """Fetch every page of the filtered new-arrivals search.

    One request per page with a delay in between (default 1.5s) — this site's
    robots.txt disallows automated access, so keep this to a single daily run
    and don't lower the delay.
    """
    filters = filters or SearchFilters()
    session = session or requests.Session()

    first_html = fetch_page_html(session, filters, page=1)
    total = parse_total_count(first_html)
    books = parse_items(first_html)

    total_pages = max(1, -(-total // filters.page_size))  # ceil division
    logger.info("snlib new-arrivals: total=%d pages=%d filters=%s", total, total_pages, filters)

    for page in range(2, total_pages + 1):
        time.sleep(delay_seconds)
        html = fetch_page_html(session, filters, page)
        books.extend(parse_items(html))

    return books
