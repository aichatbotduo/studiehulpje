import streamlit as st
from groq import Groq
from supabase import create_client, Client

# 1. Pagina instellingen
st.set_page_config(page_title="Brutale Coach SQL", page_icon="💀", layout="centered")

# 2. Database Verbinding (Secrets uit Streamlit Cloud)
try:
    URL = st.secrets["connections"]["supabase"]["url"]
    KEY = st.secrets["connections"]["supabase"]["key"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Systeemfout: Kan geen verbinding maken met de database. Controleer je Secrets!")
    st.stop()

# --- DATABASE FUNCTIES ---

def register_user(username, password):
    try:
        # Check of velden leeg zijn
        if not username or not password:
            return False, "Vul een gebruikersnaam en wachtwoord in."
        
        # Voeg gebruiker toe
        res = supabase.table("users").insert({
            "username": username, 
            "password": password
        }).execute()
        return True, "Account aangemaakt! Je kunt nu inloggen."
    except Exception as e:
        # Als de naam al bestaat geeft Supabase een error
        if "duplicate key" in str(e).lower():
            return False, "Deze gebruikersnaam bestaat al."
        return False, f"Database fout: {str(e)}"

def check_login(username, password):
    try:
        res = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        return len(res.data) > 0
    except Exception as e:
        st.error(f"Inlogfout: {e}")
        return False

def save_message_to_db(username, chat_name, role, content):
    try:
        supabase.table("chat_history").insert({
            "username": username, 
            "chat_name": chat_name, 
            "role": role, 
            "content": content
        }).execute()
    except Exception as e:
        st.sidebar.error(f"Bericht niet opgeslagen: {e}")

def load_chat_from_db(username, chat_name):
    try:
        res = supabase.table("chat_history").select("role, content")\
            .eq("username", username).eq("chat_name", chat_name)\
            .order("created_at", ascending=True).execute()
        return res.data
    except:
        return []

def get_all_chat_names(username):
    try:
        res = supabase.table("chat_history").select("chat_name").eq("username", username).execute()
        if res.data:
            # Haal unieke namen op en sorteer
            return sorted(list(set([item['chat_name'] for item in res.data])))
        return ["Mijn eerste gesprek"]
    except:
        return ["Mijn eerste gesprek"]

# --- LOGIN / REGISTRATIE SCHERM ---

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🥊 De Brutale Coach")
    tab1, tab2 = st.tabs(["🔐 Inloggen", "📝 Registreren"])

    with tab1:
        u_login = st.text_input("Gebruikersnaam", key="l_user")
        p_login = st.text_input("Wachtwoord", type="password", key="l_pass")
        if st.button("Log in"):
            if check_login(u_login, p_login):
                st.session_state.logged_in = True
                st.session_state.user = u_login
                st.rerun()
            else:
                st.error("Onjuiste login gegevens.")

    with tab2:
        u_reg = st.text_input("Kies een naam", key="r_user")
        p_reg = st.text_input("Kies een wachtwoord", type="password", key="r_pass")
        if st.button("Account aanmaken"):
            success, message = register_user(u_reg, p_reg)
            if success:
                st.success(message)
            else:
                st.error(message)
    st.stop()

# --- CHAT INTERFACE (NA LOGIN) ---

# Groq Client instellen
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("Groq API Key ontbreekt in Secrets!")
    st.stop()

# Zijbalk met chatgeschiedenis
with st.sidebar:
    st.title(f"Welkom, {st.session_state.user}")
    
    beschikbare_chats = get_all_chat_names(st.session_state.user)
    
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = beschikbare_chats[0]
    
    if st.button("➕ Nieuwe Chat"):
        nieuwe_index = len(beschikbare_chats) + 1
        st.session_state.current_chat = f"Gesprek {nieuwe_index}"
        st.rerun()
    
    st.session_state.current_chat = st.radio(
        "Kies een gesprek:", 
        beschikbare_chats, 
        index=beschikbare_chats.index(st.session_state.current_chat) if st.session_state.current_chat in beschikbare_chats else 0
    )
    
    st.divider()
    if st.button("Uitloggen"):
        st.session_state.logged_in = False
        st.rerun()

# Hoofdscherm Chat
st.title(f"💬 {st.session_state.current_chat}")

# Laad de geschiedenis uit de database
history = load_chat_from_db(st.session_state.user, st.session_state.current_chat)

# Toon de berichten
for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input voor nieuwe berichten
if prompt := st.chat_input("Wat wil je weten?"):
    # Toon user bericht
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Sla op in DB
    save_message_to_db(st.session_state.user, st.session_state.current_chat, "user", prompt)
    
    # AI Antwoord genereren
    with st.chat_message("assistant"):
        # Bouw berichtenset voor de AI
        payload = [{"role": "system", "content": "Je bent een brutale coach die korte, eerlijke antwoorden geeft."}]
        for m in history:
            payload.append({"role": m["role"], "content": m["content"]})
        payload.append({"role": "user", "content": prompt})
        
        try:
            response = client.chat.completions.create(
                messages=payload,
                model="llama-3.3-70b-versatile",
            )
            ans = response.choices[0].message.content
            st.markdown(ans)
            
            # Sla AI antwoord op in DB
            save_message_to_db(st.session_state.user, st.session_state.current_chat, "assistant", ans)
        except Exception as e:
            st.error(f"AI Fout: {e}")