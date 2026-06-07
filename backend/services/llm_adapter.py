"""Adaptateur LLM — Ollama uniquement (pour l'instant)."""
import requests
from backend.database import fetchone


class LLMAdapter:
    def __init__(self, config: dict = None):
        self._config_override = config

    def _load_config(self) -> dict:
        if self._config_override:
            return self._config_override
        cfg = fetchone("SELECT * FROM config_llm WHERE id = 1")
        return cfg or {}

    def check(self) -> str | None:
        """Vérifie que le LLM configuré est accessible.
        Retourne None si OK, un message d'erreur sinon."""
        config = self._load_config()
        endpoint = (config.get("endpoint") or "http://localhost:11434").rstrip("/")
        modele = config.get("modele") or "phi3.5"
        try:
            r = requests.get(f"{endpoint}/api/tags", timeout=5)
            if r.status_code != 200:
                return f"Ollama répond avec le statut {r.status_code}."
            models = r.json().get("models", [])
            noms_modeles = []
            for m in models:
                name = m.get("name", "")
                noms_modeles.append(name)
                if modele in name:
                    return None
            dispo = ", ".join(noms_modeles[:5])
            return (
                f"Modèle '{modele}' introuvable. "
                f"Lance 'ollama pull {modele}' dans un terminal. "
                f"Modèles disponibles : {dispo or 'aucun'}"
            )
        except requests.ConnectionError:
            return (
                "Ollama n'est pas lancé. "
                "Démarre Ollama (icône dans la barre des tâches) ou lance 'ollama serve'."
            )
        except Exception as e:
            return f"Erreur de connexion à Ollama : {e}"

    def ask(self, prompt: str, timeout: int = 120) -> str:
        config = self._load_config()
        endpoint = (config.get("endpoint") or "http://localhost:11434").rstrip("/")
        modele = config.get("modele") or "phi3.5"
        try:
            r = requests.post(
                f"{endpoint}/api/generate",
                json={"model": modele, "prompt": prompt, "stream": False},
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json().get("response", "")
        except Exception as e:
            return f"Erreur LLM : {e}"
