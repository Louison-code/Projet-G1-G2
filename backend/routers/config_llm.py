from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.database import fetchone, execute

router = APIRouter(prefix="/api/config/llm", tags=["Configuration LLM"])


class LLMConfigUpdate(BaseModel):
    mode: Optional[str] = None
    endpoint: Optional[str] = None
    api_key_chiffree: Optional[str] = None
    modele: Optional[str] = None
    prompt_system: Optional[str] = None


@router.get("")
def get_config():
    config = fetchone("SELECT * FROM config_llm WHERE id = 1")
    if not config:
        return {
            "mode": "local",
            "endpoint": "http://localhost:11434",
            "modele": "llama3.2",
            "prompt_system": "",
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
