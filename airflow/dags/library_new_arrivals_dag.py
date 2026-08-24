"""성남도서관(해오름도서관) 신착도서 중 대출가능한 SF/추리 소설 찾기.

    scrape_and_stage >> load_raw_scan >> classify_and_load_matches >> write_report

- scrape_and_stage: snlib.go.kr 신착도서 검색(해오름도서관/문학/3개월/일반도서)을
  스크래핑해서 로컬 staging 파일에 저장. robots.txt가 사이트 전체를 막아둬서
  하루 한 번(스케줄), 페이지당 딜레이를 두고 저빈도로만 호출한다.
- load_raw_scan: staging 파일을 Postgres `library.new_arrival_scan`에
  파티션(scan_date) 단위로 덮어쓰기 적재.
- classify_and_load_matches: 그 중 대출가능 + 소설류(청구기호 8_3 계열)만
  ISBN으로 알라딘 조회 -> categoryName에서 SF/추리 키워드 매칭 ->
  `library.genre_matches`에 적재하고 매칭 목록을 태스크 로그에도 남김.
  ALADIN_TTBKEY가 아직 없으면 스킵.
- write_report: 매칭 결과를 `data/reports/library/{ds}.txt`와 항상 최신
  결과를 담은 `data/reports/library/latest.txt`로 저장.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

from airflow.sdk import dag, task

sys.path.insert(0, "/opt/airflow/include")

from etl.library_load import (  # noqa: E402
    classify_and_load_matches,
    load_raw_scan,
    scrape_to_staging,
    write_text_report,
)

# 대상 도서관/조건 (필요하면 나중에 파라미터화)
TARGET_LIBRARY = "MH"  # 해오름도서관
TARGET_KDC = "8"  # 문학
TARGET_PERIOD = "3M"  # 3개월 이내
TARGET_BOOK_CLASS = "GENERAL"  # 아동/유아 도서 제외


@dag(
    dag_id="library_new_arrivals_scan",
    description="성남도서관 신착도서 중 대출가능한 SF/추리 소설 찾기",
    schedule="@daily",
    start_date=datetime(2026, 8, 20),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1},
    tags=["library", "scraper"],
)
def library_new_arrivals_scan():
    @task
    def scrape_and_stage(ds: str) -> str:
        return scrape_to_staging(
            ds, library=TARGET_LIBRARY, kdc=TARGET_KDC, period=TARGET_PERIOD, book_class=TARGET_BOOK_CLASS
        )

    @task
    def load_raw(staging_path: str, ds: str) -> int:
        return load_raw_scan(staging_path, ds)

    @task
    def classify_and_load(loaded_count: int, ds: str) -> int:
        return classify_and_load_matches(ds, ttbkey=os.environ.get("ALADIN_TTBKEY"))

    @task
    def write_report(match_count: int, ds: str) -> str:
        return write_text_report(ds)

    staged = scrape_and_stage(ds="{{ ds }}")
    loaded = load_raw(staged, ds="{{ ds }}")
    matched = classify_and_load(loaded, ds="{{ ds }}")
    write_report(matched, ds="{{ ds }}")


library_new_arrivals_scan()
