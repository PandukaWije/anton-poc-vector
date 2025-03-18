import streamlit as st
import requests
import json
import time
from datetime import datetime

# Set page config with a more modern look
st.set_page_config(
    page_title="Anton Product Information Assistant",
    page_icon="🛍️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stChat {
        border-radius: 10px;
        padding: 10px;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
    }
    .chat-message.user {
        background-color: #2b313e;
    }
    .chat-message.assistant {
        background-color: #475063;
    }
    .app-title {
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton button {
        border-radius: 20px;
        padding: 0.5rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "awaiting_processing" not in st.session_state:
    st.session_state.awaiting_processing = False
if "current_message" not in st.session_state:
    st.session_state.current_message = None

# API URL - change if needed
API_URL = "https://api.know360.io/anton_rag/"

# Function to get all chats
def get_chats():
    try:
        response = requests.get(f"{API_URL}/api/chats")
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return []

# Function to get a specific chat
def get_chat(chat_id):
    try:
        response = requests.get(f"{API_URL}/api/chats/{chat_id}")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# Function to create a new chat
def create_chat():
    try:
        response = requests.post(f"{API_URL}/api/chats")
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return None

# Function to delete a chat
def delete_chat(chat_id):
    try:
        response = requests.delete(f"{API_URL}/api/chats/{chat_id}")
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        return False

# Function to process the message after it's displayed
def process_message(chat_id, content):
    # Create a status indicator
    status = st.status("Processing your request...", expanded=False)
    
    # Create message via API
    try:
        response = requests.post(
            f"{API_URL}/api/messages",
            json={"chat_id": chat_id, "content": content}
        )
        
        if response.status_code != 200:
            status.update(label="Failed to send message", state="error")
            time.sleep(1)
            st.session_state.processing = False
            st.rerun()
            return
            
        data = response.json()
        new_chat_id = data["chat_id"]
        message_id = data["message_id"]
        
        # If this is a new chat, update the chat_id
        if chat_id is None or chat_id != new_chat_id:
            st.session_state.chat_id = new_chat_id
        
        status.update(label="Generating response...", state="running")
        
        # Create a chat message container for the assistant's response
        assistant_container = st.chat_message("assistant")
        message_placeholder = assistant_container.empty()
        
        # Stream the response
        try:
            # Connect to the streaming endpoint
            stream_response = requests.get(
                f"{API_URL}/api/messages/{message_id}/stream",
                params={"chat_id": new_chat_id},
                stream=True
            )
            
            if stream_response.status_code != 200:
                status.update(label="Error streaming response", state="error")
                time.sleep(1)
                st.session_state.processing = False
                st.rerun()
                return
            
            # Process the streamed response
            content_so_far = ""
            
            for line in stream_response.iter_lines():
                if not line:
                    continue
                    
                # SSE format: lines starting with "data: "
                if line.startswith(b"data: "):
                    data_str = line[6:].decode("utf-8")
                    
                    # Check for the [DONE] marker
                    if data_str == "[DONE]":
                        break
                        
                    try:
                        data = json.loads(data_str)
                        chunk = data.get("content", "")
                        content_so_far += chunk
                        
                        # Update the message content in the chat message
                        message_placeholder.write(content_so_far)
                            
                        # Update status to show progress
                        status.update(label=f"Generating response...", state="running")
                            
                    except json.JSONDecodeError:
                        continue
            
            # Add the complete message to our messages list
            st.session_state.messages.append({"role": "assistant", "content": content_so_far})
            
            # Update status to complete
            status.update(label="Response complete!", state="complete")
            
        except Exception as e:
            status.update(label=f"Error during streaming: {str(e)}", state="error")
            
    except Exception as e:
        status.update(label=f"Error connecting to API: {str(e)}", state="error")
    
    # Close status after a short delay
    time.sleep(0.5)
    status.update(state="complete", expanded=False)
    
    st.session_state.processing = False
    st.session_state.awaiting_processing = False
    st.session_state.current_message = None
    st.rerun()

# Main UI
st.markdown("<h1 class='app-title'>Anton Product Information Assistant</h1>", unsafe_allow_html=True)

# Top controls row
col1, col2 = st.columns([3, 1])
with col1:
    st.image('./image.png')
    st.logo(
        './image.png',
        link="https://onlinestore.anton.lk/",
    )
with col2:
    if st.button("New Chat", use_container_width=True):
        st.session_state.chat_id = None
        st.session_state.messages = []
        st.session_state.processing = False
        st.session_state.awaiting_processing = False
        st.session_state.current_message = None
        st.rerun()

# Display chat history - short divider
st.divider()

# Display chat messages
message_container = st.container()
with message_container:
    # Display existing messages
    for message in st.session_state.messages:
        st.chat_message(message["role"]).write(message["content"])

# Check if we need to process a message - this happens after the first rerun
if st.session_state.awaiting_processing and not st.session_state.processing:
    # Set processing to true to prevent duplicate processing
    st.session_state.processing = True
    # Process the stored message
    process_message(st.session_state.chat_id, st.session_state.current_message)

# Bottom area with input box
st.divider()

# Chat input
prompt = st.chat_input("Ask about our products...", disabled=st.session_state.processing)

# Handle the prompt - this approach works with Streamlit's expected behavior
if prompt:
    # Immediately add to messages
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Store the message for processing after rerun
    st.session_state.current_message = prompt
    st.session_state.awaiting_processing = True
    # Rerun to show the message first
    st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 2rem; color: #888;">
    <p>Product RAG Assistant - Powered by FastAPI & Streamlit</p>
</div>
""", unsafe_allow_html=True)
