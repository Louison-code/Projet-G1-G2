#!/usr/bin/env python3
"""
Scraper URL Directe — Prend une URL d'entreprise (Kompass, site vitrine, etc.),
utilise SocieteScraper pour extraire les 22 champs,
écrit dans data/base_reindustrialisation.db via upsert par SIREN.
"""

import re, os, sys, time, requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    from scraper_library import SocieteScraper
except ImportError:
    SocieteScraper = None
from scrapers.base import BaseScraper


# Mapping des colonnes SocieteScraper -> DB
MAPPING_COLONNES = {
    "URL": "url",
    "Nom_Entreprise": "nom_entreprise",
    "Roles": "roles",
    "Description": "description",
    "Code_Postal": "code_postal",
    "Ville": "ville",
    "Pays": "pays",
    "Telephone": "telephone",
    "Fax": "fax",
    "Email": "email",
    "Site_Web": "site_web",
    "SIREN": "siren",
    "SIRET": "siret",
    "TVA_Intracommunautaire": "tva",
    "Capital": "capital",
    "Forme_Juridique": "forme_juridique",
    "Annee_Creation": "annee_creation",
    "Effectif_Adresse": "effectif_adresse",
    "Effectif_Entreprise": "effectif_entreprise",
    "Activites_Principales": "activites_principales",
    "Activites_Secondaires": "activites_secondaires",
    "Autres_Classifications": "autres_classifications",
}


class ScraperUrlDirecte(BaseScraper):

    @property
    def nom_source(self) -> str:
        return "url_directe"

    def run(self, config: dict = None, progression: callable = None) -> list[dict]:
        config = config or {}
        urls = config.get("urls", [])
        timeout = config.get("timeout", 30)

        if not urls:
            print("  Aucune URL fournie.")
            return []

        resultats = []
        total = len(urls)

        for i, url in enumerate(urls):
            if progression:
                progression(i, total, url)
            else:
                print(f"  [{i+1}/{total}] {url[:70]}...")

            try:
                donnees = self._scraper_avec_fallback(url, timeout)

                if donnees:
                    insere = self._upsert(donnees)
                    s = "+" if donnees.get("siren") else " "
                    nom = donnees.get("nom_entreprise", "?")[:35]
                    action = "insere" if insere else "completé"
                    print(f"    [{s}] {nom:35s} | {action} | SIREN: {donnees.get('siren','')}")
                    resultats.append(donnees)
                else:
                    print(f"    ECHEC")
                    self._log_erreur(url, "SCRAPE_ECHEC", "Page inaccessible")

            except Exception as e:
                print(f"    ERREUR: {e}")
                self._log_erreur(url, "RUN_ERROR", str(e))

        print(f"\n  {len(resultats)}/{total} entreprises traitées")
        return resultats

    def _scraper_avec_fallback(self, url: str, timeout: int = 30) -> dict:
        """Tente d'abord avec SocieteScraper (sans DrissionPage),
        puis fallback extraction regex simple via requests."""
        donnees = {}

        # Méthode 1 : SocieteScraper sans navigateur (requests only)
        if SocieteScraper:
            try:
                ss = SocieteScraper()
                ss._browser = None  # Force pas de navigateur
                r = ss.scrape(url, timeout=timeout)
                if r.colonnes and r.colonnes.get("SIREN", ""):
                    donnees = self._mapper_resultat(r.colonnes, url)
                    ss.close()
                    return donnees
                ss.close()
            except Exception:
                pass

        # Méthode 2 : Extraction via requests uniquement (SocieteScraper)
        if SocieteScraper:
            try:
                resp = requests.get(url, timeout=timeout,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    allow_redirects=True)
                if resp.status_code == 200 and len(resp.text) > 2000:
                    ss2 = SocieteScraper()
                    row = ss2._extraire(resp.text, url)
                    if row:
                        donnees = self._mapper_resultat(row, url)
                        if donnees.get("nom_entreprise") and donnees.get("nom_entreprise") != url.split("/")[-1]:
                            return donnees
            except Exception:
                pass

        # Méthode 3 : Extraction regex directe depuis le HTML
        try:
            resp = requests.get(url, timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 2000:
                html = resp.text
                extrait = {"url": url}

                def _dec(net): return html.replace("&#233;", "e").replace("&#224;", "a").replace("&#231;", "c").replace("&#176;", "deg").replace("&#160;", " ").replace("&#232;", "e").replace("&#234;", "e").replace("&#238;", "i").replace("&#239;", "i").replace("&#244;", "o").replace("&#251;", "u").replace("&#252;", "u").replace("&#8220;", '"').replace("&#8221;", '"').replace("&#8217;", "'").replace("&#39;", "'").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                txt = _dec(html)

                # Nom entreprise : balise <title> (format: "SOCIETE NOM à VILLE (CP). ...")
                m = re.search(r'<title>(.+?)(?: -|\|).*?</title>', txt, re.DOTALL)
                if not m:
                    m = re.search(r'<h1[^>]*>(.+?)</h1>', txt, re.DOTALL)
                if m:
                    nom = m.group(1).strip()
                    nom = re.sub(r'^(?:Societe|Société|S\.A\.?|S\.A\.?R\.?L\.?|EURL|SARL|SAS|SASU)\s+', '', nom)
                    nom = re.sub(r'\s+&\s+SARL.*', '', nom)
                    nom = re.sub(r'\s*\(.*?\)\s*', '', nom).strip()
                    nom = re.split(r'\s+[àa]\s+[A-Z]', nom)[0]
                    nom = re.split(r'\.\s+Chiffre', nom)[0]
                    extrait["nom_entreprise"] = nom.strip()[:80]

                # SIREN
                m = re.search(r'(?:SIREN|siren)[^0-9]*(\d{9})', html)
                if m:
                    extrait["siren"] = m.group(1)

                # SIRET
                m = re.search(r'(?:SIRET|siret)[^0-9]*(\d{14})', html)
                if m:
                    extrait["siret"] = m.group(1)

                # Telephone
                m = re.search(r'(?:Tel[ée]phone|TEL|t[eé]l)[^0-9+]*(0\d(?:[\s.-]*\d{2}){4})', txt)
                if not m:
                    m = re.search(r'(?:Portable|portable|Fax|fax)[^0-9+]*(0\d(?:[\s.-]*\d{2}){4})', txt)
                if m:
                    extrait["telephone"] = re.sub(r"[\s.-]", "", m.group(1))

                # Email
                m = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', txt)
                if m:
                    extrait["email"] = m.group(0)

                # Site web
                m = re.search(r'(?:Site (?:Web|internet)|site web)[^<]*(https?://(?:www\.)?[^\s<"\']+)', txt, re.I)
                if m and 'search?' not in m.group(1):
                    extrait["site_web"] = m.group(1).rstrip('/')

                # Code postal
                m = re.search(r'(?:Code\s+postal|CP)[^0-9]*((?:0[1-9]|[1-9]\d)\d{3})', txt)
                if not m:
                    m = re.search(r'\b((?:0[1-9]|[1-9]\d)\d{3})\s+(?:Paris|Marseille|Lyon|[A-Z][A-Za-z]+)', txt)
                if m:
                    extrait["code_postal"] = m.group(1)

                # Ville
                m = re.search(r'(?:Ville|ville)[^:]*:\s*([A-Z][A-Za-zéèêëàâîïôùûç\-\s]+?)(?:<|\s+\d)', txt)
                if m:
                    extrait["ville"] = m.group(1).strip()
                if not extrait.get("ville"):
                    m = re.search(r'(\d{5})\s+([A-Z][A-Za-zéèêëàâîïôùûç\-\s]+?)(?:<|$)', txt)
                    if m:
                        extrait["ville"] = m.group(2).strip()

                # Description / activite
                m = re.search(r'Activite[^:]*:\s*([^<.]+)', txt)
                if m:
                    extrait["description"] = m.group(1).strip()[:200]

                if extrait.get("nom_entreprise") or extrait.get("siren"):
                    return {k: v for k, v in extrait.items() if v}
        except Exception:
            pass

        return donnees

    def _mapper_resultat(self, colonnes: dict, url: str) -> dict:
        """Convertit les colonnes SocieteScraper au format DB."""
        donnees = {"url": url}

        for src_key, db_key in MAPPING_COLONNES.items():
            val = colonnes.get(src_key, "")
            if val and db_key in ("siren", "siret"):
                val = re.sub(r"\D", "", val)

            if db_key == "url":
                if val and not val.startswith("http"):
                    val = donnees.get("url", "")
            if val:
                donnees[db_key] = str(val).strip()

        if not donnees.get("siren") and donnees.get("siret", "")[:9]:
            donnees["siren"] = donnees["siret"][:9]

        if not donnees.get("pays"):
            donnees["pays"] = "France"

        if donnees.get("site_web") and "kompass" in donnees["site_web"].lower():
            del donnees["site_web"]

        if donnees.get("email") and any(
            b in donnees["email"].lower() for b in ["kompass", "noreply"]
        ):
            del donnees["email"]

        return donnees


# ── CLI ──

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m scrapers.scraper_url_directe <url1> <url2> ...")
        print("       python -m scrapers.scraper_url_directe --fichier urls.txt")
        sys.exit(1)

    config = {}
    if sys.argv[1] == "--fichier":
        with open(sys.argv[2]) as f:
            config["urls"] = [l.strip() for l in f if l.strip().startswith("http")]
        print(f"{len(config['urls'])} URL(s) lues depuis {sys.argv[2]}")
    else:
        config["urls"] = [u for u in sys.argv[1:] if u.startswith("http")]
        print(f"Mode manuel: {len(config['urls'])} URL(s)")

    scraper = ScraperUrlDirecte()
    scraper.run(config)
