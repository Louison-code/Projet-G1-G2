import streamlit as st
import requests

API_LLM = "http://localhost:8000/api/config/llm"
API_CHAT = "http://localhost:8000/api/chat"

st.set_page_config(page_title="Configuration", layout="wide")
st.markdown("<h1 style='margin-bottom:0'>Configuration</h1>", unsafe_allow_html=True)


def charger_config():
    try:
        r = requests.get(API_LLM, timeout=10)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        pass
    return None


def sauvegarder_config(data: dict):
    try:
        r = requests.put(API_LLM, json=data, timeout=10)
        if r.status_code == 200:
            st.success("Configuration sauvegardée")
            return r.json()
        else:
            st.error(f"Erreur : {r.text}")
    except requests.RequestException as e:
        st.error(f"Erreur de connexion : {e}")
    return None


config = charger_config()

st.markdown("### 🤖 Modèle de langage (Ollama)")

with st.container(border=True):
    modeles_dispo = []
    erreur_ollama = None
    try:
        r = requests.get(f"{API_LLM}/models", timeout=5)
        if r.status_code == 200:
            data = r.json()
            modeles_dispo = data.get("modeles", [])
            erreur_ollama = data.get("erreur")
    except requests.RequestException:
        erreur_ollama = "Impossible de contacter l'API"

    modele_actuel = (config or {}).get("modele", "phi3.5")

    if modeles_dispo:
        index = next((i for i, m in enumerate(modeles_dispo) if m == modele_actuel), 0)
        modele = st.selectbox("Modèle", modeles_dispo, index=index)
    else:
        modele = st.text_input(
            "Modèle",
            value=modele_actuel,
            placeholder="phi3.5, llama3.2, qwen2.5...",
            help="Ollama n'est pas connecté. Saisis le nom du modèle manuellement.",
        )
        if erreur_ollama:
            st.caption(f"⚠️ {erreur_ollama}")

col_save, col_test = st.columns(2)
with col_save:
    if st.button("Sauvegarder", type="primary", use_container_width=True):
        sauvegarder_config({
            "mode": "local",
            "endpoint": "http://localhost:11434",
            "modele": modele,
        })
        st.rerun()

with col_test:
    if st.button("Tester la connexion", use_container_width=True):
        with st.spinner("Test en cours..."):
            try:
                r = requests.get(f"{API_CHAT}/check", timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("status") == "ok":
                        st.success(data["message"])
                    else:
                        st.warning(data.get("message", "Problème de connexion"))
                else:
                    st.error(f"Erreur API : {r.status_code}")
            except requests.ConnectionError:
                st.error("Impossible de contacter l'API. Backend lancé ?")

