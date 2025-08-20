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


# Router ve template setup
router = APIRouter()
TPL_DIR = pathlib.Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TPL_DIR))

# Environment variables
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.85"))


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
    threshold = float(th) if th is not None else SIM_THRESHOLD
    dup = any(float(r["sim"]) >= threshold for r in rows)
    
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
    question: str = Form(...),
    answer: str = Form(...),
    keywords: str = Form(...),
    category: str = Form(...)
):
    """Yeni soru ekler"""
    # Embedding hesapla
    vec = embed(question)
    vec_str = embedding_to_vector_str(vec)

    # Veritabanına ekle ve ID al
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO questions (question, answer, keywords, category, embedding) "
            "VALUES (%s, %s, %s, %s, %s::vector) RETURNING id",
            (question, answer, keywords, category, vec_str)
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
        "category": category
    }
    append_question_to_json(question_data)

    # Kategoriyi güncelle (yoksa ekle)
    add_category_if_new(category)

    return {"ok": True, "id": new_id}


@router.get("/questions")
def list_questions(limit: int = 50, offset: int = 0):
    """Soruları listeler"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, question, answer, keywords, category, created_at "
            "FROM questions ORDER BY id DESC LIMIT %s OFFSET %s",
            (limit, offset)
        )
        return cur.fetchall()


@router.get("/questions-table", response_class=HTMLResponse)
def questions_table(request: Request):
    """Soruları HTML tablosu olarak döndürür"""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, question, category, created_at FROM questions ORDER BY id DESC LIMIT 100"
        )
        rows = cur.fetchall()
    return templates.TemplateResponse("questions.html", {"request": request, "rows": rows})


@router.delete("/questions/{qid}")
def delete_question(qid: int):
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
    
    return {"ok": True, "deleted_id": qid, "json_updated": success}


@router.get("/questions/search")
def search_questions(query: str, limit: int = 50, offset: int = 0):
    """Soruları arar"""
    like_pattern = f"%{query}%"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, question, answer, keywords, category, created_at
            FROM questions
            WHERE question ILIKE %s OR answer ILIKE %s OR keywords ILIKE %s OR category ILIKE %s
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """, (like_pattern, like_pattern, like_pattern, like_pattern, limit, offset))
        return cur.fetchall()


@router.get("/categories.json")
def get_categories():
    """Kategorileri JSON formatında döndürür"""
    return load_categories()