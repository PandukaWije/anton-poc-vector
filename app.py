import datetime
import uuid
import streamlit as st
from pathlib import Path
from src.rag import RAGChat
# from llama_index.core import global_handler
from langfuse.llama_index import LlamaIndexInstrumentor

instrumentor = LlamaIndexInstrumentor()

# Set page config with a professional title and icon
st.set_page_config(
    page_title="Anton Online Store Assistant",
    page_icon="🛒",
    layout="centered"
)

# Custom CSS for a clean, modern e-commerce UI
theme_color = "#d32f2f"  # Anton's primary brand color
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #ffffff;
        font-family: 'Arial', sans-serif;
        max-width: 90%;
        margin: auto;
    }}
    .stTitle {{
        color: {theme_color};
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }}
    .welcome-banner {{
        background: {theme_color};
        color: #ffffff;
        padding: 2rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        text-align: center;
    }}
    .welcome-banner h2 {{
        font-size: 2rem;
        font-weight: bold;
    }}
    .chat-container {{
        background-color: #f9f9f9;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }}
    .chat-message {{
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.8rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }}
    .footer {{
        background-color: {theme_color};
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
    }}
    </style>
""", unsafe_allow_html=True)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Setup RAG Chat
@st.cache_resource
def initialize_rag():
    user_id = str(uuid.uuid4())
    session_id = str(datetime.datetime.now())
    rag_chat = RAGChat(
        documents_path="processed/scraped.json",
        website_url="https://onlinestore.anton.lk",
        support_email="support@onlinestore.anton.lk",
        business_name="Anton"
    )
    rag_chat.create_index()
    return rag_chat, user_id, session_id

rag_chat, user_id, session_id = initialize_rag()

# Header with Anton branding
col1, col2 = st.columns([1, 4])
with col1:
    st.image("assets/logo.png", width=120)
with col2:
    st.title("Anton Online Store Assistant")

# Welcome banner
st.markdown("""
<div class='welcome-banner'>
    <h2>Welcome to Anton Online Store!</h2>
    <p>Find high-quality PVC pipes, water tanks, and more.</p>
</div>
""", unsafe_allow_html=True)

# Feature highlights (e-commerce products)
# col1, col2, col3 = st.columns(3)
# col1, col2 = st.columns(2)
# with col1:
#     st.image("assets/ss.png", caption="PVC Pipes", use_container_width=True)
# with col2:
#     st.image("https://via.placeholder.com/300", caption="Water Tanks", use_container_width=True)
# with col3:
#     st.image("https://via.placeholder.com/300", caption="Hardware Essentials", use_container_width=True)
st.image("assets/ss.png", caption="PVC Pipes", use_container_width=True)

# Chat container
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🛒" if message["role"] == "assistant" else None):
        st.markdown(f"<div class='chat-message'>{message['content']}</div>", unsafe_allow_html=True)

# Accept user input
if prompt := st.chat_input("Ask me anything about Anton's products..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("assistant", avatar="🛒"):
        with instrumentor.observe(
                                user_id=user_id,
                                session_id=session_id
                                ) as trace:
            response = rag_chat.chat(prompt)
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

st.markdown("</div>", unsafe_allow_html=True)

# Footer with Anton details
st.markdown("""
<div class='footer'>
    <h3>Shop with Confidence at Anton Online Store</h3>
    <p>📞 Customer Support: +94 11 555 5555</p>
    <p>📍 No. 123, Colombo, Sri Lanka</p>
    <p>✉️ Email: support@onlinestore.anton.lk</p>
    <p style='font-size: 0.8rem;'>© 2025 Anton. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)