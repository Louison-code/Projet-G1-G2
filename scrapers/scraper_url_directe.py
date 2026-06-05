#!/usr/bin/env python3
"""
Scraper URL Directe — Prend une URL d'entreprise (Kompass, site vitrine, etc.),
utilise SocieteScraper pour extraire les 22 champs,
écrit dans data/base_reindustrialisation.db via upsert par SIREN.
"""

import re, os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scraper_library import SocieteScraper
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

        scraper = SocieteScraper()
        resultats = []
        total = len(urls)

        try:
            for i, url in enumerate(urls):
                if progression:
                    progression(i, total, url)
                else:
                    print(f"  [{i+1}/{total}] {url[:70]}...")

                try:
                    r = scraper.scrape(url, timeout=timeout)

                    if r.erreur and not r.colonnes:
                        print(f"    ERREUR: {r.erreur}")
                        self._log_erreur(url, "SCRAPE_ERROR", r.erreur)
                        continue

                    donnees = self._mapper_resultat(r.colonnes, url)
                    insere = self._upsert(donnees)

                    s = "+" if donnees.get("siren") else " "
                    nom = donnees.get("nom_entreprise", "?")[:35]
                    action = "insere" if insere else "completé"
                    print(f"    [{s}] {nom:35s} | {action} | SIREN: {donnees.get('siren','')}")
                    resultats.append(donnees)

                except Exception as e:
                    print(f"    ERREUR: {e}")
                    self._log_erreur(url, "RUN_ERROR", str(e))

        finally:
            scraper.close()

        print(f"\n  {len(resultats)}/{total} entreprises traitées")
        return resultats

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
