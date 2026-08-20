from datetime import date, timedelta


def date_key(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def default_date_range(days: int = 30) -> tuple[date, date]:
    today = date.today()
    return today - timedelta(days=days), today
