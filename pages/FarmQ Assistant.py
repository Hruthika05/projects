import os
import re
import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator
from serpapi import GoogleSearch
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv
from gtts import gTTS

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="FarmQ Assistant",
    page_icon="🌾",
    layout="wide"
)

# ---------------------------------------------------
# CUSTOM UI STYLING
# ---------------------------------------------------
st.markdown("""
<style>
body {
    background-color: #f4f7f9;
}
.header {
    background: linear-gradient(90deg, #2E7D32, #66BB6A);
    padding: 20px;
    border-radius: 15px;
    color: white;
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 20px;
}
.chat-card {
    background-color: white;
    padding: 18px;
    border-radius: 15px;
    box-shadow: 0px 4px 10px rgba(0,0,0,0.08);
    margin-bottom: 15px;
}
.user-msg {
    background-color: #E8F5E9;
    padding: 12px;
    border-radius: 12px;
}
.assistant-msg {
    padding: 12px;
    border-radius: 12px;
}
.section-box {
    background-color: #F1F8E9;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# HEADER
# ---------------------------------------------------
st.markdown('<div class="header">🌾 FarmQ – Smart Agricultural Assistant</div>', unsafe_allow_html=True)

# ---------------------------------------------------
# LOAD ENV
# ---------------------------------------------------
load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
st.sidebar.title("⚙ Language Settings")

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

input_lang = st.sidebar.selectbox("Input Language", LANGUAGES)
output_lang = st.sidebar.selectbox("Output Language", LANGUAGES)

in_lang_code = LANGUAGES[input_lang]
out_lang_code = LANGUAGES[output_lang]

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------
# LOAD MODEL
# ---------------------------------------------------
@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = load_model()

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

# ---------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------
def voice_to_text(lang_code):
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening... Speak now")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
        text = recognizer.recognize_google(audio, language=lang_code)
        return text
    except:
        st.warning("Could not recognize voice. Please try again.")
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
        "num": 6,
        "api_key": SERPAPI_KEY
    }).get_dict()
    return res.get("organic_results", [])

def extract_summary_and_suggestions(snippets):
    combined_text = " ".join(snippets)
    sentences = re.split(r'(?<=[.!?])\s+', combined_text)

    summary = " ".join(sentences[:3])

    keywords = ["should", "recommended", "apply", "use",
                "control", "prevent", "manage", "treat",
                "avoid", "irrigate", "spray"]

    suggestions = [
        s.strip() for s in sentences
        if any(k in s.lower() for k in keywords)
    ]

    return summary, suggestions[:5]

def generate_voice(text, lang):
    tts = gTTS(text=text, lang=lang)
    tts.save("reply.mp3")
    return open("reply.mp3", "rb").read()

# ---------------------------------------------------
# DISPLAY CHAT
# ---------------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-card user-msg"><b>You:</b><br>{msg["content"]}</div>',
                    unsafe_allow_html=True)

    else:
        st.markdown(f'<div class="chat-card assistant-msg"><b>FarmQ:</b><br>{msg["content"]}</div>',
                    unsafe_allow_html=True)

        if "links" in msg:
            st.markdown("### 🔗 Related Resources")
            for l in msg["links"]:
                st.markdown(f"- [{l['title']}]({l['link']})")

        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# ---------------------------------------------------
# INPUT AREA (Text + Voice Button)
# ---------------------------------------------------
col1, col2 = st.columns([10, 1])

with col1:
    prompt = st.chat_input("🌱 Ask your agricultural question...")

with col2:
    if st.button("🎤"):
        voice_text = voice_to_text(in_lang_code)
        if voice_text:
            prompt = voice_text
            st.success(f"You said: {voice_text}")

# ---------------------------------------------------
# PROCESS QUERY
# ---------------------------------------------------
if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.spinner("🔍 Fetching agricultural solution..."):

        q_en = translate(prompt, in_lang_code, "en")
        domain = classify_domain(q_en)

        results = serp_search(q_en + " agriculture farmer solution treatment management")
        snippets = [r.get("snippet", "") for r in results if r.get("snippet")]

        if snippets:
            summary_en, suggestions_en = extract_summary_and_suggestions(snippets)
        else:
            summary_en = "No reliable agricultural information found."
            suggestions_en = []

        summary_out = translate(summary_en, "en", out_lang_code)

        if suggestions_en:
            suggestions_out_list = [translate(s, "en", out_lang_code) for s in suggestions_en]
            formatted_suggestions = "".join([f"<li>{s}</li>" for s in suggestions_out_list])
        else:
            formatted_suggestions = "<li>No specific recommendations found.</li>"

        final_response = f"""
📌 <b>Detected Domain:</b> {domain}<br><br>

<div class="section-box">
<b>✅ Solution Summary:</b><br>
{summary_out}
</div>

<div class="section-box">
<b>🌱 Recommended Actions:</b>
<ul>
{formatted_suggestions}
</ul>
</div>
"""

        audio_bytes = generate_voice(summary_out, out_lang_code)

        st.session_state.messages.append({
            "role": "assistant",
            "content": final_response,
            "links": results,
            "audio": audio_bytes
        })

        st.rerun()
