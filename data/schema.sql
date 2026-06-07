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
    date_scraping TEXT,
    statut_scraping TEXT DEFAULT 'pending',
    ca REAL,
    resultat_net REAL,
    annee_financiere INTEGER,
    source_financiere TEXT,
    date_maj_financiere TEXT
);

CREATE TABLE source_scraping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT UNIQUE,
    url_base TEXT,
    type TEXT,
    actif INTEGER DEFAULT 1,
    date_dernier_scraping TEXT,
    delai_relance INTEGER DEFAULT 720,
    date_creation TEXT DEFAULT (datetime('now'))
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
    modele TEXT DEFAULT 'llama3.2'
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
INSERT OR IGNORE INTO source_scraping (nom, url_base, type, actif, delai_relance) VALUES ('kompass', 'https://www.kompass.com', 'kompass', 1, 720);
INSERT OR IGNORE INTO source_scraping (nom, url_base, type, actif, delai_relance) VALUES ('api_gouv', 'https://recherche-entreprises.api.gouv.fr', 'api', 1, 720);

-- Configuration LLM par defaut
INSERT OR IGNORE INTO config_llm (id, mode, endpoint, modele) VALUES (1, 'local', 'http://localhost:11434', 'llama3.2');
