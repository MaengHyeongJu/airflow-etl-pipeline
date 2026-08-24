"""Standalone CLI, independent of Airflow.

    python -m library_scanner.cli --library MH --kdc 8 --period 3M
    ALADIN_TTBKEY=xxx python -m library_scanner.cli --library MH --classify
"""
from __future__ import annotations

import argparse
import logging
import os

from .aladin_client import find_genre_matches
from .filters import exclude_child_literature, filter_available
from .snlib_client import SearchFilters, fetch_all_new_arrivals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", default="MH", help="도서관 코드 (기본: MH=해오름도서관)")
    parser.add_argument("--kdc", default="8", help="주제 코드 (기본: 8=문학)")
    parser.add_argument("--period", default="3M", choices=["1W", "2W", "3W", "1M", "3M"])
    parser.add_argument("--book-class", default="GENERAL", choices=["ALL", "GENERAL", "CHILD"])
    parser.add_argument("--classify", action="store_true", help="ALADIN_TTBKEY로 SF/추리 장르 판별까지 수행")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    filters = SearchFilters(library=args.library, kdc=args.kdc, period=args.period, book_class=args.book_class)
    books = fetch_all_new_arrivals(filters)
    print(f"수집: {len(books)}건")

    books = exclude_child_literature(books)
    available = filter_available(books)
    print(f"대출가능: {len(available)}건")

    if not args.classify:
        for b in available[:20]:
            print(f"  - [{b.call_number}] {b.title} / {b.author}")
        return

    ttbkey = os.environ.get("ALADIN_TTBKEY")
    if not ttbkey:
        raise SystemExit("ALADIN_TTBKEY 환경변수가 필요합니다 (--classify 사용 시)")

    matches = find_genre_matches(available, ttbkey)
    print(f"SF/추리 매칭: {len(matches)}건")
    for m in matches:
        print(f"  - [{m.matched_genre}] {m.book.title} / {m.book.author} ({m.category_path})")


if __name__ == "__main__":
    main()
