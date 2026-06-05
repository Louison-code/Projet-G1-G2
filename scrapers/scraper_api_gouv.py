#!/usr/bin/env python3
"""
Scraper API Entreprises Gouv — Parcours les codes NAF,
extrait les données via l'API recherche-entreprises.api.gouv.fr,
écrit dans data/base_reindustrialisation.db via upsert par SIREN.
"""

import re, time, json
from datetime import datetime

from scrapers.base import BaseScraper

try:
    import requests
except ImportError:
    requests = None


NB_PAGES_MAX = 100
RESULTATS_PAR_PAGE = 25
DELAI_API = 0.3

NAF_INDUSTRIELS = [
    "2811Z", "2812Z", "2813Z", "2814Z", "2815Z", "2821Z", "2822Z",
    "2823Z", "2824Z", "2825Z", "2829Z", "2830Z", "2841Z", "2849Z",
    "2891Z", "2892Z", "2893Z", "2894Z", "2895Z", "2896Z", "2899Z",
    "2910Z", "2920Z", "2931Z", "2932Z", "3011Z", "3012Z", "3020Z",
    "3030Z", "3040Z", "3091Z", "3092Z", "3099Z",
]


class ScraperApiGouv(BaseScraper):

    @property
    def nom_source(self) -> str:
        return "api_gouv"

    def run(self, config: dict = None, progression: callable = None) -> list[dict]:
        if requests is None:
            print("  requests non installe. Installation: pip install requests")
            return []

        config = config or {}
        codes_naf = config.get("codes_naf", NAF_INDUSTRIELS)
        max_pages = config.get("nb_pages", NB_PAGES_MAX)

        resultats = []
        total_codes = len(codes_naf)

        for idx, code_naf in enumerate(codes_naf):
            if progression:
                progression(idx, total_codes, f"NAF {code_naf}")
            else:
                print(f"\n  [{idx+1}/{total_codes}] Code NAF: {code_naf}")

            try:
                entreprises = self._scraper_code_naf(code_naf, max_pages)
                for donnees in entreprises:
                    insere = self._upsert(donnees)
                    resultats.append(donnees)
                print(f"    {len(entreprises)} entreprises trouvees")
            except Exception as e:
                print(f"    ERREUR: {e}")
                self._log_erreur(f"api_gouv_naf_{code_naf}", "API_ERROR", str(e))

        print(f"\n  Total: {len(resultats)} entreprises issues de l'API Gouv")
        return resultats

    def _scraper_code_naf(self, code_naf: str, max_pages: int) -> list[dict]:
        entreprises = []

        for page in range(1, max_pages + 1):
            try:
                url = "https://recherche-entreprises.api.gouv.fr/search"
                params = {
                    "activite_principale": code_naf,
                    "page": page,
                    "per_page": RESULTATS_PAR_PAGE,
                }

                r = requests.get(url, params=params, timeout=15,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json"
                    })

                if r.status_code != 200:
                    break

                data = r.json()
                results = data.get("results", [])
                if not results:
                    break

                for item in results:
                    donnees = self._extraire_item(item, code_naf)
                    if donnees.get("siren"):
                        entreprises.append(donnees)

                time.sleep(DELAI_API)

            except Exception as e:
                self._log_erreur(f"api_gouv_page_{page}_naf_{code_naf}", "PAGE_ERROR", str(e))
                break

        return entreprises

    def _extraire_item(self, item: dict, code_naf_origine: str) -> dict:
        siege = item.get("siege", {}) or {}
        if not isinstance(siege, dict):
            siege = {}

        siren = re.sub(r"\D", "", item.get("siren", ""))
        if len(siren) != 9:
            siren = ""

        siret = ""
        siege_siret = siege.get("siret", "")
        if siege_siret and len(siege_siret) == 14:
            siret = siege_siret

        donnees = {
            "url": f"https://annuaire-entreprises.data.gouv.fr/etablissement/{siret or siren}",
            "nom_entreprise": (
                item.get("nom_complet", "") or
                item.get("nom_raison_sociale", "") or
                item.get("denomination", "") or
                item.get("nom_entreprise", "") or
                item.get("nom", "") or
                ""
            ),
            "description": item.get("libelle_activite_principale", ""),
            "siren": siren,
            "siret": siret,
            "code_naf": item.get("activite_principale", "") or code_naf_origine,
            "code_postal": siege.get("code_postal", ""),
            "ville": siege.get("libelle_commune", "") or siege.get("ville", ""),
            "pays": "France",
            "forme_juridique": (
                item.get("forme_juridique", "") or
                item.get("nature_juridique", "") or
                ""
            ),
            "annee_creation": self._extraire_annee(item.get("date_creation", "")),
            "effectif_adresse": "",
            "effectif_entreprise": "",
            "activites_principales": item.get("libelle_activite_principale", ""),
            "capital": "",
            "telephone": "",
            "fax": "",
            "email": "",
            "site_web": "",
            "roles": "",
            "tva": self._tva_fr(siren),
            "departement": siege.get("departement", "") or "",
            "region": siege.get("region", "") or "",
        }

        tranche = item.get("tranche_effectif_salarie", "")
        if tranche:
            eff_map = {
                "00": "0 employe", "01": "1-2 employes", "02": "3-5 employes",
                "03": "6-9 employes", "11": "10-19 employes", "12": "20-49 employes",
                "21": "50-99 employes", "22": "100-249 employes", "31": "250-499 employes",
                "32": "500-999 employes", "41": "1000-1999 employes",
                "42": "2000-4999 employes", "51": "5000-9999 employes"
            }
            eff_val = eff_map.get(tranche, tranche)
            donnees["effectif_adresse"] = eff_val
            donnees["effectif_entreprise"] = eff_val

        cap = item.get("capital_social", "") or item.get("capital", "")
        if cap:
            num = re.sub(r"\D", "", str(cap))
            if num:
                donnees["capital"] = num + " EUR"

        donnees["roles"] = "Producteur | Prestataire de services"
        donnees["activites_secondaires"] = "Prestations annexes | Conseil"
        donnees["autres_classifications"] = self._classifications(donnees)

        if donnees.get("code_postal"):
            cdp = donnees["code_postal"]
            if re.match(r'^971', cdp):
                donnees["departement"] = "971"
            elif re.match(r'^972', cdp):
                donnees["departement"] = "972"
            elif re.match(r'^973', cdp):
                donnees["departement"] = "973"
            elif re.match(r'^974', cdp):
                donnees["departement"] = "974"
            elif re.match(r'^975', cdp):
                donnees["departement"] = "975"
            elif re.match(r'^976', cdp):
                donnees["departement"] = "976"
            elif re.match(r'^20[012]', cdp):
                donnees["departement"] = "2A" if cdp.startswith("200") else "2B"
            elif re.match(r'^(0[1-9]|[1-9]\d)', cdp):
                donnees["departement"] = re.match(r'^(0[1-9]|[1-9]\d)', cdp).group(1)

        return donnees

    def _extraire_annee(self, date_str: str) -> str:
        if not date_str:
            return ""
        m = re.search(r'\b(19[3-9]\d|20[0-2]\d)\b', date_str)
        return m.group(1) if m else ""

    def _tva_fr(self, siren: str) -> str:
        s = re.sub(r"\D", "", siren)
        if len(s) < 9:
            return ""
        try:
            return f"FR{(12+3*(int(s[:9])%97))%97:02d}{s[:9]}"
        except:
            return ""

    def _classifications(self, data: dict) -> str:
        parts = []
        if data.get("siren"):
            parts.append(f"SIREN: {data['siren']}")
        if data.get("code_naf"):
            parts.append(f"NAF: {data['code_naf']}")
        if data.get("forme_juridique"):
            parts.append(f"Forme: {data['forme_juridique']}")
        if data.get("code_postal"):
            parts.append(f"CP: {data['code_postal']}")
        if data.get("ville"):
            parts.append(f"Ville: {data['ville']}")
        return " | ".join(parts)


# ── CLI ──

if __name__ == "__main__":
    scraper = ScraperApiGouv()
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--naf":
            codes = [c.upper() for c in sys.argv[2:]] or NAF_INDUSTRIELS[:3]
            config = {"codes_naf": codes, "nb_pages": 5}
        else:
            nb = int(sys.argv[1]) if sys.argv[1].isdigit() else 3
            config = {"codes_naf": NAF_INDUSTRIELS[:nb], "nb_pages": 5}
    else:
        config = {"codes_naf": NAF_INDUSTRIELS[:2], "nb_pages": 3}
        print("  Mode demo: 2 codes NAF, 3 pages")

    scraper.run(config)
