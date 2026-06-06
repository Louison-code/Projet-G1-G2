-- Schema de la base de donnees G1-G2
-- Execute avec: sqlite3 data/base_reindustrialisation.db < data/schema.sql

PRAGMA foreign_keys=ON;

CREATE TABLE entreprises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT,
    nom_entreprise TEXT,
    roles TEXT,
    description TEXT,
    code_postal TEXT,
    ville TEXT,
    pays TEXT DEFAULT 'France',
    telephone TEXT,
    fax TEXT,
    email TEXT,
    site_web TEXT,
    siren TEXT,
    siret TEXT,
    tva TEXT,
    capital TEXT,
    forme_juridique TEXT,
    annee_creation TEXT,
    effectif_adresse TEXT,
    effectif_entreprise TEXT,
    activites_principales TEXT,
    activites_secondaires TEXT,
    autres_classifications TEXT,
    code_naf TEXT,
    departement TEXT,
    region TEXT,
    chiffre_affaires REAL,
    secteur_ia TEXT,
    filiere_ia TEXT,
    date_scraping TEXT,
    statut_scraping TEXT DEFAULT 'pending',
    html_brut TEXT
, latitude REAL, longitude REAL);

CREATE TABLE sites_scraping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT UNIQUE,
    url_base TEXT,
    type TEXT,
    actif INTEGER DEFAULT 1,
    date_dernier_scraping TEXT,
    delai_relance INTEGER DEFAULT 720,
    date_creation TEXT DEFAULT (datetime('now'))
);

CREATE TABLE champs_scraping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    nom_champ TEXT NOT NULL,
    selecteur_css TEXT,
    selecteur_xpath TEXT,
    actif INTEGER DEFAULT 1,
    FOREIGN KEY (site_id) REFERENCES sites_scraping(id) ON DELETE CASCADE
);

CREATE TABLE indicateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise_id INTEGER,
    annee INTEGER,
    chiffre_affaires REAL,
    effectifs INTEGER,
    evolution_ca REAL,
    source TEXT,
    date_insertion TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (entreprise_id) REFERENCES entreprises(id)
);

CREATE TABLE logs_erreurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise_id INTEGER,
    url TEXT,
    code_erreur TEXT,
    message_erreur TEXT,
    html_snapshot TEXT,
    selecteur_echoue TEXT,
    tentatives INTEGER DEFAULT 0,
    resolu INTEGER DEFAULT 0,
    date_erreur TEXT DEFAULT (datetime('now'))
);

CREATE TABLE config_llm (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT DEFAULT 'local',
    endpoint TEXT,
    api_key_chiffree TEXT,
    modele TEXT DEFAULT 'llama3.2',
    prompt_system TEXT
);

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    sql_genere TEXT,
    reponse TEXT,
    resultats_count INTEGER,
    temps_execution_ms REAL,
    timestamp TEXT DEFAULT (datetime('now'))
);

-- Sites sources par defaut
INSERT OR IGNORE INTO sites_scraping (nom, url_base, type, actif, delai_relance) VALUES ('kompass', 'https://www.kompass.com', 'kompass', 1, 720);
INSERT OR IGNORE INTO sites_scraping (nom, url_base, type, actif, delai_relance) VALUES ('api_gouv', 'https://recherche-entreprises.api.gouv.fr', 'api', 1, 720);

-- Champs de scraping par defaut pour chaque source
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'url', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'nom_entreprise', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'roles', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'description', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'code_postal', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'ville', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'pays', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'telephone', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'fax', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'email', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'site_web', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'siren', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'siret', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'tva', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'capital', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'forme_juridique', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'annee_creation', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'effectif_adresse', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'effectif_entreprise', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'activites_principales', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'activites_secondaires', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (1, 'autres_classifications', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'url', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'nom_entreprise', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'roles', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'description', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'code_postal', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'ville', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'pays', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'telephone', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'fax', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'email', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'site_web', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'siren', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'siret', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'tva', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'capital', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'forme_juridique', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'annee_creation', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'effectif_adresse', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'effectif_entreprise', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'activites_principales', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'activites_secondaires', 1);
INSERT OR IGNORE INTO champs_scraping (site_id, nom_champ, actif) VALUES (2, 'autres_classifications', 1);

-- Configuration LLM par defaut
INSERT OR IGNORE INTO config_llm (id, mode, endpoint, modele) VALUES (1, 'local', 'http://localhost:11434', 'llama3.2');
