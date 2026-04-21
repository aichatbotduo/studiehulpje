import streamlit as st
from groq import Groq

# 1. Pagina instellingen & Stijl
st.set_page_config(page_title="Brutale Studiecoach", page_icon="💀", layout="wide")

# Custom CSS voor de "Brutale" look
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1 { color: #ff4b4b !important; font-family: 'Courier New'; }
    .stSidebar { background-color: #161b22; }
    .stChatMessage { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. Inlog Systeem
# Gebruikersnaam en wachtwoord lijst
USER_CREDS = {
    "damian": "123",
    "leraar": "10",
    "student1": "pinda"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Log in bij je Coach")
    u = st.text_input("Gebruikersnaam").lower()
    p = st.text_input("Wachtwoord", type="password")
    if st.button("Start Sessie"):
        if u in USER_CREDS and USER_CREDS[u] == p:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Fout! Ga eerst maar eens leren inloggen.")
    st.stop()

# --- VANAF HIER: INGELOGD ---

# 3. Initialiseer Opslag (Session State)
# We maken een plekje voor alle chats van deze sessie
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {"Gesprek 1": []}

if "current_chat_name" not in st.session_state:
    st.session_state.current_chat_name = "Gesprek 1"

# 4. API Configuratie (Secrets)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 5. Sidebar met Chat-beheer
with st.sidebar:
    st.title(f"👤 {st.session_state.user.capitalize()}")
    
    # Knop voor nieuwe chat
    if st.button("➕ Nieuwe Chat"):
        new_name = f"Gesprek {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_name] = []
        st.session_state.current_chat_name = new_name
        st.rerun()

    # Kies tussen de verschillende chats
    chat_keuze = st.radio("Je actieve chats:", list(st.session_state.all_chats.keys()))
    st.session_state.current_chat_name = chat_keuze

    st.divider()
    if st.button("Uitloggen"):
        st.session_state.logged_in = False
        st.rerun()

# 6. Het Chat Scherm
st.title(f"💀 {st.session_state.current_chat_name}")
st.write(f"*Je bent nu aan het chatten als {st.session_state.user}*")

# Haal de berichten op van de geselecteerde chat
current_history = st.session_state.all_chats[st.session_state.current_chat_name]

# Toon de chat-geschiedenis op het scherm
for msg in current_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 7. Input verwerken
if prompt := st.chat_input("Stel je (domme) vraag..."):
    # Voeg vraag toe aan de huidige chat
    current_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # AI Antwoord genereren
    with st.chat_message("assistant"):
        # System prompt instellen
        instructies = f"Je bent een brutale studiecoach. Je praat met {st.session_state.user}. Deadline: vrijdag 16:00."
        
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": instructies}, *current_history],
            model="llama-3.3-70b-versatile",
        )
        
        answer = completion.choices[0].message.content
        st.markdown(answer)
        
        # Voeg antwoord toe aan de geschiedenis
        current_history.append({"role": "assistant", "content": answer})