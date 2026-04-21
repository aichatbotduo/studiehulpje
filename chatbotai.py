import streamlit as st
from groq import Groq
import sqlite3
import os

# 1. Pagina instellingen & Stijl
st.set_page_config(page_title="Brutale Coach Pro", page_icon="🔐", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1 { color: #ff4b4b !important; font-family: 'Courier New'; }
    .stChatMessage { border-radius: 10px; border: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

# 2. Database Functies (SQLite)
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Tabel voor chats: slaat gebruiker, rol (user/assistant) en het bericht op
    c.execute('''CREATE TABLE IF NOT EXISTS chats 
                 (username TEXT, role TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def save_message(username, role, content):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO chats VALUES (?, ?, ?)", (username, role, content))
    conn.commit()
    conn.close()

def load_chat_history(username):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT role, content FROM chats WHERE username=?", (username,))
    data = c.fetchall()
    conn.close()
    # Maak er weer een lijst van dictionaries van voor de AI
    return [{"role": row[0], "content": row[1]} for row in data]

# Initialiseer de database bij opstarten
init_db()

# 3. Gebruikers & Login
USER_CREDS = {
    "damian": "wachtwoord123",
    "leraar": "cijfer10",
    "student1": "pindakaas"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Log in op de Database")
    user_input = st.text_input("Gebruikersnaam").lower()
    pass_input = st.text_input("Wachtwoord", type="password")
    
    if st.button("Koppelen met Database"):
        if user_input in USER_CREDS and USER_CREDS[user_input] == pass_input:
            st.session_state.logged_in = True
            st.session_state.user = user_input
            # Haal DIRECT de oude chats uit de database voor deze gebruiker
            st.session_state.messages = load_chat_history(user_input)
            st.rerun()
        else:
            st.error("Verkeerd wachtwoord. Ga terug naar de kleuterschool.")
    st.stop()

# 4. API Setup (Streamlit Secrets)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 5. Interface na inloggen
st.sidebar.title(f"👤 {st.session_state.user}")
if st.sidebar.button("Uitloggen"):
    st.session_state.logged_in = False
    st.rerun()

st.title(f"💀 Coach van {st.session_state.user.capitalize()}")
st.info("Al je gesprekken worden veilig bewaard in de SQL-database.")

# Toon de geschiedenis die we uit de DB hebben geladen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Chat Logica
if prompt := st.chat_input("Stel je vraag..."):
    # 1. Opslaan in Session State (voor scherm)
    st.session_state.messages.append({"role": "user", "content": prompt})
    # 2. Opslaan in Database (voor altijd)
    save_message(st.session_state.user, "user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # De AI aanroep
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"Je bent een brutale coach. Je praat met {st.session_state.user}. Ken je feiten over de deadline (vrijdag 16:00)."},
                *st.session_state.messages
            ],
            model="llama-3.3-70b-versatile",
        )
        answer = chat_completion.choices[0].message.content
        st.markdown(answer)
        
        # Sla ook het antwoord op in de DB en session state
        st.session_state.messages.append({"role": "assistant", "content": answer})
        save_message(st.session_state.user, "assistant", answer)