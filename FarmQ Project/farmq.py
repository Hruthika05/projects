import os
import re
import base64
import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator
from serpapi import GoogleSearch
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
from gtts import gTTS


st.set_page_config(page_title="FarmQ Assistant", layout="wide")

if st.button("⬅ Back to Home"):
    st.switch_page("Home.py")

st.write("---")
# ---------------------------
# CONFIG
# ---------------------------
load_dotenv()
st.set_page_config(page_title="🌾 FarmQ Assistant", layout="centered")

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# ---------------------------
# LANGUAGES
# ---------------------------
LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Gujarati": "gu",
    "Bengali": "bn"
}

# ---------------------------
# SIDEBAR
# ---------------------------
st.sidebar.header("🌐 Language Settings")
input_lang = st.sidebar.selectbox("Input Language", LANGUAGES)
output_lang = st.sidebar.selectbox("Output Language", LANGUAGES)

in_lang_code = LANGUAGES[input_lang]
out_lang_code = LANGUAGES[output_lang]

# ---------------------------
# SESSION STATE
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "audio" not in st.session_state:
    st.session_state.audio = None

# ---------------------------
# LOAD MODEL
# ---------------------------
@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = load_model()

# ---------------------------
# DOMAINS
# ---------------------------
AGRI_DOMAINS = {
    "Soil": "soil fertility nutrients",
    "Seed Quality": "seed germination quality",
    "Irrigation": "water irrigation drought",
    "Pests": "pests insects crop damage",
    "Fertilizers": "fertilizer nutrients",
    "Diseases": "plant diseases fungus",
    "Weed Management": "weeds control",
    "Weather": "weather temperature rainfall",
    "General": "general agriculture"
}

domain_names = list(AGRI_DOMAINS.keys())
domain_embeddings = model.encode(list(AGRI_DOMAINS.values()), convert_to_tensor=True)

# ---------------------------
# FUNCTIONS
# ---------------------------
def voice_to_text(lang):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙 Speak now...")
        audio = r.listen(source, timeout=6, phrase_time_limit=8)
    try:
        return r.recognize_google(audio, language=lang)
    except:
        return ""

def translate(text, src, tgt):
    try:
        return GoogleTranslator(source=src, target=tgt).translate(text)
    except:
        return text

def classify_domain(text):
    emb = model.encode(text, convert_to_tensor=True)
    sims = util.cos_sim(emb, domain_embeddings)[0]
    return domain_names[sims.argmax()]

def serp_search(query):
    if not SERPAPI_KEY:
        return []
    res = GoogleSearch({
        "engine": "google",
        "q": query,
        "num": 5,
        "api_key": SERPAPI_KEY
    }).get_dict()
    return res.get("organic_results", [])

def summarize(snippets):
    text = " ".join(snippets)
    sents = re.split(r'(?<=[.!?])\s+', text)
    return " ".join(sents[:3])

def generate_voice(text, lang):
    tts = gTTS(text=text, lang=lang)
    tts.save("reply.mp3")
    return open("reply.mp3", "rb").read()

# ---------------------------
# UI
# ---------------------------
st.title("🌾 FarmQ Assistant")

# CHAT HISTORY
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Useful links
        if "links" in msg:
            for l in msg["links"]:
                st.markdown(f"🔗 [{l['title']}]({l['link']})")

        # 🔊 Voice output BELOW links
        if msg["role"] == "assistant" and "audio" in msg:
            st.markdown("**🔊 Voice Output**")
            st.audio(msg["audio"], format="audio/mp3")


# ---------------------------
# INPUT (BOTTOM – CHATGPT STYLE)
# ---------------------------
col1, col2 = st.columns([10, 1])

with col1:
    prompt = st.chat_input("Ask about crops, pests, irrigation...")

with col2:
    if st.button("🎤"):
        prompt = voice_to_text(in_lang_code)

# ---------------------------
# PROCESS
# ---------------------------
if prompt:
    # User message
    with st.spinner("Processing..."):
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # Translate input
        q_en = translate(prompt, in_lang_code, "en")

        # Domain
        domain = classify_domain(q_en)

        # Search
        results = serp_search(q_en + " agriculture")
        snippets = [r.get("snippet", "") for r in results]

        # Summary
        summary_en = summarize(snippets)
        summary_out = translate(summary_en, "en", out_lang_code)

        # Save AI message
        audio_bytes = generate_voice(summary_out, out_lang_code)

        st.session_state.messages.append({
            "role": "assistant",
            "content": f"📌 **Domain:** {domain}\n\n{summary_out}",
            "links": results,
            "audio": audio_bytes
        })

        # Generate voice (SAFE)
        st.session_state.audio = generate_voice(summary_out, out_lang_code)

        st.rerun()