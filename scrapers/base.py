from abc import ABC, abstractmethod
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                       "data", "base_reindustrialisation.db")

COLONNES_CLIENT = [
    "url", "nom_entreprise", "roles", "description", "code_postal",
    "ville", "pays", "telephone", "fax", "email", "site_web",
    "siren", "siret", "tva", "capital", "forme_juridique",
    "annee_creation", "effectif_adresse", "effectif_entreprise",
    "activites_principales", "activites_secondaires", "autres_classifications"
]


class BaseScraper(ABC):

    @abstractmethod
    def run(self, config: dict = None, progression: callable = None) -> list[dict]:
        pass

    @property
    @abstractmethod
    def nom_source(self) -> str:
        pass

    # ── Connexion DB ──

    def _db(self):
        return sqlite3.connect(DB_PATH)

    def _date_now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Upsert intelligent par SIREN ──

    def _upsert(self, donnees: dict) -> bool:
        """
        Insère ou complète une entreprise par SIREN.
        - SIREN existe déjà : on ne remplit que les champs vides/manquants
        - SIREN nouveau : on insère la ligne
        Retourne True si insertion, False si mise à jour.
        """
        siren = donnees.get("siren", "").strip()
        if not siren:
            return False

        conn = self._db()
        try:
            cur = conn.execute("SELECT * FROM entreprises WHERE siren = ?", (siren,))
            ligne = cur.fetchone()

            date_maintenant = self._date_now()

            if ligne:
                noms_colonnes = [desc[0] for desc in cur.description]
                existant = dict(zip(noms_colonnes, ligne))

                champs_a_maj = {}
                for k, v in donnees.items():
                    if k in existant and k not in ("id", "date_scraping", "statut_scraping"):
                        val_actuelle = existant.get(k)
                        nouvelle_val = str(v).strip() if v else ""
                        if nouvelle_val and not (val_actuelle and str(val_actuelle).strip()):
                            champs_a_maj[k] = nouvelle_val

                if champs_a_maj:
                    champs_a_maj["date_scraping"] = date_maintenant
                    set_clause = ", ".join(f"{k} = ?" for k in champs_a_maj)
                    conn.execute(
                        f"UPDATE entreprises SET {set_clause} WHERE siren = ?",
                        list(champs_a_maj.values()) + [siren]
                    )
                    conn.commit()
                return False
            else:
                colonnes = list(donnees.keys())
                valeurs = list(donnees.values())
                if "date_scraping" not in colonnes:
                    colonnes.append("date_scraping")
                    valeurs.append(date_maintenant)
                if "statut_scraping" not in colonnes:
                    colonnes.append("statut_scraping")
                    valeurs.append("success")
                if "pays" not in colonnes:
                    colonnes.append("pays")
                    valeurs.append("France")

            cols = ", ".join(colonnes)
            ph = ", ".join(["?"] * len(colonnes))
            conn.execute(
                f"INSERT INTO entreprises ({cols}) VALUES ({ph})",
                valeurs
            )
            conn.commit()
            return True

        finally:
            conn.close()

    # ── Helper : marquer une erreur dans logs_erreurs ──

    def _log_erreur(self, url: str, code: str, message: str, entreprise_id: int = None):
        conn = self._db()
        try:
            conn.execute(
                "INSERT INTO logs_erreurs (entreprise_id, url, code_erreur, message_erreur) "
                "VALUES (?, ?, ?, ?)",
                (entreprise_id, url, code, message)
            )
            conn.commit()
        finally:
            conn.close()
