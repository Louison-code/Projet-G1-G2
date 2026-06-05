"""
====================================================================
PROJET G1/G2 — COLLECTE MASSIVE (API GOUV)
====================================================================
Ce script est la version finale "Production".
Il va aspirer TOUTES les entreprises liées à la réindustrialisation
et créer la base de données directement sur ton Bureau.
"""

import sqlite3
import time
import requests
import os
from datetime import datetime

# ─── CONFIGURATION DE LA MACHINE DE COLLECTE ──────────────────────
API_BASE    = "https://recherche-entreprises.api.gouv.fr/search"

# On force la création du fichier sur ton Bureau Windows/Mac
BUREAU = os.path.join(os.path.expanduser("~"), "Desktop")
DB_PATH = os.path.join(BUREAU, "Base_Reindustrialisation_Finale.db")

DELAI       = 0.5     # Pause de sécurité pour ne pas se faire bannir par l'État
PAGE_SIZE   = 25      # Max autorisé
MAX_PAGES   = 400     # Jusqu'à 10 000 entreprises par code NAF

# La liste de tes codes NAF (j'ai mis les principaux de l'industrie)
CODES_NAF_INDUSTRIE = [
    "2910Z", "3011Z", "2811Z", "2511Z", "1011Z", "1013A", "1020Z", 
    "2410Z", "2420Z", "2431Z", "2611Z", "2612Z", "2620Z"
] 
# (Tu peux rajouter les autres codes NAF dans cette liste si besoin)

# ─── CRÉATION DE LA BASE DE DONNÉES (SCHÉMA POWER BI) ─────────────

def init_db(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entreprises (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            lien_kompass     TEXT UNIQUE,
            siret            TEXT,
            siren            TEXT,
            code_naf         TEXT,
            raison_sociale   TEXT NOT NULL,
            forme_juridique  TEXT,
            adresse          TEXT,
            ville            TEXT,
            code_postal      TEXT,
            telephone        TEXT,
            email            TEXT,
            chiffre_affaires REAL,
            effectifs        INTEGER,
            statut_scraping  TEXT DEFAULT 'success',
            date_scraping    TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn

# ─── MOTEUR D'ASPIRATION ──────────────────────────────────────────

def appel_api(params, tentatives=3):
    for i in range(tentatives):
        try:
            resp = requests.get(API_BASE, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                print(f"\n  ⚠️  Le serveur de l'État sature — pause de 10s...")
                time.sleep(10)
            else:
                print(f"\n  ❌  Erreur serveur {resp.status_code}")
                time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"\n  ⚠️  Bug réseau : {e}")
            time.sleep(3)
    return None

def parser_resultat(hit):
    siege = {}
    etabs = hit.get("matching_etablissements") or hit.get("siege") or {}
    if isinstance(etabs, list) and etabs:
        siege = etabs[0]
    elif isinstance(etabs, dict):
        siege = etabs

    def g(d, *keys, default=""):
        for k in keys:
            v = d.get(k)
            if v not in (None, "", []): return str(v)
        return default

    # Reconstitution de l'adresse propre
    num     = g(siege, "numero_voie")
    typ     = g(siege, "type_voie")
    nom_v   = g(siege, "libelle_voie")
    adresse = " ".join(filter(None, [num, typ, nom_v])).strip()

    siren = g(hit, "siren")
    
    # Transformation des effectifs
    eff_brut = g(hit, "tranche_effectif_salarie")
    effectifs_estimes = None
    if eff_brut:
        try: effectifs_estimes = int(eff_brut) * 5 
        except: pass

    return {
        "lien_kompass"    : f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}",
        "siret"           : g(siege, "siret"),
        "siren"           : siren,
        "code_naf"        : g(hit, "activite_principale"),
        "raison_sociale"  : g(hit, "nom_raison_sociale", "nom_complet"),
        "forme_juridique" : g(hit, "nature_juridique"),
        "adresse"         : adresse,
        "ville"           : g(siege, "libelle_commune"),
        "code_postal"     : g(siege, "code_postal"),
        "telephone"       : None, 
        "email"           : None, 
        "chiffre_affaires": None, 
        "effectifs"       : effectifs_estimes,
        "statut_scraping" : "success"
    }

def sauvegarder(batch, conn):
    if not batch: return 0
    inserts = [b for b in batch if b.get("siren")]
    if not inserts: return 0
    conn.executemany("""
        INSERT OR IGNORE INTO entreprises (
            lien_kompass, siret, siren, code_naf, raison_sociale, 
            forme_juridique, adresse, ville, code_postal, telephone, 
            email, chiffre_affaires, effectifs, statut_scraping, date_scraping
        ) VALUES (
            :lien_kompass, :siret, :siren, :code_naf, :raison_sociale,
            :forme_juridique, :adresse, :ville, :code_postal, :telephone,
            :email, :chiffre_affaires, :effectifs, :statut_scraping, datetime('now')
        )
    """, inserts)
    conn.commit()
    return len(inserts)

# ─── LANCEMENT DE LA BOUCLE PRINCIPALE ────────────────────────────

def lancer_collecte_massive(conn):
    print("\n" + "🔥" * 30)
    print("  DÉMARRAGE DE LA COLLECTE MASSIVE")
    print(f"  Fichier de destination : {DB_PATH}")
    print("🔥" * 30 + "\n")

    total_insere = 0

    for idx, naf in enumerate(CODES_NAF_INDUSTRIE):
        print(f"\n▶️ Démarrage du secteur NAF : {naf} ({idx+1}/{len(CODES_NAF_INDUSTRIE)})")
        insere_naf, page = 0, 1
        
        while page <= MAX_PAGES:
            data = appel_api({"activite_principale": naf, "page": page, "per_page": PAGE_SIZE, "is_siege": "true"})
            
            if not data or not data.get("results"): 
                break
                
            n = sauvegarder([parser_resultat(r) for r in data["results"]], conn)
            insere_naf += n
            total_insere += n
            
            # Affichage de la progression dans la console
            print(f"   ↳ Page {page} scannée... +{n} entreprises ajoutées (Total NAF: {insere_naf})", end="\r")
            
            # Si on a atteint la dernière page pour ce code NAF
            if page * PAGE_SIZE >= data.get("total_results", 0): 
                break
                
            page += 1
            time.sleep(DELAI)
            
        print(f"\n✅ NAF {naf} terminé. {insere_naf} entreprises insérées.")

# ─── LE DÉCLENCHEUR ───────────────────────────────────────────────

if __name__ == "__main__":
    connexion = init_db(DB_PATH)
    lancer_collecte_massive(connexion)
    connexion.close()
