import streamlit as st
from groq import Groq
from supabase import create_client, Client

# 1. Pagina instellingen
st.set_page_config(page_title="Brutale Coach", page_icon="💀")

# 2. Database Verbinding
# Zorg dat deze in Streamlit Secrets staan!
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
supabase: Client = create_client(URL, KEY)

# --- DATABASE FUNCTIES ---
def register_user(username, password):
    try:
        supabase.table("users").insert({"username": username, "password": password}).execute()
        return True
    except:
        return False

def check_login(username, password):
    res = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
    return len(res.data) > 0

def save_message_to_db(username, chat_name, role, content):
    supabase.table("chat_history").insert({
        "username": username, "chat_name": chat_name, "role": role, "content": content
    }).execute()

def load_chat_from_db(username, chat_name):
    res = supabase.table("chat_history").select("role, content")\
        .eq("username", username).eq("chat_name", chat_name)\
        .order("created_at", ascending=True).execute()
    return res.data

def get_all_chat_names(username):
    res = supabase.table("chat_history").select("chat_name").eq("username", username).execute()
    if res.data:
        return sorted(list(set([item['chat_name'] for item in res.data])))
    return ["Gesprek 1"]

# --- LOGIN / REGISTRATIE SCHERM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Toegang tot de Coach")
    tab1, tab2 = st.tabs(["Inloggen", "Registreren"])

    with tab1:
        u_login = st.text_input("Gebruikersnaam", key="l_user")
        p_login = st.text_input("Wachtwoord", type="password", key="l_pass")
        if st.button("Log in"):
            if check_login(u_login, p_login):
                st.session_state.logged_in = True
                st.session_state.user = u_login
                st.rerun()
            else:
                st.error("Onjuiste gegevens")

    with tab2:
        u_reg = st.text_input("Kies Gebruikersnaam", key="r_user")
        p_reg = st.text_input("Kies Wachtwoord", type="password", key="r_pass")
        if st.button("Account aanmaken"):
            if u_reg and p_reg:
                if register_user(u_reg, p_reg):
                    st.success("Account aangemaakt! Je kunt nu inloggen.")
                else:
                    st.error("Naam al bezet of database fout.")
            else:
                st.warning("Vul alles in!")
    st.stop()

# --- CHAT INTERFACE (NA LOGIN) ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.title(f"👤 {st.session_state.user}")
    beschikbare_chats = get_all_chat_names(st.session_state.user)
    
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = beschikbare_chats[0]
    
    if st.button("➕ Nieuwe Chat"):
        st.session_state.current_chat = f"Gesprek {len(beschikbare_chats) + 1}"
        st.rerun()
    
    st.session_state.current_chat = st.radio("Je gesprekken:", beschikbare_chats, 
                                             index=beschikbare_chats.index(st.session_state.current_chat) if st.session_state.current_chat in beschikbare_chats else 0)
    
    if st.button("Log uit"):
        st.session_state.logged_in = False
        st.rerun()

st.title(f"💬 {st.session_state.current_chat}")
history = load_chat_from_db(st.session_state.user, st.session_state.current_chat)

for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Vraag iets aan je coach..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    save_message_to_db(st.session_state.user, st.session_state.current_chat, "user", prompt)
    
    with st.chat_message("assistant"):
        msg_payload = [{"role": "system", "content": "Je bent een brutale coach."}]
        for m in history:
            msg_payload.append({"role": m["role"], "content": m["content"]})
        msg_payload.append({"role": "user", "content": prompt})
        
        compl = client.chat.completions.create(messages=msg_payload, model="llama-3.3-70b-versatile")
        ans = compl.choices[0].message.content
        st.markdown(ans)
        save_message_to_db(st.session_state.user, st.session_state.current_chat, "assistant", ans)