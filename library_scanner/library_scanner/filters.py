"""Post-scrape filtering helpers.

Excluding children's literature is normally done server-side via
`searchBookClass=GENERAL` (confirmed to drop 청구기호 "아"/"유"/"J" prefixed
items entirely). `exclude_child_literature` is kept as a defensive
second pass in case filters are ever loosened to `ALL`.
"""
from __future__ import annotations

import re

from .models import NewArrivalBook

CHILD_CALL_NUMBER_PREFIXES = ("아 ", "유 ", "J ")

# KDC 8xx 문학: 가운데 자리는 언어(1=한국,2=중국,3=일본,4=영미,5=독일,6=프랑스...),
# 끝자리 3이 소설(예: 813, 823, 833.6, 843 ...). 811=시, 812=희곡, 814=수필 등은 제외돼서
# 알라딘 조회 대상을 소설류로만 좁혀 불필요한 API 호출을 줄인다.
_FICTION_CALL_NUMBER_RE = re.compile(r"^8\d3(\.\d+)?[^\d]")


def filter_available(books: list[NewArrivalBook]) -> list[NewArrivalBook]:
    return [b for b in books if b.is_available]


def exclude_child_literature(books: list[NewArrivalBook]) -> list[NewArrivalBook]:
    return [
        b
        for b in books
        if not (b.call_number and b.call_number.startswith(CHILD_CALL_NUMBER_PREFIXES))
    ]


def is_fiction_call_number(call_number: str | None) -> bool:
    if not call_number:
        return False
    return bool(_FICTION_CALL_NUMBER_RE.match(call_number.strip() + "-"))
