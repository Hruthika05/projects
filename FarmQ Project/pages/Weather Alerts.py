import streamlit as st
import requests
import base64
import matplotlib.pyplot as plt
from gtts import gTTS
from datetime import datetime
import calendar

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="🌦 Weather Alerts", layout="wide")

# ---------------------------
# NAVIGATION
# ---------------------------
if st.button("⬅ Back to Home"):
    st.switch_page("Home.py")

st.write("---")

# ---------------------------
# CONFIG
# ---------------------------
WEATHER_API_KEY = "bf77ad70479adb5c96802491b3c7e445"
BASE_WEATHER = "https://api.openweathermap.org/data/2.5/weather"
BASE_FORECAST = "https://api.openweathermap.org/data/2.5/forecast"

# ---------------------------
# SIDEBAR UI (MATCHING CROP PRICE PAGE)
# ---------------------------
st.sidebar.markdown("""
<div style='padding:20px; border-radius:15px;
background: linear-gradient(135deg,#ffd6ff,#caffbf);
text-align:center'>
<h2 style='color:#6a4c93;'>🌦 Weather Alerts</h2>
<p style='font-size:14px; color:#3a0ca3;'>
Crop-wise weather & voice advisory
</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# MAIN HEADER CARD
# ---------------------------
st.markdown("""
<div style='text-align:center; padding:30px; border-radius:15px;
background: linear-gradient(135deg,#caffbf,#ffd6ff);'>
<h2 style='color:#9b5de5;'>🌾 Smart Weather Alerts</h2>
<p style='font-size:16px; color:#000000'>
Live Weather • Crop Alerts • Seasonal Advice • Voice Support
</p>
</div>
""", unsafe_allow_html=True)

st.write("")

# ---------------------------
# SESSION MEMORY
# ---------------------------
if "farmer_weather" not in st.session_state:
    st.session_state.farmer_weather = {"city": "", "crops": ""}

profile = st.session_state.farmer_weather

# ---------------------------
# INPUT SECTION (CLEAN)
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    city = st.text_input("📍 Enter Village / City", profile["city"] or "Guntur")

with col2:
    crop_text = st.text_input(
        "🌾 Enter Crop Name(s)",
        placeholder="Rice, Cotton, Tomato",
        value=profile["crops"]
    )

enable_voice = st.checkbox("🔊 Enable Voice Alerts", True)

profile["city"] = city
profile["crops"] = crop_text
crops = [c.strip().title() for c in crop_text.split(",") if c.strip()]

# ---------------------------
# WEATHER FUNCTIONS
# ---------------------------
def fetch_weather(city):
    return requests.get(BASE_WEATHER, params={
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }).json()

def fetch_forecast(city):
    return requests.get(BASE_FORECAST, params={
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }).json()

def speak(text):
    tts = gTTS(text=text, lang="en")
    tts.save("alert.mp3")
    with open("alert.mp3", "rb") as f:
        return base64.b64encode(f.read()).decode()

def crop_alert(crop, temp, hum, wind, rain):
    tips = []
    if temp > 35:
        tips.append("High temperature – irrigate early morning.")
    if temp < 15:
        tips.append("Low temperature – growth may slow.")
    if hum > 80:
        tips.append("High humidity – fungal disease risk.")
    if wind > 10:
        tips.append("Strong wind – avoid spraying.")
    if rain:
        tips.append("Rain expected – reduce irrigation.")
    return " ".join(tips) if tips else "Weather conditions are favorable."

def seasonal_reminder(crop):
    month = calendar.month_name[datetime.now().month]
    return f"{month}: Monitor {crop} growth, nutrition, and pests."

# ---------------------------
# ACTION BUTTON
# ---------------------------
if st.button("🌦 Get Weather Alerts"):
    if not crops:
        st.warning("⚠ Please enter at least one crop name.")
    else:
        weather = fetch_weather(city)

        if weather.get("cod") != 200:
            st.error("❌ Unable to fetch weather data.")
        else:
            temp = weather["main"]["temp"]
            hum = weather["main"]["humidity"]
            wind = weather["wind"]["speed"]
            condition = weather["weather"][0]["description"].title()
            rain = "rain" in condition.lower()

            # ---------------------------
            # WEATHER METRIC CARDS
            # ---------------------------
            st.markdown("### 🌦 Current Weather")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🌡 Temperature", f"{temp} °C")
            m2.metric("💧 Humidity", f"{hum}%")
            m3.metric("🌬 Wind Speed", f"{wind} m/s")
            m4.metric("🌥 Condition", condition)

            # ---------------------------
            # CROP ALERTS
            # ---------------------------
            st.markdown("### 🚨 Crop-Specific Alerts")
            voice_text = f"Weather update for {city}. {condition}. "

            for crop in crops:
                alert = crop_alert(crop, temp, hum, wind, rain)
                st.warning(f"🌾 **{crop}** → {alert}")
                voice_text += f"For {crop}, {alert}. "

            # ---------------------------
            # SEASONAL ADVICE
            # ---------------------------
            st.markdown("### 📅 Seasonal Reminders")
            for crop in crops:
                st.success(f"🌱 **{crop}** → {seasonal_reminder(crop)}")

            # ---------------------------
            # VOICE
            # ---------------------------
            if enable_voice:
                st.markdown("### 🔊 Voice Advisory")
                audio = speak(voice_text)
                st.audio(base64.b64decode(audio))

            # ---------------------------
            # FORECAST GRAPH
            # ---------------------------
            forecast = fetch_forecast(city)
            temps, days = [], []

            for i in range(0, 40, 8):
                temps.append(forecast["list"][i]["main"]["temp"])
                days.append(datetime.fromtimestamp(
                    forecast["list"][i]["dt"]
                ).strftime("%a"))

            st.markdown("### 📊 7-Day Temperature Forecast")
            plt.figure(figsize=(8,4))
            plt.plot(days, temps, marker="o")
            plt.xlabel("Day")
            plt.ylabel("Temperature (°C)")
            plt.grid(True)
            st.pyplot(plt)

# ---------------------------
# FOOTER
# ---------------------------
st.markdown("---")
st.caption("🌾 FarmQ AI • Smart Weather • Crop Intelligence")