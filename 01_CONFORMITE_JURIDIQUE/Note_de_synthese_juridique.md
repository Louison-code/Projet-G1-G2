# Note de Synthèse Juridique — Projet G1-G2

## Contexte (T0 — Conformité & Cadre Légal)

Le projet collecte des données d'entreprises via deux sources : l'API publique data.gouv.fr (données SIRENE/INSEE) et le scraping du site Kompass.com. La présente note résume l'audit légal et éthique réalisé conformément au WBS T0.1.1 (Étude de la jurisprudence du Web Scraping).

## 1. Analyse de conformité (1.1 Audit légal & éthique)

### 1.1 RGPD
- Les données collectées (raison sociale, SIRET, adresse) sont des données non personnelles ou relevant de l'activité professionnelle
- Finalité légitime déclarée : réindustrialisation et analyse économique
- Principe de minimisation respecté : pas de données sensibles, pas d'emails personnels
- Droit d'opposition et procédure de suppression prévus

### 1.2 CGU et conformité AI Act
- L'API data.gouv.fr est librement accessible (Licence Ouverte Etalab) — aucun risque
- Kompass.com impose le respect de son robots.txt et de ses CGU : un crawler poli avec rate limiting est conforme
- Le projet n'utilise pas d'IA générative soumise à l'AI Act — les traitements sont statistiques et déterministes

### 1.3 Quotas éthiques et faisabilité
- Scraping limité à des horaires définis, avec délai minimum de 1s entre requêtes
- Aucun contournement de mesures techniques (pas de login forcé, pas de CAPTCHA bypass)
- Respect des listes blanche/noire définies dans la charte éthique

## 2. Cadre légal applicable

| Source | Statut |
|--------|--------|
| API data.gouv.fr | ✅ Libre et ouvert — pas de restriction |
| Scraping Kompass | ⚠️ Autorisé sous réserve du robots.txt et des CGU |
| Données SIRENE | ✅ Données publiques réutilisables (Loi République numérique 2016) |
| Code pénal art. 323-1 | ❌ Interdit l'accès frauduleux — non applicable ici |

## 3. Recommandations

1. Privilégier systématiquement l'API publique avant le scraping direct
2. Maintenir un délai de 1s entre requêtes et respecter le Crawl-delay du robots.txt
3. Ne pas stocker les bases dans des dépôts publics (`.gitignore` déjà configuré)
4. Documenter la source de chaque donnée pour assurer la traçabilité
5. Mettre à jour cette note si la jurisprudence ou la réglementation évolue

## Références

- RGPD (UE) 2016/679 — eur-lex.europa.eu
- Loi République numérique 2016 — legifrance.gouv.fr
- Code pénal art. 323-1 — legifrance.gouv.fr
- CNIL — Recommandations sur le web scraping — cnil.fr
- Licence Ouverte Etalab — etalab.gouv.fr
- API Recherche d'Entreprises — recherche-entreprises.api.gouv.fr
