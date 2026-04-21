import streamlit as st
from groq import Groq
import json
import os

# 1. Pagina instellingen & Stijl
st.set_page_config(page_title="Brutale Studiecoach Pro", page_icon="💀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1 { color: #ff4b4b !important; font-family: 'Courier New', monospace; }
    .stSidebar { background-color: #161b22; }
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. Hulpfuncties voor Opslag
def save_user_data(username, data):
    filename = f"{username}_chats.json"
    with open(filename, "w") as f:
        json.dump(data, f)

def load_user_data(username):
    filename = f"{username}_chats.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {"Gesprek 1": []}

# 3. Inlog Systeem
USER_CREDS = {"damian": "123", "leraar": "10", "student1": "pinda"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Studiecoach Login")
    u = st.text_input("Gebruikersnaam").lower()
    p = st.text_input("Wachtwoord", type="password")
    
    if st.button("Inloggen"):
        if u in USER_CREDS and USER_CREDS[u] == p:
            st.session_state.logged_in = True
            st.session_state.user = u
            # Belangrijk: laad de data direct in de session_state
            st.session_state.all_chats = load_user_data(u)
            st.session_state.current_chat_name = list(st.session_state.all_chats.keys())[0]
            st.rerun()
        else:
            st.error("Onjuiste gegevens.")
    st.stop()

# --- INGELOGD ---

# 4. API Setup
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 5. Sidebar met Chat-beheer
with st.sidebar:
    st.title(f"👤 {st.session_state.user.capitalize()}")
    st.divider()
    
    # Nieuwe chat maken
    if st.button("➕ Nieuw Gesprek"):
        new_name = f"Gesprek {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_name] = []
        st.session_state.current_chat_name = new_name
        save_user_data(st.session_state.user, st.session_state.all_chats)
        st.rerun()

    # Chat selecteren
    chat_opties = list(st.session_state.all_chats.keys())
    # Zorg dat de radio button de huidige chat selecteert
    geselecteerd = st.radio("Kies je gesprek:", chat_opties, 
                           index=chat_opties.index(st.session_state.current_chat_name))
    
    # Als de gebruiker een andere chat aanklikt
    if geselecteerd != st.session_state.current_chat_name:
        st.session_state.current_chat_name = geselecteerd
        st.rerun()

    st.divider()
    if st.button("Uitloggen"):
        st.session_state.logged_in = False
        st.rerun()

# 6. Hoofdscherm: Haal de JUISTE berichtenlijst op
st.title(f"💀 {st.session_state.current_chat_name}")

# Hier pakken we de lijst die bij de geselecteerde chatnaam hoort
huidige_berichten = st.session_state.all_chats[st.session_state.current_chat_name]

# Toon alleen de geschiedenis van DIT gesprek
for msg in huidige_berichten:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. Chat Input
if prompt := st.chat_input("Vraag iets..."):
    # Voeg toe aan de specifieke lijst van deze chat
    huidige_berichten.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        system_prompt = f"Je bent een brutale coach. Je praat met {st.session_state.user}."
        
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}] + huidige_berichten,
            model="llama-3.3-70b-versatile",
        )
        
        response = completion.choices[0].message.content
        st.markdown(response)
        
        # Sla antwoord op in de lijst EN in het JSON bestand
        huidige_berichten.append({"role": "assistant", "content": response})
        save_user_data(st.session_state.user, st.session_state.all_chats)