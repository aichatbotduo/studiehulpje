import streamlit as st
from groq import Groq
import os

# 1. Interface & Grafisch Ontwerp
st.set_page_config(page_title="Brutale Studiecoach", page_icon="💀")
st.title("💀 Je Brutale Studie Maatje")
st.markdown("*Hou op met zeuren en ga aan het werk. Ik onthoud alles wat je zegt, dus pas maar op.*")

# 2. API Configuratie (Directe methode)
# Let op: Deel deze code niet zomaar op internet met je key erin!
MY_GROQ_KEY = "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"
client = Groq(api_key=MY_GROQ_KEY)
#updated crog
# Bestandsnaam voor het permanente geheugen
MEMORY_FILE = "geheugen.txt"

# 3. Context & Persona (Prompt Engineering)
system_prompt_base = """
Je bent een brutale, sarcastische en zeer strenge studiecoach voor studenten. 
Je hebt een hekel aan luiheid en excuses.

GEGEVENS DIE JE MOET WETEN:
- De deadline voor Project Kletsrobot is aanstaande vrijdag om 16:00 op It's Learning.
- De student bouwt een AI-chatbot met Streamlit en Groq.
- Belangrijke onderdelen: Python-code, Video-demo en Documentatie.

INSTRUCTIES VOOR JE GEDRAG:
- Geef korte, gemene en sarcastische antwoorden in het Nederlands.
- Als de student klaagt over werk, brand hem dan af.
- Herinner de student er constant aan dat de deadline nadert en hij waarschijnlijk gaat falen.
- Gebruik de informatie uit het 'GEHEUGEN' hieronder om de student te confronteren.
"""

# Initialiseer de chatgeschiedenis in de browser-sessie (voor het huidige gesprek)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Toon de huidige chatgeschiedenis op het scherm
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Input verwerken & Geheugen-systeem
# 4. Input verwerken & Geheugen-systeem
if prompt := st.chat_input("Stel je (domme) vraag..."):
    # Voeg het bericht van de gebruiker toe aan de sessie
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- GEHEUGEN OPSLAAN (Gebruiker) ---
    with open(MEMORY_FILE, "a") as f:
        f.write(f"Student: {prompt}\n")

    # --- HET GEHEUGEN INLADEN ---
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            vorig_geheugen = f.read()
    else:
        vorig_geheugen = "Nog geen herinneringen."

    # --- ANTWOORD GENEREREN ---
    with st.chat_message("assistant"):
        volledige_instructies = f"{system_prompt_base}\n\nGEHEUGEN VAN VORIGE SESSIES:\n{vorig_geheugen}"
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": volledige_instructies},
                *st.session_state.messages
            ],
            model="llama-3.3-70b-versatile",
        )
        
        answer = chat_completion.choices[0].message.content
        st.markdown(answer)
        
        # --- GEHEUGEN OPSLAAN (Assistent) ---
        # Nu slaan we ook op wat de bot heeft gezegd!
        with open(MEMORY_FILE, "a") as f:
            f.write(f"Coach: {answer}\n")
        
        # Voeg het antwoord toe aan de sessiegeschiedenis
        st.session_state.messages.append({"role": "assistant", "content": answer})