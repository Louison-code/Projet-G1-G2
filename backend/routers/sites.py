from fastapi import APIRouter, HTTPException
from backend.database import fetchone, fetchall, execute
from backend.models.site import Site, SiteCreate, SiteUpdate

router = APIRouter(prefix="/api/sites", tags=["Sites"])


@router.get("")
def lister_sites(actif: bool = None):
    if actif is not None:
        return fetchall("SELECT * FROM sites_scraping WHERE actif = ? ORDER BY nom", (int(actif),))
    return fetchall("SELECT * FROM sites_scraping ORDER BY nom")


@router.post("", status_code=201)
def creer_site(data: SiteCreate):
    id_ = execute(
        "INSERT INTO sites_scraping (nom, url_base, type, actif, delai_relance) VALUES (?, ?, ?, ?, ?)",
        (data.nom, data.url_base, data.type, int(data.actif), data.delai_relance)
    )
    return fetchone("SELECT * FROM sites_scraping WHERE id = ?", (id_,))


@router.get("/{id}")
def detail_site(id: int):
    site = fetchone("SELECT * FROM sites_scraping WHERE id = ?", (id,))
    if not site:
        raise HTTPException(404, "Site introuvable")
    champs = fetchall("SELECT * FROM champs_scraping WHERE site_id = ? ORDER BY nom_champ", (id,))
    return {**site, "champs": champs}


@router.put("/{id}")
def modifier_site(id: int, data: SiteUpdate):
    site = fetchone("SELECT * FROM sites_scraping WHERE id = ?", (id,))
    if not site:
        raise HTTPException(404, "Site introuvable")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return site
    if "actif" in updates:
        updates["actif"] = int(updates["actif"])
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    execute(f"UPDATE sites_scraping SET {set_clause} WHERE id = ?",
            list(updates.values()) + [id])
    return fetchone("SELECT * FROM sites_scraping WHERE id = ?", (id,))


@router.delete("/{id}")
def supprimer_site(id: int):
    site = fetchone("SELECT * FROM sites_scraping WHERE id = ?", (id,))
    if not site:
        raise HTTPException(404, "Site introuvable")
    execute("DELETE FROM sites_scraping WHERE id = ?", (id,))
    return {"message": "Site supprimé", "id": id}


@router.get("/{id}/champs")
def lister_champs_site(id: int):
    site = fetchone("SELECT * FROM sites_scraping WHERE id = ?", (id,))
    if not site:
        raise HTTPException(404, "Site introuvable")
    return fetchall("SELECT * FROM champs_scraping WHERE site_id = ? ORDER BY nom_champ", (id,))
