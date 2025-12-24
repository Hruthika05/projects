import os
import base64
import re
from typing import List, Tuple

import streamlit as st
from audiorecorder import audiorecorder
import speech_recognition as sr
from pydub import AudioSegment
from serpapi import GoogleSearch
import boto3
from deep_translator import GoogleTranslator
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
import pandas as pd
from dotenv import load_dotenv

# ---------------------------
# Load environment
# ---------------------------
load_dotenv()  # loads .env from project root

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
POLLY_VOICE = os.getenv("POLLY_VOICE", "Aditi")

# Validate keys early
if not SERPAPI_KEY:
    st.warning("SERPAPI_KEY not found in .env — SerpApi search will be disabled until key is provided.")
if not (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY):
    st.warning("AWS credentials not found in .env — Polly voice will be disabled until keys are provided.")

# Configure boto3 if keys available (boto3 will also pick up envs automatically)
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    boto3.setup_default_session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )
polly_client = boto3.client("polly", region_name=AWS_REGION) if (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) else None

# ---------------------------
# UI config
# ---------------------------
st.set_page_config(page_title="🌾 FarmQ Domain Classifier + SerpApi", layout="centered")
st.title("🌾 FarmQ Domain Classifier — Browser Mic + SerpApi + Polly")
st.write("Type or record your agricultural question. The app classifies domain, fetches SerpApi results, summarizes, and speaks the summary (Aditi).")

# ---------------------------
# Train or load classifier
# ---------------------------
@st.cache_resource
def train_model() -> Tuple[MultinomialNB, CountVectorizer]:
    try:
        df = pd.read_csv("Agri_dataset.csv")
        X = df["Questions"].astype(str)
        y = df["Label"].astype(str)
    except Exception:
        # fallback tiny dataset
        data = {
            "Questions": [
                "My soil is too dry",
                "Seeds not germinating properly",
                "Water is not reaching crops",
                "Pests are attacking the plants",
                "Fertilizer burned the leaves",
                "Crops have yellow spots",
                "Weeds growing fast",
                "Cold weather harming crops"
            ],
            "Label": [
                "Soil", "Seed Quality", "Irrigation", "Pests",
                "Fertilizers", "Diseases", "Weed Management", "Ambient Conditions"
            ]
        }
        df = pd.DataFrame(data)
        X = df["Questions"]
        y = df["Label"]

    vectorizer = CountVectorizer()
    X_vec = vectorizer.fit_transform(X)
    model = MultinomialNB()
    model.fit(X_vec, y)
    return model, vectorizer

model, vectorizer = train_model()

# ---------------------------
# Helpers
# ---------------------------
def translate_text(text: str, src="auto", dest="en") -> str:
    try:
        return GoogleTranslator(source=src, target=dest).translate(text)
    except Exception:
        return text

def classify_domain(text: str) -> str:
    try:
        v = vectorizer.transform([text])
        return model.predict(v)[0]
    except Exception:
        return "General"

def serpapi_search(query: str, num=5):
    if not SERPAPI_KEY:
        return []
    params = {
        "engine": "google",
        "q": query,
        "num": num,
        "api_key": SERPAPI_KEY,
    }
    try:
        search = GoogleSearch(params)
        res = search.get_dict()
        organic = res.get("organic_results", []) or res.get("organic", [])
        results = []
        for r in organic:
            link = r.get("link") or r.get("url")
            title = r.get("title") or ""
            snippet = r.get("snippet") or r.get("snippet_text") or ""
            if link:
                results.append({"title": title, "link": link, "snippet": snippet})
            if len(results) >= num:
                break
        return results
    except Exception as e:
        st.error(f"SerpApi error: {e}")
        return []

def build_summary_from_snippets(snippets: List[str]) -> str:
    # Simple snippet-based summarization: join top snippets, keep short.
    joined = " ".join([s for s in snippets if s])
    # If too short or empty, fallback message
    if not joined.strip():
        return "I couldn't fetch a concise summary. Please check the links below for details."
    # Return first ~3 short sentences
    parts = re.split(r'(?<=[.!?])\s+', joined)
    return " ".join(parts[:3])

def synthesize_polly_b64(text: str) -> str:
    if not polly_client:
        return None
    try:
        resp = polly_client.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=POLLY_VOICE)
        audio_bytes = resp["AudioStream"].read()
        return base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as e:
        st.error(f"Polly error: {e}")
        return None

def play_hidden_audio_b64(b64_audio: str):
    # B1: hidden <audio autoplay hidden>
    if not b64_audio:
        return
    audio_html = f"""
    <audio autoplay hidden>
      <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
    </audio>
    <script>
      (async function(){{
         try {{
           const a = document.querySelector('audio[autoplay]');
           if (a) {{
             await a.play();
           }}
         }} catch(e){{console.log('Autoplay failed', e);}}
      }})();
    </script>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

# ---------------------------
# Input area
# ---------------------------
st.sidebar.header("Input")
mode = st.sidebar.radio("Input mode", ["Type Query", "Record in browser"])

if mode == "Type Query":
    user_q = st.text_area("Enter your agricultural question", height=140)
else:
    st.write("Use the browser recorder below. Click **Start** then **Stop** when done.")
    audio = audiorecorder("Start recording", "Stop and save")
    user_q = ""
    if audio is not None and len(audio) > 0:
        # audiorecorder returns a pydub AudioSegment-like object with export()
        try:
            wav_bytes = audio.export().read()
            # Use speech_recognition to transcribe from bytes
            recognizer = sr.Recognizer()
            audio_data = sr.AudioData(wav_bytes, sample_rate=44100, sample_width=2)
            try:
                user_q = recognizer.recognize_google(audio_data)
                st.success(f"Recognized: {user_q}")
            except Exception as e:
                st.error(f"Speech recognition failed: {e}")
                user_q = ""
        except Exception as e:
            st.error(f"Audio processing failed: {e}")
            user_q = ""

# ---------------------------
# Action
# ---------------------------
if st.button("🔍 Classify & Get Solutions"):
    if not user_q or not user_q.strip():
        st.warning("Please type or record a query first.")
    else:
        with st.spinner("Processing..."):
            # translate to English for classification & search
            translated = translate_text(user_q)
            if translated.lower() != user_q.lower():
                st.info(f"Translated: {translated}")

            domain = classify_domain(translated)
            st.success(f"Predicted domain: **{domain}**")

            # Build SerpApi query (domain + boosters)
            boosters = "soil fertility OR pest management OR irrigation OR fertilizer OR disease management"
            serp_query = f"{translated} {domain} {boosters}"

            search_results = serpapi_search(serp_query, num=5)
            if not search_results:
                st.warning("No SerpApi results found (check SERPAPI_KEY). Trying a broader query...")
                serp_query2 = f"{translated} agriculture {domain}"
                search_results = serpapi_search(serp_query2, num=5)

            # Summarize using top snippets
            snippets = [r.get("snippet", "") for r in search_results]
            summary = build_summary_from_snippets(snippets)
            st.subheader("🔎 Summary")
            st.write(summary)

            # show top links
            st.subheader("🔗 Top links")
            if search_results:
                for r in search_results:
                    st.markdown(f"- [{r['title']}]({r['link']})")
                    if r.get("snippet"):
                        st.caption(r["snippet"])
            else:
                st.info("No links available from SerpApi results.")

            # Synthesize with Polly and autoplay hidden audio (B1)
            if polly_client:
                speak_text = f"{summary} For more details I have provided links on the screen."
                audio_b64 = synthesize_polly_b64(speak_text)
                if audio_b64:
                    play_hidden_audio_b64(audio_b64)
            else:
                st.info("Polly not configured — no voice output.")

# Footer
st.markdown("---")
st.caption("FarmQ • SerpApi + Polly • Keep your .env secret")