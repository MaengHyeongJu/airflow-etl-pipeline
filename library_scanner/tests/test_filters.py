import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from library_scanner.filters import exclude_child_literature, filter_available, is_fiction_call_number
from library_scanner.models import NewArrivalBook


def _book(**overrides) -> NewArrivalBook:
    defaults = dict(
        rec_key="1",
        book_key="2",
        title="테스트 도서",
        author="홍길동",
        publisher="출판사",
        pub_year="2026",
        call_number="813.7-ㅎ123ㄱ",
        isbn="9791100000000",
        library="해오름도서관",
        room="[해오름]제1종합자료실(2층)",
        status_text="대출가능[비치중]",
    )
    defaults.update(overrides)
    return NewArrivalBook(**defaults)


def test_filter_available_keeps_only_loanable():
    books = [
        _book(status_text="대출가능[비치중]"),
        _book(status_text="대출불가[대출중]"),
        _book(status_text="대출불가[대출대기중]"),
        _book(status_text="대출불가[상호대차중]"),
    ]
    assert [b.status_text for b in filter_available(books)] == ["대출가능[비치중]"]


def test_exclude_child_literature_by_call_number_prefix():
    books = [
        _book(call_number="813.7-ㅎ123ㄱ"),
        _book(call_number="아 813.8-ㅌ556ㅌ-2"),
        _book(call_number="유 808.9-ㅅ194-26"),
        _book(call_number=None),
    ]
    kept = exclude_child_literature(books)
    assert [b.call_number for b in kept] == ["813.7-ㅎ123ㄱ", None]


def test_is_fiction_call_number():
    assert is_fiction_call_number("813.7-ㅎ643ㅂ") is True
    assert is_fiction_call_number("833.6-ㅈ554-1=2") is True
    assert is_fiction_call_number("843.6-ㅅ994") is True
    assert is_fiction_call_number("863-ㅂ7745여-2=2") is True
    assert is_fiction_call_number("818-ㅅ642ㄲ=2") is False  # 수필
    assert is_fiction_call_number("802.5-ㅈ176ㄸ=2") is False
    assert is_fiction_call_number(None) is False
