# Plan de développement — Projet G1-G2

> Dernière mise à jour : 06/06/2026
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
- [x] Définir le schéma SQLite (7 tables : entreprises, sites_scraping, champs_scraping, indicateurs, logs_erreurs, config_llm, conversations)
- [x] Créer la base `data/base_reindustrialisation.db`
- [x] Insérer les 2 sites sources (kompass, api_gouv)
- [x] Mettre les colonnes `lat`/`lon` dans `entreprises` pour la géolocalisation
- [x] Ajouter index UNIQUE(siren) et index(siret) pour déduplication

---

## Étape 2 — Scraping (collecte des données)

### 2.1 Scraping Kompass
- [x] Installer DrissionPage
- [x] Développer le scraper Kompass avec 8 workers Chrome en parallèle
- [x] Gérer le mode EAGER pour accélérer le chargement
- [x] Implémenter la file d'attente et la gestion d'erreurs
- [x] Tester sur 5 échantillons → valider l'extraction (SIREN, NAF, email, téléphone, site web)
- [x] Lancer la collecte sur les URLs de test

### 2.2 Scraping API Gouv
- [x] Développer le script d'appel API REST
- [x] Gérer la pagination (25 résultats/page, 400 pages max)
- [x] Cibler 13 codes NAF industriels (2910Z, 3011Z, 2811Z...)
- [x] Parser les réponses JSON → extraire SIRET, SIREN, NAF, raison sociale, adresse
- [x] Gérer les erreurs 429 (rate limiting) avec backoff

### 2.3 Pipeline post-traitement
- [x] Nettoyage : suppression doublons SIREN/SIRET, normalisation (ville, email, SIREN)
- [x] Indicateurs : alimenter la table `indicateurs` (CA, effectifs, année)
- [x] Géolocalisation : adresse → coordonnées GPS (Nominatim OSM)
- [x] Classification : détection secteur IA + filière par mots-clés et code NAF
- [x] Export : Excel (PowerBI) + CSV + JSON dans `exports/`

### 2.4 Refonte dans l'architecture cible
- [x] `scrapers/base.py` — classe abstraite BaseScraper avec upsert par SIREN et connexion DB
- [x] `scrapers/scraper_kompass.py` — scraper Kompass (BaseScraper, 6 workers, 22 champs clients)
- [x] `scrapers/scraper_api_gouv.py` — scraper API Gouv (BaseScraper, pagination par NAF)
- [x] `scrapers/scraper_url_directe.py` — scraper URL directe (via SocieteScraper, 22 champs)
- [ ] `scrapers/linkedin.py` — scraper LinkedIn (si nécessaire)
- [ ] `backend/services/scraper_manager.py` — orchestrateur qui lit la config BDD et lance les scrapers

---

## Étape 3 — Backend API (FastAPI)

### 3.1 Structure du backend
- [x] Créer `backend/main.py` — point d'entrée FastAPI ✅ (stub)
- [x] Créer `backend/config.py` — configuration centralisée ✅ (stub)
- [x] Créer `backend/database.py` — connexion SQLite ✅ (stub)
- [x] Créer les dossiers `models/`, `routers/`, `services/` ✅

### 3.2 Modèles Pydantic
- [ ] `backend/models/entreprise.py` — modèle Entreprise (id, siret, siren, naf, raison_sociale, ville...)
- [ ] `backend/models/site.py` — modèle Site (id, nom, url_base, type, actif, delai_relance)
- [ ] `backend/models/champ.py` — modèle Champ (id, site_id, nom_champ, selecteur_css, selecteur_xpath)
- [ ] `backend/models/conversation.py` — modèle Conversation (id, question, sql_genere, reponse)

### 3.3 Routes API
- [ ] `backend/routers/sites.py` :
  - `GET /api/sites` — lister tous les sites
  - `POST /api/sites` — ajouter un site
  - `GET /api/sites/{id}` — détail d'un site
  - `PUT /api/sites/{id}` — modifier un site
  - `DELETE /api/sites/{id}` — supprimer un site
- [ ] `backend/routers/champs.py` :
  - `GET /api/champs` — lister tous les champs
  - `POST /api/champs` — ajouter un champ
  - `PUT /api/champs/{id}` — modifier un champ
  - `DELETE /api/champs/{id}` — supprimer un champ
- [ ] `backend/routers/scraping.py` :
  - `POST /api/scrape/run` — lancer le scraping
  - `GET /api/scrape/status` — statut en cours
  - `POST /api/scrape/stop` — arrêter
  - `GET /api/scrape/logs` — historique
  - `GET /api/scrape/sites-a-rescraper` — sites en retard
  - `POST /api/scrape/relancer-si-besoin` — relancer les sites en retard
- [ ] `backend/routers/config_llm.py` :
  - `GET /api/config/llm` — voir config
  - `PUT /api/config/llm` — changer mode/modele
- [ ] `backend/routers/export.py` :
  - `POST /api/export` — exporter un graphique (PNG, HTML, PDF, CSV)
- [ ] `backend/routers/dashboard.py` :
  - `GET /api/dashboard/stats` — statistiques globales
  - `GET /api/dashboard/geography` — répartition géographique

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
- [ ] `frontend/pages/01_dashboard.py` :
  - KPIs : nombre d'entreprises, CA moyen, effectifs totaux
  - Carte de France (répartition géographique)
  - Graphique secteurs d'activité (camembert)
  - Graphique CA par région (barres)
  - Dernier scraping : date, statut, compteurs

### 4.3 Page Scraping
- [ ] `frontend/pages/02_scraping.py` :
  - Notification : "X sites nécessitent une mise à jour"
  - Boutons : Lancer / Arrêter / Vérifier les délais
  - Barre de progression + logs en direct
  - Liste des sites configurés (ajouter, modifier, supprimer)
  - Liste des champs par site (ajouter, activer/désactiver)

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
- [ ] `backend/services/llm_adapter.py` :
  - Mode local : appeler Ollama (http://localhost:11434)
  - Mode API : appeler OpenAI / Mistral
  - Fonction `ask(prompt)` → réponse texte
- [ ] `backend/services/rag_engine.py` :
  - Qualification : question, action ou visuel ?
  - Text-to-SQL : question française → requête SQL
  - Exécution SQL (lecture seule)
  - Reformulation de la réponse
  - Génération d'actions structurées (ajout site/champ)
  - Génération de spécifications Plotly (graphiques)

### 5.2 Route Chat
- [ ] `backend/routers/chat.py` :
  - `POST /api/chat` — envoyer une question
  - `GET /api/chat/history` — historique des conversations

### 5.3 Page Chat
- [ ] `frontend/pages/03_chat.py` :
  - Champ de texte pour poser une question
  - Historique de la conversation
  - Affichage des réponses textes
  - Affichage des graphiques Plotly (intégrés dans le chat)
  - Boutons d'export sous chaque graphique (PNG, HTML, PDF, CSV)

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

### 6.3 Indicateurs financiers
- [x] Alimenter la table `indicateurs` (CA, effectifs par année) — via pipeline_post_traitement.py
- [ ] Afficher l'évolution dans le temps sur le dashboard

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
| 1 — Mise en place | 15 | 15 | 0 |
| 2 — Scraping | 19 | 17 | 2 |
| 3 — Backend API | 25 | 5 | 20 |
| 4 — Frontend | 15 | 5 | 10 |
| 5 — Chatbot RAG | 10 | 0 | 10 |
| 6 — Avancées | 10 | 2 | 8 |
| 7 — Tests | 8 | 0 | 8 |
| 8 — Déploiement | 5 | 0 | 5 |
| **Total** | **107** | **44** | **63** |
