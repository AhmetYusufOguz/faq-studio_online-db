import os
from typing import Optional
from fastapi import APIRouter, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pathlib

from ..db import get_conn
from ..utils.embeddings import embed, embedding_to_vector_str
from ..utils.json_io import append_question_to_json, remove_question_from_json
from ..utils.categories import load_categories, add_category_if_new
from ..logger import logger
from ..config import settings


# Router ve template setup
router = APIRouter()
TPL_DIR = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TPL_DIR))

# Environment variables
DEFAULT_THRESHOLD = settings.SIM_THRESHOLD


@router.post("/check-duplicate")
def check_duplicate(
    request: Request,
    question: str = Form(...),
    th: Optional[float] = Query(None),
    k: int = Query(3, ge=1, le=10),
):
    """Benzer soru kontrolü yapar"""
    # Embedding hesapla
    q = embed(question)
    vec_str = embedding_to_vector_str(q)
    
    # Veritabanından benzer soruları bul
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, question, answer, keywords, category, "
            "       1 - (embedding <=> %s::vector) AS sim "
            "FROM questions "
            "ORDER BY embedding <=> %s::vector ASC LIMIT %s",
            (vec_str, vec_str, k)
        )
        rows = cur.fetchall()
    
    if not rows:
        return {"duplicate": False, "results": []}
    
    # Benzerlik kontrolü
    threshold = float(th) if th is not None else DEFAULT_THRESHOLD
    dup = any(float(r["sim"]) >= threshold for r in rows)
    
    logger.debug(
        "Duplicate check qlen=%s th=%.2f topk=%s result=%s req_id=%s ip=%s",
        len(question), threshold, k, {"duplicate": dup},
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    
    return {
        "duplicate": dup, 
        "threshold": threshold,
        "results": [
            {"id": r["id"], "question": r["question"], "sim": float(r["sim"])} 
            for r in rows
        ]
    }


@router.post("/add")
def add_question(
    request: Request,
    question: str = Form(...),
    answer: str = Form(...),
    keywords: str = Form(...),
    category: str = Form(...),
    created_by: str = Form("anonymous")  # 👈 yeni alan
):
    """Yeni soru ekler"""
    # Embedding hesapla
    vec = embed(question)
    vec_str = embedding_to_vector_str(vec)

    # Veritabanına ekle ve ID al - created_by alanını da ekle!
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO questions (question, answer, keywords, category, embedding, created_by) "  # 👈 created_by eklendi
            "VALUES (%s, %s, %s, %s, %s::vector, %s) RETURNING id",  # 👈 %s eklendi
            (question, answer, keywords, category, vec_str, created_by)  # 👈 created_by eklendi
        )
        result = cur.fetchone()
        new_id = result.get("id") if hasattr(result, 'get') else result[0]
        conn.commit()

    # JSON dosyasına ekle
    question_data = {
        "id": new_id, 
        "question": question, 
        "answer": answer, 
        "keywords": keywords, 
        "category": category,
        "created_by": created_by  # 👈 JSON'a da ekle
    }
    append_question_to_json(question_data)

    # Kategoriyi güncelle (yoksa ekle)
    add_category_if_new(category)

    logger.info(
        "Added id=%s cat=%s qlen=%s by=%s req_id=%s ip=%s",
        new_id, category, len(question), created_by,
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    
    return {"ok": True, "id": new_id}


@router.get("/questions")
def list_questions(
    request: Request,
    limit: int = 50, 
    offset: int = 0
):
    """Soruları listeler"""
    logger.debug(
        "List questions limit=%s offset=%s req_id=%s ip=%s",
        limit, offset,
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, question, answer, keywords, category, created_at, created_by "  # 👈 created_by eklendi
            "FROM questions ORDER BY id DESC LIMIT %s OFFSET %s",
            (limit, offset)
        )
        return cur.fetchall()


@router.get("/questions-table", response_class=HTMLResponse)
def questions_table(request: Request):
    """Soruları HTML tablosu olarak döndürür"""
    logger.debug(
        "Questions table req_id=%s ip=%s",
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, question, category, created_at FROM questions ORDER BY id DESC LIMIT 100"
        )
        rows = cur.fetchall()
    return templates.TemplateResponse("questions.html", {"request": request, "rows": rows})


@router.delete("/questions/{qid}")
def delete_question(
    request: Request,
    qid: int,
    deleted_by: str = Form("anonymous")  # 👈 Sadece log için
):
    """Soru siler"""
    # Veritabanından sil
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM questions WHERE id = %s RETURNING id", (qid,))
        deleted = cur.fetchone()
        if not deleted:
            raise HTTPException(status_code=404, detail="Soru bulunamadı")
        conn.commit()

    # JSON dosyasından sil
    success = remove_question_from_json(qid)
    
    logger.info(
        "Deleted id=%s deleted_by=%s req_id=%s ip=%s",
        qid, deleted_by,  # 👈 Silen kişiyi logla (sadece log için)
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    
    return {"ok": True, "deleted_id": qid, "json_updated": success}


@router.get("/questions/search")
def search_questions(
    request: Request,
    query: str, 
    limit: int = 50, 
    offset: int = 0
):
    """Soruları arar"""
    logger.debug(
        "Search query=%s limit=%s offset=%s req_id=%s ip=%s",
        query, limit, offset,
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    
    like_pattern = f"%{query}%"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, question, answer, keywords, category, created_at, created_by
            FROM questions
            WHERE question ILIKE %s OR answer ILIKE %s OR keywords ILIKE %s OR category ILIKE %s
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (like_pattern, like_pattern, like_pattern, like_pattern, limit, offset))
        return cur.fetchall()


@router.get("/categories.json")
def get_categories(request: Request):
    """Kategorileri JSON formatında döndürür"""
    logger.debug(
        "Get categories req_id=%s ip=%s",
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown')
    )
    
    return load_categories()