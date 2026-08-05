import streamlit as st
import random

st.set_page_config(page_title="📈 Crop Market Prices", layout="wide")

if st.button("⬅ Back to Home"):
    st.switch_page("Home.py")

st.write("---")


st.set_page_config(page_title="📈 Crop Market Price", layout="wide")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("""
<div style='padding:20px; border-radius:15px; background: linear-gradient(135deg,#ffd6ff,#caffbf); text-align:center'>
<h2 style='color:#6a4c93;'>📈 Crop Prices</h2>
<p style='font-size:14px; color:#3a0ca3;'>Approximate market prices</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center; padding:30px; border-radius:15px; background: linear-gradient(135deg,#caffbf,#ffd6ff);'>
<h2 style='color:#9b5de5;'>📈 Crop Market Prices</h2>
<p style='font-size:16px; color:#000000'>Get approximate current prices for any crop</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Crop Price Simulation
# -----------------------------
crop_list = ["Rice","Wheat","Maize","Tomato","Onion","Potato","Chilli","Cotton","Banana"]

crop_selected = st.selectbox("🌾 Select Crop", crop_list)
state = st.text_input("📍 Enter State/District", "Maharashtra")

if st.button("📊 Show Approx Price") and crop_selected:
    base_price = random.randint(1500, 4000)
    low = int(base_price * 0.95)
    high = int(base_price * 1.08)

    st.success(f"🌾 Crop: {crop_selected}")
    st.info(f"📍 Location: {state}")
    st.metric("💰 Approx Modal Price (₹/quintal)", base_price)
    st.write(f"Min: ₹{low} | Max: ₹{high}")
    st.info(f"🔮 Predicted Short-Term Range: ₹{low} – ₹{high}")