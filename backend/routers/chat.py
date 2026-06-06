from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.database import fetchone, fetchall, execute
from backend.models.conversation import Conversation, ConversationCreate

router = APIRouter(prefix="/api/chat", tags=["Chatbot RAG"])


class QuestionRequest(BaseModel):
    question: str


@router.post("")
def poser_question(req: QuestionRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(400, "Question vide")

    import time
    debut = time.time()

    # Stub : réponse simple basée sur des mots-clés
    q = question.lower()

    if "combien" in q and ("entreprise" in q or "societe" in q):
        total = fetchone("SELECT COUNT(*) AS n FROM entreprises")
        n = total["n"] if total else 0
        reponse = f"Il y a actuellement {n} entreprises dans la base de données."
        sql = "SELECT COUNT(*) FROM entreprises"

    elif "siren" in q:
        mot = q.replace("siren", "").strip()
        if mot and mot[-1] == "?":
            mot = mot[:-1]
        if mot:
            entreprise = fetchone("SELECT * FROM entreprises WHERE siren LIKE ?", (f"%{mot}%",))
            if entreprise:
                reponse = f"Entreprise trouvée : {entreprise['nom_entreprise']} (SIREN: {entreprise['siren']}), {entreprise['ville']}"
                sql = f"SELECT * FROM entreprises WHERE siren LIKE '%{mot}%'"
            else:
                reponse = f"Aucune entreprise trouvée avec ce SIREN."
                sql = f"SELECT * FROM entreprises WHERE siren LIKE '%{mot}%'"
        else:
            reponse = "Veuillez préciser un numéro SIREN."
            sql = ""

    elif "secteur" in q or "filiere" in q:
        secteurs = fetchall("SELECT secteur_ia, COUNT(*) AS n FROM entreprises WHERE secteur_ia IS NOT NULL AND secteur_ia != '' GROUP BY secteur_ia ORDER BY n DESC")
        if secteurs:
            lignes = "\n".join(f"- {s['secteur_ia']}: {s['n']} entreprises" for s in secteurs)
            reponse = f"Répartition par secteur IA :\n{lignes}"
        else:
            reponse = "Aucune classification par secteur disponible."
        sql = "SELECT secteur_ia, COUNT(*) FROM entreprises GROUP BY secteur_ia"

    elif "dernier" in q or "recent" in q:
        dernier = fetchone("SELECT nom_entreprise, date_scraping FROM entreprises ORDER BY date_scraping DESC LIMIT 1")
        if dernier and dernier.get("date_scraping"):
            reponse = f"Dernière entreprise scrapée : {dernier['nom_entreprise']} le {dernier['date_scraping']}"
        else:
            reponse = "Aucun scraping récent."
        sql = "SELECT nom_entreprise, date_scraping FROM entreprises ORDER BY date_scraping DESC LIMIT 1"

    elif "aide" in q or "help" in q or "peux" in q:
        reponse = (
            "Je peux répondre à des questions comme :\n"
            "- « Combien d'entreprises dans la base ? »\n"
            "- « Cherche le SIREN 562082909 »\n"
            "- « Quels sont les secteurs IA ? »\n"
            "- « Dernière entreprise scrapée »"
        )
        sql = ""

    else:
        reponse = "Je n'ai pas compris votre question. Tapez « aide » pour voir les questions possibles."
        sql = ""

    temps_ms = round((time.time() - debut) * 1000, 2)

    # Enregistrer la conversation
    execute(
        "INSERT INTO conversations (question, sql_genere, reponse, resultats_count, temps_execution_ms) "
        "VALUES (?, ?, ?, ?, ?)",
        (question, sql, reponse, 0 if not sql else 1, temps_ms)
    )

    return {
        "question": question,
        "reponse": reponse,
        "sql_genere": sql,
        "temps_ms": temps_ms,
    }


@router.get("/history")
def historique(limite: int = 20):
    return fetchall(
        "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?",
        (limite,)
    )
