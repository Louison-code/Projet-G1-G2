from fastapi import APIRouter
from backend.database import fetchone, fetchall

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def stats_globales():
    total = fetchone("SELECT COUNT(*) AS n FROM entreprises")
    avec_siren = fetchone("SELECT COUNT(*) AS n FROM entreprises WHERE siren IS NOT NULL AND siren != ''")
    avec_email = fetchone("SELECT COUNT(*) AS n FROM entreprises WHERE email IS NOT NULL AND email != ''")
    avec_tel = fetchone("SELECT COUNT(*) AS n FROM entreprises WHERE telephone IS NOT NULL AND telephone != ''")
    avec_ca = fetchone("SELECT COUNT(*) AS n FROM entreprises WHERE ca IS NOT NULL")

    return {
        "total_entreprises": total["n"] if total else 0,
        "avec_siren": avec_siren["n"] if avec_siren else 0,
        "avec_email": avec_email["n"] if avec_email else 0,
        "avec_telephone": avec_tel["n"] if avec_tel else 0,
        "avec_ca": avec_ca["n"] if avec_ca else 0,
    }


@router.get("/geography")
def geographie():
    rows = fetchall(
        "SELECT departement, COUNT(*) AS n FROM entreprises "
        "WHERE departement IS NOT NULL AND departement != '' "
        "GROUP BY departement ORDER BY n DESC"
    )
    regions = fetchall(
        "SELECT region, COUNT(*) AS n FROM entreprises "
        "WHERE region IS NOT NULL AND region != '' "
        "GROUP BY region ORDER BY n DESC"
    )
    return {
        "par_departement": rows,
        "par_region": regions,
    }


@router.get("/evolution")
def evolution():
    return fetchall(
        "SELECT annee_financiere AS annee, COUNT(*) AS entreprises, "
        "ROUND(AVG(ca), 0) AS ca_moyen, "
        "ROUND(AVG(resultat_net), 0) AS resultat_moyen "
        "FROM entreprises WHERE ca IS NOT NULL "
        "GROUP BY annee_financiere ORDER BY annee_financiere"
    )


@router.get("/dernier-scraping")
def dernier_scraping():
    return fetchone(
        "SELECT date_scraping, statut_scraping, COUNT(*) AS n "
        "FROM entreprises WHERE date_scraping = (SELECT MAX(date_scraping) FROM entreprises) "
        "GROUP BY statut_scraping"
    )
