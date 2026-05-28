# Projet G1-G2 — Collecte de données pour la Réindustrialisation

Pipeline complet de collecte, traitement et visualisation de données d'entreprises françaises liées à la réindustrialisation.

## Structure du projet

```
00_GESTION_DE_PROJET/       — Cadrage, planning, suivi d'équipe, risques, présentations
01_CONFORMITE_JURIDIQUE/    — Documentation juridique et liste blanche
02_ENVIRONNEMENT_ET_LOGICIELS/ — Guides d'installation, configuration, liens
03_IA/                      — Documentation IA, datasets, tests de performance
04_SCRAPER/                 — Moteurs d'extraction (API Gouv + scraping Kompass)
05_VISUALISATION_POWERBI_ET_PILOTAGE/ — Dashboards, rapports, interface
06_LIVRABLES_FINAUX/        — Rapports finaux, supports, manuels
```

## Scripts de scraping (04_SCRAPER)

| Script | Source | Description |
|---|---|---|
| `api_entreprises_gouv.py` | API data.gouv.fr | Collecte via l'API publique par codes NAF industriels |
| `kompass_max_speed.py` | Kompass | Scraping parallélisé (8 workers Chrome) avec mode EAGER |
| `traitement_max_speed.py` | — | Pipeline ETL : nettoyage + export Excel (Power BI) et JSON |

## Prérequis

```bash
pip install DrissionPage openpyxl pandas requests
```

## Utilisation

```bash
# 1. Collecte via API Gouv
python 04_SCRAPER/developpement_du_moteur_d_extraction_ET_Traitement_des_donnees_extraites/scraping\ rapide/api_entreprises_gouv.py

# 2. Scraping Kompass (nécessite liste_URL_KOMPASS.xlsx)
python 04_SCRAPER/developpement_du_moteur_d_extraction_ET_Traitement_des_donnees_extraites/scraping\ rapide/kompass_max_speed.py

# 3. Pipeline ETL (après scraping)
python 04_SCRAPER/developpement_du_moteur_d_extraction_ET_Traitement_des_donnees_extraites/scraping\ rapide/traitement_max_speed.py
```
