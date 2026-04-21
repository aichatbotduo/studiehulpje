import streamlit as st
from groq import Groq
import os

# 1. Pagina instellingen & Stijl
st.set_page_config(page_title="Brutale Studiecoach", page_icon="💀", layout="wide")

# CSS voor een vette look
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    h1 { color: #ff4b4b !important; }
    .stSidebar { background-color: #161b22; }
    </style>
""", unsafe_allow_html=True)

# 2. API & Geheugen Setup
MY_GROQ_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=MY_GROQ_KEY)

# Initialiseer de chats-opslag als die nog niet bestaat
if "all_chats" not in st.session_state:
    st.session_state.all_chats = {"Chat 1": []}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = "Chat 1"

# 3. Sidebar voor Chat Beheer
with st.sidebar:
    st.title("📂 Je Gesprekken")
    
    # Knop voor een nieuwe chat
    if st.button("➕ Nieuwe Chat"):
        new_chat_name = f"Chat {len(st.session_state.all_chats) + 1}"
        st.session_state.all_chats[new_chat_name] = []
        st.session_state.current_chat = new_chat_name
        st.rerun()

    # Selectiebox om te wisselen tussen chats
    chat_selection = st.radio("Kies een gesprek:", list(st.session_state.all_chats.keys()), index=list(st.session_state.all_chats.keys()).index(st.session_state.current_chat))
    st.session_state.current_chat = chat_selection

    st.divider()
    st.error("🚨 Deadline: Vrijdag 16:00!")

# 4. Chat Interface
st.title(f"💀 {st.session_state.current_chat}")

# Haal de berichten van de geselecteerde chat op
current_messages = st.session_state.all_chats[st.session_state.current_chat]

# Toon de geschiedenis van de geselecteerde chat
for message in current_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Input verwerken
if prompt := st.chat_input("Stel je vraag aan de coach..."):
    # Voeg toe aan de geselecteerde chat
    current_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Antwoord genereren
    with st.chat_message("assistant"):
        # We sturen de specifieke geschiedenis van DEZE chat mee
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Je bent een brutale studiecoach. Wees kort en gemeen."},
                *current_messages
            ],
            model="llama-3.3-70b-versatile",
        )
        
        answer = chat_completion.choices[0].message.content
        st.markdown(answer)
        current_messages.append({"role": "assistant", "content": answer})