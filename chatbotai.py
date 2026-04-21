import streamlit as st
from groq import Groq

# 1. Configuratie & Stijl
st.set_page_config(page_title="Brutale Coach Login", page_icon="🔐")

# 2. Gebruikers Database (Simpel)
# In een echte app gebruik je een database, maar voor je project werkt dit prima:
USER_CREDS = {
    "damian": "wachtwoord123",
    "leraar": "cijfer10",
    "student1": "pindakaas"
}

# 3. Inlog Logica
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

if not st.session_state.logged_in:
    st.title("🔐 Log in op je Studiecoach")
    username = st.text_input("Gebruikersnaam").lower()
    password = st.text_input("Wachtwoord", type="password")
    
    if st.button("Log in"):
        if username in USER_CREDS and USER_CREDS[username] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success(f"Welkom {username}!")
            st.rerun()
        else:
            st.error("Onjuiste inloggegevens. De coach vindt je nu al dom.")
    st.stop() # Stop de rest van de code als je niet bent ingelogd

# --- VANAF HIER IS DE CODE ALLEEN ZICHTBAAR ALS JE BENT INGELOGD ---

# 4. API Setup
MY_GROQ_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=MY_GROQ_KEY)

# Initialiseer opslag voor ALLE gebruikers als die nog niet bestaat
if "user_chats" not in st.session_state:
    st.session_state.user_chats = {}

# Zorg dat de huidige gebruiker een plekje heeft voor zijn chats
if st.session_state.user not in st.session_state.user_chats:
    st.session_state.user_chats[st.session_state.user] = []

st.sidebar.title(f"👤 Gebruiker: {st.session_state.user}")
if st.sidebar.button("Uitloggen"):
    st.session_state.logged_in = False
    st.rerun()

st.title(f"💀 Coach voor {st.session_state.user}")

# 5. Chat Interface (Gekoppeld aan de gebruiker)
user_history = st.session_state.user_chats[st.session_state.user]

for message in user_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Stel je vraag..."):
    user_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": f"Je bent een brutale coach. Je praat nu met {st.session_state.user}."},
                *user_history
            ],
            model="llama-3.3-70b-versatile",
        )
        answer = chat_completion.choices[0].message.content
        st.markdown(answer)
        user_history.append({"role": "assistant", "content": answer})