"""Moteur RAG — Text-to-SQL sur la base de données."""
import sqlite3
import re
import unicodedata
from backend.database import fetchall, fetchone, get_connection
from backend.config import DB_PATH
from backend.services.llm_adapter import LLMAdapter


def _normaliser(texte: str) -> str:
    return unicodedata.normalize("NFKD", texte).encode("ASCII", "ignore").decode("ASCII").lower()

CAPACITES = """Je peux répondre à des questions sur la base de données d'entreprises industrielles, par exemple :

**Questions générales :**
- « Combien d'entreprises dans la base ? »
- « Quel est le nombre total d'entreprises ? »

**Recherche par localisation :**
- « Quelles entreprises sont à Lille ? »
- « Combien d'entreprises dans le 59 ? »
- « Donne les entreprises de la région PACA »

**Recherche par secteur :**
- « Quels sont les secteurs d'activité ? »
- « Combien d'entreprises dans le secteur automobile ? »
- « Donne les entreprises du code NAF 28.11Z »

**Recherche par nom :**
- « Cherche l'entreprise VALEO »
- « Trouve les entreprises qui contiennent "SAFRAN" »

**Statistiques :**
- « Quel est le capital moyen des entreprises ? »
- « Quelle est la répartition par région ? »
- « Donne le top 10 des villes »

**Scraping et configuration :**
- « Quelles sont les sources de scraping ? »
- « Donne la liste des sites configurés »
- « Quels sont les champs disponibles ? »"""


def _est_question_capacite(question: str) -> bool:
    q = _normaliser(question).rstrip("?!.;,")
    mots_capacite = [
        "ce que tu peux faire", "qu est-ce que tu peux", "que fais-tu",
        "quelles sont tes capacites", "aide", "help", "que sais-tu faire",
        "comment fonctionnes-tu", "a quoi sers-tu", "tu peux faire quoi",
        "disponible", "capable", "what can you do", "commandes",
        "que peux-tu faire", "que peut tu faire", "que peut-on faire",
        "que faire", "tu fais quoi", "comment ca marche", "comment ça marche",
    ]
    return any(m in q for m in mots_capacite)


def _normaliser(texte: str) -> str:
    """Enlève accents et caractères spéciaux pour la comparaison."""
    import unicodedata
    return unicodedata.normalize("NFKD", texte).encode("ASCII", "ignore").decode("ASCII").lower()


def _est_hors_sujet(question: str) -> bool:
    q = _normaliser(question).strip().rstrip("?!.;,")
    mots_hors_sujet = [
        "meteo", "temps qu il fait", "aujourd hui il fait",
        "recette", "cuisine", "gateau", "restaurant",
        "film", "serie", "musique", "chanson",
        "sport", "match", "football", "ligue des champions",
        "politique", "president", "election", "gouvernement",
        "blague", "histoire drole", "raconte",
        "qui es-tu", "ton nom", "comment tu t appelles",
    ]
    if any(m in q for m in mots_hors_sujet):
        return True
    # Salutations seules (pas suivies d'une vraie question)
    if q.strip() in ("salut", "bonjour", "coucou", "hello", "hey", "bonsoir"):
        return True
    return False


def _extraire_sql(reponse: str) -> str:
    """Extrait la requête SQL depuis la réponse du LLM."""
    m = re.search(r"```sql\s*\n?(.*?)\n?```", reponse, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"(SELECT\s+.+?)(?:;|\n\n|$)", reponse, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return reponse.strip()


class RAGEngine:
    def __init__(self, llm: LLMAdapter = None):
        self.llm = llm or LLMAdapter()

    def _batir_schema(self) -> str:
        """Construit la description du schéma de la base de données."""
        tables = fetchall(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        parties = []
        for t in tables:
            nom = t["name"]
            cols = fetchall(f"PRAGMA table_info({nom})")
            colonnes = []
            for c in cols:
                colonnes.append(f"  - {c['name']} ({c['type']})")
            parties.append(f"Table {nom}:\n" + "\n".join(colonnes))
        return "\n\n".join(parties)

    def _exemple_colonnes(self) -> str:
        """Donne des exemples de valeurs pour les colonnes clés."""
        exemples = []
        try:
            e = fetchone(
                "SELECT nom_entreprise, ville, code_naf, departement, region FROM entreprises LIMIT 1"
            )
            if e:
                exemples.append(
                    "Exemple d'une ligne dans entreprises : "
                    + ", ".join(f"{k}='{v}'" for k, v in e.items() if v)
                )
        except Exception:
            pass
        return "\n".join(exemples)

    def _generer_sql(self, question: str) -> str:
        """Étape 1 : le LLM génère une requête SQL depuis la question."""
        schema = self._batir_schema()
        exemples = self._exemple_colonnes()
        prompt = (
            "Tu es un assistant SQL. Tu dois répondre UNIQUEMENT avec une requête SQL "
            "valide pour une base SQLite.\n\n"
            f"Voici le schéma de la base de données :\n\n{schema}\n\n"
            f"{exemples}\n\n"
            "Règles :\n"
            "- Réponds UNIQUEMENT avec la requête SQL, rien d'autre.\n"
            "- Utilise les opérateurs SQLite valides (LIKE, IN, BETWEEN...).\n"
            "- Pour les recherches textuelles, préfère LIKE avec des '%'.\n"
            "- LIMITE les résultats à 20 maximum si non précisé.\n"
            "- N'utilise pas de requêtes d'écriture (INSERT, UPDATE, DELETE, DROP).\n\n"
            f"Question : {question}\n\n"
            "SQL :"
        )
        reponse = self.llm.ask(prompt)
        sql = _extraire_sql(reponse)
        return sql

    def _executer_sql(self, sql: str) -> dict:
        """Exécute une requête SQL en lecture seule et retourne les résultats."""
        sql_strip = sql.strip().upper()
        if not sql_strip.startswith("SELECT"):
            return {"erreur": "Seules les requêtes SELECT sont autorisées.", "lignes": [], "colonnes": []}

        conn = get_connection()
        try:
            cur = conn.execute(sql)
            colonnes = [desc[0] for desc in cur.description]
            lignes = [dict(zip(colonnes, row)) for row in cur.fetchmany(50)]
            return {"lignes": lignes, "colonnes": colonnes, "total": len(lignes)}
        except Exception as e:
            return {"erreur": str(e), "lignes": [], "colonnes": []}
        finally:
            conn.close()

    def _reformuler(self, question: str, sql: str, resultats: dict) -> str:
        """Étape 3 : le LLM reformule les résultats en français."""
        if resultats.get("erreur"):
            return f"Erreur lors de l'exécution de la requête : {resultats['erreur']}"

        lignes = resultats.get("lignes", [])
        if not lignes:
            return "Aucun résultat trouvé pour votre question."

        lignes_texte = "\n".join(
            " | ".join(f"{k}={v}" for k, v in row.items()) for row in lignes[:10]
        )
        prompt = (
            "Tu es un assistant qui répond en français à des questions sur une base "
            "de données d'entreprises industrielles.\n\n"
            f"Question : {question}\n\n"
            f"Requête SQL exécutée : {sql}\n\n"
            f"Résultats ({len(lignes)} lignes) :\n{lignes_texte}\n\n"
            "Réponds en français, de manière claire et concise. "
            "Si les résultats contiennent des entreprises, cite les noms. "
            f"{'Limite l\'affichage aux 10 premiers résultats.' if len(lignes) > 10 else ''}"
        )
        return self.llm.ask(prompt)

    def ask(self, question: str) -> dict:
        """Point d'entrée : pose une question et retourne la réponse structurée."""

        erreur_llm = self.llm.check()
        if erreur_llm:
            return {
                "reponse": "Aucun LLM connecté",
                "sql_genere": "",
                "resultats": [],
                "erreur_sql": erreur_llm,
            }

        if _est_hors_sujet(question):
            return {
                "reponse": "Je suis spécialisé dans la base de données d'entreprises industrielles. "
                           "Je ne peux répondre qu'aux questions sur les entreprises, le scraping "
                           "et la configuration. Tape « aide » pour voir ce que je sais faire.",
                "sql_genere": "",
                "resultats": [],
                "erreur_sql": None,
            }

        if _est_question_capacite(question):
            return {
                "reponse": CAPACITES,
                "sql_genere": "",
                "resultats": [],
                "erreur_sql": None,
            }

        sql = self._generer_sql(question)

        if sql.startswith("Erreur"):
            return {
                "reponse": sql,
                "sql_genere": "",
                "resultats": [],
                "erreur_sql": sql,
            }

        resultats = self._executer_sql(sql)
        if resultats.get("erreur"):
            return {
                "reponse": f"Erreur lors de l'exécution : {resultats['erreur']}",
                "sql_genere": sql,
                "resultats": [],
                "erreur_sql": resultats["erreur"],
            }

        reponse = self._reformuler(question, sql, resultats)
        if reponse.startswith("Erreur"):
            return {
                "sql_genere": sql,
                "resultats": resultats.get("lignes", []),
                "reponse": reponse,
                "erreur_sql": reponse,
            }

        return {
            "sql_genere": sql,
            "resultats": resultats.get("lignes", []),
            "reponse": reponse,
            "erreur_sql": None,
        }
