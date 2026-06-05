# Charte Éthique du Projet G1-G2


## Préambule

Le projet G1-G2 est un projet académique mené dans le cadre de Centrale Lille. Il vise à collecter et structurer des données d'entreprises à des fins de réindustrialisation et d'analyse économique. La présente charte fixe les principes éthiques que tout membre de l'équipe s'engage à respecter.

## 1. Transparence

- Le scraping est effectué avec un **User-Agent explicite et identifiable** : `CartoIndustrielleBot/1.0 (Projet académique Centrale Lille ; contact: <carine.guillaud@relocalisations.fr>
>)`.
- Aucune tentative de masquer, falsifier ou usurper l'identité du robot.
- La source de chaque donnée collectée est documentée et traçable.

## 2. Respect des sites cibles

- **robots.txt** : consulté et respecté pour chaque site avant tout scraping.
- **CGU** : lues et respectées. En cas d'interdiction explicite du scraping, le site est ajouté à la liste noire.
- **Aucun contournement** de mesures techniques (CAPTCHA, blocage IP, login forcé, etc.).
- Le scraping est interrompu immédiatement si le site manifeste une opposition technique (ralentissement, erreurs 429/503).

## 3. Politesse et rate limiting

- Délai minimum de **1 s entre requêtes** (2,5 s min / 5 s max pour Kompass).
- Pause d'au moins **60 s entre chaque batch** de 50 entreprises.
- Scraping limité aux **heures creuses** (préférentiellement la nuit) pour ne pas impacter le service.

## 4. Protection des données (RGPD)

- **Minimisation** : seules les données professionnelles (raison sociale, SIRET, adresse, téléphone) sont collectées. Aucune donnée personnelle (email privé, données sensibles).
- **Finalité** : les données sont utilisées exclusivement pour l'analyse économique et la réindustrialisation.
- **Sécurité** : les bases de données ne sont pas stockées dans des dépôts publics.
- **Droit d'opposition** : toute entreprise peut demander la suppression de ses données. Une adresse de contact est disponible dans le User-Agent.

## 5. Listes blanche et noire

- **Liste blanche** : sites dont le scraping est explicitement autorisé (API data.gouv.fr, SIRENE).
- **Liste noire** : sites interdits (CGU opposées, robots.txt restrictif, opposition constatée).
- Les listes sont tenues à jour dans le dépôt du projet.



Tout membre de l'équipe s'engage à respecter cette charte. 
---

**Références** : Note de synthèse juridique (T0.1.1) — RGPD (UE) 2016/679 — CNIL Recommandations web scraping
