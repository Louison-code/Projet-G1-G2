from fastapi import APIRouter, HTTPException
from backend.database import fetchone, fetchall, execute
from backend.models.champ import Champ, ChampCreate, ChampUpdate

router = APIRouter(prefix="/api/champs", tags=["Champs"])


@router.get("")
def lister_champs(site_id: int = None):
    if site_id:
        return fetchall("SELECT * FROM champs_scraping WHERE site_id = ? ORDER BY nom_champ", (site_id,))
    return fetchall("SELECT c.*, s.nom AS site_nom FROM champs_scraping c "
                    "LEFT JOIN sites_scraping s ON c.site_id = s.id "
                    "ORDER BY s.nom, c.nom_champ")


@router.post("", status_code=201)
def creer_champ(data: ChampCreate):
    site = fetchone("SELECT * FROM sites_scraping WHERE id = ?", (data.site_id,))
    if not site:
        raise HTTPException(404, "Site introuvable")
    existant = fetchone(
        "SELECT * FROM champs_scraping WHERE site_id = ? AND nom_champ = ?",
        (data.site_id, data.nom_champ)
    )
    if existant:
        raise HTTPException(409, f"Le champ '{data.nom_champ}' existe déjà pour ce site")
    id_ = execute(
        "INSERT INTO champs_scraping (site_id, nom_champ, selecteur_css, selecteur_xpath, actif) "
        "VALUES (?, ?, ?, ?, ?)",
        (data.site_id, data.nom_champ, data.selecteur_css, data.selecteur_xpath, int(data.actif))
    )
    return fetchone("SELECT * FROM champs_scraping WHERE id = ?", (id_,))


@router.put("/{id}")
def modifier_champ(id: int, data: ChampUpdate):
    champ = fetchone("SELECT * FROM champs_scraping WHERE id = ?", (id,))
    if not champ:
        raise HTTPException(404, "Champ introuvable")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return champ
    if "actif" in updates:
        updates["actif"] = int(updates["actif"])
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    execute(f"UPDATE champs_scraping SET {set_clause} WHERE id = ?",
            list(updates.values()) + [id])
    return fetchone("SELECT * FROM champs_scraping WHERE id = ?", (id,))


@router.delete("/{id}")
def supprimer_champ(id: int):
    champ = fetchone("SELECT * FROM champs_scraping WHERE id = ?", (id,))
    if not champ:
        raise HTTPException(404, "Champ introuvable")
    execute("DELETE FROM champs_scraping WHERE id = ?", (id,))
    return {"message": "Champ supprimé", "id": id}
