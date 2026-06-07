from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests

from backend.database import fetchone, execute

router = APIRouter(prefix="/api/config/llm", tags=["Configuration LLM"])


class LLMConfigUpdate(BaseModel):
    mode: Optional[str] = None
    endpoint: Optional[str] = None
    api_key_chiffree: Optional[str] = None
    modele: Optional[str] = None


@router.get("/models")
def lister_modeles():
    """Liste les modèles disponibles dans Ollama."""
    try:
        config = fetchone("SELECT * FROM config_llm WHERE id = 1")
        endpoint = (config.get("endpoint") or "http://localhost:11434").rstrip("/") if config else "http://localhost:11434"
        r = requests.get(f"{endpoint}/api/tags", timeout=5)
        if r.status_code != 200:
            return {"modeles": [], "erreur": f"Ollama répond avec le statut {r.status_code}"}
        models = r.json().get("models", [])
        # Extraire les noms sans la balise :latest
        noms = []
        for m in models:
            name = m.get("name", "")
            if name.endswith(":latest"):
                name = name[:-7]
            noms.append(name)
        return {"modeles": sorted(noms)}
    except requests.ConnectionError:
        return {"modeles": [], "erreur": "Ollama n'est pas lancé"}
    except Exception as e:
        return {"modeles": [], "erreur": str(e)}


@router.get("")
def get_config():
    config = fetchone("SELECT * FROM config_llm WHERE id = 1")
    if not config:
        return {
            "mode": "local",
            "endpoint": "http://localhost:11434",
            "modele": "llama3.2",
        }
    if config.get("api_key_chiffree"):
        config["api_key_chiffree"] = "***" if config["api_key_chiffree"] else ""
    return config


@router.put("")
def update_config(data: LLMConfigUpdate):
    config = fetchone("SELECT * FROM config_llm WHERE id = 1")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return get_config()

    if "api_key_chiffree" in updates and updates["api_key_chiffree"] in (None, "", "***"):
        del updates["api_key_chiffree"]

    if config:
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        execute(f"UPDATE config_llm SET {set_clause} WHERE id = 1",
                list(updates.values()))
    else:
        cols = ", ".join(updates.keys())
        ph = ", ".join(["?"] * len(updates))
        execute(f"INSERT INTO config_llm ({cols}) VALUES ({ph})",
                list(updates.values()))

    return get_config()
