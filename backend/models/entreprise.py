from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EntrepriseBase(BaseModel):
    url: Optional[str] = None
    nom_entreprise: Optional[str] = None
    roles: Optional[str] = None
    description: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = "France"
    telephone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    site_web: Optional[str] = None
    siren: Optional[str] = None
    siret: Optional[str] = None
    tva: Optional[str] = None
    capital: Optional[str] = None
    forme_juridique: Optional[str] = None
    annee_creation: Optional[str] = None
    effectif_adresse: Optional[str] = None
    effectif_entreprise: Optional[str] = None
    activites_principales: Optional[str] = None
    activites_secondaires: Optional[str] = None
    autres_classifications: Optional[str] = None
    code_naf: Optional[str] = None
    departement: Optional[str] = None
    region: Optional[str] = None
    chiffre_affaires: Optional[float] = None
    secteur_ia: Optional[str] = None
    filiere_ia: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EntrepriseCreate(EntrepriseBase):
    pass


class EntrepriseUpdate(BaseModel):
    nom_entreprise: Optional[str] = None
    roles: Optional[str] = None
    description: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    pays: Optional[str] = None
    telephone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    site_web: Optional[str] = None
    tva: Optional[str] = None
    capital: Optional[str] = None
    forme_juridique: Optional[str] = None
    annee_creation: Optional[str] = None
    effectif_adresse: Optional[str] = None
    effectif_entreprise: Optional[str] = None
    activites_principales: Optional[str] = None
    activites_secondaires: Optional[str] = None
    autres_classifications: Optional[str] = None
    code_naf: Optional[str] = None
    departement: Optional[str] = None
    region: Optional[str] = None
    chiffre_affaires: Optional[float] = None
    secteur_ia: Optional[str] = None
    filiere_ia: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class Entreprise(EntrepriseBase):
    id: int
    statut_scraping: Optional[str] = None
    date_scraping: Optional[str] = None
