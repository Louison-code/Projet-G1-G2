import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

API_URL = "http://localhost:8000/api/dashboard"

st.set_page_config(page_title="Tableau de bord", layout="wide")

st.markdown("""
<style>
.kpi-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 1.2rem 1rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    border: 1px solid #e9ecef;
}
.kpi-card .kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #0d6efd;
    line-height: 1.2;
}
.kpi-card .kpi-value.muted {
    color: #adb5bd;
}
.kpi-card .kpi-label {
    font-size: 0.85rem;
    color: #6c757d;
    margin-top: 0.25rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.chart-container {
    background: white;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    padding: 0.5rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='margin-bottom:0'>Tableau de bord</h1>", unsafe_allow_html=True)
st.markdown("Vue d'ensemble des donnees collectees et indicateurs cles.")


def fetch(endpoint: str) -> dict | list | None:
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        st.error(f"Erreur de connexion a l'API : {e}")
        return None


stats = fetch("/stats")
geography = fetch("/geography")
evolution_data = fetch("/evolution")
dernier = fetch("/dernier-scraping")

if not stats:
    st.warning("Impossible de charger les donnees. Verifiez que le backend FastAPI est lance sur http://localhost:8000")
    st.stop()


col1, col2, col3, col4 = st.columns(4)
total = stats['total_entreprises']

def kpi(value, label, unit="", muted=False):
    cls = "kpi-value muted" if muted else "kpi-value"
    display = value if unit == "%" else str(value)
    if unit == "%" and not muted:
        display = f"{value}"
    return f"""
    <div class="kpi-card">
        <div class="{cls}">{display}{unit}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """

with col1:
    st.markdown(kpi(total, "Entreprises"), unsafe_allow_html=True)
with col2:
    email_taux = round(stats['avec_email'] / total * 100, 1) if total else 0
    st.markdown(kpi(f"{email_taux}", "Avec email", "%"), unsafe_allow_html=True)
with col3:
    tel_taux = round(stats['avec_telephone'] / total * 100, 1) if total else 0
    st.markdown(kpi(f"{tel_taux}", "Avec telephone", "%"), unsafe_allow_html=True)
with col4:
    st.markdown(kpi(stats.get('avec_ca', 0), "Avec CA"), unsafe_allow_html=True)


st.markdown("<hr style='margin:1.5rem 0 1rem 0;opacity:0.2'>", unsafe_allow_html=True)
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("<h3 style='font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;'>Repartition par region</h3>", unsafe_allow_html=True)
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    if geography and geography.get('par_region') and len(geography['par_region']) > 0:
        df_regions = pd.DataFrame(geography['par_region'])
        fig = px.bar(
            df_regions, x='region', y='n',
            color='n', color_continuous_scale='Blues',
            text_auto=True
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(
            xaxis_title="", yaxis_title="Nombre d'entreprises",
            margin=dict(t=10, b=80, l=10, r=10), height=350,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnee regionale disponible.")
    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("<hr style='margin:1.5rem 0 1rem 0;opacity:0.2'>", unsafe_allow_html=True)
col_evo, col_info = st.columns([2, 1])

with col_evo:
    st.markdown("<h3 style='font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;'>Evolution temporelle</h3>", unsafe_allow_html=True)
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    if evolution_data and len(evolution_data) > 0:
        df_evo = pd.DataFrame(evolution_data)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_evo['annee'], y=df_evo['entreprises'],
            mode='lines+markers', name='Entreprises',
            line=dict(color='#0d6efd', width=3),
            marker=dict(size=8)
        ))
        fig.update_layout(
            xaxis_title="Annee", yaxis_title="Nombre d'entreprises",
            margin=dict(t=10, b=10, l=10, r=10), height=300,
            hovermode='x unified', legend=dict(orientation='h', y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnee d'evolution disponible.")
    st.markdown("</div>", unsafe_allow_html=True)

with col_info:
    st.markdown("<h3 style='font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;'>Dernier scraping</h3>", unsafe_allow_html=True)
    if dernier:
        st.markdown(f"""
        <div style="background:#f8f9fa;border-radius:12px;padding:1.2rem;border:1px solid #e9ecef;margin-bottom:1rem;">
            <p style="margin:0 0 0.25rem;color:#6c757d;font-size:0.85rem;">Date</p>
            <p style="margin:0 0 1rem;font-size:1.1rem;font-weight:600;">{dernier.get('date_scraping', 'Inconnue')}</p>
            <p style="margin:0 0 0.25rem;color:#6c757d;font-size:0.85rem;">Statut</p>
            <p style="margin:0 0 1rem;font-size:1.1rem;font-weight:600;">{dernier.get('statut_scraping', 'Inconnu')}</p>
            <p style="margin:0 0 0.25rem;color:#6c757d;font-size:0.85rem;">Nouvelles entreprises</p>
            <p style="margin:0;font-size:1.1rem;font-weight:600;">{dernier.get('n', 0)}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Aucun scraping recent.")

    st.markdown("<h3 style='font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;'>Top 10 departements</h3>", unsafe_allow_html=True)
    st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
    if geography and geography.get('par_departement') and len(geography['par_departement']) > 0:
        df_depts = pd.DataFrame(geography['par_departement']).head(10)
        fig = px.bar(
            df_depts, x='n', y='departement', orientation='h',
            color='n', color_continuous_scale='Blues',
            text_auto=True
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(
            xaxis_title="", yaxis_title="",
            margin=dict(t=10, b=10, l=10, r=10), height=280,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnee departementale disponible.")
    st.markdown("</div>", unsafe_allow_html=True)
