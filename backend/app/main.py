import os, json, pathlib, numpy as np, requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from .db import get_conn, init_db

load_dotenv()
app = FastAPI(title="FAQ Studio")
templates = Jinja2Templates(directory=str(pathlib.Path(__file__).parent / "templates"))
EMBED_MODEL = os.getenv("EMBED_MODEL","bge-m3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL","http://ollama:11434")
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD","0.70"))
JSON_PATH = os.getenv("JSON_PATH","/app/data/questions.json")

def ensure_json_file():
    p = pathlib.Path(JSON_PATH)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        p.write_text("[]", encoding="utf-8")

def embed(text: str):
    r = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=20  # kısa tut ki takılırsa çabuk dönsün
    )
    r.raise_for_status()
    return np.array(r.json().get("embedding"), dtype=np.float32)

@app.on_event("startup")
def startup():
    ensure_json_file()
    init_db()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request,
                                                    "categories": ["tahakkuk","tahsilat","diger"]})

@app.post("/check-duplicate")
def check_duplicate(question: str = Form(...)):
    q = embed(question)
    vec_str = "[" + ",".join(f"{x:.6f}" for x in q.tolist()) + "]"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, question, answer, keywords, category, "
            "       1 - (embedding <=> %s::vector) AS sim "
            "FROM questions ORDER BY embedding <=> %s::vector ASC LIMIT 1",
            (vec_str, vec_str)
        )
        row = cur.fetchone()
    if not row: return {"duplicate": False}
    sim = float(row["sim"])
    # short queries are noisy → require a bit higher sim
    if len(question.split()) < 4 and sim >= (SIM_THRESHOLD + 0.05):
        is_dup = True
    else:
        is_dup = sim >= SIM_THRESHOLD
    return {"duplicate": is_dup, "similarity": sim, "match": row}

@app.post("/add")
def add_item(question: str = Form(...), answer: str = Form(...),
            keywords: str = Form(...), category: str = Form(...)):
    vec = embed(question)
    vec_str = "[" + ",".join(f"{x:.6f}" for x in vec.tolist()) + "]"

    # JSON append
    # data = json.loads(pathlib.Path(JSON_PATH).read_text(encoding="utf-8"))
    # read with 'utf-8-sig' so BOM (if any) is ignored
    raw = pathlib.Path(JSON_PATH).read_text(encoding="utf-8-sig")
    if not raw.strip():
        raw = "[]"
    data = json.loads(raw)
    data.append({"question": question, "answer": answer, "keywords": keywords, "category": category})
    pathlib.Path(JSON_PATH).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # DB insert
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
        cur.execute("SELECT id, question, answer, keywords, category, created_at FROM questions ORDER BY id DESC LIMIT %s OFFSET %s",
                    (limit, offset))
        return cur.fetchall()
