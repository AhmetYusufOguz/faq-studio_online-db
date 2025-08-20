import os
import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Local imports
from .db import init_db
from .utils.json_io import ensure_json_file
from .utils.categories import ensure_categories_file, load_categories
from .routes import questions, stats

# Docker Compose ile çalıştırma:
# docker compose build api
# docker compose up -d --force-recreate api
# Logları görmek    :   docker logs -f ai_faq_api

# Durum kontrolü    :   docer ps
# Durdurma          :   docker compose down
# Başlatma          :   docker compose up -d

# PostgreSQL'e bakma:   docker exec -it ai_faq_db psql -U faq -d faqdb
# Soruları listeleme:   SELECT id, question, category, created_at FROM questions ORDER BY id DESC;

# Load environment variables
load_dotenv()

# FastAPI app initialization
app = FastAPI(title="FAQ Studio")

# Template setup
TPL_DIR = pathlib.Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TPL_DIR))

# Environment variables
SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.85"))


@app.on_event("startup")
def startup():
    """Uygulama başlatma işlemleri"""
    ensure_json_file()
    ensure_categories_file()
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Ana sayfa"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "categories": load_categories(), 
            "th_default": SIM_THRESHOLD
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)