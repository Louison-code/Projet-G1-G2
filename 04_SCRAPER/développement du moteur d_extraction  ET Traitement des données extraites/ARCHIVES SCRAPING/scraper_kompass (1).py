"""
============================================================
PROJET G1/G2 - F-2049 | Réindustrialisation Française
T3.1.3 : Développement du moteur d'extraction
============================================================
Auteurs (RACI R) : Louison Baudouin, Yessine Hachicha,
                   Rana Amri, Cisco Barnaud
Responsable (A)  : Louison Baudouin
Superviseur      : Louison Baudouin
Date             : 2026
------------------------------------------------------------
Outil principal  : Playwright (Python)
Motif du choix   : Kompass est un site dynamique JS (React)
                   → BeautifulSoup/Requests insuffisants
Cible            : 7 100 URLs Kompass fournies par le client
                   (fichier liste_URL_KOMPASS.xlsx)
Stockage         : SQLite (entreprises.db)
------------------------------------------------------------
Installation prérequis :
    pip install playwright openpyxl
    playwright install chromium
============================================================
"""

import asyncio
import sqlite3
import time
import random
import logging
import json
import re
from datetime import datetime
from pathlib import Path

import openpyxl
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# ============================================================
# CONFIGURATION GLOBALE
# ============================================================
CONFIG = {
    # Fichiers
    "excel_input":      "liste_URL_KOMPASS.xlsx",
    "db_path":          "entreprises.db",
    "log_path":         "scraper_kompass.log",
    # Playwright
    "headless":         True,
    "timeout_page":     30_000,          # 30s par page
    "timeout_selector": 10_000,          # 10s pour trouver un sélecteur
    # Politesse (respect robots.txt Kompass)
    "delay_min":        2.5,             # secondes min entre requêtes
    "delay_max":        5.0,             # secondes max entre requêtes
    "batch_size":       50,              # entreprises par batch
    "pause_between_batches": 60,         # 1 minute entre batches
    # User-Agent (charte éthique T0.1.4)
    "user_agent": (
        "CartoIndustrielleBot/1.0 "
        "(Projet académique Centrale Lille ; "
        "contact: louison.baudouin@centrale.centralelille.fr)"
    ),
    # Reprendre depuis une URL précise (resume)
    "start_from_url":   None,
}

# ============================================================
# CONFIGURATION LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(CONFIG["log_path"], encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("KompassScraper")


# ============================================================
# SECTION 1 : LECTURE DES URLs DEPUIS L'EXCEL CLIENT
# (T3.1.1 - Analyse des sources)
# ============================================================
def charger_urls_excel(chemin_excel: str) -> list[dict]:
    """
    Charge les URLs et métadonnées depuis le fichier Excel fourni par le client.
    Colonnes attendues : LIEN KOMPASS | RAISON SOCIALE | LOCALISATION | ACTIVTE | SITE WEB
    """
    logger.info(f"Chargement des URLs depuis {chemin_excel} ...")
    wb = openpyxl.load_workbook(chemin_excel, read_only=True)
    ws = wb["Base"]

    headers = None
    urls = []
    for row in ws.iter_rows(values_only=True):
        if headers is None:
            headers = row
            continue
        if not row[0]:  # URL vide → ignorer
            continue
        urls.append({
            "lien_kompass":  row[0] or "",
            "raison_sociale": row[1] or "",
            "localisation":  row[2] or "",
            "description":   row[3] or "",
            "site_web":      row[4] or "",
        })

    logger.info(f"{len(urls)} URLs chargées depuis l'Excel.")
    return urls


# ============================================================
# SECTION 2 : INITIALISATION / CONNEXION BASE DE DONNÉES
# (T1.1.4 - Base SQL locale)
# ============================================================
def init_db(db_path: str) -> sqlite3.Connection:
    """
    Initialise la connexion SQLite et crée les tables si inexistantes.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Charger le schéma depuis init_db.sql si la base est vide
    cursor = conn.cursor()
    cursor.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='entreprises'"
    )
    if cursor.fetchone()[0] == 0:
        logger.info("Création des tables SQL depuis init_db.sql ...")
        with open("init_db.sql", "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
    return conn


def url_deja_scrapee(conn: sqlite3.Connection, lien_kompass: str) -> bool:
    """Retourne True si cette URL a déjà été traitée avec succès."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT statut_scraping FROM entreprises WHERE lien_kompass = ?",
        (lien_kompass,)
    )
    row = cursor.fetchone()
    return row is not None and row["statut_scraping"] == "success"


def upsert_entreprise(conn: sqlite3.Connection, data: dict) -> int:
    """Insert ou met à jour une entreprise dans la base."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO entreprises (
            lien_kompass, raison_sociale, siren, siret, code_naf,
            forme_juridique, date_creation, adresse, ville, code_postal,
            departement, site_web, telephone, email,
            chiffre_affaires, effectifs, description, html_brut,
            statut_scraping, date_scraping
        ) VALUES (
            :lien_kompass, :raison_sociale, :siren, :siret, :code_naf,
            :forme_juridique, :date_creation, :adresse, :ville, :code_postal,
            :departement, :site_web, :telephone, :email,
            :chiffre_affaires, :effectifs, :description, :html_brut,
            :statut_scraping, :date_scraping
        )
        ON CONFLICT(lien_kompass) DO UPDATE SET
            siren           = excluded.siren,
            siret           = excluded.siret,
            code_naf        = excluded.code_naf,
            forme_juridique = excluded.forme_juridique,
            adresse         = excluded.adresse,
            ville           = excluded.ville,
            code_postal     = excluded.code_postal,
            departement     = excluded.departement,
            site_web        = excluded.site_web,
            telephone       = excluded.telephone,
            email           = excluded.email,
            chiffre_affaires= excluded.chiffre_affaires,
            effectifs       = excluded.effectifs,
            description     = excluded.description,
            html_brut       = excluded.html_brut,
            statut_scraping = excluded.statut_scraping,
            date_scraping   = excluded.date_scraping
    """, data)
    conn.commit()
    return cursor.lastrowid


def log_erreur(conn: sqlite3.Connection, lien: str, code: str, msg: str, html: str = ""):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs_erreurs (lien_kompass, code_erreur, message_erreur, html_snapshot)
        VALUES (?, ?, ?, ?)
    """, (lien, code, msg, html[:5000] if html else ""))
    conn.commit()


# ============================================================
# SECTION 3 : NETTOYAGE HTML
# (T3.1.4 - Traitement des données extraites)
# ============================================================
def nettoyer_html(html_brut: str) -> str:
    """
    Supprime les balises script, style, nav, footer du HTML brut.
    Réduit la taille avant envoi à l'IA (T2) — gestion fenêtre de contexte (T2.4.3).
    """
    # Supprimer les balises inutiles
    for tag in ["script", "style", "nav", "footer", "header", "svg", "noscript", "iframe"]:
        html_brut = re.sub(
            rf"<{tag}[^>]*>.*?</{tag}>", "", html_brut,
            flags=re.DOTALL | re.IGNORECASE
        )
    # Supprimer les commentaires HTML
    html_brut = re.sub(r"<!--.*?-->", "", html_brut, flags=re.DOTALL)
    # Supprimer les attributs de style inline
    html_brut = re.sub(r'\s+style="[^"]*"', "", html_brut)
    # Compresser les espaces multiples
    html_brut = re.sub(r"\s+", " ", html_brut).strip()
    # Tronquer à 50 000 caractères max (fenêtre de contexte LLM)
    return html_brut[:50_000]


# ============================================================
# SECTION 4 : EXTRACTION DES DONNÉES DEPUIS LE HTML
# (T3.1.3 - Moteur d'extraction)
# ============================================================
def extraire_donnees_kompass(html: str, meta_excel: dict) -> dict:
    """
    Extrait les champs structurés depuis le HTML Kompass nettoyé.
    Utilise des sélecteurs regex + patterns Kompass connus.
    Note : certains champs seront enrichis par l'IA en T2.
    """

    def chercher(pattern, texte, groupe=1, defaut=None):
        m = re.search(pattern, texte, re.IGNORECASE | re.DOTALL)
        return m.group(groupe).strip() if m else defaut

    # SIRET (14 chiffres)
    siret = chercher(r"SIRET[^:]*:\s*([0-9]{14}|[0-9]{3}\s[0-9]{3}\s[0-9]{3}\s[0-9]{5})", html)
    if siret:
        siret = re.sub(r"\s", "", siret)
    # SIREN (9 premiers chiffres du SIRET)
    siren = siret[:9] if siret and len(siret) >= 9 else chercher(
        r"\b([0-9]{9})\b", html
    )

    # Code NAF
    code_naf = chercher(r"NAF\s*[:\-]?\s*([0-9]{4}[A-Z])", html)

    # Forme juridique
    forme = None
    for fj in ["SAS", "SARL", "SA", "EURL", "SNC", "SCI", "EI", "SASU"]:
        if fj in html.upper():
            forme = fj
            break

    # Date de création
    date_creation = chercher(r"fond[ée]{1,2}e?\s+en\s+(\d{4})", html)
    if not date_creation:
        date_creation = chercher(r"cr[ée]{1,2}[e]?\s+en\s+(\d{4})", html)

    # Localisation (depuis méta Excel ou HTML)
    loc = meta_excel.get("localisation", "")
    ville = re.sub(r"\s*-\s*France.*", "", loc).strip() if loc else ""
    code_postal = chercher(r"\((\d{5})\)", html)

    # Effectifs
    effectifs = None
    m = re.search(r"(\d{1,5})\s+(?:salariés?|employés?|collaborateurs?)", html, re.I)
    if m:
        try:
            effectifs = int(m.group(1))
        except ValueError:
            pass

    # Chiffre d'affaires
    ca = None
    m = re.search(
        r"(?:CA|chiffre d.affaires)[^\d]*(\d[\d\s,.]*)\s*(?:€|EUR|millions?|M€)?",
        html, re.I
    )
    if m:
        try:
            val = re.sub(r"[\s\xa0]", "", m.group(1)).replace(",", ".")
            ca = float(val)
        except ValueError:
            pass

    return {
        "lien_kompass":   meta_excel["lien_kompass"],
        "raison_sociale": meta_excel.get("raison_sociale", ""),
        "siren":          siren or "",
        "siret":          siret or "",
        "code_naf":       code_naf or "",
        "forme_juridique": forme or "",
        "date_creation":  date_creation or "",
        "adresse":        "",              # extrait lors du scraping Playwright
        "ville":          ville,
        "code_postal":    code_postal or "",
        "departement":    "",
        "site_web":       meta_excel.get("site_web", ""),
        "telephone":      "",
        "email":          "",
        "chiffre_affaires": ca,
        "effectifs":      effectifs,
        "description":    meta_excel.get("description", ""),
        "html_brut":      html,            # envoyé à l'IA (T2)
        "statut_scraping": "success",
        "date_scraping":  datetime.now().isoformat(),
    }


# ============================================================
# SECTION 5 : MOTEUR DE NAVIGATION PLAYWRIGHT
# (T3.1.3 - Navigation JS, gestion délais, User-Agent, Headers)
# ============================================================
async def scraper_une_page(page, url: str, conn: sqlite3.Connection, meta: dict) -> bool:
    """
    Scrape une fiche Kompass avec Playwright.
    Gère : délais d'attente, User-Agent, scroll, erreurs.
    Retourne True si succès, False sinon.
    """
    try:
        # Navigation avec timeout
        response = await page.goto(url, timeout=CONFIG["timeout_page"], wait_until="domcontentloaded")

        # Vérifier le code HTTP
        if response and response.status == 403:
            logger.warning(f"[BLOCKED 403] {url}")
            log_erreur(conn, url, "BLOCKED_403", "Accès refusé par le serveur")
            return False
        if response and response.status == 404:
            logger.warning(f"[NOT FOUND 404] {url}")
            log_erreur(conn, url, "NOT_FOUND_404", "Page introuvable")
            return False

        # Attendre le chargement JavaScript
        await page.wait_for_timeout(2000)

        # Scroll pour déclencher le lazy-loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)

        # Récupérer le HTML complet rendu
        html_brut = await page.content()

        # Vérifier présence de CAPTCHA (Kompass en utilise parfois)
        if any(kw in html_brut.lower() for kw in ["captcha", "are you a robot", "bot detection"]):
            logger.warning(f"[CAPTCHA] {url}")
            log_erreur(conn, url, "CAPTCHA", "CAPTCHA détecté — pause longue requise", html_brut)
            return False

        # Nettoyer le HTML
        html_propre = nettoyer_html(html_brut)

        # Extraire les données structurées
        donnees = extraire_donnees_kompass(html_propre, meta)

        # Sauvegarder en base
        upsert_entreprise(conn, donnees)
        logger.info(f"[OK] {meta['raison_sociale']} — {url}")
        return True

    except PlaywrightTimeout:
        logger.error(f"[TIMEOUT] {url}")
        log_erreur(conn, url, "TIMEOUT", f"Délai dépassé ({CONFIG['timeout_page']}ms)")
        return False
    except Exception as e:
        logger.error(f"[ERREUR] {url} → {str(e)[:200]}")
        log_erreur(conn, url, "EXCEPTION", str(e)[:500])
        return False


# ============================================================
# SECTION 6 : ORCHESTRATEUR PRINCIPAL
# (T3.1.2 - Architecture modulaire + exécution asynchrone)
# ============================================================
async def lancer_scraping(urls: list[dict], conn: sqlite3.Connection):
    """
    Orchestrateur principal : lance Playwright, parcourt les URLs par batch.
    """
    total   = len(urls)
    succes  = 0
    erreurs = 0
    ignores = 0

    async with async_playwright() as pw:
        # Lancer Chromium en mode headless
        browser = await pw.chromium.launch(headless=CONFIG["headless"])
        context = await browser.new_context(
            user_agent=CONFIG["user_agent"],
            viewport={"width": 1366, "height": 768},
            extra_http_headers={
                "Accept-Language": "fr-FR,fr;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            java_script_enabled=True,
        )
        page = await context.new_page()

        logger.info(f"Démarrage scraping : {total} URLs à traiter")

        for idx, meta in enumerate(urls, start=1):
            url = meta["lien_kompass"]

            # Skip si déjà scrapée avec succès
            if url_deja_scrapee(conn, url):
                logger.debug(f"[SKIP] {url} (déjà en base)")
                ignores += 1
                continue

            # Délai de politesse aléatoire (charte éthique T0.1.4)
            delai = random.uniform(CONFIG["delay_min"], CONFIG["delay_max"])
            await asyncio.sleep(delai)

            # Pause longue entre batches
            if idx % CONFIG["batch_size"] == 0:
                logger.info(f"--- Batch {idx // CONFIG['batch_size']} terminé — pause {CONFIG['pause_between_batches']}s ---")
                await asyncio.sleep(CONFIG["pause_between_batches"])

            # Scraping de la page
            ok = await scraper_une_page(page, url, conn, meta)
            if ok:
                succes += 1
            else:
                erreurs += 1

            # Log de progression toutes les 100 URLs
            if idx % 100 == 0:
                taux = round(succes / (succes + erreurs) * 100, 1) if (succes + erreurs) > 0 else 0
                logger.info(
                    f"Progression: {idx}/{total} | "
                    f"Succès: {succes} | Erreurs: {erreurs} | "
                    f"Taux succès: {taux}%"
                )

        await context.close()
        await browser.close()

    logger.info("=" * 60)
    logger.info(f"SCRAPING TERMINÉ")
    logger.info(f"Total traité  : {total - ignores}")
    logger.info(f"Succès        : {succes}")
    logger.info(f"Erreurs       : {erreurs}")
    logger.info(f"Ignorés (déjà en base) : {ignores}")
    logger.info(f"Taux de succès : {round(succes / max(succes + erreurs, 1) * 100, 1)}%")
    logger.info("=" * 60)


# ============================================================
# POINT D'ENTRÉE
# ============================================================
def main():
    logger.info("=" * 60)
    logger.info("PROJET G1/G2 | Scraper Kompass v1.0")
    logger.info(f"Démarrage : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 1. Vérifications
    excel_path = Path(CONFIG["excel_input"])
    if not excel_path.exists():
        logger.error(f"Fichier Excel introuvable : {excel_path}")
        return

    # 2. Charger les URLs
    urls = charger_urls_excel(str(excel_path))

    # 3. Initialiser la base
    conn = init_db(CONFIG["db_path"])
    logger.info(f"Base de données : {CONFIG['db_path']}")

    # 4. Lancer le scraping
    asyncio.run(lancer_scraping(urls, conn))

    # 5. Rapport final
    cursor = conn.cursor()
    cursor.execute("SELECT statut_scraping, count(*) FROM entreprises GROUP BY statut_scraping")
    for row in cursor.fetchall():
        logger.info(f"  Statut '{row[0]}' : {row[1]} entreprises")

    conn.close()
    logger.info("Connexion base fermée. Scraping complet.")


if __name__ == "__main__":
    main()
