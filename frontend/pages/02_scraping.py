import streamlit as st
import requests
import time

API_BASE = "http://localhost:8000/api"

st.set_page_config(page_title="Scraping", layout="wide")

st.markdown("""
<style>
.card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 1.2rem;
    border: 1px solid #e9ecef;
    margin-bottom: 1rem;
}
.card-title {
    font-size: 0.85rem;
    color: #6c757d;
    margin: 0 0 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.card-value {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
}
.stat-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
}
.stat-item {
    flex: 1;
    min-width: 120px;
}
hr.section {
    margin: 1.5rem 0 1rem;
    opacity: 0.2;
}
.site-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0.8rem;
    background: white;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    margin-bottom: 0.4rem;
}
.site-row:hover {
    background: #f8f9fa;
}
.badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-success { background: #d1e7dd; color: #0f5132; }
.badge-warning { background: #fff3cd; color: #664d03; }
.badge-secondary { background: #e2e3e5; color: #41464b; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='margin-bottom:0'>Scraping</h1>", unsafe_allow_html=True)
st.markdown("Lancer, arreter et configurer la collecte de donnees.")


def api_get(path: str):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        st.error(f"Erreur API: {e}")
        return None


def api_post(path: str, data: dict = None):
    try:
        r = requests.post(f"{API_BASE}{path}", json=data or {}, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        try:
            return e.response.json() if e.response else {"message": str(e)}
        except:
            return {"message": str(e)}


def api_put(path: str, data: dict):
    try:
        r = requests.put(f"{API_BASE}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        try:
            return e.response.json() if e.response else {"message": str(e)}
        except:
            return {"message": str(e)}


def api_delete(path: str):
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        try:
            return e.response.json() if e.response else {"message": str(e)}
        except:
            return {"message": str(e)}


if "scraping_status" not in st.session_state:
    st.session_state.scraping_status = None
if "refresh_counter" not in st.session_state:
    st.session_state.refresh_counter = 0


sites = api_get("/sites")
sites_retard = api_get("/scrape/sites-a-rescraper")
status = api_get("/scrape/status")


nb_sites = len(sites) if sites else 0
nb_retard = len(sites_retard) if sites_retard else 0

# ─── Bandeau notification ───
if nb_retard > 0:
    st.warning(f"**{nb_retard} source(s) necessitent une mise a jour** (delai de rafraichissement depasse)")
    col_notif1, col_notif2 = st.columns([1, 5])
    with col_notif1:
        if st.button("Mettre a jour", use_container_width=True, type="primary"):
            res = api_post("/scrape/relancer-si-besoin")
            if res:
                st.success(res.get("message", "Sources relances"))
                st.rerun()

# ─── Controles scraping ───
st.markdown("<h3 style='font-size:1.1rem;font-weight:600;margin:1rem 0 0.5rem;'>Controle du scraping</h3>", unsafe_allow_html=True)

col_source, col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1, 1])
with col_source:
    source = st.selectbox("Source", ["api_gouv"], label_visibility="collapsed")

with col_btn1:
    disabled_run = status and status.get("en_cours", False)
    if st.button("Lancer", type="primary", use_container_width=True, disabled=disabled_run):
        res = api_post("/scrape/run", {"source": source, "config": {}})
        if res:
            st.success(res.get("message", "Scraping lance"))
            time.sleep(0.5)
            st.rerun()
with col_btn2:
    if st.button("Arreter", use_container_width=True, disabled=not disabled_run):
        res = api_post("/scrape/stop")
        if res:
            st.warning(res.get("message", "Arret demande"))
            time.sleep(0.5)
            st.rerun()
with col_btn3:
    if st.button("Actualiser", use_container_width=True):
        st.rerun()

# ─── Progression ───
if status:
    en_cours = status.get("en_cours", False)
    p_faits = status.get("faits", 0)
    p_total = status.get("total", 0)
    p_message = status.get("dernier_message", "")
    p_source = status.get("source", "")

    cols_stat = st.columns(4)
    cols_stat[0].markdown(
        f"<div class='card'><div class='card-title'>Statut</div>"
        f"<div class='card-value' style='color:{'#0d6efd' if en_cours else '#198754'}'>{'En cours' if en_cours else 'Inactif'}</div></div>",
        unsafe_allow_html=True)
    cols_stat[1].markdown(
        f"<div class='card'><div class='card-title'>Source</div>"
        f"<div class='card-value'>{p_source or '-'}</div></div>",
        unsafe_allow_html=True)
    progression_label = "codes NAF" if "NAF" in p_message else "sources"
    cols_stat[2].markdown(
        f"<div class='card'><div class='card-title'>Progression</div>"
        f"<div class='card-value'>{p_faits} / {p_total}</div>"
        f"<div class='kpi-label'>{progression_label}</div></div>",
        unsafe_allow_html=True)

    erreurs = status.get("erreurs", 0)
    if erreurs:
        cols_stat[3].markdown(
            f"<div class='card'><div class='card-title'>Erreurs</div>"
            f"<div class='card-value' style='color:#dc3545'>{erreurs}</div></div>",
            unsafe_allow_html=True)
    else:
        cols_stat[3].markdown(
            f"<div class='card'><div class='card-title'>Dernier message</div>"
            f"<div class='card-value' style='font-size:0.9rem'>{p_message or '-'}</div></div>",
            unsafe_allow_html=True)

    if en_cours and p_total > 0:
        progress = min(p_faits / p_total, 1.0)
        label_progress = f"{p_faits} / {p_total} codes NAF ({int(progress*100)}%)" if "NAF" in p_message else f"{p_faits} / {p_total} ({int(progress*100)}%)"
        st.progress(progress, text=label_progress)

    if en_cours:
        time.sleep(1)
        st.rerun()


st.markdown("<hr class='section'>", unsafe_allow_html=True)

# ─── Onglets: Sources / Logs ───
tab_sites, tab_logs = st.tabs(["Sources configurees", "Historique des erreurs"])


# ════════════════════════════════════════════
# TAB 1: Sources
# ════════════════════════════════════════════
with tab_sites:
    col_add1, col_add2 = st.columns([4, 1])
    with col_add1:
        st.markdown(f"**{nb_sites} source(s) configuree(s)**")
    with col_add2:
        if st.button("+ Nouvelle source", use_container_width=True):
            st.session_state.show_add_site = True

    # ── Formulaire ajout ──
    if st.session_state.get("show_add_site"):
        with st.form("form_add_site", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nom = st.text_input("Nom", placeholder="Ex: API Gouv")
                url_base = st.text_input("URL de base", placeholder="https://...")
            with c2:
                type_site = st.selectbox("Type de source", ["api", "site_web", "manuel", "linkedin"])
                delai = st.number_input("Delai de rafraichissement (heures)", min_value=1, value=720)
            col_b1, col_b2 = st.columns([1, 5])
            with col_b1:
                submitted = st.form_submit_button("Ajouter", type="primary", use_container_width=True)
            with col_b2:
                if st.form_submit_button("Annuler", use_container_width=True):
                    st.session_state.show_add_site = False
                    st.rerun()
            if submitted:
                if nom and url_base:
                    res = api_post("/sites", {"nom": nom, "url_base": url_base, "type": type_site, "actif": True, "delai_relance": delai})
                    if res and "message" not in res:
                        st.success(f"Source '{nom}' ajoutee")
                        st.session_state.show_add_site = False
                        st.rerun()
                    else:
                        st.error(res.get("message", "Erreur lors de l'ajout"))
                else:
                    st.warning("Le nom et l'URL sont obligatoires")

    # ── Liste des sources ──
    if sites:
        for s in sites:
            cols = st.columns([3, 2, 1.5, 0.8, 0.8, 0.8])
            dernier = s.get("date_dernier_scraping", "Jamais") or "Jamais"
            if dernier != "Jamais":
                dernier = dernier[:19] if len(dernier) > 19 else dernier

            badge_class = "badge-success" if s.get("actif") else "badge-secondary"
            badge_text = "Actif" if s.get("actif") else "Inactif"

            with cols[0]:
                st.markdown(f"**{s.get('nom', '-')}**")
            with cols[1]:
                st.markdown(f"<span style='color:#6c757d;font-size:0.9rem'>{s.get('type', '-')}</span>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<span style='font-size:0.85rem;color:#6c757d'>{dernier[:10] if dernier != 'Jamais' else 'Jamais'}</span>", unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f"<span class='badge {badge_class}'>{badge_text}</span>", unsafe_allow_html=True)
            with cols[4]:
                if st.button("Modifier", key=f"edit_site_{s['id']}"):
                    st.session_state.editing_site = s
                    st.rerun()
            with cols[5]:
                if st.button("Supprimer", key=f"del_site_{s['id']}"):
                    res = api_delete(f"/sites/{s['id']}")
                    if res:
                        st.success(res.get("message", "Source supprimee"))
                        st.rerun()

    # ── Modal edition source ──
    if st.session_state.get("editing_site"):
        s = st.session_state.editing_site
        with st.form("form_edit_site"):
            st.markdown(f"**Modifier : {s.get('nom', '')}**")
            c1, c2 = st.columns(2)
            with c1:
                e_nom = st.text_input("Nom", value=s.get("nom", ""))
                e_url = st.text_input("URL de base", value=s.get("url_base", ""))
            with c2:
                e_type = st.selectbox("Type de source", ["api", "site_web", "manuel", "linkedin"],
                                      index=["api", "site_web", "manuel", "linkedin"].index(s.get("type", "api")))
                e_delai = st.number_input("Delai (heures)", min_value=1, value=s.get("delai_relance", 720))
            e_actif = st.checkbox("Actif", value=bool(s.get("actif", True)))
            col_b1, col_b2 = st.columns([1, 5])
            with col_b1:
                if st.form_submit_button("Enregistrer", type="primary", use_container_width=True):
                    updates = {"nom": e_nom, "url_base": e_url, "type": e_type, "delai_relance": e_delai, "actif": e_actif}
                    res = api_put(f"/sites/{s['id']}", updates)
                    if res and "message" not in res:
                        st.success("Source modifiee")
                        st.session_state.editing_site = None
                        st.rerun()
                    else:
                        st.error(res.get("message", "Erreur"))
            with col_b2:
                if st.form_submit_button("Annuler", use_container_width=True):
                    st.session_state.editing_site = None
                    st.rerun()
    else:
        st.session_state.editing_site = None


# ════════════════════════════════════════════
# TAB 2: Logs
# ════════════════════════════════════════════
with tab_logs:
    logs = api_get("/scrape/logs?limite=100")
    if logs:
        st.markdown(f"**{len(logs)} entree(s) d'erreur**")
        for log in logs[:50]:
            date_log = log.get("date_erreur", "")[:19] if log.get("date_erreur") else ""
            message = log.get("message_erreur", "") or log.get("message", "") or ""
            code = log.get("code_erreur", "") or ""
            url = log.get("url", "") or ""
            resolu = log.get("resolu", 1)
            color = "#dc3545" if not resolu else "#6c757d"
            st.markdown(
                f"<div style='display:flex;gap:1rem;padding:0.3rem 0;border-bottom:1px solid #f0f0f0;font-size:0.9rem'>"
                f"<span style='color:{color};font-weight:600;min-width:50px'>{'ERR' if not resolu else 'OK'}</span>"
                f"<span style='color:#6c757d;min-width:150px'>{date_log}</span>"
                f"<span>{message[:200]}</span>"
                f"</div>", unsafe_allow_html=True)
    else:
        st.info("Aucune erreur enregistree.")
