"""Load helpers for the library new-arrivals scan (partition-overwrite by scan_date)."""
from __future__ import annotations

import json
import logging

from airflow.providers.postgres.hooks.postgres import PostgresHook

logger = logging.getLogger(__name__)

CONN_ID = "datamart_postgres"
STAGING_DIR = "/opt/airflow/data/staging/library"


def scrape_to_staging(ds: str, libraries: list[str], kdc: str, period: str, book_class: str) -> str:
    from library_scanner.snlib_client import SearchFilters, fetch_all_new_arrivals

    all_books = []
    for library in libraries:
        filters = SearchFilters(library=library, kdc=kdc, period=period, book_class=book_class)
        books = fetch_all_new_arrivals(filters)
        logger.info("scrape_to_staging ds=%s library=%s books=%d", ds, library, len(books))
        all_books.extend(books)

    from pathlib import Path

    out_path = f"{STAGING_DIR}/dt={ds}/scan.json"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([b.__dict__ for b in all_books], f, ensure_ascii=False)

    logger.info("scrape_to_staging ds=%s total_books=%d -> %s", ds, len(all_books), out_path)
    return out_path


def load_raw_scan(staging_path: str, ds: str) -> int:
    from library_scanner.filters import exclude_child_literature, filter_available

    with open(staging_path, encoding="utf-8") as f:
        raw = json.load(f)

    from library_scanner.models import NewArrivalBook

    books = [NewArrivalBook(**row) for row in raw]
    books = exclude_child_literature(books)  # searchBookClass=GENERAL로 이미 걸러지지만 방어적으로 한 번 더

    hook = PostgresHook(postgres_conn_id=CONN_ID)
    hook.run("DELETE FROM library.new_arrival_scan WHERE scan_date = %(ds)s", parameters={"ds": ds})

    if not books:
        return 0

    rows = [
        (
            ds,
            b.rec_key,
            b.book_key,
            b.title,
            b.author,
            b.publisher,
            b.pub_year,
            b.call_number,
            b.isbn,
            b.library,
            b.room,
            b.status_text,
            filter_available([b]) != [],
            b.cover_image_url,
        )
        for b in books
    ]
    hook.insert_rows(
        table="library.new_arrival_scan",
        rows=rows,
        target_fields=[
            "scan_date", "rec_key", "book_key", "title", "author", "publisher", "pub_year",
            "call_number", "isbn", "library_name", "room", "status_text", "is_available", "cover_image_url",
        ],
        commit_every=200,
    )
    logger.info("load_raw_scan ds=%s loaded=%d", ds, len(rows))
    return len(rows)


def classify_and_load_matches(ds: str, ttbkey: str | None) -> int:
    from library_scanner.aladin_client import find_genre_matches
    from library_scanner.filters import is_fiction_call_number
    from library_scanner.models import NewArrivalBook

    if not ttbkey:
        from airflow.exceptions import AirflowSkipException

        raise AirflowSkipException(
            "ALADIN_TTBKEY not configured yet — skipping genre classification until it's set"
        )

    hook = PostgresHook(postgres_conn_id=CONN_ID)
    rows = hook.get_records(
        """
        SELECT rec_key, book_key, title, author, publisher, pub_year, call_number,
               isbn, library_name, room, status_text
        FROM library.new_arrival_scan
        WHERE scan_date = %(ds)s AND is_available = true AND isbn IS NOT NULL
        """,
        parameters={"ds": ds},
    )
    candidates = [
        NewArrivalBook(
            rec_key=r[0], book_key=r[1], title=r[2], author=r[3], publisher=r[4], pub_year=r[5],
            call_number=r[6], isbn=r[7], library=r[8], room=r[9], status_text=r[10],
        )
        for r in rows
    ]
    candidates = [b for b in candidates if is_fiction_call_number(b.call_number)]

    matches = find_genre_matches(candidates, ttbkey)

    hook.run("DELETE FROM library.genre_matches WHERE scan_date = %(ds)s", parameters={"ds": ds})
    if matches:
        match_rows = [
            (ds, m.book.rec_key, m.book.book_key, m.book.title, m.book.author, m.book.isbn,
             m.book.call_number, m.book.library, m.matched_genre, m.category_path, m.description)
            for m in matches
        ]
        hook.insert_rows(
            table="library.genre_matches",
            rows=match_rows,
            target_fields=[
                "scan_date", "rec_key", "book_key", "title", "author", "isbn",
                "call_number", "library_name", "matched_genre", "category_path", "description",
            ],
        )

    logger.info(
        "classify_and_load_matches ds=%s candidates=%d matches=%d", ds, len(candidates), len(matches)
    )
    for m in matches:
        logger.info(
            "  [%s] %s / %s (%s) - %s: %s",
            m.matched_genre, m.book.title, m.book.author, m.book.library,
            m.category_path, m.description or "(줄거리 정보 없음)",
        )
    return len(matches)


REPORT_DIR = "/opt/airflow/data/reports/library"


def write_text_report(ds: str) -> str:
    """SF/추리 매칭 결과를 사람이 바로 읽을 수 있는 텍스트 파일로 저장.

    `data/reports/library/{ds}.txt`에 그날 결과를, `latest.txt`에는 항상
    가장 최근 결과를 덮어써서 날짜를 몰라도 바로 확인할 수 있게 한다.
    """
    from pathlib import Path

    hook = PostgresHook(postgres_conn_id=CONN_ID)
    rows = hook.get_records(
        """
        SELECT matched_genre, title, author, library_name, call_number, isbn, category_path, description
        FROM library.genre_matches
        WHERE scan_date = %(ds)s
        ORDER BY library_name, matched_genre, title
        """,
        parameters={"ds": ds},
    )

    sf_count = sum(1 for r in rows if r[0] == "SF")
    mystery_count = sum(1 for r in rows if r[0] == "MYSTERY")

    lines = [
        f"성남도서관 신착 SF/추리 대출가능 도서 ({ds} 스캔)",
        "=" * 60,
        f"총 {len(rows)}건 (SF {sf_count} / 추리·스릴러 {mystery_count})",
        "",
    ]
    for genre, title, author, library_name, call_number, isbn, category_path, description in rows:
        lines.append(f"[{genre}] {title} / {author or '-'}")
        lines.append(f"    도서관: {library_name} | 청구기호: {call_number or '-'} | ISBN: {isbn or '-'}")
        lines.append(f"    카테고리: {category_path}")
        lines.append(f"    줄거리: {description or '(정보 없음)'}")
        lines.append("")

    if not rows:
        lines.append("(오늘은 조건에 맞는 대출가능 SF/추리 신착도서가 없습니다)")

    text = "\n".join(lines)

    Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)
    dated_path = f"{REPORT_DIR}/{ds}.txt"
    latest_path = f"{REPORT_DIR}/latest.txt"
    for path in (dated_path, latest_path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    logger.info("write_text_report ds=%s matches=%d -> %s", ds, len(rows), dated_path)
    return dated_path
