"""Point d'entrée de l'API FastAPI."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import sites, scraping, dashboard, config_llm, export, chat

app = FastAPI(
    title="API G1-G2 - Réindustrialisation",
    description="Backend de l'application de scraping et RAG pour la réindustrialisation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sites.router)
app.include_router(scraping.router)
app.include_router(dashboard.router)
app.include_router(config_llm.router)
app.include_router(export.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0", "base": "data/base_reindustrialisation.db"}


@app.get("/")
def racine():
    return {
        "application": "API G1-G2 - Réindustrialisation",
        "documentation": "/docs",
        "endpoints": [
            "/api/health",
            "/api/sites",
            "/api/scrape/run",
            "/api/scrape/status",
            "/api/dashboard/stats",
            "/api/config/llm",
            "/api/export",
            "/api/chat",
        ],
    }
