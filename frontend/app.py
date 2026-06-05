"""Point d'entrée de l'interface Streamlit."""
import streamlit as st

st.set_page_config(page_title="G1-G2 - Réindustrialisation", layout="wide")
st.title("🏭 Projet G1-G2 - Réindustrialisation")

st.markdown("""
Bienvenue sur l'application de collecte, pilotage et visualisation.

Utilisez les onglets ci-dessus pour naviguer :
- **📊 Dashboard** — KPIs et graphiques
- **🕷️ Scraping** — Lancer et configurer le scraping
- **💬 Chat** — Interroger la base en langage naturel
- **⚙️ Configuration** — Paramètres LLM, export, etc.
""")
