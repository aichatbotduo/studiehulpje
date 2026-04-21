import streamlit as st
from groq import Groq
from supabase import create_client, Client

# 1. Pagina instellingen
st.set_page_config(page_title="Brutale Coach SQL", page_icon="💀")

# 2. Directe verbinding maken met de database
# Deze pakt de gegevens uit je secrets
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
supabase: Client = create_client(URL, KEY)

# Functie om berichten op te slaan
def save_message_to_db(username, chat_name, role, content):
    try:
        supabase.table("chat_history").insert({
            "username": username,
            "chat_name": chat_name,
            "role": role,
            "content": content
        }).execute()
    except Exception as e:
        st.error(f"Fout bij opslaan: {e}")

# Functie om berichten op te halen
def load_chat_from_db(username, chat_name):
    try:
        response = supabase.table("chat_history").select("role, content")\
            .eq("username", username)\
            .eq("chat_name", chat_name)\
            .order("created_at", ascending=True)\
            .execute()
        return response.data
    except:
        return []

# 3. Login Systeem (Hetzelfde gebleven)
USER_CREDS = {"damian": "123", "leraar": "10"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    u = st.text_input("Gebruiker")
    p = st.text_input("Wachtwoord", type="password")
    if st.button("Log in"):
        if u in USER_CREDS and USER_CREDS[u] == p:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.rerun()
    st.stop()

# --- NA LOGIN ---

# 4. Groq Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# We houden de chatnaam simpel voor nu
chat_naam = "Hoofdchat"

st.title(f"💀 Welkom {st.session_state.user}")

# Laad geschiedenis uit de database
history = load_chat_from_db(st.session_state.user, chat_naam)

# Toon berichten
for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Stel je vraag..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Sla op in database
    save_message_to_db(st.session_state.user, chat_naam, "user", prompt)
    
    # AI Antwoord
    with st.chat_message("assistant"):
        messages = [{"role": "system", "content": "Je bent een brutale coach."}]
        for m in history:
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": prompt})
        
        completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
        )
        ans = completion.choices[0].message.content
        st.markdown(ans)
        
        # Sla antwoord op in database
        save_message_to_db(st.session_state.user, chat_naam, "assistant", ans)