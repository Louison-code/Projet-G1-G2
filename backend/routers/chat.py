from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import time

from backend.database import fetchone, fetchall, execute
from backend.models.conversation import Conversation, ConversationCreate
from backend.services.rag_engine import RAGEngine
from backend.services.llm_adapter import LLMAdapter

router = APIRouter(prefix="/api/chat", tags=["Chatbot RAG"])
rag = RAGEngine()


class QuestionRequest(BaseModel):
    question: str


@router.get("/check")
def verifier_connexion():
    """Teste la connexion au LLM configuré."""
    llm = LLMAdapter()
    erreur = llm.check()
    if erreur:
        return {"status": "error", "message": erreur}
    return {"status": "ok", "message": "LLM connecté et prêt."}


@router.post("")
def poser_question(req: QuestionRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(400, "Question vide")

    debut = time.time()
    resultat = rag.ask(question)
    temps_ms = round((time.time() - debut) * 1000, 2)

    execute(
        "INSERT INTO conversations (question, sql_genere, reponse, resultats_count, temps_execution_ms) "
        "VALUES (?, ?, ?, ?, ?)",
        (question, resultat["sql_genere"], resultat["reponse"],
         len(resultat["resultats"]), temps_ms)
    )

    return {
        "question": question,
        "reponse": resultat["reponse"],
        "sql_genere": resultat["sql_genere"],
        "resultats": resultat["resultats"],
        "temps_ms": temps_ms,
    }


@router.get("/history")
def historique(limite: int = 50):
    return fetchall(
        "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?",
        (limite,)
    )


@router.delete("/history")
def effacer_historique():
    execute("DELETE FROM conversations")
    return {"message": "Historique effacé"}
