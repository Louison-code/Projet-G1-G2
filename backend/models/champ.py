from pydantic import BaseModel
from typing import Optional


class ChampBase(BaseModel):
    site_id: int
    nom_champ: str
    selecteur_css: Optional[str] = None
    selecteur_xpath: Optional[str] = None
    actif: bool = True


class ChampCreate(ChampBase):
    pass


class ChampUpdate(BaseModel):
    nom_champ: Optional[str] = None
    selecteur_css: Optional[str] = None
    selecteur_xpath: Optional[str] = None
    actif: Optional[bool] = None


class Champ(ChampBase):
    id: int
