"""
PROJET G1/G2 — SCRAPER KOMPASS (MULTI-ONGLETS SÉCURISÉ)
- Utilise un vrai navigateur pour contrer les protections et charger les données.
- Ouvre 4 onglets en parallèle (Temps divisé par 4 : ~2h30 au total).
- Utilise un Lock SQL pour écrire dans la base de données sans crash.
"""
import sqlite3, re, time, threading, random
import openpyxl
import concurrent.futures
from DrissionPage import ChromiumPage, ChromiumOptions

CONFIG = {
    "excel_input": "liste_URL_KOMPASS.xlsx",
    "db_path": "base_reindustrialisation_test.db",
    "max_onglets": 4,  # 4 onglets en même temps (ne pas mettre plus pour ne pas saturer la RAM)
    "taille_test": 7500
}

# Verrou de sécurité pour la base de données
db_lock = threading.Lock()

def init_db(path):
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entreprises (
            id INTEGER PRIMARY KEY AUTOINCREMENT, lien_kompass TEXT UNIQUE, siret TEXT, siren TEXT, 
            code_naf TEXT, raison_sociale TEXT NOT NULL, forme_juridique TEXT, adresse TEXT, 
            ville TEXT, code_postal TEXT, telephone TEXT, email TEXT, chiffre_affaires REAL, 
            effectifs INTEGER, statut_scraping TEXT DEFAULT 'pending'
        );
    """)
    conn.commit()
    return conn

def extraire_un_onglet(meta, page, conn):
    """Cette fonction est gérée par chaque onglet en parallèle"""
    url = meta["lien_kompass"]
    tab = page.new_tab() # Création d'un nouvel onglet invisible
    
    try:
        tab.get(url)
        time.sleep(random.uniform(0.5, 1.5)) # Petit délai pour laisser Kompass afficher la page
        
        # Fonctions de nettoyage
        def clean_text(text): return re.sub(r'\s+', ' ', text).strip() if text else ""
        def find_regex(pattern, defaut=""):
            try:
                m = re.search(pattern, tab.html, re.I | re.S)
                if m: return clean_text(m.group(1) if m.groups() else m.group(0))
            except: pass
            return defaut

        # Extraction ultra-ciblée (On est sur un vrai navigateur, donc ça marche)
        siret_brut = find_regex(r"SIRET[^:]*:\s*([\d\s]{14,20})")
        siret = re.sub(r"\s", "", siret_brut)[:14] if siret_brut else ""
        siren = siret[:9] if siret else re.sub(r"\D", "", find_regex(r"\b(\d{9})\b"))[:9]

        tel = ""
        try:
            tel_link = tab.ele('@href^tel:', timeout=0.5)
            if tel_link: tel = tel_link.attr('href').replace('tel:', '').strip()
        except: pass

        adresse = find_regex(r'"streetAddress"\s*:\s*"([^"]+)"')
        if not adresse:
            try:
                adr_ele = tab.ele('.basic-address-card', timeout=0.5) or tab.ele('.contact-address', timeout=0.5)
                if adr_ele: adresse = clean_text(adr_ele.text)
            except: pass

        ca_val = None
        try:
            tr_ca = tab.ele('xpath://tr[th[contains(., "Chiffre d\'affaires")]]', timeout=0.5)
            ca_str = tr_ca.ele('tag:td').text if tr_ca else ""
            if ca_str and any(x in ca_str.lower() for x in ['m', 'k', '€', 'eur']):
                num = re.sub(r'[^\d,.]', '', ca_str).replace(',', '.')
                if num: ca_val = float(num) * (1_000_000 if 'm' in ca_str.lower() else 1_000 if 'k' in ca_str.lower() else 1)
        except: pass

        eff_val = None
        try:
            tr_eff = tab.ele('xpath://tr[th[contains(., "Effectifs")]]', timeout=0.5)
            if tr_eff: eff_val = int(re.sub(r'[^\d]', '', tr_eff.ele('tag:td').text))
        except: pass

        ville_nom = str(meta.get("ville", "")).split('-')[0]

        # Sauvegarde en base de données avec le VERROU (pour ne pas crasher SQLite)
        with db_lock:
            conn.execute("""
                INSERT OR REPLACE INTO entreprises (
                    lien_kompass, raison_sociale, siret, siren, code_naf, forme_juridique, 
                    adresse, ville, code_postal, telephone, email, chiffre_affaires, effectifs, statut_scraping
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'success')
            """, (
                url, meta["raison_sociale"], siret, siren, find_regex(r"NAF\s*[:\-]?\s*(\d{4}[A-Z])"), 
                find_regex(r"\b(SAS|SARL|SA|EURL|SNC|SASU|EI)\b"), adresse[:150], ville_nom, 
                find_regex(r'"postalCode"\s*:\s*"(\d{5})"'), tel, find_regex(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'), 
                ca_val, eff_val
            ))
            conn.commit()
            
        print(f"✅ {meta['raison_sociale'][:20]:<20} | SIREN: {siren if siren else 'Rien'} | CA: {ca_val if ca_val else 'Rien'}")
        
    except Exception as e:
        print(f"❌ Échec sur {meta['raison_sociale'][:20]}")
    finally:
        tab.close() # On referme l'onglet obligatoirement pour libérer la RAM

def lancer_scraping_parallele():
    start_time = time.time()
    print(f"🚀 DÉMARRAGE : {CONFIG['max_onglets']} onglets en simultané (Vrai navigateur)...")

    try:
        wb = openpyxl.load_workbook(CONFIG["excel_input"], read_only=True)
        urls = [{"lien_kompass": r[0], "raison_sociale": r[1], "ville": r[2]} for r in list(wb["Base"].iter_rows(values_only=True))[1:] if r[0]]
        urls_a_traiter = urls[:CONFIG["taille_test"]]
    except Exception as e:
        return print(f"❌ Erreur Excel : {e}")

    conn = init_db(CONFIG["db_path"])
    
    # Configuration du navigateur principal
    co = ChromiumOptions().headless(True)
    co.set_argument('--blink-settings=imagesEnabled=false')
    co.set_argument('--disable-gpu')
    page = ChromiumPage(addr_or_opts=co)

    total = len(urls_a_traiter)
    
    # Lancement des 4 travailleurs en parallèle
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG["max_onglets"]) as executor:
        futures = []
        for meta in urls_a_traiter:
            futures.append(executor.submit(extraire_un_onglet, meta, page, conn))
        
        # Attendre que tout soit fini
        concurrent.futures.wait(futures)

    page.quit()
    conn.close()
    
    duree = int(time.time() - start_time)
    print(f"\n🏁 TERMINÉ ! Les {total} entreprises ont été traitées en {duree // 3600}h et {(duree % 3600) // 60} minutes.")

if __name__ == "__main__": 
    lancer_scraping_parallele()