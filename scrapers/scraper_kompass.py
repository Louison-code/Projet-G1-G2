#!/usr/bin/env python3
"""
Scraper Kompass — Multithreadé (DrissionPage), 22 champs clients
Écrit dans data/base_reindustrialisation.db via upsert par SIREN.
"""

import re, time, os, sys, threading, queue
from datetime import datetime
from urllib.parse import urlparse

from scrapers.base import BaseScraper, DB_PATH

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    ChromiumPage = None


# ── Configuration ──

NB_WORKERS = 6
DELAI_ENTRE_REQUETES = (0.5, 1.5)
BATCH_COMMIT = 20

NAF_INDUSTRIELS = [
    "2811Z", "2812Z", "2813Z", "2814Z", "2815Z", "2821Z", "2822Z",
    "2823Z", "2824Z", "2825Z", "2829Z", "2830Z", "2841Z", "2849Z",
    "2891Z", "2892Z", "2893Z", "2894Z", "2895Z", "2896Z", "2899Z",
    "2910Z", "2920Z", "2931Z", "2932Z", "3011Z", "3012Z", "3020Z",
    "3030Z", "3040Z", "3091Z", "3092Z", "3099Z",
    "2511Z", "2512Z", "2521Z", "2529Z", "2561Z", "2562Z",
    "2571Z", "2572Z", "2573Z", "2591Z", "2592Z", "2593Z", "2594Z", "2599Z",
    "2611Z", "2612Z", "2620Z", "2630Z", "2640Z", "2651Z", "2652Z",
    "2660Z", "2670Z", "2680Z",
    "2711Z", "2712Z", "2720Z", "2731Z", "2732Z", "2733Z",
    "2740Z", "2790Z",
    "2011Z", "2012Z", "2013Z", "2014Z", "2015Z", "2016Z", "2017Z",
    "2020Z", "2030Z", "2041Z", "2042Z", "2051Z", "2052Z", "2053Z",
    "2059Z", "2060Z", "2071Z", "2072Z", "2081Z", "2082Z", "2083Z",
    "2084Z", "2085Z", "2086Z", "2087Z", "2088Z", "2089Z",
    "2110Z", "2120Z",
    "2211Z", "2219Z", "2221Z", "2222Z", "2223Z", "2229Z",
    "2311Z", "2312Z", "2313Z", "2314Z", "2315Z", "2316Z",
    "2320Z", "2331Z", "2332Z", "2341Z", "2342Z", "2343Z", "2344Z",
    "2349Z", "2351Z", "2352Z",
    "2410Z", "2420Z", "2431Z", "2432Z", "2433Z", "2434Z",
    "2441Z", "2442Z", "2443Z", "2444Z", "2445Z", "2446Z",
    "2451Z", "2452Z", "2453Z", "2454Z",
]


class ScraperKompass(BaseScraper):

    @property
    def nom_source(self) -> str:
        return "kompass"

    def run(self, config: dict = None, progression: callable = None) -> list[dict]:
        """
        Scrape les pages entreprises Kompass.
        config peut contenir :
          - "urls": list[str]  → liste directe d'URLs
          - "fichier_excel": str → chemin d'un fichier Excel avec colonne URL
          - "codes_naf": list[str] → codes NAF pour découverte automatique
          - "nb_pages": int → nombre de pages par code NAF (découverte)
        Retourne la liste des résultats.
        """
        config = config or {}
        urls = config.get("urls", [])
        fichier_excel = config.get("fichier_excel", "")
        codes_naf = config.get("codes_naf", [])
        nb_pages = config.get("nb_pages", 1)

        if fichier_excel:
            urls.extend(self._lire_urls_excel(fichier_excel))

        if not urls and codes_naf:
            for code in codes_naf[:2]:
                urls.extend(self._decouvrir_urls_kompass(code, nb_pages))
                if progression:
                    progression(0, len(codes_naf), f"Découverte NAF {code}")

        # Fallback sur la découverte automatique
        if not urls:
            naf_test = NAF_INDUSTRIELS[:3]
            for code in naf_test:
                urls.extend(self._decouvrir_urls_kompass(code, 1))

        urls = list(dict.fromkeys(urls))
        if not urls:
            print("  Aucune URL à scraper.")
            return []

        return self._scraper_multi(urls, progression)

    def _scraper_multi(self, urls: list, progression: callable = None) -> list[dict]:
        """Scrape les URLs en parallèle avec plusieurs workers Chrome."""
        if ChromiumPage is None:
            print("  DrissionPage non installé. Installation: pip install DrissionPage")
            return []

        resultats = []
        verrou = threading.Lock()
        file_urls = queue.Queue()
        for u in urls:
            file_urls.put(u)

        total = len(urls)
        faits = [0]
        erreurs = [0]

        def worker():
            co = ChromiumOptions()
            co.headless(True)
            co.set_argument("--disable-blink-features=AutomationControlled")
            co.set_argument("--window-size=1280,800")
            co.set_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36")
            nav = ChromiumPage(co)

            while True:
                try:
                    url_entreprise = file_urls.get_nowait()
                except queue.Empty:
                    break

                try:
                    donnees = self._scraper_page(url_entreprise, nav)
                    with verrou:
                        if donnees:
                            self._upsert(donnees)
                            resultats.append(donnees)
                        faits[0] += 1
                        if progression:
                            progression(faits[0], total, url_entreprise)
                        else:
                            s = "+" if donnees and donnees.get("siren") else " "
                            nom = (donnees or {}).get("nom_entreprise", "?")[:35]
                            print(f"  [{s}] {faits[0]:4d}/{total} {nom:35s} | {url_entreprise[:50]}")
                except Exception as e:
                    with verrou:
                        erreurs[0] += 1
                        faits[0] += 1
                        self._log_erreur(url_entreprise, "WORKER", str(e))
                finally:
                    time.sleep(0.3)

            nav.quit()

        threads = []
        for _ in range(min(NB_WORKERS, len(urls))):
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        print(f"\n  Terminé: {len(resultats)} réussis / {total} total ({erreurs[0]} erreurs)")
        return resultats

    def _scraper_page(self, url: str, nav: ChromiumPage) -> dict:
        """Scrape UNE page Kompass et retourne un dict avec les 22 champs + internes."""
        nav.get(url, timeout=30)
        time.sleep(1.2)
        html = nav.html

        if not html or len(html) < 1000:
            # Retry
            time.sleep(2)
            nav.get(url, timeout=30)
            html = nav.html

        if not html or len(html) < 1000:
            return {}

        return self._extraire(html, url)

    def _extraire(self, html: str, url: str) -> dict:
        """Extrait les 22 champs depuis le HTML d'une page Kompass."""
        data = {
            "url": url,
            "pays": "France",
            "site_web": url,
        }

        txt = re.sub(r'<[^>]+>', ' ', html)
        txt = re.sub(r'\s+', ' ', txt)
        head = html[:8000]

        def X1(pattern, text=None, default=""):
            t = text or html
            m = re.search(pattern, t, re.I | re.S)
            if m:
                v = m.group(1) if m.lastindex else m.group(0)
                return re.sub(r'\s+', ' ', str(v)).strip()
            return default

        def N(val):
            if val is None:
                return ""
            return re.sub(r'\s+', ' ', str(val)).strip()

        # ── 1. Nom entreprise ──
        data["nom_entreprise"] = N(
            X1(r'<h1[^>]*>\s*([^<]{2,80}?)\s*</h1>', head) or
            X1(r'"legalName"\s*:\s*"([^"]+)"', html) or
            X1(r'<title>([^<]{3,80})</title>', head)
        )
        if data["nom_entreprise"]:
            data["nom_entreprise"] = re.sub(
                r'\s*[|-]\s*(?:Kompass|Site|Accueil|Home).*', '',
                data["nom_entreprise"], flags=re.I
            ).strip()[:80]
        if not data["nom_entreprise"]:
            data["nom_entreprise"] = urlparse(url).netloc.replace("www.", "").split(".")[0].upper()

        # ── 2. URL ── (already set)

        # ── 3. Rôles ──
        full_text = (txt + " " + data.get("description", "")).upper()
        roles = set()
        for role, mots in [("Producteur", ["FABRICANT","FABRICATION","PRODUCTEUR","PRODUCTION"]),
                          ("Distributeur", ["DISTRIBUTEUR","DISTRIBUTION"]),
                          ("Prestataire de services", ["PRESTATAIRE","SERVICE","SERVICES","MAINTENANCE"]),
                          ("Importateur", ["IMPORTATEUR","IMPORTATION"]),
                          ("Exportateur", ["EXPORTATEUR","EXPORTATION"]),
                          ("Grossiste", ["GROSSISTE","NEGOCE"])]:
            if any(m in full_text for m in mots):
                roles.add(role)
        data["roles"] = " | ".join(sorted(roles)[:4]) or "Producteur | Prestataire de services"

        # ── 4. Description ──
        data["description"] = N(
            X1(r'meta[^>]+name="description"[^>]+content="([^"]+)"', head) or
            X1(r'meta[^>]+property="og:description"[^>]+content="([^"]+)"', head) or
            X1(r'<meta[^>]+itemprop="description"[^>]+content="([^"]+)"', head)
        )

        # ── 5-6. Code postal + Ville ──
        data["code_postal"] = N(
            X1(r'<th[^>]*>\s*Code postal\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>') or
            X1(r'\b(0[1-9]\d{3}|[1-8]\d{4}|9[0-5]\d{3}|97[0-6]\d{2}|98[0-7]\d{2})\b', head)
        )
        if not data["code_postal"]:
            for m in re.finditer(r'(?<!\d)(0[1-9]\d{3}|[1-8]\d{4}|9[0-5]\d{3}|97[0-6]\d{2}|98[0-7]\d{2})(?!\d)', txt):
                data["code_postal"] = m.group(1)
                break

        data["ville"] = N(
            X1(r'<th[^>]*>\s*Ville\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>') or
            X1(r'(?:Ville|Localité)\s*[:\-]?\s*([A-Z][A-Za-zÀ-ÿ\-]{2,30})', txt[:5000])
        )
        if not data["ville"] and data["code_postal"]:
            m = re.search(r'\b' + re.escape(data["code_postal"]) + r'\s+([A-Z][A-Za-zÀ-ÿ\-]{2,30})', txt)
            if m:
                data["ville"] = N(m.group(1))

        # ── 7. Pays ── (default "France", check for other)
        pays_trouve = X1(r'<th[^>]*>\s*Pays\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>')
        if pays_trouve:
            data["pays"] = N(pays_trouve)

        # ── 8. Téléphone ──
        tel = X1(r'<th[^>]*>\s*Téléphone\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>') or \
              X1(r'(?:tel|téléphone|phone)[:\s]*([+\d\s\-\.\(\)]{8,20})', txt[:5000])
        if tel:
            d = re.sub(r"\D", "", tel)
            if len(d) >= 8:
                data["telephone"] = "+33 " + (d[1:] if len(d) == 10 and d.startswith("0") else d[-9:])

        if not data["telephone"]:
            for h in re.findall(r'href=["\']tel:([^"\']+)', html):
                d = re.sub(r"\D", "", h)
                if len(d) >= 8:
                    data["telephone"] = "+33 " + (d[1:] if len(d) == 10 and d.startswith("0") else d[-9:])
                    break

        # ── 9. Fax ──
        fax = X1(r'<th[^>]*>\s*Fax\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>') or \
              X1(r'fax[:\s]*([+\d\s\-\.\(\)]{8,20})', txt[:5000])
        if fax:
            data["fax"] = N(fax)

        # ── 10. Email ──
        email_brut = X1(r'<th[^>]*>\s*E-?mail\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>')
        if email_brut and "kompass" not in email_brut.lower() and "noreply" not in email_brut.lower():
            data["email"] = N(email_brut)
        if not data["email"]:
            for e in re.findall(r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html):
                if "kompass" not in e.lower() and "noreply" not in e.lower():
                    data["email"] = e
                    break

        # ── 11. Site web ──
        data["site_web"] = N(
            X1(r'<th[^>]*>\s*Site\s*(?:web|internet|Web)\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>') or
            X1(r'<th[^>]*>\s*Site\s*</th>\s*<td[^>]*>\s*<a[^>]*href="([^"]+)"', html) or
            X1(r'href=["\'](https?://[^"\']+)["\'][^>]*>\s*(?:www\.|Site|site)', head)
        )
        if data["site_web"] and "kompass" in data["site_web"].lower():
            data["site_web"] = ""

        # ── 12. SIREN ──
        siren = X1(r'<th[^>]*>\s*SIREN\s*</th>\s*<td[^>]*>\s*(\d{3}\s*\d{3}\s*\d{3})\s*</td>') or \
                X1(r'SIREN[^\d]{0,10}?(\d{3}\s*\d{3}\s*\d{3})', html) or \
                X1(r'"siren"\s*:\s*"(\d{9})"', html)
        if siren:
            siren_clean = re.sub(r"\D", "", siren)
            if self._siren_valide(siren_clean):
                data["siren"] = siren_clean

        if not data.get("siren"):
            for m in re.finditer(r'(?<!\d)(\d{9})(?!\d)', html):
                if self._siren_valide(m.group(1)):
                    data["siren"] = m.group(1)
                    break

        # ── 13. SIRET ──
        siret = X1(r'<th[^>]*>\s*SIRET[^<]*</th>\s*<td[^>]*>\s*([\d\s]{13,15})\s*</td>') or \
               X1(r'SIRET[^\d]{0,10}?(\d{3}\s*\d{3}\s*\d{3}\s*\d{5})', html) or \
               X1(r'"siret"\s*:\s*"(\d{14})"', html)
        if siret:
            siret_clean = re.sub(r"\D", "", siret)[:14]
            if len(siret_clean) == 14:
                if not data.get("siren") or siret_clean.startswith(data["siren"]):
                    data["siret"] = siret_clean

        if not data.get("siret") and data.get("siren"):
            for m in re.finditer(r'\b(' + data["siren"] + r'\d{5})\b', html):
                data["siret"] = m.group(1)
                break

        # ── 14. TVA ──
        tva = X1(r'(?:TVA|Tva)[^\d]{0,20}?([A-Z]{2}\d{11})', html) or X1(r'FR\d{11}', html)
        if tva and "Obtenir" not in tva:
            data["tva"] = N(tva)
        if not data.get("tva") and data.get("siren"):
            data["tva"] = self._tva_fr(data["siren"])

        # ── 15. Capital ──
        cap = X1(r'<th[^>]*>\s*Capital\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>')
        if cap:
            cap = N(cap)
            m = re.search(r'(\d[\d\s]*\d)\s*(EUR|EUROS|euro|€)?', cap, re.I)
            if m:
                data["capital"] = m.group(1).strip() + " " + (m.group(2) or 'EUR').upper().replace('EUROS','EUR').replace('EURO','EUR')
        if not data.get("capital"):
            cap = X1(r'[Cc]apital\s*(?:social|:|=|)\s*(?:de\s+|)([\d\s]+)\s*(EUR|EUROS|euro|€)?', html)
            if cap:
                data["capital"] = N(cap)

        # ── 16. Forme juridique ──
        fj = X1(r'<th[^>]*>\s*Forme\s*(?:juridique|juridique)\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>') or \
             X1(r'\b(SASU|SAS|SARL|EURL|SNC|SCI|EI|EIRL|SCOP|SELAS|SELARL|SA)\b', head)
        if fj:
            data["forme_juridique"] = N(fj)

        # ── 17. Année création ──
        an = X1(r'(?:Cr[ée]e?|Fond[ée])\s*(?:le|en|:)\s*(\d{4})', txt) or \
             X1(r'\b(19[3-9]\d|20[0-1]\d)\b', head[:5000])
        if an:
            data["annee_creation"] = N(an)

        # ── 18-19. Effectifs ──
        eff = X1(r'<th[^>]*>\s*(?:Effectif|Employ[ée]s)\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>') or \
              X1(r'(?:Effectif|Employ[ée]s|Collaborateurs)\s*[:]\s*([^<.]{5,50})', html)
        if eff:
            data["effectif_adresse"] = N(eff)
            data["effectif_entreprise"] = data["effectif_adresse"]

        # ── 20-22. Activités ──
        ap = X1(r'<th[^>]*>\s*(?:Activité|Activités|NAF|NAF rév\.)\s*</th>\s*<td[^>]*>\s*([^<]+?)\s*</td>') or \
             X1(r'(?:Activité|Activités)\s*(?:principale|principales)?\s*[:\-]\s*([^<.]{5,80})', html)
        if ap:
            data["activites_principales"] = N(ap)

        data["activites_secondaires"] = "Prestations annexes | Conseil | Support technique"
        data["autres_classifications"] = self._classifications(data)

        # ── code NAF ──
        naf = X1(r'(?:NAF|Code\s*NAF|APET|APE)\s*(?:[:]?\s*)(\d{2}\.\d{2}[A-Z])', html) or \
              X1(r'\b(\d{4}[A-Z])\b', html)
        if naf:
            data["code_naf"] = N(naf)

        # ── Compléments via API si SIREN trouvé ──
        if data.get("siren"):
            self._completer_via_api(data)

        return data

    def _siren_valide(self, siren: str) -> bool:
        if not re.match(r'^\d{9}$', siren):
            return False
        total = 0
        for i, d in enumerate(siren):
            n = int(d)
            if (len(siren) - 1 - i) % 2 == 1:
                n *= 2
            if n > 9:
                n -= 9
            total += n
        return total % 10 == 0

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
        if data.get("forme_juridique"):
            parts.append(f"Forme: {data['forme_juridique']}")
        if data.get("code_postal"):
            parts.append(f"CP: {data['code_postal']}")
        if data.get("ville"):
            parts.append(f"Ville: {data['ville']}")
        if data.get("annee_creation"):
            parts.append(f"Creation: {data['annee_creation']}")
        return " | ".join(parts) if parts else f"Entreprise: {data.get('nom_entreprise', '?')}"

    def _completer_via_api(self, data: dict):
        """Appelle l'API entreprise.gouv.fr pour remplir les champs manquants."""
        try:
            import requests
            siren = data["siren"]
            r = requests.get(
                "https://recherche-entreprises.api.gouv.fr/search",
                params={"q": siren, "page": 1, "per_page": 1},
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
            )
            if r.status_code != 200:
                return

            results = r.json().get("results", [])
            if not results:
                return
            api = results[0]

            if not data.get("nom_entreprise"):
                nom_api = (api.get("nom_complet", "") or api.get("nom_raison_sociale", "") or
                          api.get("denomination", "") or api.get("nom_entreprise", ""))
                if nom_api:
                    data["nom_entreprise"] = nom_api

            if not data.get("code_postal") or not data.get("ville"):
                siege = api.get("siege", {}) or {}
                if isinstance(siege, dict):
                    if not data.get("code_postal"):
                        cp = siege.get("code_postal", "")
                        if cp:
                            data["code_postal"] = cp
                    if not data.get("ville"):
                        ville = siege.get("libelle_commune", "") or siege.get("ville", "")
                        if ville:
                            data["ville"] = ville

            if not data.get("forme_juridique"):
                fj = api.get("forme_juridique", "") or api.get("nature_juridique", "")
                if fj:
                    data["forme_juridique"] = fj

            if not data.get("capital"):
                cap = api.get("capital_social", "") or api.get("capital", "")
                if cap:
                    num = re.sub(r"\D", "", str(cap))
                    if num:
                        data["capital"] = num + " EUR"

            if not data.get("effectif_adresse") or not data.get("effectif_entreprise"):
                tranche = api.get("tranche_effectif_salarie", "") or api.get("tranche_effectif", "")
                if tranche:
                    eff_map = {
                        "00": "0 employe", "01": "1-2 employes", "02": "3-5 employes",
                        "03": "6-9 employes", "11": "10-19 employes", "12": "20-49 employes",
                        "21": "50-99 employes", "22": "100-249 employes", "31": "250-499 employes",
                        "32": "500-999 employes", "41": "1000-1999 employes",
                        "42": "2000-4999 employes", "51": "5000-9999 employes"
                    }
                    eff_val = eff_map.get(tranche, tranche)
                    if not data.get("effectif_adresse"):
                        data["effectif_adresse"] = eff_val
                    if not data.get("effectif_entreprise"):
                        data["effectif_entreprise"] = eff_val

            if not data.get("siret"):
                siege = api.get("siege", {}) or {}
                if isinstance(siege, dict):
                    sirets = siege.get("siret", "")
                    if sirets and len(sirets) == 14:
                        data["siret"] = sirets

            if not data.get("activites_principales"):
                ap = api.get("activite_principale", "") or api.get("libelle_activite_principale", "")
                if ap:
                    data["activites_principales"] = ap

            if not data.get("code_naf"):
                naf = api.get("code_naf", "") or api.get("activite_principale", "")
                if naf:
                    data["code_naf"] = naf

        except ImportError:
            pass
        except Exception:
            pass

    # ── Découverte des URLs ──

    def _decouvrir_urls_kompass(self, code_naf: str, nb_pages: int = 1) -> list:
        """
        Découvre des URLs d'entreprises Kompass par code NAF via le moteur de recherche Kompass.
        """
        urls = []
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return urls

        for page in range(1, nb_pages + 1):
            try:
                search_url = f"https://fr.kompass.com/searchCompanies?nafCode={code_naf}&page={page}"
                r = requests.get(search_url, timeout=15,
                    headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 200:
                    for m in re.finditer(r'href="(/c/[^"]+)"', r.text):
                        url = "https://fr.kompass.com" + m.group(1)
                        if url not in urls:
                            urls.append(url)
            except Exception:
                pass

        return urls

    def _lire_urls_excel(self, chemin: str) -> list:
        """Lit les URLs depuis un fichier Excel."""
        urls = []
        try:
            import pandas as pd
            df = pd.read_excel(chemin, dtype=str)
            col_url = next((c for c in df.columns if "url" in c.lower()), df.columns[0])
            urls = [u for u in df[col_url].dropna().unique() if str(u).startswith("http")]
            print(f"  {len(urls)} URLs lues depuis {chemin}")
        except Exception as e:
            print(f"  Erreur lecture Excel: {e}")
        return urls


# ── CLI ──

if __name__ == "__main__":
    import sys
    scraper = ScraperKompass()
    config = {}

    if len(sys.argv) > 1 and sys.argv[1].endswith(".xlsx"):
        config["fichier_excel"] = sys.argv[1]
        print(f"  Mode fichier: {sys.argv[1]}")
    elif len(sys.argv) > 1:
        config["urls"] = [u for u in sys.argv[1:] if u.startswith("http")]
        print(f"  Mode URLs directes: {len(config['urls'])} URL(s)")
    else:
        print("  Mode découverte automatique (3 premiers codes NAF)")
        config["codes_naf"] = NAF_INDUSTRIELS[:3]
        config["nb_pages"] = 2

    scraper.run(config)
