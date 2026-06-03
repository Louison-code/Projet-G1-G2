# Benchmark des Bibliothèques de Scraping

**Tâche WBS T1.1.3** — Benchmark des bibliothèques de Scraping    
**Contexte :** Projet de collecte et structuration de données d'entreprises (100 000 sites cibles)

---

## 1. Critères d'évaluation

| # | Critère | Pondération | Détail |
|---|---------|-------------|--------|
| C1 | Passage à l'échelle (100k sites) | 25% | Capacité à scraper 100 000 sites sans saturation mémoire |
| C2 | Stockage SQL | 20% | Intégration native avec SQLite / compatibilité Power BI |
| C3 | Export Power BI | 15% | Génération de fichiers .xlsx formatés pour Power BI |
| C4 | Scraping unitaire incrémental | 15% | Possibilité d'ajouter 1 site → DB → Power BI sans tout relancer |
| C5 | Anti-bot / Cloudflare | 10% | Capacité à contourner Cloudflare, CAPTCHA, anti-scraping |
| C6 | Performance (vitesse brute) | 10% | Requêtes/s, parallélisme, consommation mémoire |
| C7 | Maintenabilité | 5% | Documentation, communauté, courbe d'apprentissage |

---

## 2. Bibliothèques comparées

| Bibliothèque | Version | Type | Licence |
|-------------|---------|------|---------|
| **DrissionPage** | 4.x | Browser automation (Chrome/Edge) | BSD |
| **Playwright** (Microsoft) | 1.x | Browser automation (Chromium/Firefox/WebKit) | Apache 2.0 |
| **Selenium** | 4.x | Browser automation (multi-browser) | Apache 2.0 |
| **Scrapy** | 2.x | Framework scraping asynchrone | BSD |
| **requests + BeautifulSoup** | req 2.x / bs4 4.x | HTTP + parsing HTML | Apache 2.0 / MIT |
| **requests** (API uniquement) | 2.x | HTTP client | Apache 2.0 |

---

## 3. Benchmark détaillé

### 3.1 DrissionPage — ✅ Actuellement utilisé

| Critère | Note | Commentaire |
|---------|------|-------------|
| C1 (100k sites) | ⚠️ 6/10 | Multi-threading possible (8 threads max recommandé) ; chaque thread = 1 onglet Chrome → mémoire élevée |
| C2 (SQL intégration) | ✅ 9/10 | Compatible sqlite3 stdlib ; pas d'ORM nécessaire |
| C3 (Power BI) | ✅ 9/10 | Export OpenPyXL natif ; pandas + .xlsx formaté = compatible Power BI |
| C4 (Incremental) | ✅ 9/10 | Scraping unitaire simple : 1 URL → 1 onglet → 1 ligne SQL ; facile à ajouter |
| C5 (Anti-bot) | ✅ 9/10 | Conçu pour contourner Cloudflare ; modifie les fingerprints navigateur |
| C6 (Performance) | ⚠️ 5/10 | Browser headless + multi-threading = lourd (500 Mo-1 Go RAM pour 8 threads) |
| C7 (Maintenabilité) | ⚠️ 5/10 | Communauté petite (< 5k stars), documentation en chinois/anglais |

**→ 6,5/10 pondéré**

### 3.2 Playwright (Microsoft)

| Critère | Note | Commentaire |
|---------|------|-------------|
| C1 (100k sites) | ✅ 8/10 | Async natif + multi-contextes ; moins lourd que Selenium |
| C2 (SQL intégration) | ✅ 9/10 | Même écosystème Python (sqlite3, pandas, openpyxl) |
| C3 (Power BI) | ✅ 9/10 | Idem DrissionPage — pandas/openpyxl en aval |
| C4 (Incremental) | ✅ 9/10 | Scraping unitaire simple via `page.goto()` |
| C5 (Anti-bot) | ⚠️ 6/10 | Détectable par Cloudflare (fingersprint) ; nécessite `playwright-stealth` |
| C6 (Performance) | ✅ 8/10 | Async + contexts légers ; meilleur que Selenium |
| C7 (Maintenabilité) | ✅ 8/10 | Microsoft, 70k+ stars, doc excellente, grosse communauté |

**→ 7,8/10 pondéré**

### 3.3 Selenium

| Critère | Note | Commentaire |
|---------|------|-------------|
| C1 (100k sites) | ⚠️ 5/10 | Lourd, chaque instance = 1 driver + 1 browser complet |
| C2 (SQL intégration) | ✅ 9/10 | Même écosystème Python |
| C3 (Power BI) | ✅ 9/10 | Idem |
| C4 (Incremental) | ✅ 9/10 | Idem |
| C5 (Anti-bot) | ❌ 3/10 | Très détectable par Cloudflare, fingerprints standards |
| C6 (Performance) | ❌ 4/10 | Le plus lent des browsers automatisés |
| C7 (Maintenabilité) | ✅ 9/10 | Standard industriel, communauté immense |

**→ 5,8/10 pondéré**

### 3.4 Scrapy

| Critère | Note | Commentaire |
|---------|------|-------------|
| C1 (100k sites) | ✅ 10/10 | Framework conçu pour ça ; async, middleware, pipelines, file rotation |
| C2 (SQL intégration) | ✅ 8/10 | Pipeline SQL possible mais nécessite implémentation manuelle |
| C3 (Power BI) | ⚠️ 6/10 | Export via pipelines CSV/JSON/XLSX ; nécessite Item Exporters |
| C4 (Incremental) | ⚠️ 5/10 | Pas conçu pour le scraping unitaire ; orienté crawl en masse |
| C5 (Anti-bot) | ❌ 3/10 | Requêtes HTTP uniquement (pas de JS) ; bloque sur Cloudflare |
| C6 (Performance) | ✅ 9/10 | Async Twisted, très rapide, mémoire faible |
| C7 (Maintenabilité) | ✅ 8/10 | Grosse communauté, doc riche, mature |

**→ 6,8/10 pondéré**

### 3.5 requests + BeautifulSoup

| Critère | Note | Commentaire |
|---------|------|-------------|
| C1 (100k sites) | ✅ 9/10 | Léger, rapide, facile à paralléliser |
| C2 (SQL intégration) | ✅ 9/10 | Idem |
| C3 (Power BI) | ✅ 9/10 | Idem |
| C4 (Incremental) | ✅ 9/10 | Idem |
| C5 (Anti-bot) | ❌ 1/10 | Bloque sur tout site dynamique (JS), Cloudflare, CAPTCHA |
| C6 (Performance) | ✅ 9/10 | ultra-léger, pas de browser |
| C7 (Maintenabilité) | ✅ 9/10 | Très connu, doc abondante |

**→ 6,7/10 pondéré** (excellent pour API, inutilisable pour Kompass)

### 3.6 requests (API seulement)

| Critère | Note | Commentaire |
|---------|------|-------------|
| C1 (100k sites) | ✅ 9/10 | Limité par rate limiting de l'API, pas par la lib |
| C2 (SQL intégration) | ✅ 9/10 | Idem |
| C3 (Power BI) | ✅ 9/10 | Idem |
| C4 (Incremental) | ✅ 10/10 | 1 requête API = 1 entreprise |
| C5 (Anti-bot) | ✅ 10/10 | API publique, pas de blocage |
| C6 (Performance) | ✅ 10/10 | Ultra-léger |
| C7 (Maintenabilité) | ✅ 10/10 | Stdlib-like |

**→ 9,4/10 pondéré** — mais limité à data.gouv.fr (ne remplace pas le scraping browser)

---

## 4. Tableau récapitulatif

| Bibliothèque | C1 100k | C2 SQL | C3 PBI | C4 Unitaire | C5 Anti-bot | C6 Perf | C7 Maint | **Note pondérée** |
|-------------|---------|--------|--------|-------------|-------------|---------|----------|:---:|
| **DrissionPage** | 6 | 9 | 9 | 9 | 9 | 5 | 5 | **6,5** |
| **Playwright** | 8 | 9 | 9 | 9 | 6 | 8 | 8 | **7,8** |
| Selenium | 5 | 9 | 9 | 9 | 3 | 4 | 9 | 5,8 |
| Scrapy | 10 | 8 | 6 | 5 | 3 | 9 | 8 | 6,8 |
| requests + BS4 | 9 | 9 | 9 | 9 | 1 | 9 | 9 | 6,7 |
| requests (API) | 9 | 9 | 9 | 10 | 10 | 10 | 10 | **9,4** |

---

## 5. Recommandation pour l'architecture du projet

### Architecture hybride retenue

```
┌─────────────────────────────────────────────────────────────┐
│                    Architecture                             │
├─────────────────┬─────────────────┬─────────────────────────┤
│  Source API      │  Scraping Browser │  Scraping unitaire     │
│  data.gouv.fr    │  DrissionPage     │  DrissionPage          │
│  (requests)      │  (batch 100k)     │  (1 site à la fois)    │
├─────────────────┼─────────────────┼─────────────────────────┤
│  → SQLite       │  → SQLite       │  → SQLite               │
│  → openpyxl/PBI │  → openpyxl/PBI │  → openpyxl/PBI         │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### Choix par source

| Source | Bibliothèque | Justification |
|--------|-------------|---------------|
| **API data.gouv.fr** | `requests` | API REST publique, pas de browser nécessaire (9,4/10) |
| **Kompass (batch 100k)** | **DrissionPage** | Seule lib capable de passer Cloudflare sur Kompass ; déjà testée et validée sur 7 100 URLs |
| **Kompass (1 site)** | **DrissionPage** | Même stack, réutilisation du code existant ; ajout SQL + Power BI en temps réel |
| **Sites web entreprises** | `requests` ou `DrissionPage` | `requests` si site statique ; DrissionPage si JS/Cloudflare |

### Pourquoi garder DrissionPage plutôt que migrer vers Playwright ?

1. **Anti-bot** : DrissionPage a été spécifiquement choisi et testé pour contourner Cloudflare sur Kompass — c'est le critère bloquant
2. **Code existant** : 3 scraper DrissionPage déjà opérationnels et validés sur 7 100 entreprises
3. **Incrémental** : l'ajout unitaire est déjà implémenté (1 URL → 1 ligne SQL → 1 export Power BI)
4. **Playwright serait préférable** si on repartait de zéro, mais la migration ne justifie pas le coût

### Limitations connues et mitigations

| Limitation | Mitigation |
|-----------|-----------|
| DrissionPage mémoire élevée sur 100k | Batching par lots de 50 avec pause (déjà implémenté) |
| Communauté DrissionPage petite | Documentation interne et scripts de référence dans le projet |
| Cloudflare peut changer | Suivre les mises à jour de DrissionPage ; fallback Playwright si nécessaire |

---

## 6. Conclusion

| Pour 100 000 sites | Pour 1 site unitaire |
|--------------------|---------------------|
| DrissionPage + requests (API) | DrissionPage (réutilise le même code) |
| SQLite pour le stockage | SQLite (même base) |
| Export openpyxl → Power BI | openpyxl → Power BI (même pipeline) |
| Batching par 50 avec pauses | Exécution directe sans batch |
