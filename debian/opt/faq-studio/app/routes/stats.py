from fastapi import APIRouter, Request
from ..db import get_conn
from ..logger import logger

router = APIRouter()


@router.get("/stats/categories")
def stats_categories(request: Request):
    """Kategorilere göre soru sayılarını döndürür"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT category, COUNT(*) AS cnt
            FROM questions
            GROUP BY category
            ORDER BY cnt DESC, category
        """)
        result = cur.fetchall()
    
    logger.debug(
        "Categories stats req_id=%s ip=%s",
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    return result


@router.get("/stats/total")
def stats_total(request: Request):
    """Toplam soru sayısını döndürür"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS total FROM questions")
        row = cur.fetchone()
        total = row["total"]
    
    logger.debug(
        "Total count=%s req_id=%s ip=%s",
        total,
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    return {"total": total}


@router.get("/stats/recent")
def stats_recent(request: Request, days: int = 7):
    """Son N gün içindeki soru sayısını döndürür"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS recent_count
            FROM questions
            WHERE created_at >= NOW() - INTERVAL '%s days'
        """, (days,))
        row = cur.fetchone()
        recent_count = row["recent_count"]
    
    logger.debug(
        "Recent count=%s days=%s req_id=%s ip=%s",
        recent_count, days,
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    return {"recent_count": recent_count, "days": days}


@router.get("/stats/by-date")
def stats_by_date(request: Request, limit: int = 30):
    """Günlere göre soru sayılarını döndürür"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM questions
            WHERE created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, (limit,))
        result = cur.fetchall()
    
    logger.debug(
        "Stats by date limit=%s count=%s req_id=%s ip=%s",
        limit, len(result),
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    return result