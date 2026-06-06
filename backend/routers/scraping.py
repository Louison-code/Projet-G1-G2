import threading, time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.database import fetchone, fetchall, execute

router = APIRouter(prefix="/api/scrape", tags=["Scraping"])

scraping_status = {
    "en_cours": False,
    "source": "",
    "demarre_le": None,
    "termine_le": None,
    "total": 0,
    "faits": 0,
    "erreurs": 0,
    "dernier_message": "",
}


class RunRequest(BaseModel):
    source: str = ""
    config: dict = {}


@router.post("/run")
def lancer_scraping(req: RunRequest):
    if scraping_status["en_cours"]:
        raise HTTPException(409, "Un scraping est déjà en cours")

    scraping_status["en_cours"] = True
    scraping_status["source"] = req.source or "toutes"
    scraping_status["demarre_le"] = datetime.now().isoformat()
    scraping_status["total"] = 0
    scraping_status["faits"] = 0
    scraping_status["erreurs"] = 0
    scraping_status["dernier_message"] = "Démarrage..."

    def tache():
        try:
            from backend.services.scraper_manager import lancer_scraping as manager_run
            resultat = manager_run(
                source=req.source or None,
                config=req.config,
                progression=_progress
            )
            scraping_status["dernier_message"] = resultat.get("message", "Terminé")
            scraping_status["total"] = resultat.get("total", 0)
            scraping_status["faits"] = resultat.get("reussites", 0)
        except Exception as e:
            scraping_status["dernier_message"] = f"Erreur: {str(e)}"
        finally:
            scraping_status["en_cours"] = False
            scraping_status["termine_le"] = datetime.now().isoformat()

    t = threading.Thread(target=tache, daemon=True)
    t.start()
    return {"message": "Scraping lancé", "source": req.source or "toutes"}


def _progress(faits, total, message=""):
    scraping_status["faits"] = faits
    scraping_status["total"] = total
    scraping_status["dernier_message"] = str(message)[:200] if message else ""


@router.get("/status")
def status_scraping():
    return scraping_status


@router.post("/stop")
def arreter_scraping():
    if not scraping_status["en_cours"]:
        raise HTTPException(400, "Aucun scraping en cours")
    scraping_status["en_cours"] = False
    scraping_status["dernier_message"] = "Arrêt demandé"
    return {"message": "Arrêt demandé"}


@router.get("/logs")
def logs_erreurs(limite: int = 50, resolu: bool = None):
    if resolu is not None:
        return fetchall(
            "SELECT * FROM logs_erreurs WHERE resolu = ? ORDER BY date_erreur DESC LIMIT ?",
            (int(resolu), limite)
        )
    return fetchall("SELECT * FROM logs_erreurs ORDER BY date_erreur DESC LIMIT ?", (limite,))


@router.post("/relancer-si-besoin")
def relancer_sites_retard():
    maintenant = datetime.now()
    sites = fetchall("SELECT * FROM sites_scraping WHERE actif = 1")
    relances = []
    for site in sites:
        dernier = site.get("date_dernier_scraping")
        if not dernier:
            continue
        try:
            date_dernier = datetime.fromisoformat(dernier)
        except:
            continue
        delai = timedelta(hours=site.get("delai_relance", 720))
        if maintenant - date_dernier > delai:
            execute(
                "UPDATE sites_scraping SET date_dernier_scraping = NULL WHERE id = ?",
                (site["id"],)
            )
            relances.append(site["nom"])
    return {"message": f"{len(relances)} site(s) à relancer", "sites": relances}


@router.get("/sites-a-rescraper")
def sites_a_rescraper():
    maintenant = datetime.now().isoformat()
    return fetchall(
        "SELECT * FROM sites_scraping WHERE actif = 1 AND "
        "(date_dernier_scraping IS NULL OR "
        "  datetime(date_dernier_scraping, '+' || delai_relance || ' hours') < ?)",
        (maintenant,)
    )
