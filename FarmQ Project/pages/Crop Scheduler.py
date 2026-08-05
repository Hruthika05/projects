import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="📅 Crop Scheduler", layout="wide")

if st.button("⬅ Back to Home"):
    st.switch_page("Home.py")

st.write("---")


# =========================
# Page Config
# =========================
st.set_page_config(page_title="📅 Crop Scheduler", layout="wide")

# =========================
# Sidebar UI
# =========================
st.sidebar.markdown("""
<div style='padding:20px; border-radius:15px; background: linear-gradient(135deg,#caffbf,#ffd6ff); text-align:center'>
<h2 style='color:#6a4c93;'>📅 Crop Scheduler</h2>
<p style='font-size:14px; color:#3a0ca3;'>Plan your crops & harvest timelines efficiently</p>
</div>
""", unsafe_allow_html=True)

# =========================
# Header
# =========================
st.markdown("""
<div style='text-align:center; padding:25px; border-radius:15px; background: linear-gradient(135deg,#ffd6ff,#caffbf);'>
<h2 style='color:#9b5de5;'>📅 Dynamic Crop Scheduler</h2>
<p style='font-size:16px; color:#000000'>Type your crops and get a detailed sowing/growing/harvest plan</p>
</div>
""", unsafe_allow_html=True)

st.write("---")

# =========================
# Month Order
# =========================
MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

# =========================
# Crop Duration (months)
# =========================
CROP_DURATION = {
    "rice": {"sowing": 2, "growing": 4, "harvest": 1},
    "wheat": {"sowing": 2, "growing": 4, "harvest": 1},
    "maize": {"sowing": 1, "growing": 3, "harvest": 1},
    "tomato": {"sowing": 2, "growing": 3, "harvest": 1},
    "onion": {"sowing": 2, "growing": 4, "harvest": 1},
    "potato": {"sowing": 2, "growing": 3, "harvest": 1},
    "chilli": {"sowing": 2, "growing": 4, "harvest": 1},
    "cotton": {"sowing": 2, "growing": 4, "harvest": 1},
}

DEFAULT_DURATION = {"sowing": 2, "growing": 3, "harvest": 1}

# =========================
# User Input
# =========================
st.subheader("🌾 Enter Your Crops and Sowing Month")
num_crops = st.number_input("Number of Crops", min_value=1, max_value=10, value=1, step=1)

user_crops = []
for i in range(num_crops):
    crop_name = st.text_input(f"Crop {i+1} Name", key=f"crop_{i}")
    start_month = st.selectbox(f"Crop {i+1} Sowing Start Month", MONTH_ORDER, key=f"month_{i}")
    if crop_name:
        user_crops.append({"name": crop_name.strip(), "start": start_month})

# =========================
# Compute Schedule
# =========================
def compute_schedule(crops):
    schedule = []
    for c in crops:
        crop = c["name"].lower()
        start = c["start"]
        duration = CROP_DURATION.get(crop, DEFAULT_DURATION)
        start_idx = MONTH_ORDER.index(start)
        sowing_end = (start_idx + duration["sowing"] - 1) % 12
        growing_end = (sowing_end + duration["growing"]) % 12
        harvest_end = (growing_end + duration["harvest"]) % 12

        schedule.append({
            "Crop": c["name"].title(),
            "Sowing": f"{start} - {MONTH_ORDER[sowing_end]}",
            "Growing": f"{MONTH_ORDER[(sowing_end+1)%12]} - {MONTH_ORDER[growing_end]}",
            "Harvesting": f"{MONTH_ORDER[(growing_end+1)%12]} - {MONTH_ORDER[harvest_end]}"
        })
    return pd.DataFrame(schedule)

# =========================
# Display Plan
# =========================
if st.button("📊 Generate Schedule") and user_crops:
    plan_df = compute_schedule(user_crops)
    st.subheader("📋 Detailed Crop Plan")
    st.table(plan_df)

    # =========================
    # Line Chart Visualization
    # =========================
    chart_data = []
    for idx, row in plan_df.iterrows():
        crop_name = row["Crop"]
        for stage in ["Sowing", "Growing", "Harvesting"]:
            months = row[stage].split(" - ")
            start_idx = MONTH_ORDER.index(months[0]) + 1
            end_idx = MONTH_ORDER.index(months[1]) + 1
            chart_data.append({"Crop": crop_name, "Stage": stage, "Month": start_idx, "Value": 1})
            chart_data.append({"Crop": crop_name, "Stage": stage, "Month": end_idx, "Value": 1})

    chart_df = pd.DataFrame(chart_data)
    st.subheader("📊 Crop Timeline (Line Chart)")
    line_chart = alt.Chart(chart_df).mark_line(point=True).encode(
        x=alt.X('Month:Q', title='Month', scale=alt.Scale(domain=[1,12])),
        y=alt.Y('Crop:N', title='Crop'),
        color='Stage:N',
        tooltip=['Crop','Stage','Month']
    ).properties(height=50*len(user_crops)+50)
    st.altair_chart(line_chart, use_container_width=True)

    # =========================
    # Tips Panel
    # =========================
    st.markdown("""
    <div style='margin-top:20px; padding:15px; border-radius:12px; background:#e0f7fa;'>
    <h4 style='color:#00796b;'>💡 Tips:</h4>
    <ul>
    <li>Adjust start months based on your local climate.</li>
    <li>Rotate crops to maintain soil fertility.</li>
    <li>Plan irrigation according to crop stages.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("✨ Enter crops and select sowing start months to generate schedule.")