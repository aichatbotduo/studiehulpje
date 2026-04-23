import streamlit as st
import bcrypt
from groq import Groq
from supabase import create_client, Client

# 1. Pagina instellingen
st.set_page_config(page_title="Brutale Coach SQL", page_icon="💀")

# 2. Database Verbinding
URL = st.secrets["connections"]["supabase"]["url"]
KEY = st.secrets["connections"]["supabase"]["key"]
supabase: Client = create_client(URL, KEY)

# --- NIEUWE HASH FUNCTIES ---

def hash_password(password):
    # Verandert "wachtwoord123" in een onleesbare reeks zoals "$2b$12$..."
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    # Controleert of het ingevoerde wachtwoord matcht met de hash
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- AANGEPASTE DATABASE FUNCTIES ---

def register_user(username, password):
    try:
        hashed_pw = hash_password(password)
        supabase.table("users").insert({
            "username": username, 
            "password": hashed_pw
        }).execute()
        return True, "Account aangemaakt!"
    except Exception as e:
        if "duplicate key" in str(e).lower():
            return False, "Deze gebruikersnaam bestaat al."
        return False, f"Fout: {e}"

def check_login(username, password):
    try:
        res = supabase.table("users").select("*").eq("username", username).execute()
        if res.data:
            stored_hashed_pw = res.data[0]["password"]
            # Gebruik bcrypt om te vergelijken
            if verify_password(password, stored_hashed_pw):
                return True
        return False
    except Exception as e:
        st.error(f"Login fout: {e}")
        return False

# --- DE REST VAN JE CODE (Hetzelfde als voorheen) ---

def save_message_to_db(username, chat_name, role, content):
    try:
        supabase.table("chat_history").insert({
            "username": username, "chat_name": chat_name, "role": role, "content": content
        }).execute()
    except: pass

def load_chat_from_db(username, chat_name):
    try:
        res = supabase.table("chat_history").select("role, content")\
            .eq("username", username).eq("chat_name", chat_name)\
            .order("created_at", ascending=True).execute()
        return res.data
    except: return []

def get_all_chat_names(username):
    try:
        res = supabase.table("chat_history").select("chat_name").eq("username", username).execute()
        if res.data:
            return sorted(list(set([item['chat_name'] for item in res.data])))
        return ["Gesprek 1"]
    except: return ["Gesprek 1"]

# --- LOGIN / REGISTRATIE INTERFACE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Veilige Toegang")
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
                st.error("Onjuiste gegevens.")

    with tab2:
        u_reg = st.text_input("Gebruikersnaam", key="r_user")
        p_reg = st.text_input("Wachtwoord", type="password", key="r_pass")
        if st.button("Account aanmaken"):
            if u_reg and p_reg:
                success, msg = register_user(u_reg, p_reg)
                if success: st.success(msg)
                else: st.error(msg)
    st.stop()

# --- CHAT GEDEELTE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.title(f"👤 {st.session_state.user}")
    beschikbare_chats = get_all_chat_names(st.session_state.user)
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = beschikbare_chats[0]
    
    if st.button("➕ Nieuwe Chat"):
        st.session_state.current_chat = f"Gesprek {len(beschikbare_chats) + 1}"
        st.rerun()
    
    st.session_state.current_chat = st.radio("Chats:", beschikbare_chats, index=0)
    
    if st.button("Log uit"):
        st.session_state.logged_in = False
        st.rerun()

st.title(f"💬 {st.session_state.current_chat}")
history = load_chat_from_db(st.session_state.user, st.session_state.current_chat)

for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Vraag iets..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    save_message_to_db(st.session_state.user, st.session_state.current_chat, "user", prompt)
    
    with st.chat_message("assistant"):
        payload = [{"role": "system", "content": "Je bent een brutale coach."}]
        for m in history: payload.append({"role": m["role"], "content": m["content"]})
        payload.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(messages=payload, model="llama-3.3-70b-versatile")
        ans = response.choices[0].message.content
        st.markdown(ans)
        save_message_to_db(st.session_state.user, st.session_state.current_chat, "assistant", ans)