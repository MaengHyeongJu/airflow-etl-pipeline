import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from library_scanner.aladin_client import classify_genre, extract_category_paths, extract_description


def test_extract_category_paths_handles_list_shape():
    item = {
        "categoryIdList": {
            "categoryInfo": [
                {"categoryId": 1, "categoryName": "국내도서>소설/시/희곡>한국소설>추리/미스터리/스릴러"},
                {"categoryId": 2, "categoryName": "국내도서>베스트셀러"},
            ]
        }
    }
    assert extract_category_paths(item) == [
        "국내도서>소설/시/희곡>한국소설>추리/미스터리/스릴러",
        "국내도서>베스트셀러",
    ]


def test_extract_category_paths_handles_single_dict_shape():
    item = {"categoryIdList": {"categoryInfo": {"categoryId": 1, "categoryName": "국내도서>소설/시/희곡>SF"}}}
    assert extract_category_paths(item) == ["국내도서>소설/시/희곡>SF"]


def test_extract_category_paths_falls_back_to_top_level_category_name():
    item = {"categoryName": "국내도서>소설/시/희곡>한국소설"}
    assert extract_category_paths(item) == ["국내도서>소설/시/희곡>한국소설"]


def test_classify_genre_matches_sf():
    item = {"categoryIdList": {"categoryInfo": [{"categoryName": "국내도서>소설/시/희곡>외국소설>SF"}]}}
    assert classify_genre(item) == ("SF", "국내도서>소설/시/희곡>외국소설>SF")


def test_classify_genre_matches_mystery():
    item = {"categoryIdList": {"categoryInfo": [{"categoryName": "국내도서>소설/시/희곡>한국소설>추리/미스터리/스릴러"}]}}
    genre, path = classify_genre(item)
    assert genre == "MYSTERY"


def test_classify_genre_returns_none_for_unrelated_category():
    item = {"categoryIdList": {"categoryInfo": [{"categoryName": "국내도서>에세이"}]}}
    assert classify_genre(item) is None


def test_extract_description_normalizes_whitespace():
    item = {"description": "  줄거리\n  요약  텍스트  "}
    assert extract_description(item) == "줄거리 요약 텍스트"


def test_extract_description_truncates_long_text():
    item = {"description": "가" * 400}
    result = extract_description(item, max_length=300)
    assert len(result) == 300
    assert result.endswith("…")


def test_extract_description_returns_none_when_missing():
    assert extract_description({}) is None
    assert extract_description({"description": ""}) is None
