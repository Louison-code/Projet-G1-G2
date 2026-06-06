from pydantic import BaseModel
from typing import Optional


class Indicateur(BaseModel):
    id: int
    entreprise_id: int
    annee: int
    chiffre_affaires: Optional[float] = None
    effectifs: Optional[int] = None
    evolution_ca: Optional[float] = None
    source: Optional[str] = None
    date_insertion: Optional[str] = None


class IndicateurCreate(BaseModel):
    entreprise_id: int
    annee: int
    chiffre_affaires: Optional[float] = None
    effectifs: Optional[int] = None
    evolution_ca: Optional[float] = None
    source: Optional[str] = None
