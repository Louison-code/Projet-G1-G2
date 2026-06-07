# Plan de développement — Projet G1-G2

> Dernière mise à jour : 07/06/2026 (nettoyage BDD + suppression indicateurs/champs_scraping)
> Légende : ✅ Terminé | 🔧 En cours | ☐ Pas commencé

---

## Étape 1 — Mise en place du projet

### 1.1 Structure du dépôt
- [x] Créer l'arborescence du projet (backend/, frontend/, scrapers/, data/, config/, docs/)
- [x] Configurer `.gitignore` (exclure *.db, __pycache__)
- [x] Séparer les fichiers livrables (83 fichiers déplacés vers Google Drive)

### 1.2 Configuration
- [x] Créer `config/requirements.txt` (dépendances Python)
- [x] Créer `config/.env.example` (variables d'environnement)
- [x] Créer `start.py` — lancement FastAPI + Streamlit
- [x] Créer `start.bat` — double-clic Windows
- [x] Créer `README.md` — présentation du projet

### 1.3 Base de données
- [x] Définir le schéma SQLite initial (7 tables) → réduit à 5 tables : entreprises, source_scraping, logs_erreurs, config_llm, conversations
- [x] Créer la base `data/base_reindustrialisation.db`
- [x] Insérer les 2 sites sources (kompass, api_gouv)
- [x] Mettre les colonnes `lat`/`lon` dans `entreprises` pour la géolocalisation
- [x] Ajouter index UNIQUE(siren) et index(siret) pour déduplication

---

## Étape 2 — Scraping (collecte des données)

### 2.1 Scraping Kompass
- [x] Installer DrissionPage
- [x] Développer le scraper Kompass avec 6 workers Chrome en parallèle
- [x] Gérer le mode headless pour accélérer le chargement
- [x] Implémenter la file d'attente et la gestion d'erreurs
- [x] Extraction via regex + complétion API Gouv
- [x] Upsert par SIREN dans la base commune
- [x] Code prêt (scraper_kompass.py)
- [x] ⛔ **Abandonné : DataDome CAPTCHA** — Kompass.com est protégé par DataDome, un anti-bot payant. Pas de solution gratuite viable. Les données de contact (email, téléphone) devront venir d'autres sources (LinkedIn, scraping manuel).

### 2.2 Scraping API Gouv
- [x] Développer le script d'appel API REST
- [x] Gérer la pagination (25 résultats/page, 400 pages max)
- [x] Cibler 13 codes NAF industriels (2910Z, 3011Z, 2811Z...)
- [x] Parser les réponses JSON → extraire SIRET, SIREN, NAF, raison sociale, adresse
- [x] Gérer les erreurs 429 (rate limiting) avec backoff

### 2.3 Pipeline post-traitement
- [x] Nettoyage : suppression doublons SIREN/SIRET, normalisation (ville, email, SIREN)
- [x] ~~Indicateurs : alimenter la table `indicateurs` (CA, effectifs, année)~~ → supprimée, fusionnée dans `entreprises.ca`
- [x] Géolocalisation : adresse → coordonnées GPS (Nominatim OSM)
- [x] Classification : détection secteur IA + filière par mots-clés et code NAF
- [x] Export : Excel (PowerBI) + CSV + JSON dans `exports/`

### 2.4 Refonte dans l'architecture cible
- [x] `scrapers/base.py` — classe abstraite BaseScraper avec upsert par SIREN et connexion DB
- [x] `scrapers/scraper_kompass.py` — scraper Kompass (BaseScraper, 6 workers, 22 champs clients)
- [x] `scrapers/scraper_api_gouv.py` — scraper API Gouv (BaseScraper, pagination par NAF)
- [x] `scrapers/scraper_url_directe.py` — scraper URL directe (via SocieteScraper, 22 champs) → 🔇 retiré (sans intérêt, doublon API Gouv)
- [ ] `scrapers/linkedin.py` — scraper LinkedIn (si nécessaire)
- [x] `backend/services/scraper_manager.py` — orchestrateur qui lit la config BDD et lance les scrapers
- [x] ~~Rendre les scrapers dynamiques~~ → Abandonné : `champs_scraping` supprimée, scrapers 100% hardcodés

### 2.5 Tests scraping (06/06/2026)
- [x] **API Gouv** ✅ — 125 entreprises importées en 3 pages (code NAF 28.11Z)
- [x] **URL directe** ✅ — SAFRAN extrait depuis societe.com (SIREN trouvé)
- [x] **Kompass** ⛔ Abandonné (DataDome CAPTCHA)

---

## Étape 3 — Backend API (FastAPI)

### 3.1 Structure du backend
- [x] Créer `backend/main.py` — point d'entrée FastAPI avec 33 routes
- [x] Créer `backend/config.py` — configuration centralisée
- [x] Créer `backend/database.py` — connexion SQLite + helpers (fetchone, fetchall, execute)
- [x] Créer les dossiers `models/`, `routers/`, `services/`

### 3.2 Modèles Pydantic
- [x] `backend/models/entreprise.py` — modèle Entreprise (32 champs dont 22 client)
- [x] `backend/models/site.py` — modèle SiteScraping (nom, url, type, delai)
- [x] `backend/models/champ.py` — modèle ChampScraping (selecteurs CSS/XPath)
- [x] `backend/models/conversation.py` — modèle Conversation (question, sql, réponse)
- [x] `backend/models/indicateur.py` — modèle Indicateur (CA, effectifs par année)

### 3.3 Routes API
- [x] `backend/routers/sites.py` :
  - `GET /api/sites` — lister tous les sites
  - `POST /api/sites` — ajouter un site
  - `GET /api/sites/{id}` — détail d'un site + ses champs
  - `PUT /api/sites/{id}` — modifier un site
  - `DELETE /api/sites/{id}` — supprimer un site
  - `GET /api/sites/{id}/champs` — lister les champs d'un site
- [x] `backend/routers/champs.py` :
  - `GET /api/champs` — lister tous les champs (avec filtre site_id)
  - `POST /api/champs` — ajouter un champ
  - `PUT /api/champs/{id}` — modifier un champ
  - `DELETE /api/champs/{id}` — supprimer un champ
- [x] `backend/routers/scraping.py` :
  - `POST /api/scrape/run` — lancer le scraping (api_gouv ou url)
  - `GET /api/scrape/status` — statut en cours (thread dédié)
  - `POST /api/scrape/stop` — arrêter
  - `GET /api/scrape/logs` — historique des erreurs
  - `GET /api/scrape/sites-a-rescraper` — sites en retard
  - `POST /api/scrape/relancer-si-besoin` — relancer les sites en retard
- [x] `backend/routers/config_llm.py` :
  - `GET /api/config/llm` — voir config
  - `PUT /api/config/llm` — changer mode/modele/endpoint
- [x] `backend/routers/export.py` :
  - `POST /api/export` — exporter CSV ou JSON
- [x] `backend/routers/dashboard.py` :
  - `GET /api/dashboard/stats` — KPIs (total, siren, email, tel, geo)
  - `GET /api/dashboard/geography` — répartition dépt/région
  - `GET /api/dashboard/secteurs` — secteurs IA
  - `GET /api/dashboard/filiere` — filières
  - `GET /api/dashboard/evolution` — évolution temporelle (via `entreprises.ca`)
  - `GET /api/dashboard/dernier-scraping` — dernière collecte
- [x] `backend/routers/chat.py` :
  - `POST /api/chat` — poser une question (mots-clés pour l'instant)
  - `GET /api/chat/history` — historique des conversations

### 3.4 Tests API
- [ ] Tester tous les endpoints avec Swagger (http://localhost:8000/docs)
- [ ] Vérifier les réponses JSON, les codes HTTP, les erreurs

---

## Étape 4 — Interface Utilisateur (Streamlit)

### 4.1 Structure du frontend
- [x] Créer `frontend/app.py` — point d'entrée avec navigation ✅ (stub)
- [x] Créer `frontend/pages/` — dossier des pages ✅
- [x] Créer les 4 pages stubs ✅

### 4.2 Page Dashboard
- [x] `frontend/pages/01_dashboard.py` :
  - KPIs : nombre d'entreprises, CA moyen, % géolocalisées, % email
  - Graphique secteurs d'activité (camembert)
  - Graphique CA par région (barres)
  - Évolution temporelle (entreprises + CA)
  - Dernier scraping : date, statut, compteurs
  - Top 10 départements

### 4.3 Page Scraping
- [x] `frontend/pages/02_scraping.py` :
  - Notification : "X sources nécessitent une mise à jour"
  - Boutons : Lancer / Arrêter / Actualiser
  - Barre de progression + statut en direct (rafraîchissement auto)
  - Liste des sources configurées (ajouter, modifier, supprimer)
  - Liste des champs par source (ajouter, activer/désactiver)
  - Historique des erreurs
  - Terminologie unifiée : "source" au lieu de "site"

### 4.4 Page Configuration
- [ ] `frontend/pages/04_config.py` :
  - Sélecteur LLM (local Ollama / API OpenAI)
  - Champ endpoint, modèle, clé API
  - Chemin de la base de données
  - Format d'export par défaut (PNG, HTML, PDF, CSV)
  - À propos : version, licence

---

## Étape 5 — Chatbot RAG

### 5.1 Moteur RAG
- [x] `backend/services/llm_adapter.py` :
  - Mode local : appeler Ollama (http://localhost:11434)
  - Mode API : appeler OpenAI / Mistral
  - Fonction `ask(prompt)` → réponse texte
- [x] `backend/services/rag_engine.py` :
  - Lecture dynamique du schéma BDD (sqlite_master)
  - Text-to-SQL : question française → requête SQL
  - Exécution SQL (lecture seule)
  - Reformulation de la réponse en français

### 5.2 Route Chat
- [x] `backend/routers/chat.py` :
  - `POST /api/chat` — envoyer une question via le RAG engine
  - `GET /api/chat/history` — historique des conversations
  - `DELETE /api/chat/history` — effacer l'historique

### 5.3 Page Chat
- [x] `frontend/pages/03_chat.py` :
  - Champ de texte pour poser une question
  - Historique de la conversation
  - Affichage des réponses textes avec requête SQL dans expander
  - Bouton effacer l'historique

### 5.4 Page Configuration LLM
- [x] `frontend/pages/04_config.py` :
  - Sélecteur de modèle Ollama
  - Champ endpoint, modèle
  - Bouton test connexion
  - Sauvegarde en BDD via l'API

### 5.5 API LLM externe (future)
- [ ] Ajouter la prise en charge d'API externes (OpenAI, Mistral...) avec sélecteur de mode et gestion de clé API

---

## Étape 6 — Fonctionnalités avancées

### 6.1 Géolocalisation
- [x] Ajouter colonnes `lat`/`lon` dans `entreprises`
- [ ] Géocoder les adresses au scraping (Nominatim ou Google Maps)
- [ ] Afficher la carte interactive sur le dashboard

### 6.2 Graphiques dynamiques (LLM → Plotly)
- [ ] Intégrer la génération de graphiques par le LLM
- [ ] Types supportés : carte bulles, barres, camembert, histogramme, nuage de points, séries temporelles
- [ ] Exporter au format PNG (Kaleido), HTML (Plotly.js), PDF

### 6.3 Données financières (CA, résultat net)
- [ ] **Objectif** : enrichir les entreprises avec leur chiffre d'affaires et résultat net pour les cartographies industrielles
- [ ] **Champs ajoutés** dans `entreprises` : `ca`, `resultat_net`, `annee_financiere`, `source_financiere`, `date_maj_financiere`
- [ ] **Table `indicateurs` supprimée** (fusionnée dans `entreprises`)

**Solutions possibles pour scraper les données financières :**

| Solution | Coût | Avantages | Inconvénients |
|---|---|---|---|
| **API Entreprise (gouv.fr)** | Gratuit | Données officielles DGFIP, fiable | Habilitation nécessaire (quelques semaines), seulement 3 derniers exercices, pas les micro-entreprises |
| **Pappers API** | 30€/mois (500 req) | API propre, toutes les données, facile à intégrer | Payant au volume, 100 requêtes gratuites pour tester |
| **Scraping Pappers.fr** | Gratuit | Site 100% gratuit en consultation, historique complet | Risque de blocage (anti-bot), lent |
| **Scraping Societe.com** | Gratuit | Données financières disponibles | Anti-bot (proxies nécessaires), fragile |

**Recommandation** : commencer par scraper Pappers.fr (site gratuit) ciblé sur les NAF industriels (~50k entreprises), et basculer sur l'API Entreprise (gouv) une fois l'habilitation obtenue pour fiabiliser les données.

### 6.4 Scraping fin par entreprise
- [ ] Permettre de rescraper une entreprise spécifique (et non toute la source)
- [ ] Ajouter une table ou un champ pour cibler des URLs individuelles à rescraper
- [ ] Interface UI pour lancer le scraping d'une seule fiche entreprise

### 6.5 Scraper générique CSS
- [x] Annulé — Kompass + LinkedIn suffisent pour couvrir tous les champs. Pas de besoin métier identifié.

---

## Étape 7 — Tests & Qualité

### 7.1 Tests backend
- [ ] Tests unitaires des modèles Pydantic
- [ ] Tests des routes API (pytest + httpx)
- [ ] Tests du RAG engine (Text-to-SQL avec requêtes types)

### 7.2 Tests scraping
- [ ] Tests du scraper Kompass (avec pages mockées)
- [ ] Tests de l'API Gouv (avec réponses mockées)
- [ ] Tests du scraper manager (orchestration)

### 7.3 Tests frontend
- [ ] Tests Streamlit (navigation, affichage)
- [ ] Tests chatbot (questions + vérification des réponses)

---

## Étape 8 — Déploiement & Livraison

### 8.1 Finalisation
- [ ] Figer `requirements.txt` avec les versions exactes
- [ ] Écrire la documentation déploiement client
- [ ] Créer le dossier livrable client (sans les fichiers Drive)

### 8.2 Livraison
- [ ] Dossier livrable sur GitHub (code uniquement)
- [ ] Fichiers binaires sur Google Drive
- [ ] Lien Drive dans le README.md
- [ ] `start.bat` → double-clic → application prête

---

## Récapitulatif

| Étape | Total tâches | ✅ Fait | ☐ Reste |
|-------|-------------|---------|---------|
| 1 — Mise en place | 13 | 13 | 0 |
| 2 — Scraping | 27 | 24 | 3 |
| 3 — Backend API | 18 | 16 | 2 |
| 4 — Frontend | 12 | 9 | 3 |
| 5 — Chatbot RAG | 4 | 4 | 0 |
| 6 — Avancées | 13 | 1 | 12 |
| 7 — Tests | 8 | 0 | 8 |
| 8 — Déploiement | 7 | 0 | 7 |
| **Total** | **101** | **67** | **34** |
