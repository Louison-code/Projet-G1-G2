from datetime import datetime
from backend.database import fetchall, fetchone, execute

SCRAPERS_DISPONIBLES = {
    "api": ("scrapers.scraper_api_gouv", "ScraperApiGouv"),
    "api_gouv": ("scrapers.scraper_api_gouv", "ScraperApiGouv"),
    "kompass": ("scrapers.scraper_kompass", "ScraperKompass"),
}


def _instancier_scraper(type_src: str):
    import importlib
    key = type_src.lower().replace(" ", "_")
    if key not in SCRAPERS_DISPONIBLES:
        return None
    module_path, class_name = SCRAPERS_DISPONIBLES[key]
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)()
    except (ImportError, AttributeError):
        return None


def lancer_scraping(source: str = None, config: dict = None, progression: callable = None) -> dict:
    config = config or {}
    progression = progression or _progression_stub

    sites = fetchall("SELECT * FROM sites_scraping WHERE actif = 1")
    if source:
        sites = [s for s in sites if s.get("nom") == source or s.get("type") == source]

    total_global = 0
    reussites_global = 0
    sources_traitees = 0

    for idx, site in enumerate(sites):
        nom = site.get("nom", "?")
        type_src = site.get("type", "?")
        site_id = site.get("id")

        progression(idx + 1, max(len(sites), 1), f"Preparation de {nom}")

        champs = fetchall(
            "SELECT nom_champ, selecteur_css, selecteur_xpath FROM champs_scraping "
            "WHERE site_id = ? AND actif = 1 ORDER BY nom_champ",
            (site_id,)
        )
        noms_champs = [c["nom_champ"] for c in champs] if champs else []

        config_source = dict(config)
        config_source["nom_source"] = nom
        if noms_champs:
            config_source["champs"] = noms_champs
        if champs:
            config_source["selecteurs"] = {c["nom_champ"]: c for c in champs}

        def _progression_source(faits, total, message=""):
            progression(faits, total, f"[{nom}] {message}")

        scraper = _instancier_scraper(type_src)
        if not scraper:
            progression(idx + 1, max(len(sites), 1), f"Type ignore: {type_src}")
            execute("INSERT INTO logs_erreurs (url, code_erreur, message_erreur) VALUES (?, ?, ?)",
                    (nom, "TYPE_INCONNU", f"type de source: {type_src}"))
            continue

        try:
            resultats = scraper.run(config_source, progression=_progression_source)
            nb = len(resultats) if resultats else 0
            total_global += nb
            reussites_global += nb
            sources_traitees += 1

            execute(
                "UPDATE sites_scraping SET date_dernier_scraping = ? WHERE id = ?",
                (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), site_id)
            )
            progression(idx + 1, max(len(sites), 1), f"{nom} : {nb} entreprise(s)")
        except Exception as e:
            execute(
                "INSERT INTO logs_erreurs (url, code_erreur, message_erreur) VALUES (?, ?, ?)",
                (nom, "MANAGER_ERROR", str(e)[:500])
            )
            progression(idx + 1, max(len(sites), 1), f"{nom} : erreur {str(e)[:80]}")
            continue

    # Fallback : si source demandee mais pas trouvee en BDD, lancer le scraper directement
    if not sites and source:
        scraper = _instancier_scraper(source)
        if scraper:
            progression(0, 1, f"Lancement de {source}...")
            try:
                resultats = scraper.run(config, progression=progression)
                nb = len(resultats) if resultats else 0
                return {
                    "message": f"{nb} entreprise(s) traitee(s) via {source}",
                    "total": nb,
                    "reussites": nb,
                    "sources": 1,
                }
            except Exception as e:
                execute(
                    "INSERT INTO logs_erreurs (url, code_erreur, message_erreur) VALUES (?, ?, ?)",
                    (source, "MANAGER_ERROR", str(e)[:500])
                )
                return {"message": f"Erreur: {str(e)[:120]}", "total": 0, "reussites": 0, "sources": 0}

    return {
        "message": f"{reussites_global} entreprise(s) traitee(s) sur {sources_traitees} source(s)",
        "total": total_global,
        "reussites": reussites_global,
        "sources": sources_traitees,
    }


def _progression_stub(faits, total, message=""):
    pass
