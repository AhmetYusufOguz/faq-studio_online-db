import os, json, pathlib, numpy as np, requests
from typing import Optional
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from .db import get_conn, init_db

# Docker Compose ile çalıştırma:
# docker compose build api
# docker compose up -d --force-recreate api
# Logları görmek    :   docker logs -f ai_faq_api

# Durum kontrolü    :   docer ps
# Durdurma          :   docker compose down
# Başlatma          :   docker compose up -d

# PostgreSQL'e bakma:   docker exec -it ai_faq_db psql -U faq -d faqdb
# Soruları listeleme:   SELECT id, question, category, created_at FROM questions ORDER BY id DESC LIMIT 10;

load_dotenv()
app = FastAPI(title="FAQ Studio")
TPL_DIR = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TPL_DIR))

EMBED_MODEL = os.getenv("EMBED_MODEL","bge-m3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL","http://ollama:11434")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD","0.85"))
JSON_PATH = os.getenv("JSON_PATH","/app/data/questions.json")
CATEGORIES_PATH = "/app/data/categories.json"

def load_categories():
    p = pathlib.Path(CATEGORIES_PATH)
    if p.exists():
        raw = p.read_text(encoding="utf-8-sig").strip()
        if raw:
            return json.loads(raw)
    return ["tahakkuk","tahsilat","diger"]

def ensure_json_file():
    p = pathlib.Path(JSON_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("[]", encoding="utf-8")

def embed(text: str):
    r = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=20
    )
    r.raise_for_status()
    return np.array(r.json().get("embedding"), dtype=np.float32)

def ensure_categories_file():
    p = pathlib.Path(CATEGORIES_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text(json.dumps(["tahakkuk","tahsilat","diger"], ensure_ascii=False, indent=2), encoding="utf-8")

@app.on_event("startup")
def startup():
    ensure_json_file()
    ensure_categories_file()
    init_db()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "categories": load_categories(), "th_default": SIM_THRESHOLD}
    )

@app.post("/check-duplicate")
def check_duplicate(
    request: Request,
    question: str = Form(...),
    th: Optional[float] = Query(None),
    k: int = Query(3, ge=1, le=10),
):
    q = embed(question)
    vec_str = "[" + ",".join(f"{x:.6f}" for x in q.tolist()) + "]"
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
    threshold = float(th) if th is not None else SIM_THRESHOLD
    dup = any(float(r["sim"]) >= threshold for r in rows)
    return {"duplicate": dup, "threshold": threshold,
            "results": [{"id": r["id"], "question": r["question"], "sim": float(r["sim"])} for r in rows]}

@app.post("/add")
def add_item(
    question: str = Form(...),
    answer: str = Form(...),
    keywords: str = Form(...),
    category: str = Form(...)
):
    vec = embed(question)
    vec_str = "[" + ",".join(f"{x:.6f}" for x in vec.tolist()) + "]"

    # Append to JSON (tolerate BOM / empty)
    raw = pathlib.Path(JSON_PATH).read_text(encoding="utf-8-sig")
    if not raw.strip():
        raw = "[]"
    data = json.loads(raw)
    data.append({"question": question, "answer": answer, "keywords": keywords, "category": category})
    pathlib.Path(JSON_PATH).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Update categories.json
    cats = json.loads(pathlib.Path(CATEGORIES_PATH).read_text(encoding="utf-8"))
    if category not in cats:
        cats.append(category)
        pathlib.Path(CATEGORIES_PATH).write_text(json.dumps(cats, ensure_ascii=False, indent=2), encoding="utf-8")

    # Insert into DB
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO questions (question, answer, keywords, category, embedding) "
            "VALUES (%s, %s, %s, %s, %s::vector)",
            (question, answer, keywords, category, vec_str)
        )
        conn.commit()
    return {"ok": True}

@app.get("/questions")
def list_questions(limit: int = 50, offset: int = 0):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, question, answer, keywords, category, created_at "
            "FROM questions ORDER BY id DESC LIMIT %s OFFSET %s",
            (limit, offset)
        )
        return cur.fetchall()

@app.get("/questions-table", response_class=HTMLResponse)
def questions_table(request: Request):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, question, category, created_at FROM questions ORDER BY id DESC LIMIT 100"
        )
        rows = cur.fetchall()
    return templates.TemplateResponse("questions.html", {"request": request, "rows": rows})
