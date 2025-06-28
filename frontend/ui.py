import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="TailorTalk",
    page_icon="🗕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #2E86AB;
        margin-bottom: 2rem;
    }
    .chat-container {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f9f9f9;
    }
    .user-message {
        background-color: #E3F2FD;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    .assistant-message {
        background-color: #F1F8E9;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# App configuration
BACKEND_URL = "http://localhost:8000"

def check_backend_health():
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def send_chat_message(message):
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={"message": message},
            timeout=10
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"response": f"❌ Connection error: {str(e)}"}

def get_availability(date):
    try:
        response = requests.post(
            f"{BACKEND_URL}/availability",
            json={"date": date},
            timeout=10
        )
        return response.json()
    except:
        return {"available_slots": []}

# Sidebar
with st.sidebar:
    st.header("🗕️ TailorTalk")
    st.markdown("**Your AI Appointment Assistant**")

    if check_backend_health():
        st.success("🟢 Backend Connected")
    else:
        st.error("🔴 Backend Disconnected")
        st.warning("Please start the backend server:\n```bash\ncd backend\npython main.py\n```")

    st.markdown("---")
    st.subheader("Quick Actions")

    selected_date = st.date_input("Check Availability", datetime.now().date())
    if st.button("Check Slots"):
        date_str = selected_date.strftime("%Y-%m-%d")
        availability = get_availability(date_str)
        if availability.get("available_slots"):
            st.success(f"Available slots for {date_str}:")
            for slot in availability["available_slots"][:5]:
                st.write(f"• {slot}")
        else:
            st.warning("No available slots found")

    st.markdown("---")
    st.subheader("💡 How to Use")
    st.markdown("""
    **Try these examples:**
    - "Check availability for tomorrow"
    - "Book an appointment at 2 PM today"
    - "What slots are free on 2024-12-15?"
    - "Schedule a meeting for next Monday at 10 AM"
    """)

# Main content
st.markdown('<h1 class="main-header">TailorTalk 🗕️</h1>', unsafe_allow_html=True)
st.markdown("**AI-Powered Appointment Booking Assistant**")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm your appointment booking assistant. I can help you check availability, book appointments, and manage your schedule. How can I help you today?"}
    ]

st.subheader("💬 Chat with Assistant")
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_data = send_chat_message(prompt)
            response = response_data.get("response", "Sorry, I couldn't process your request.")
            st.markdown(response)

            if response_data.get("available_slots"):
                st.markdown("**Available Time Slots:**")
                cols = st.columns(3)
                for i, slot in enumerate(response_data["available_slots"][:6]):
                    with cols[i % 3]:
                        if st.button(f"🗕️ {slot}", key=f"slot_{i}"):
                            booking_message = f"Book appointment at {slot}"
                            st.session_state.messages.append({"role": "user", "content": booking_message})
                            booking_response = send_chat_message(booking_message)
                            st.session_state.messages.append({"role": "assistant", "content": booking_response["response"]})
                            st.rerun()

            if response_data.get("booking_confirmed"):
                st.balloons()
                st.success("🎉 Appointment booked successfully!")

    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your appointment booking assistant. How can I help you today?"}
        ]
        st.rerun()

with col2:
    st.markdown("**Status:** " + ("🟢 Online" if check_backend_health() else "🔴 Offline"))

with col3:
    st.markdown("**Version:** 1.0.0")

with st.expander("📊 Today's Schedule Overview"):
    today = datetime.now().strftime("%Y-%m-%d")
    availability = get_availability(today)

    if availability.get("available_slots"):
        st.success(f"**{len(availability['available_slots'])}** slots available today")
        slots_df = pd.DataFrame({
            'Time': availability['available_slots'][:10],
            'Status': ['Available'] * min(10, len(availability['available_slots']))
        })
        st.dataframe(slots_df, use_container_width=True)
    else:
        st.warning("No available slots for today")

with st.expander("💡 Pro Tips"):
    st.markdown("""
    1. **Natural Language**: You can speak naturally! Try "I need an appointment tomorrow afternoon"
    2. **Specific Times**: Be specific with times like "2:30 PM" or "14:30"
    3. **Date Formats**: Use formats like "2024-12-15", "tomorrow", or "next Monday"
    4. **Quick Booking**: Click on available time slots to book instantly
    5. **Check Availability**: Ask "What's available this week?" for multiple options
    """)
