# app.py
import json
import streamlit as st
from langchain_core.messages import AIMessage, SystemMessage

from core.database.sync_db import get_session
from rh_agent.graph import generate_stream


@st.cache_resource
def get_db_session():
    """Initialize and cache the database session for the Streamlit app."""
    db = get_session()
    return db

st.set_page_config(page_title="AI Chat Bot", page_icon="🤖")
st.title("🤖 OTBS AI Chat Bot Assistant ")

# 1) Session memory
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = "default-thread"

# 2) Show previous messages
for msg in st.session_state.messages:
    if isinstance(msg, dict):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role != "system":
            with st.chat_message(role):
                st.markdown(content)
    elif isinstance(msg, SystemMessage):
        continue
    else:
        role = "assistant" if isinstance(msg, AIMessage) else "user"
        with st.chat_message(role):
            st.markdown(msg.content)

# 3) Input
prompt = st.chat_input("Type your message...")
if prompt:
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        
        placeholder = st.empty()
        response_text = ""
        
        try:
            # Use the cached database session
            db_session = get_db_session()
            
            response_text = ""
            for event_str in generate_stream(prompt, st.session_state.thread_id, db_session):
                data = json.loads(event_str.strip())
                
                if data["type"] == "step":
                    placeholder.info(data["content"])
                elif data["type"] == "token":
                    response_text += data["content"]
                    placeholder.markdown(response_text)
                elif data["type"] == "error":
                    st.error(f"Error: {data['content']}")
            
        except Exception as e:
            st.error(f"Failed to get response: {str(e)}")
            response_text = f"Error: {str(e)}"

    # save final response
    assistant_msg = {"role": "assistant", "content": response_text}
    st.session_state.messages.append(assistant_msg) 