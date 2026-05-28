"""
PROJET G1/G2 — SCRAPER KOMPASS (VERSION MAXIMALE VITESSE)
══════════════════════════════════════════════════════════
PRINCIPE : chaque worker = 1 Chrome indépendant en mode EAGER
  → EAGER = Chrome arrête d'attendre dès que le HTML est prêt,
    sans attendre images / CSS / polices / trackers Kompass.
    C'est le gain le plus important : -60% sur le temps de chargement.

ESTIMATION :
  8 workers × ~1.5s/URL = 7 100 URLs en ~22-30 minutes

INSTALLATION :
  pip install DrissionPage openpyxl

USAGE Thonny : F5 directement, les fichiers doivent être dans le même dossier.
"""

import sqlite3, re, time, threading, queue, random
import openpyxl
from DrissionPage import ChromiumPage, ChromiumOptions

# ══════════════════════════════════════════════════════
#  CONFIG — modifie max_workers selon ta RAM
#  8 Go RAM  → workers = 6
#  12 Go RAM → workers = 8
#  16 Go RAM → workers = 10
# ══════════════════════════════════════════════════════
CONFIG = {
    "excel_input" : "liste_URL_KOMPASS.xlsx",
    "db_path"     : "base_reindustrialisation.db",
    "max_workers" : 8,
    "timeout_page": 10,    # secondes max pour charger une page
    "timeout_ele" : 0.2,   # secondes max pour trouver un élément DOM
    "batch_commit": 15,    # inserts avant un flush SQL
}

db_lock = threading.Lock()

# ══════════════════════════════════════════════════════
#  BASE DE DONNÉES
# ══════════════════════════════════════════════════════
def init_db(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entreprises (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            lien_kompass     TEXT UNIQUE,
            siret            TEXT,
            siren            TEXT,
            code_naf         TEXT,
            raison_sociale   TEXT NOT NULL,
            forme_juridique  TEXT,
            adresse          TEXT,
            ville            TEXT,
            code_postal      TEXT,
            telephone        TEXT,
            email            TEXT,
            chiffre_affaires REAL,
            effectifs        INTEGER,
            statut_scraping  TEXT DEFAULT 'pending',
            date_scraping    TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_statut ON entreprises(statut_scraping);
        CREATE INDEX IF NOT EXISTS idx_siren  ON entreprises(siren);
    """)
    conn.commit()
    return conn


def charger_urls(excel_path, conn):
    wb  = openpyxl.load_workbook(excel_path, read_only=True)
    all_urls = [
        {"lien_kompass": r[0], "raison_sociale": str(r[1] or ""), "ville": str(r[2] or "")}
        for r in wb["Base"].iter_rows(values_only=True)
        if r[0] and str(r[0]).startswith("http")
    ]
    with db_lock:
        deja = {row[0] for row in conn.execute(
            "SELECT lien_kompass FROM entreprises WHERE statut_scraping='success'"
        ).fetchall()}

    restantes = [u for u in all_urls if u["lien_kompass"] not in deja]
    print(f"  Total Excel       : {len(all_urls)}")
    print(f"  Déjà en base      : {len(deja)}")
    print(f"  Restant à scraper : {len(restantes)}")
    return restantes


# ══════════════════════════════════════════════════════
#  NAVIGATEUR — mode EAGER = LE PLUS RAPIDE
# ══════════════════════════════════════════════════════
def creer_navigateur():
    co = ChromiumOptions()
    co.headless(True)

    # ── EAGER : arrête d'attendre dès que le HTML est prêt ──────────────
    # Sans ça Chrome attend images + CSS + polices + trackers → +3s/page
    co.set_argument("--page-load-strategy=eager")

    # ── Désactiver tout ce qui est inutile ───────────────────────────────
    co.set_argument("--blink-settings=imagesEnabled=false")  # pas d'images
    co.set_argument("--disable-gpu")
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument("--disable-extensions")
    co.set_argument("--disable-background-networking")
    co.set_argument("--disable-sync")
    co.set_argument("--disable-translate")
    co.set_argument("--disable-notifications")
    co.set_argument("--disable-logging")
    co.set_argument("--mute-audio")
    co.set_argument("--disable-infobars")
    co.set_argument("--ignore-certificate-errors")

    # ── Bloquer CSS, polices et médias (HTML seul suffit pour les regex) ─
    co.set_pref("profile.managed_default_content_settings.stylesheets", 2)
    co.set_pref("profile.managed_default_content_settings.fonts",       2)
    co.set_pref("profile.managed_default_content_settings.media_stream", 2)

    return ChromiumPage(addr_or_opts=co)


# ══════════════════════════════════════════════════════
#  EXTRACTION D'UNE PAGE — tout en regex sur le HTML brut
# ══════════════════════════════════════════════════════
def extraire(meta, page):
    url = meta["lien_kompass"]

    def c(t):
        return re.sub(r'\s+', ' ', str(t)).strip() if t else ""

    def rx(pattern, html, default=""):
        try:
            m = re.search(pattern, html, re.I | re.S)
            if m:
                return c(m.group(1) if m.lastindex else m.group(0))
        except Exception:
            pass
        return default

    try:
        page.get(url, timeout=CONFIG["timeout_page"])
        # Pas de sleep — on lit le HTML immédiatement grâce au mode eager
        html = page.html

        # ── SIRET / SIREN ──────────────────────────────────────────────
        siret_raw = rx(r"SIRET[^:]*:\s*([\d\s]{14,20})", html)
        siret = re.sub(r"\s", "", siret_raw)[:14] if siret_raw else ""
        siren = siret[:9] if len(siret) >= 9 else re.sub(r"\D", "", rx(r"\b(\d{9})\b", html))[:9]

        # ── TÉLÉPHONE — chercher d'abord href="tel:" dans le HTML ──────
        tel = rx(r'href=["\']tel:([+\d\s\.\-]{7,15})["\']', html)
        if not tel:
            tel = rx(r'(?:téléphone|phone|tel)[^\d]*(\+?[\d\s\.\-]{10,15})', html)

        # ── ADRESSE ────────────────────────────────────────────────────
        adresse = rx(r'"streetAddress"\s*:\s*"([^"]{5,100})"', html)
        if not adresse:
            # fallback : bloc adresse textuel
            adresse = rx(r'(?:adresse|address)[^<]{0,30}<[^>]+>\s*([^<]{10,100})', html)

        # ── CODE POSTAL ────────────────────────────────────────────────
        cp = rx(r'"postalCode"\s*:\s*"(\d{5})"', html)
        if not cp:
            cp = rx(r'\b(\d{5})\b', html)

        # ── NAF / FORME JURIDIQUE ──────────────────────────────────────
        naf  = rx(r'(?:NAF|APE)[^:]*:\s*(\d{4}[A-Z])', html)
        fjur = rx(r'\b(SAS|SARL|SA|EURL|SNC|SASU|SCI|EI|GIE|SCOP)\b', html)

        # ── EMAIL ──────────────────────────────────────────────────────
        email = rx(r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', html)

        # ── CHIFFRE D'AFFAIRES — chercher dans le HTML brut ────────────
        ca_val = None
        ca_str = rx(r"Chiffre d.affaires[^<]*<[^>]*>\s*([^<]{2,30})", html)
        if ca_str:
            num = re.sub(r"[^\d,.]", "", ca_str).replace(",", ".")
            if num:
                try:
                    mult = 1_000_000 if "m" in ca_str.lower() else 1_000 if "k" in ca_str.lower() else 1
                    ca_val = float(num) * mult
                except ValueError:
                    pass

        # ── EFFECTIFS ──────────────────────────────────────────────────
        eff_val = None
        eff_str = rx(r"Effectifs?[^<]*<[^>]*>\s*([^<]{1,20})", html)
        if eff_str:
            n = re.sub(r"[^\d]", "", eff_str)
            if n:
                try:
                    eff_val = int(n)
                except ValueError:
                    pass

        ville = str(meta.get("ville", "")).split("-")[0].strip()

        return {
            "lien_kompass"    : url,
            "raison_sociale"  : meta["raison_sociale"],
            "siret"           : siret,
            "siren"           : siren,
            "code_naf"        : naf,
            "forme_juridique" : fjur,
            "adresse"         : adresse[:200],
            "ville"           : ville,
            "code_postal"     : cp,
            "telephone"       : tel,
            "email"           : email,
            "chiffre_affaires": ca_val,
            "effectifs"       : eff_val,
            "statut_scraping" : "success",
        }

    except Exception:
        return {
            "lien_kompass"   : url,
            "raison_sociale" : meta["raison_sociale"],
            "statut_scraping": "error",
        }


# ══════════════════════════════════════════════════════
#  SAUVEGARDE BATCH
# ══════════════════════════════════════════════════════
def flush(batch, conn):
    if not batch:
        return
    with db_lock:
        conn.executemany("""
            INSERT OR REPLACE INTO entreprises (
                lien_kompass, raison_sociale, siret, siren, code_naf,
                forme_juridique, adresse, ville, code_postal, telephone,
                email, chiffre_affaires, effectifs, statut_scraping, date_scraping
            ) VALUES (
                :lien_kompass, :raison_sociale, :siret, :siren, :code_naf,
                :forme_juridique, :adresse, :ville, :code_postal, :telephone,
                :email, :chiffre_affaires, :effectifs, :statut_scraping, datetime('now')
            )
        """, [
            {
                "lien_kompass"    : r.get("lien_kompass", ""),
                "raison_sociale"  : r.get("raison_sociale", ""),
                "siret"           : r.get("siret", ""),
                "siren"           : r.get("siren", ""),
                "code_naf"        : r.get("code_naf", ""),
                "forme_juridique" : r.get("forme_juridique", ""),
                "adresse"         : r.get("adresse", ""),
                "ville"           : r.get("ville", ""),
                "code_postal"     : r.get("code_postal", ""),
                "telephone"       : r.get("telephone", ""),
                "email"           : r.get("email", ""),
                "chiffre_affaires": r.get("chiffre_affaires"),
                "effectifs"       : r.get("effectifs"),
                "statut_scraping" : r.get("statut_scraping", "error"),
            }
            for r in batch
        ])
        conn.commit()


# ══════════════════════════════════════════════════════
#  WORKER — 1 thread = 1 Chrome = file d'URLs indépendante
# ══════════════════════════════════════════════════════
def worker(wid, tq, conn, cpt, cpt_lock, total):
    page  = creer_navigateur()
    batch = []

    while True:
        try:
            meta = tq.get(timeout=5)
        except queue.Empty:
            break

        res = extraire(meta, page)

        # Retry une fois sur erreur avec petit délai
        if res["statut_scraping"] == "error":
            time.sleep(random.uniform(1, 2))
            res = extraire(meta, page)

        batch.append(res)
        if len(batch) >= CONFIG["batch_commit"]:
            flush(batch, conn)
            batch.clear()

        with cpt_lock:
            cpt[0] += 1
            fait = cpt[0]
            ok   = "✅" if res["statut_scraping"] == "success" else "❌"
            pct  = int(fait / total * 100)
            bar  = "█" * (pct // 5) + "░" * (20 - pct // 5)
            nom  = res["raison_sociale"][:28]
            print(f"\r  [{bar}] {pct:3d}% {fait:5d}/{total} {ok} {nom:<28}", end="", flush=True)

        tq.task_done()

    flush(batch, conn)
    page.quit()


# ══════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════
def lancer():
    start = time.time()
    print("=" * 62)
    print("  KOMPASS MAX SPEED — PROJET G1/G2")
    print("=" * 62)

    conn = init_db(CONFIG["db_path"])

    try:
        urls = charger_urls(CONFIG["excel_input"], conn)
    except Exception as e:
        print(f"❌ Erreur Excel : {e}")
        conn.close()
        return

    if not urls:
        print("✅ Tout est déjà en base.")
        conn.close()
        return

    n = len(urls)
    w = min(CONFIG["max_workers"], n)

    # Estimation basée sur mode eager (~1.5s/URL)
    est = round(n / w * 1.5 / 60, 0)
    print(f"\n  ⚡ Mode EAGER activé (pas d'attente images/CSS/polices)")
    print(f"  🔧 {w} navigateurs Chrome indépendants")
    print(f"  ⏱️  Estimation : ~{int(est)} minutes\n")

    tq        = queue.Queue()
    cpt       = [0]
    cpt_lock  = threading.Lock()

    for meta in urls:
        tq.put(meta)

    threads = []
    for i in range(w):
        t = threading.Thread(
            target=worker,
            args=(i + 1, tq, conn, cpt, cpt_lock, n),
            daemon=True
        )
        t.start()
        threads.append(t)
        time.sleep(1.5)   # décalage de démarrage pour éviter la surcharge initiale

    for t in threads:
        t.join()

    duree = int(time.time() - start)
    h, m, s = duree // 3600, (duree % 3600) // 60, duree % 60

    stats = dict(conn.execute(
        "SELECT statut_scraping, COUNT(*) FROM entreprises GROUP BY statut_scraping"
    ).fetchall())

    print(f"\n\n{'=' * 62}")
    print(f"  ✅ Succès  : {stats.get('success', 0):,}")
    print(f"  ❌ Erreurs : {stats.get('error',   0):,}")
    print(f"  ⏱️  Durée   : {h}h {m}min {s}s")
    print(f"  📁 Base    : {CONFIG['db_path']}")
    print(f"{'=' * 62}")

    conn.close()


if __name__ == "__main__":
    lancer()
