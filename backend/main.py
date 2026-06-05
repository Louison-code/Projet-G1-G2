"""Point d'entrée de l'API FastAPI."""
from fastapi import FastAPI

app = FastAPI(title="API G1-G2 - Réindustrialisation")

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0"}
