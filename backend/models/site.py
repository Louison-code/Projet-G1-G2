from pydantic import BaseModel
from typing import Optional


class SiteBase(BaseModel):
    nom: str
    url_base: str
    type: str
    actif: bool = True
    delai_relance: int = 720


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    nom: Optional[str] = None
    url_base: Optional[str] = None
    type: Optional[str] = None
    actif: Optional[bool] = None
    delai_relance: Optional[int] = None


class Site(SiteBase):
    id: int
    date_dernier_scraping: Optional[str] = None
    date_creation: Optional[str] = None
