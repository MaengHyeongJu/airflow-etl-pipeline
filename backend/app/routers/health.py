from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..db import get_conn

router = APIRouter(tags=["health"])


@router.get("/health")
def health(conn: Connection = Depends(get_conn)) -> dict:
    conn.execute(text("SELECT 1"))
    return {"status": "ok"}
