import csv, json, io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from backend.database import fetchall

router = APIRouter(prefix="/api/export", tags=["Export"])

COLONNES_EXPORT = [
    "url", "nom_entreprise", "roles", "description", "code_postal",
    "ville", "pays", "telephone", "fax", "email", "site_web",
    "siren", "siret", "tva", "capital", "forme_juridique",
    "annee_creation", "effectif_adresse", "effectif_entreprise",
    "activites_principales", "activites_secondaires", "autres_classifications",
    "code_naf", "departement", "region", "chiffre_affaires",
    "secteur_ia", "filiere_ia", "latitude", "longitude",
]


class ExportRequest(BaseModel):
    format: str = "csv"
    filtre: Optional[dict] = None


@router.post("")
def exporter(req: ExportRequest):
    if req.format not in ("csv", "json"):
        return {"erreur": "Format non supporté. Utilisez 'csv' ou 'json'."}

    sql = "SELECT " + ", ".join(f'"{c}"' for c in COLONNES_EXPORT) + " FROM entreprises ORDER BY nom_entreprise"
    params = ()

    if req.filtre and req.filtre.get("departement"):
        sql += " WHERE departement = ?"
        params = (req.filtre["departement"],)

    rows = fetchall(sql, params)
    data = [{c: r.get(c, "") for c in COLONNES_EXPORT} for r in rows]

    if req.format == "json":
        return StreamingResponse(
            io.StringIO(json.dumps(data, ensure_ascii=False, indent=2)),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=export_entreprises.json"}
        )

    output = io.StringIO()
    w = csv.writer(output, delimiter=";")
    w.writerow(COLONNES_EXPORT)
    for row in data:
        w.writerow([row[c] for c in COLONNES_EXPORT])
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export_entreprises.csv"}
    )
