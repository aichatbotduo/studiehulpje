import streamlit as st
from groq import Groq
import json
import os

# 1. Pagina instellingen & Stijl
st.set_page_config(page_title="Brutale Studiecoach Pro", page_icon="💀", layout="wide")

# Custom CSS voor een professionele "Dark Mode" look
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1 { color: #ff4b4b !important; font-family: 'Courier New', monospace; }
    .stSidebar { background-color: #161b22; }
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; }
    /* Kleur van de gebruikersnaam in de sidebar */
    .user-text { color: #ffffff; font-weight: bold; font-size: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. Hulpfuncties voor Opslag (JSON bestandjes)
def save_user_data(username, data):
    """Slaat de chats op in een bestand genaamd gebruikersnaam_chats.json"""
    filename = f"{username}_chats.json"
    with open(filename, "w") as f:
        json.dump(data, f)

def load_user_data(username):
    """Laadt de chats van een specifieke gebruiker"""
    filename = f"{username}_chats.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {"Gesprek 1": []} # Standaard als er nog geen data is

# 3. Inlog Systeem
USER_CREDS = {
    "damian": "123",
    "leraar": "10",
    "student1": "pinda"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Studiecoach Login")
    st.write("Log in om je persoonlijke gesprekken te laden.")
    u = st.text_input("Gebruikersnaam").lower()
    p = st.text_input("Wachtwoord", type="password")
    
    if st.button("Inloggen"):
        if u in USER_CREDS and USER_CREDS[u] == p:
            st.session_state.logged_in = True
            st.session_state.user = u
            # LAAD DATA: Zodra je inlogt, halen we jouw specifieke chats op
            st.session_state.all_chats = load_user_data(u)
            st.session_state.current_chat_name = list(st.session_state.all_chats.keys())[0]
            st.rerun()
        else:
            st.error("Onjuiste gegevens. De coach vindt je nu al een mislukking.")
    st.stop()

# --- VANAF HIER: INGELOGD ---

# 4. API Configuratie
# Zorg dat je GROQ_API_KEY in Streamlit Secrets staat!
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 5. Sidebar met Chat-beheer
with st.sidebar:
    st.markdown(f"<p class='user-text'>👤 Gebruiker: {st.session_state.user.capitalize()}</p>", unsafe_allow_html=True)
    st.divider()
    
    st.subheader("📂 Je Gesprekken")
    
    # Knop voor nieuwe chat
    if st.button("➕ Nieuw Gesprek"):
        new_id = len(st.session_state.all_chats) + 1
        new_name = f"Gesprek {new_id}"
        st.session_state.all_chats[new_name] = []
        st.session_state.current_chat_name = new_name
        save_user_data(st.session_state.user, st.session_state.all_chats)
        st.rerun()

    # Selectielijst voor gesprekken
    chat_list = list(st.session_state.all_chats.keys())
    # Zoek de index van de huidige chat om de radiobutton goed te zetten
    current_index = chat_list.index(st.session_state.current_chat_name)
    
    selected_chat = st.radio("Kies een chat:", chat_list, index=current_index)
    
    # Als je een andere chat kiest in de radiobutton
    if selected_chat != st.session_state.current_chat_name:
        st.session_state.current_chat_name = selected_chat
        st.rerun()

    st.divider()
    if st.button("Uitloggen"):
        st.session_state.logged_in = False
        st.rerun()

# 6. Hoofdscherm Chat Interface
st.title(f"💀 {st.session_state.current_chat_name}")
st.info(f"Welkom terug, {st.session_state.user}. De deadline is nog steeds vrijdag 16:00. Werk door.")

# Haal de berichten op van de geselecteerde chat
messages = st.session_state.all_chats[st.session_state.current_chat_name]

# Toon geschiedenis
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. Chat Input & AI Logica
if prompt := st.chat_input("Zeg iets stoms..."):
    # Voeg gebruiker bericht toe
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Genereer AI antwoord
    with st.chat_message("assistant"):
        # De instructies voor de AI
        system_msg = f"Je bent een brutale, sarcastische studiecoach. Je praat met {st.session_state.user}."
        
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "system", "content": system_msg}, *messages],
                model="llama-3.3-70b-versatile",
            )
            ans = completion.choices[0].message.content
            st.markdown(ans)
            
            # Voeg AI antwoord toe aan de lijst
            messages.append({"role": "assistant", "content": ans})
            
            # OPSLAAN: Sla de hele boel direct op in het JSON bestand
            save_user_data(st.session_state.user, st.session_state.all_chats)
            
        except Exception as e:
            st.error(f"Foutje met de AI: {e}")