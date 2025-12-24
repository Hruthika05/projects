import streamlit as st
from chat import classify_query

# Page settings
st.set_page_config(page_title="FarmQ Chatbot", page_icon="🌱", layout="centered")

# Custom CSS
st.markdown("""
    <style>
    body {
        background-color: #f4f9f4;
    }
    .chat-bubble {
        padding: 12px 16px;
        border-radius: 15px;
        margin: 8px 0;
        max-width: 70%;
        font-size: 16px;
        line-height: 1.4;
    }
    .user-bubble {
        background-color: #d1e7dd;
        text-align: right;
        margin-left: auto;
        color: #1b4332;
        font-weight: 500;
    }
    .bot-bubble {
        background-color: #e7f1ff;
        text-align: left;
        margin-right: auto;
        color: #023e8a;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2909/2909765.png", width=100)
st.sidebar.title("🌱 FarmQ Chatbot")
st.sidebar.write("Your smart assistant for agricultural queries.")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Input box
query = st.text_input("💬 Ask your farming question:")

if query:
    # Store user input
    st.session_state.messages.append({"role": "user", "text": query})

    # Classify
    domain = classify_query(query)
    bot_reply = f"🔎 This looks related to **{domain}**.\n\n✅ I can suggest solutions or connect you with a **{domain} expert**."

    # Store bot response
    st.session_state.messages.append({"role": "bot", "text": bot_reply})

# Display chat
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble user-bubble'>👨‍🌾 {msg['text']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='chat-bubble bot-bubble'>🤖 {msg['text']}</div>", unsafe_allow_html=True)
