import streamlit as st

st.set_page_config(
    page_title="🌾 FarmQ – Farmer App",
    page_icon="🌾",
    layout="centered"
)

# ---------- FARMER HOME DASHBOARD ----------
st.markdown("""
<div style='background:#2e7d32; padding:20px; border-radius:15px; text-align:center; color:white'>
<h2>🌾 FarmQ</h2>
<p>All-in-one Farmer Assistant</p>
</div>
""", unsafe_allow_html=True)

st.write("### 🚜 Choose a Service")

c1, c2 = st.columns(2)
c3, c4 = st.columns(2)

with c1:
    if st.button("💬 FarmQ Assistant"):
        st.switch_page("pages/farmq.py")

with c2:
    if st.button("🌦 Weather Alerts"):
        st.switch_page("pages/Weather Alerts.py")


st.markdown("---")