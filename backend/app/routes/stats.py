from fastapi import APIRouter
from ..db import get_conn

router = APIRouter()


@router.get("/stats/categories")
def stats_categories():
    """Kategorilere göre soru sayılarını döndürür"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT category, COUNT(*) AS cnt
            FROM questions
            GROUP BY category
            ORDER BY cnt DESC, category
        """)
        return cur.fetchall()


@router.get("/stats/total")
def stats_total():
    """Toplam soru sayısını döndürür"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM questions")
        row = cur.fetchone()
        return {"total": row["total"]}


@router.get("/stats/recent")
def stats_recent(days: int = 7):
    """Son N gün içindeki soru sayısını döndürür"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS recent_count
            FROM questions
            WHERE created_at >= NOW() - INTERVAL '%s days'
        """, (days,))
        row = cur.fetchone()
        return {"recent_count": row["recent_count"], "days": days}


@router.get("/stats/by-date")
def stats_by_date(limit: int = 30):
    """Günlere göre soru sayılarını döndürür"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM questions
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (limit,))
        return cur.fetchall()