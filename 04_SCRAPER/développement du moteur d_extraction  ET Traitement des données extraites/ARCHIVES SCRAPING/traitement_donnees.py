"""
============================================================
PROJET G1/G2 - F-2049 | Réindustrialisation Française
T3.1.4 : Traitement des données extraites
============================================================
Auteurs (RACI R) : Yessine Hachicha
Accountable (A)  : Louison Baudouin
Date             : 2026
------------------------------------------------------------
Ce module prend en entrée les données brutes insérées en base
par scraper_kompass.py et les normalise avant envoi à l'IA (T2).

Étapes :
  1. Chargement depuis SQLite (entreprises.db)
  2. Nettoyage Regex des champs texte
  3. Standardisation des formats (dates, CA, effectifs)
  4. Dédoublonnage
  5. Export CSV/JSON propre pour le Groupe IA (T2)
============================================================
"""

import sqlite3
import re
import json
import csv
import logging
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================
CONFIG = {
    "db_path":           "entreprises.db",
    "export_csv":        "export_ia_kompass.csv",
    "export_json":       "export_ia_kompass.json",
    "log_path":          "traitement_donnees.log",
    "seuil_ca_min":      0,              # CA minimum pour garder l'entrée
    "seuil_effectifs_min": 0,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(CONFIG["log_path"], encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("TraitementDonnees")


# ============================================================
# SECTION 1 : NETTOYAGE REGEX DES CHAMPS
# (T4.3.1 - Scripts de nettoyage Regex)
# ============================================================

def nettoyer_texte(texte: str) -> str:
    """Supprime les caractères spéciaux, normalise les espaces."""
    if not texte:
        return ""
    texte = re.sub(r"[^\w\s\-\.,;\:\(\)@\/]", " ", texte, flags=re.UNICODE)
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte


def normaliser_siren(siren: str) -> str:
    """Garde uniquement les 9 chiffres du SIREN."""
    if not siren:
        return ""
    chiffres = re.sub(r"\D", "", siren)
    return chiffres[:9] if len(chiffres) >= 9 else ""


def normaliser_siret(siret: str) -> str:
    """Garde uniquement les 14 chiffres du SIRET."""
    if not siret:
        return ""
    chiffres = re.sub(r"\D", "", siret)
    return chiffres[:14] if len(chiffres) >= 14 else ""


def normaliser_code_naf(code_naf: str) -> str:
    """Format attendu : 4 chiffres + 1 lettre majuscule (ex: 6201Z)."""
    if not code_naf:
        return ""
    m = re.search(r"(\d{4}[A-Za-z])", code_naf)
    return m.group(1).upper() if m else ""


def normaliser_date(date_str: str) -> str:
    """
    Tente de parser la date en format AAAA-MM-JJ.
    Accepte : 'AAAA', 'JJ/MM/AAAA', 'AAAA-MM-JJ'.
    """
    if not date_str:
        return ""
    date_str = date_str.strip()
    # Format AAAA seul
    if re.fullmatch(r"\d{4}", date_str):
        return f"{date_str}-01-01"
    # Format JJ/MM/AAAA
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    # Déjà au bon format
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_str):
        return date_str
    return ""


def normaliser_chiffre_affaires(valeur) -> float | None:
    """
    Convertit des chaînes du type '1.2M €', '1,2 M€', '1200000' en float euros.
    """
    if valeur is None:
        return None
    if isinstance(valeur, (int, float)):
        return float(valeur)
    valeur = str(valeur).strip()
    # Millions
    m = re.search(r"([\d\.,]+)\s*[Mm]", valeur)
    if m:
        try:
            return float(m.group(1).replace(",", ".")) * 1_000_000
        except ValueError:
            pass
    # Milliers
    m = re.search(r"([\d\.,]+)\s*[Kk]", valeur)
    if m:
        try:
            return float(m.group(1).replace(",", ".")) * 1_000
        except ValueError:
            pass
    # Nombre brut
    valeur_propre = re.sub(r"[^\d,\.]", "", valeur).replace(",", ".")
    try:
        return float(valeur_propre)
    except ValueError:
        return None


def normaliser_effectifs(valeur) -> int | None:
    """Extrait un entier propre depuis un champ effectifs."""
    if valeur is None:
        return None
    if isinstance(valeur, int):
        return valeur
    m = re.search(r"(\d+)", str(valeur))
    return int(m.group(1)) if m else None


def normaliser_url(url: str) -> str:
    """Normalise une URL : lowercase scheme, supprime trailing slash."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")


# ============================================================
# SECTION 2 : DÉDOUBLONNAGE
# (T4.3.3 - Dédoublonnage et Intégrité)
# ============================================================

def detecter_doublons(entreprises: list[dict]) -> list[dict]:
    """
    Détecte les doublons basés sur le SIREN.
    Conserve l'entrée avec le plus de champs renseignés.
    """
    vus_siren = {}
    for ent in entreprises:
        siren = ent.get("siren", "")
        if not siren:
            continue
        if siren not in vus_siren:
            vus_siren[siren] = ent
        else:
            # Garder l'entrée la plus complète (nb de champs non-vides)
            ancien = vus_siren[siren]
            score_nouveau = sum(1 for v in ent.values() if v)
            score_ancien  = sum(1 for v in ancien.values() if v)
            if score_nouveau > score_ancien:
                vus_siren[siren] = ent

    doublons = len(entreprises) - len(vus_siren)
    logger.info(f"Dédoublonnage : {doublons} doublons supprimés sur {len(entreprises)} entrées")
    return list(vus_siren.values())


# ============================================================
# SECTION 3 : VALIDATION D'INTÉGRITÉ
# (T4.3.3 - Intégrité)
# ============================================================

def valider_entreprise(ent: dict) -> tuple[bool, list[str]]:
    """
    Vérifie la cohérence d'un enregistrement.
    Retourne (valide: bool, erreurs: list[str]).
    """
    erreurs = []
    if not ent.get("raison_sociale"):
        erreurs.append("raison_sociale manquante")
    if ent.get("siren") and len(ent["siren"]) != 9:
        erreurs.append(f"SIREN invalide: {ent['siren']}")
    if ent.get("siret") and len(ent["siret"]) != 14:
        erreurs.append(f"SIRET invalide: {ent['siret']}")
    if ent.get("chiffre_affaires") and ent["chiffre_affaires"] < 0:
        erreurs.append("CA négatif incohérent")
    if ent.get("effectifs") and ent["effectifs"] < 0:
        erreurs.append("Effectifs négatifs incohérents")
    return len(erreurs) == 0, erreurs


# ============================================================
# SECTION 4 : PIPELINE COMPLET
# ============================================================

def pipeline_nettoyage(db_path: str) -> list[dict]:
    """
    Pipeline complet : chargement → nettoyage → dédup → validation.
    Retourne la liste des entreprises propres pour le Groupe IA (T2).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Charger uniquement les entrées scrapées avec succès
    cursor.execute("""
        SELECT lien_kompass, raison_sociale, siren, siret, code_naf,
               forme_juridique, date_creation, adresse, ville, code_postal,
               departement, site_web, telephone, email,
               chiffre_affaires, effectifs, description, html_brut,
               date_scraping
        FROM entreprises
        WHERE statut_scraping = 'success'
    """)
    rows = cursor.fetchall()
    conn.close()

    logger.info(f"Entreprises chargées depuis la base : {len(rows)}")

    entreprises_propres = []
    nb_invalides = 0

    for row in rows:
        ent = dict(row)

        # --- Nettoyage champ par champ ---
        ent["raison_sociale"]   = nettoyer_texte(ent.get("raison_sociale", ""))
        ent["siren"]            = normaliser_siren(ent.get("siren", ""))
        ent["siret"]            = normaliser_siret(ent.get("siret", ""))
        ent["code_naf"]         = normaliser_code_naf(ent.get("code_naf", ""))
        ent["date_creation"]    = normaliser_date(ent.get("date_creation", ""))
        ent["ville"]            = nettoyer_texte(ent.get("ville", ""))
        ent["code_postal"]      = ent.get("code_postal", "") or ""
        ent["site_web"]         = normaliser_url(ent.get("site_web", ""))
        ent["chiffre_affaires"] = normaliser_chiffre_affaires(ent.get("chiffre_affaires"))
        ent["effectifs"]        = normaliser_effectifs(ent.get("effectifs"))
        ent["description"]      = nettoyer_texte(ent.get("description", ""))

        # Supprimer le HTML brut de l'export (trop volumineux pour CSV)
        html_pour_ia = ent.pop("html_brut", "")

        # --- Validation ---
        valide, erreurs = valider_entreprise(ent)
        if not valide:
            logger.warning(f"[INVALIDE] {ent.get('raison_sociale')} → {erreurs}")
            nb_invalides += 1

        entreprises_propres.append(ent)

    logger.info(f"Nettoyage terminé : {len(entreprises_propres)} entrées")
    logger.info(f"Entrées avec avertissements : {nb_invalides}")

    # --- Dédoublonnage ---
    entreprises_propres = detecter_doublons(entreprises_propres)
    return entreprises_propres


def exporter_csv(entreprises: list[dict], chemin: str):
    """Export CSV pour compatibilité Excel / Power Query."""
    if not entreprises:
        logger.warning("Aucune donnée à exporter en CSV.")
        return
    champs = list(entreprises[0].keys())
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entreprises)
    logger.info(f"Export CSV : {chemin} ({len(entreprises)} lignes)")


def exporter_json(entreprises: list[dict], chemin: str):
    """Export JSON structuré pour le Groupe IA (T2)."""
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(entreprises, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"Export JSON : {chemin} ({len(entreprises)} entrées)")


# ============================================================
# POINT D'ENTRÉE
# ============================================================
def main():
    logger.info("=" * 60)
    logger.info("PROJET G1/G2 | Traitement Données Kompass v1.0")
    logger.info(f"Démarrage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    db_path = CONFIG["db_path"]
    if not Path(db_path).exists():
        logger.error(f"Base de données introuvable : {db_path}")
        logger.error("Lancez d'abord scraper_kompass.py pour peupler la base.")
        return

    # Pipeline de nettoyage
    entreprises_propres = pipeline_nettoyage(db_path)

    if not entreprises_propres:
        logger.warning("Aucune donnée propre disponible. Vérifiez la base.")
        return

    # Exports
    exporter_csv(entreprises_propres,  CONFIG["export_csv"])
    exporter_json(entreprises_propres, CONFIG["export_json"])

    logger.info("=" * 60)
    logger.info("TRAITEMENT TERMINÉ")
    logger.info(f"Fichiers générés :")
    logger.info(f"  → {CONFIG['export_csv']} (pour Power BI / Power Query)")
    logger.info(f"  → {CONFIG['export_json']} (pour le Groupe IA - T2)")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
