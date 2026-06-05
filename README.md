# Projet G1-G2 — Collecte de données pour la Réindustrialisation

Pipeline complet de collecte, traitement et visualisation de données d'entreprises françaises.

## Structure du projet

```
├── backend/                 # API REST (FastAPI)
│   ├── main.py              # Point d'entrée
│   ├── config.py            # Configuration
│   ├── database.py          # Connexion SQLite
│   ├── models/              # Modèles Pydantic
│   ├── routers/             # Endpoints API
│   └── services/            # Logique métier
│
├── frontend/                # Interface utilisateur (Streamlit)
│   ├── app.py               # Point d'entrée
│   └── pages/               # Onglets
│
├── scrapers/                # Moteurs d'extraction
│   ├── base.py              # Classe de base (ABC)
│   ├── kompass.py           # Scraping Kompass
│   └── api_gouv.py          # Scraping API Gouv
│
├── data/                    # Stockage
│   ├── base_reindustrialisation.db
│   └── exports/
│
├── config/                  # Configuration
│   ├── requirements.txt
│   └── .env.example
│
├── docs/                    # Documentation
│   ├── gestion_projet/      # Ex-00_GESTION_DE_PROJET
│   ├── conformite_juridique/ # Ex-01_CONFORMITE_JURIDIQUE
│   ├── environnement/       # Ex-02_ENVIRONNEMENT_ET_LOGICIELS
│   ├── ia/                  # Ex-03_IA
│   └── archives/scraping/   # Ex-04_SCRAPING (archives)
│
├── start.py                 # Lancement (FastAPI + Streamlit)
├── start.bat                # Lancement Windows
├── status.md                # Suivi d'avancement
├── livrables_drive.md       # Fichiers à mettre sur Google Drive
└── README.md
```

## Installation

```bash
pip install -r config/requirements.txt
```

## Utilisation

```bash
# Lancer l'application (API + interface)
python start.py
# Ou double-clic sur start.bat
```

## Ressources externes

Les fichiers binaires (PDF, PPT, Excel, images, DB) sont sur Google Drive.
Voir `livrables_drive.md` pour la liste complète.

## Statut actuel

Voir `status.md` pour le détail.
