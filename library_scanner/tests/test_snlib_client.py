import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from library_scanner.filters import exclude_child_literature, filter_available
from library_scanner.snlib_client import parse_items, parse_total_count

FIXTURE = (Path(__file__).parent / "fixtures" / "haeoreum_literature_general_page1.html").read_text(
    encoding="utf-8"
)


def test_parse_total_count():
    assert parse_total_count(FIXTURE) == 429


def test_parse_items_extracts_expected_fields():
    books = parse_items(FIXTURE)
    assert len(books) == 50  # searchRecordCount=50 요청 결과

    first = books[0]
    assert first.rec_key and first.book_key
    assert first.title
    assert first.library == "해오름도서관"
    assert first.status_text  # 4가지 상태 문구 중 하나


def test_general_book_class_excludes_child_literature_already():
    books = parse_items(FIXTURE)
    # searchBookClass=GENERAL 로 받은 목록이므로 아동/유아 청구기호가 없어야 함
    assert exclude_child_literature(books) == books


def test_filter_available_matches_status_prefix():
    books = parse_items(FIXTURE)
    available = filter_available(books)
    assert all(b.status_text.startswith("대출가능") for b in available)
    assert 0 < len(available) < len(books)
