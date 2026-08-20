from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Connection

from .config import settings

engine = create_engine(settings.datamart_reader_dsn, pool_pre_ping=True)


def get_conn() -> Generator[Connection, None, None]:
    with engine.connect() as conn:
        yield conn
