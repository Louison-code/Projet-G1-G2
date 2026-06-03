-- ============================================================
-- PROJET G1/G2 - F-2049 | Réindustrialisation Française
-- T1.1.4 : Déploiement de la base SQL locale
-- Auteur : Louison Baudouin (R/A)
-- Date   : 2026
-- ============================================================

-- Supprimer les tables si elles existent (reset complet)
DROP TABLE IF EXISTS logs_erreurs;
DROP TABLE IF EXISTS indicateurs;
DROP TABLE IF EXISTS entreprises;

-- ============================================================
-- TABLE PRINCIPALE : entreprises
-- Contient toutes les données extraites par le scraper (T3)
-- ============================================================
CREATE TABLE entreprises (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Identifiants
    lien_kompass        TEXT UNIQUE,          -- URL source Kompass (clé naturelle)
    siret               TEXT,                 -- 14 chiffres
    siren               TEXT,                 -- 9 chiffres
    code_naf            TEXT,                 -- ex: 6201Z
    -- Informations société
    raison_sociale      TEXT NOT NULL,
    forme_juridique     TEXT,                 -- SAS, SARL, SA, etc.
    date_creation       TEXT,                 -- format AAAA-MM-JJ
    -- Localisation
    adresse             TEXT,
    ville               TEXT,
    code_postal         TEXT,
    departement         TEXT,
    region              TEXT,
    -- Contact & web
    site_web            TEXT,
    telephone           TEXT,
    email               TEXT,
    -- Données financières & RH
    chiffre_affaires    REAL,                 -- en euros, float
    effectifs           INTEGER,
    -- Activité / filière
    description         TEXT,                 -- description brute Kompass
    secteur_ia          TEXT,                 -- label attribué par le module IA (T2)
    filiere_ia          TEXT,                 -- filière industrielle (T2)
    -- Métadonnées de collecte
    date_scraping       TEXT,                 -- horodatage ISO 8601
    statut_scraping     TEXT DEFAULT 'pending', -- pending / success / error / blocked
    html_brut           TEXT,                 -- HTML nettoyé envoyé à l'IA (T3.1.4)
    CONSTRAINT chk_statut CHECK (statut_scraping IN ('pending','success','error','blocked','partial'))
);

-- ============================================================
-- TABLE INDICATEURS : données temporelles enrichies
-- Permet le suivi évolutif par entreprise
-- ============================================================
CREATE TABLE indicateurs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise_id       INTEGER NOT NULL,
    annee               INTEGER NOT NULL,     -- ex: 2024
    chiffre_affaires    REAL,
    effectifs           INTEGER,
    evolution_ca        REAL,                 -- % vs année précédente
    source              TEXT,                 -- ex: 'kompass', 'api_insee', 'site_web'
    date_insertion      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE LOGS_ERREURS : journal de bord du scraper
-- Essentiel pour le module d'auto-réparation (T4)
-- ============================================================
CREATE TABLE logs_erreurs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    entreprise_id       INTEGER,
    lien_kompass        TEXT,
    code_erreur         TEXT,                 -- ex: 'TIMEOUT', 'BLOCKED_403', 'CAPTCHA', 'SELECTOR_FAIL'
    message_erreur      TEXT,
    html_snapshot       TEXT,                 -- HTML au moment de l'erreur (pour l'auto-repair T4)
    selecteur_echoue    TEXT,                 -- sélecteur CSS/XPath ayant échoué
    tentatives          INTEGER DEFAULT 1,
    resolu              INTEGER DEFAULT 0,    -- 0=non résolu, 1=résolu par auto-repair
    date_erreur         TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (entreprise_id) REFERENCES entreprises(id) ON DELETE SET NULL
);

-- ============================================================
-- INDEX pour accélérer les requêtes Power BI
-- ============================================================
CREATE INDEX idx_entreprises_siren      ON entreprises(siren);
CREATE INDEX idx_entreprises_ville      ON entreprises(ville);
CREATE INDEX idx_entreprises_code_naf   ON entreprises(code_naf);
CREATE INDEX idx_entreprises_statut     ON entreprises(statut_scraping);
CREATE INDEX idx_entreprises_secteur_ia ON entreprises(secteur_ia);
CREATE INDEX idx_indicateurs_annee      ON indicateurs(annee);
CREATE INDEX idx_logs_code_erreur       ON logs_erreurs(code_erreur);
CREATE INDEX idx_logs_resolu            ON logs_erreurs(resolu);

-- ============================================================
-- DONNÉES DE TEST (jeu de 3 entreprises fictives)
-- ============================================================
INSERT INTO entreprises (lien_kompass, raison_sociale, siren, code_naf, ville, site_web, statut_scraping, date_scraping)
VALUES
    ('https://ca.kompass.com/fr/c/test-01/', 'ENTREPRISE_TEST_01', '802244988', '2711Z', 'Valserhône', 'https://test01.fr', 'success', datetime('now')),
    ('https://ca.kompass.com/fr/c/test-02/', 'ENTREPRISE_TEST_02', '529558496', '3320A', 'La Ricamarie', 'https://test02.fr', 'pending', datetime('now')),
    ('https://ca.kompass.com/fr/c/test-03/', 'ENTREPRISE_TEST_03', '477995161', '6201Z', 'Grigny', 'https://test03.fr', 'error', datetime('now'));

INSERT INTO logs_erreurs (entreprise_id, lien_kompass, code_erreur, message_erreur)
VALUES (3, 'https://ca.kompass.com/fr/c/test-03/', 'TIMEOUT', 'Page ne répond pas après 30s — délai dépassé');

SELECT 'Base de données initialisée avec succès.' AS status;
SELECT 'Tables créées : entreprises, indicateurs, logs_erreurs' AS tables;
SELECT count(*) || ' entreprises en base.' AS compte FROM entreprises;
