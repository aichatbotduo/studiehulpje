import streamlit as st
from groq import Groq
from st_supabase_connection import SupabaseConnection

# 1. Pagina instellingen
st.set_page_config(page_title="Brutale Coach SQL", page_icon="💀")

# 2. Database Verbinding
# Zorg dat 'url' en 'key' in je Streamlit Secrets staan!
conn = st.connection("supabase", type=SupabaseConnection)

def save_message_to_db(username, chat_name, role, content):
    conn.table("chat_history").insert({
        "username": username,
        "chat_name": chat_name,
        "role": role,
        "content": content
    }).execute()

def load_chat_from_db(username, chat_name):
    query = conn.table("chat_history").select("role, content")\
        .eq("username", username)\
        .eq("chat_name", chat_name)\
        .order("created_at", ascending=True)\
        .execute()
    return query.data

def get_all_chat_names(username):
    query = conn.table("chat_history").select("chat_name")\
        .eq("username", username)\
        .execute()
    names = list(set([item['chat_name'] for item in query.data]))
    return names if names else ["Gesprek 1"]

# 3. Login Systeem
USER_CREDS = {"damian": "123", "leraar": "10"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    u = st.text_input("Gebruiker")
    p = st.text_input("Wachtwoord", type="password")
    if st.button("Log in"):#test
        if u in USER_CREDS and USER_CREDS[u] == p:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.rerun()
    st.stop()

# --- NA LOGIN ---

# 4. Sidebar & Chat Beheer
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.title(f"👤 {st.session_state.user}")
    
    beschikbare_chats = get_all_chat_names(st.session_state.user)
    
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = beschikbare_chats[0]
    
    if st.button("➕ Nieuwe Chat"):
        st.session_state.current_chat = f"Gesprek {len(beschikbare_chats) + 1}"
        st.rerun()
    
    st.session_state.current_chat = st.radio("Chats:", beschikbare_chats, 
                                             index=beschikbare_chats.index(st.session_state.current_chat))

# 5. Chat Interface
st.title(f"💀 {st.session_state.current_chat}")

# Laad berichten uit de SQL database
history = load_chat_from_db(st.session_state.user, st.session_state.current_chat)

for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Zeg wat..."):
    # Gebruiker bericht
    with st.chat_message("user"):
        st.markdown(prompt)
    save_message_to_db(st.session_state.user, st.session_state.current_chat, "user", prompt)
    
    # AI antwoord
    with st.chat_message("assistant"):
        instructies = [{"role": "system", "content": "Je bent een brutale coach."}]
        full_history = instructies + history + [{"role": "user", "content": prompt}]
        
        completion = client.chat.completions.create(
            messages=full_history,
            model="llama-3.3-70b-versatile",
        )
        ans = completion.choices[0].message.content
        st.markdown(ans)
        save_message_to_db(st.session_state.user, st.session_state.current_chat, "assistant", ans)