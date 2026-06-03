# Liste Noire — Sites interdits ou restreints (T0.1.3)

**Dernière mise à jour :** Juin 2026

> Sites dont le scraping est **interdit** ou **restreint** (CGU opposées, robots.txt restrictif, opposition constatée).

| Entreprise / Site | URL | Source | Motif | Statut | Ajouté le |
|---|---|---|---|---|---|
| Kompass.com | `https://ca.kompass.com/fr/c/*` | Kompass | `Disallow: /c/` dans robots.txt | Interdit | Juin 2026 |
| — | `https://www.kompass.com/searchCompanies` | Kompass | `Disallow: /searchCompanies` dans robots.txt | Interdit | Juin 2026 |
| — | `https://www.kompass.com/o/` | Kompass | `Disallow: /o/` dans robots.txt | Interdit | Juin 2026 |

## Règles générales

- Tout site dont les **CGU interdisent explicitement le scraping** → liste noire
- Tout site qui répond par un **blocage technique** (CAPTCHA, 403, blocage IP) → liste noire
- Tout site qui fait une **opposition explicite** (contact, email) → liste noire
- Tout site dont le `robots.txt` contient `Disallow: /` pour `User-agent: *` → liste noire

## Procédure d'ajout

1. Vérifier le robots.txt et les CGU du site
2. Noter le motif précis dans le tableau
3. Ajouter la date et la personne ayant pris la décision

---

*Document évolutif — mettre à jour dès qu'un nouveau site est blacklisté.*
