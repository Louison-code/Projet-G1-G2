import streamlit as st
import requests
import time

API_URL = "http://localhost:8000/api/chat"
TIMEOUT = 180

st.set_page_config(page_title="Chat RAG", layout="wide")
st.markdown(
    "<h1 style='margin-bottom:0'>Chat RAG</h1>",
    unsafe_allow_html=True,
)
st.markdown("Posez une question en français sur la base de données.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "historique_charge" not in st.session_state:
    try:
        r = requests.get(f"{API_URL}/history?limite=50", timeout=10)
        if r.status_code == 200:
            historique = r.json()
            for h in reversed(historique):
                st.session_state.messages.append(
                    {"role": "user", "content": h["question"], "temps": h.get("temps_execution_ms")}
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": h["reponse"], "sql": h.get("sql_genere")}
                )
    except requests.RequestException:
        pass
    st.session_state.historique_charge = True


def envoyer_question(question: str):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("_Réflexion en cours..._")
        try:
            debut = time.time()
            r = requests.post(
                API_URL,
                json={"question": question},
                timeout=TIMEOUT,
            )
            temps = round((time.time() - debut) * 1000)
            if r.status_code == 200:
                data = r.json()
                reponse = data["reponse"]
                sql = data.get("sql_genere", "")
                if sql:
                    reponse += f"\n\n```sql\n{sql}\n```"
                placeholder.markdown(reponse)
                st.session_state.messages.append(
                    {"role": "assistant", "content": data["reponse"], "sql": sql, "temps": temps}
                )
            else:
                placeholder.error(f"Erreur API : {r.status_code}")
        except requests.Timeout:
            placeholder.error("La requête a pris trop de temps. Essayez une question plus simple.")
        except requests.ConnectionError:
            placeholder.error("Impossible de contacter l'API. Vérifiez que le backend est lancé.")
        except Exception as e:
            placeholder.error(f"Erreur : {e}")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        sql = msg.get("sql")
        if sql:
            with st.expander("Voir la requête SQL", expanded=False):
                st.code(sql, language="sql")


question = st.chat_input("Posez votre question sur les entreprises...")
if question:
    envoyer_question(question)
    st.rerun()


col1, col2 = st.columns([8, 1])
with col2:
    if st.button("Effacer", use_container_width=True):
        try:
            requests.delete(f"{API_URL}/history", timeout=5)
        except requests.RequestException:
            pass
        st.session_state.messages = []
        st.rerun()
