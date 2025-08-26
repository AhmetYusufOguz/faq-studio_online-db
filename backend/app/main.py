import os
import pathlib
import uuid
import time
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Local imports
from .db import init_db, get_conn
from .utils.json_io import ensure_json_file
from .utils.categories import ensure_categories_file, load_categories
from .routes import questions, stats
from .logger import logger
from .config import settings
from .utils.chroma_service import chroma_service
from .utils.embeddings import embed

# Docker Compose ile çalıştırma:
# docker compose build api
# docker compose up -d --force-recreate api
# Logları görmek    :   docker logs -f ai_faq_api

# Durum kontrolü    :   docer ps
# Durdurma          :   docker compose down
# Başlatma          :   docker compose up -d

# PostgreSQL'e bakma:   docker exec -it ai_faq_db psql -U faq -d faqdb
# Soruları listeleme:   SELECT id, question, category, created_at, created_by FROM questions ORDER BY id DESC LIMIT 10;
# Soru güncelleme   :   UPDATE questions SET created_by = 'tester1' WHERE id = 33;


# FastAPI app initialization
app = FastAPI(title="FAQ Studio")

# Template setup
TPL_DIR = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TPL_DIR))


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Tüm istekleri loglayan middleware"""
    request_id = str(uuid.uuid4())[:8]
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")[:100]  # Trim long UAs
    
    # X-Forwarded-For support
    if forwarded_for := request.headers.get("x-forwarded-for"):
        client_ip = forwarded_for.split(",")[0].strip()
    
    # Request state'e ekle (diğer fonksiyonlarda kullanmak için)
    request.state.request_id = request_id
    request.state.client_ip = client_ip
    
    logger.debug(
        "REQ [%s] %s %s from %s UA=%s",
        request_id, request.method, request.url.path, client_ip, user_agent
    )
    
    # Latency measurement
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000  # milliseconds
    
    logger.debug(
        "RES [%s] Status: %s Latency: %.2fms",
        request_id, response.status_code, process_time
    )
    return response


async def load_existing_questions_to_chroma():
    """Mevcut soruları ChromaDB'ye yükler"""
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, question, answer, keywords, category FROM questions")
            rows = cur.fetchall()
            
            for row in rows:
                embedding = embed(row["question"])
                chroma_service.add_question(
                    row["id"], row["question"], row["answer"], 
                    row["keywords"], row["category"], embedding.tolist()
                )
                # Küçük bir bekleme süresi ekleyerek Ollama'ya aşırı yük binmesini önle
                await asyncio.sleep(0.1)
            
            logger.info("Loaded %s questions to ChromaDB", len(rows))
    except Exception as e:
        logger.error("Error loading questions to ChromaDB: %s", e)


@app.on_event("startup")
async def startup():
    """Uygulama başlatma işlemleri"""
    logger.info("Application starting…")
    ensure_json_file()
    ensure_categories_file()
    init_db()
    
    # ChromaDB'yi başlat ve embedding fonksiyonunu ayarla
    chroma_service.initialize_embeddings(embed)
    
    # Mevcut soruları ChromaDB'ye yükle
    await load_existing_questions_to_chroma()
    
    logger.info("DB init ok; OLLAMA_BASE_URL=%s EMBED_MODEL=%s", settings.OLLAMA_BASE_URL, settings.EMBED_MODEL)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Ana sayfa"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "categories": load_categories(), 
            "th_default": settings.SIM_THRESHOLD
        }
    )


# Route'ları include et
app.include_router(questions.router)
app.include_router(stats.router)


# Health check endpoint
@app.get("/health")
def health_check():
    """Sağlık kontrolü endpoint'i"""
    return {"status": "healthy", "service": "FAQ Studio"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global hata yakalayıcı"""
    logger.error(
        "Exception: %s - %s req_id=%s ip=%s path=%s",
        type(exc).__name__, str(exc),
        getattr(request.state, 'request_id', 'unknown'),
        getattr(request.state, 'client_ip', 'unknown'),
        request.url.path
    )
    
    # Default error response (isterseniz özelleştirebilirsiniz)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)