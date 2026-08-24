#!/usr/bin/env bash
# 성남도서관 신착도서(SF/추리) 스캐너용 스키마.
# 기존 datamart DB 안에 별도 schema로 분리해서 센서/로그 ETL 마트와는 독립적으로 둔다.
set -euo pipefail

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DATAMART_DB_NAME" <<-EOSQL
    CREATE SCHEMA IF NOT EXISTS library AUTHORIZATION "${DATAMART_ETL_USER}";
    GRANT USAGE ON SCHEMA library TO "${DATAMART_ETL_USER}";

    SET ROLE "${DATAMART_ETL_USER}";

    -- 필터(도서관/주제/기간/일반도서) 조건으로 스크랩한 원본 목록, 일자 파티션 overwrite
    CREATE TABLE IF NOT EXISTS library.new_arrival_scan (
        scan_date        DATE NOT NULL,
        rec_key          TEXT NOT NULL,
        book_key         TEXT NOT NULL,
        title            TEXT NOT NULL,
        author           TEXT,
        publisher        TEXT,
        pub_year         TEXT,
        call_number      TEXT,
        isbn             TEXT,
        library_name     TEXT NOT NULL,
        room             TEXT,
        status_text      TEXT NOT NULL,
        is_available     BOOLEAN NOT NULL,
        cover_image_url  TEXT,
        loaded_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (scan_date, rec_key, book_key)
    );
    CREATE INDEX IF NOT EXISTS ix_new_arrival_scan_available
        ON library.new_arrival_scan (scan_date, is_available);

    -- 알라딘 categoryName으로 SF/추리 판별에 성공한 최종 결과, 일자 파티션 overwrite
    CREATE TABLE IF NOT EXISTS library.genre_matches (
        scan_date       DATE NOT NULL,
        rec_key         TEXT NOT NULL,
        book_key        TEXT NOT NULL,
        title           TEXT NOT NULL,
        author          TEXT,
        isbn            TEXT,
        call_number     TEXT,
        matched_genre   TEXT NOT NULL,
        category_path   TEXT NOT NULL,
        checked_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (scan_date, rec_key, book_key)
    );

    RESET ROLE;
EOSQL
