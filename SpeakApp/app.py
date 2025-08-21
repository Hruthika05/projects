from flask import Flask, render_template, request, jsonify
import requests
from geopy.geocoders import Nominatim
from googletrans import Translator
import boto3

app = Flask(__name__)

OPENWEATHER_API_KEY = "your-api-key"  # Replace with your key

# AWS Polly setup
try:
    polly_client = boto3.client('polly', region_name='us-east-1')
except Exception:
    polly_client = None

translator = Translator()
geolocator = Nominatim(user_agent="travel_planner_app", timeout=10)

VOICE_MAP = {
    "en": "Joanna", "zh-cn": "Zhiyu", "es": "Conchita", "fr": "Celine",
    "hi": "Aditi", "ja": "Mizuki", "de": "Vicki", "it": "Carla", "ru": "Tatyana"
}

def translate_text(text, lang_code):
    try:
        if lang_code != "en":
            return translator.translate(text, dest=lang_code).text
        return text
    except:
        return text

def geocode_location(place):
    try:
        loc = geolocator.geocode(place)
        if loc:
            return {"lat": loc.latitude, "lon": loc.longitude, "name": loc.address}
    except:
        pass
    return None

def osrm_route(lat1, lon1, lat2, lon2):
    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        r = requests.get(url, timeout=10).json()
        if r.get("routes"):
            dist_km = round(r["routes"][0]["distance"] / 1000, 1)
            dur_min = round(r["routes"][0]["duration"] / 60, 1)
            return dist_km, dur_min
    except:
        pass
    return None, None

def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=10).json()
        if r.get("cod") != 200:
            return None
        return {
            "temp": r["main"]["temp"],
            "conditions": r["weather"][0]["description"],
            "humidity": r["main"]["humidity"],
            "wind": r["wind"]["speed"]
        }
    except:
        return None

def estimate_traffic(weather_desc, distance_km, duration_min):
    if not weather_desc:
        return "Moderate"
    weather_desc = weather_desc.lower()
    if "rain" in weather_desc or "storm" in weather_desc or "snow" in weather_desc:
        return "High"
    if distance_km and duration_min and distance_km < 50 and duration_min > 120:
        return "High"
    return "Moderate"

def suggest_transport(distance_km):
    if distance_km <= 5:
        return "🚶‍♂️ Walk"
    elif distance_km <= 15:
        return "🚴‍♂️ Bike"
    elif distance_km <= 300:
        return "🚗 Car"
    else:
        return "✈️ Plane"

def generate_voice(text, lang_code):
    if not polly_client:
        return None
    try:
        voice_id = VOICE_MAP.get(lang_code, "Joanna")
        resp = polly_client.synthesize_speech(Text=text, OutputFormat="mp3", VoiceId=voice_id)
        out_path = "static/output.mp3"
        with open(out_path, "wb") as f:
            f.write(resp["AudioStream"].read())
        return out_path
    except:
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/plan", methods=["POST"])
def plan_trip():
    data = request.get_json()
    start = data.get("start")
    dest = data.get("dest")
    lang = data.get("lang", "en")
    mode = data.get("mode", "manual")

    start_geo = geocode_location(start)
    dest_geo = geocode_location(dest)
    if not start_geo or not dest_geo:
        return jsonify({"error": "Location not found"}), 400

    distance_km, duration_min = osrm_route(start_geo["lat"], start_geo["lon"], dest_geo["lat"], dest_geo["lon"])
    weather = get_weather(dest)
    traffic = estimate_traffic(weather['conditions'] if weather else None, distance_km, duration_min)
    recommendation = suggest_transport(distance_km if distance_km else 0)

    # Full translated text
    output_text = (
        f"From {start} to {dest}: Distance {distance_km} km, Duration {duration_min} min. "
        f"Weather: {weather['conditions'] if weather else 'N/A'}, {weather['temp'] if weather else ''}°C. "
        f"Traffic: {traffic}. Recommended Mode: {recommendation}."
    )
    translated_text = translate_text(output_text, lang)
    translated_recommendation = translate_text(f"Recommended Mode: {recommendation}", lang)
    translated_traffic = translate_text(traffic, lang)

    audio_path = None
    if mode == "voice":
        audio_path = generate_voice(translated_text, lang)

    return jsonify({
        "start": translate_text(start, lang),
        "dest": translate_text(dest, lang),
        "distance": distance_km,
        "duration": duration_min,
        "weather": {
            "temp": f"{weather['temp']}°C" if weather else "N/A",
            "conditions": translate_text(weather['conditions'], lang) if weather else "N/A",
            "humidity": f"{weather['humidity']}%" if weather else "N/A",
            "wind": f"{weather['wind']} m/s" if weather else "N/A"
        } if weather else None,
        "traffic": translated_traffic,
        "recommendation": translated_recommendation,
        "output_text": translated_text,
        "audio_path": audio_path
    })

if __name__ == "__main__":
    app.run(debug=True)

