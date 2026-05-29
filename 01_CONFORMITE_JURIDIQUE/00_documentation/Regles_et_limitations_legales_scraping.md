# Règles et Limitations Légales du Projet G1-G2

## Conformité RGPD (Règlement Général sur la Protection des Données)

- **Données personnelles** : ne collecter que les données strictement nécessaires (raison sociale, SIRET, adresse — pas de données personnelles des salariés)
- **Finalité** : les données collectées doivent avoir une finalité légitime et déclarée (réindustrialisation)
- **Proportionnalité** : ne pas collecter d'emails personnels, téléphones portables, ou données sensibles
- **Droit d'opposition** : les entreprises ciblées peuvent demander la suppression de leurs données
- **Sécurité** : les bases de données doivent être stockées de façon sécurisée (accès restreint)

## Utilisation de l'API publique data.gouv.fr

- ✅ L'API `recherche-entreprises.api.gouv.fr` est libre et ouverte — pas de restriction légale
- ✅ Les données du répertoire SIRENE sont publiques (INSEE)
- ✅ Respecter un délai entre les requêtes pour ne pas saturer le service (0.5s minimum — déjà configuré)
- ❌ Ne pas revendre les données brutes sans transformation significative

## Scraping du site Kompass.com

- ⚠️ Consulter le fichier `robots.txt` de Kompass pour connaître les restrictions
- ⚠️ Respecter les conditions générales d'utilisation (CGU) du site
- ⚠️ Ne pas contourner de mesures techniques de protection (login, captcha, blocage)
- ⚠️ Limiter la fréquence des requêtes pour ne pas impacter le service
- ⚠️ Les données collectées doivent être utilisées à des fins non commerciales ou avec droit de réutilisation

## Cadre légal français

- **Loi pour une République numérique** (2016) : les informations publiques des entreprises sont librement réutilisables
- **Code des relations entre le public et l'administration** : libre accès aux documents administratifs (données INSEE, SIRENE)
- **Loi informatique et libertés** : encadre la collecte de données personnelles
- **Respect des conditions d'utilisation** des sites web (art. 323-1 du code pénal — accès frauduleux à un système)

## Recommandations pour le projet

1. Toujours privilégier l'API publique (data.gouv.fr) avant le scraping direct
2. Respecter un délai minimum entre les requêtes (rate limiting)
3. Ne pas stocker les bases de données dans des dossiers publics (GitHub) — le `.gitignore` les exclut déjà
4. Documenter la source des données (transparence)
5. Prévoir une procédure de suppression des données sur demande
