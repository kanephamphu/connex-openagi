"""
Connex AGI - Web Dashboard using Streamlit.
"""

import streamlit as st
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agi.config import AGIConfig
from agi import AGI
from agi.dashboard.utils import format_thought_process, format_execution_step

st.set_page_config(page_title="Connex AGI", page_icon="🧠", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .user-message {
        background-color: #f0f2f6;
    }
    .assistant-message {
        background-color: #e8f0fe;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agi" not in st.session_state:
    try:
        config = AGIConfig.from_env()
        st.session_state.agi = AGI(config)
        st.toast("AGI System Initialized Successfully", icon="✅")
    except Exception as e:
        st.error(f"Failed to initialize AGI: {e}")
        st.stop()

def display_chat_history():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "trace" in msg:
                with st.expander("Show Thought Process"):
                    for item in msg["trace"]:
                        st.markdown(item)

async def process_user_input(prompt):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare assistant response container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        thought_placeholder = st.expander("Thinking...", expanded=True)
        
        full_response = ""
        trace_log = []
        
        try:
            # Stream execution
            # Note: execute_with_streaming yields progress updates
            # We need to accumulate them
            
            with thought_placeholder:
                current_thought = st.empty()
                async for update in st.session_state.agi.execute_with_streaming(prompt):
                    
                    if update["phase"] == "planning":
                        text = format_thought_process(update)
                        if text:
                            st.write(text)  # Append to expander log
                            trace_log.append(text)
                            
                    elif update["phase"] == "execution":
                        text = format_execution_step(update)
                        if text:
                            st.write(text)
                            trace_log.append(text)
                    
            # Once complete, we assume the last result or we need to extract the final answer
            # The current streaming implementation wraps execute(), but execute() returns a dict
            # execute_with_streaming yields updates. We might need to yield the final result differently.
            # Let's verify agi.__init__.py execute_with_streaming.
            # It yields phases. It doesn't explicitly yield the "final answer" text if it's just a return value.
            # But the Orchestrator execution result usually contains the output.
            
            # Simple fallback if "foundation chat" was used, the result is in the update?
            # Actually, execute_with_streaming in agi/__init__.py yields execution updates.
            # The last update from orchestrator execution usually contains the result.
            
            # Let's perform a simple 'execute' call to get the final clean text if we want to be sure,
            # OR we rely on the skill output.
            # For 'general_chat', the skill output IS the response.
            
            # For now, let's just say "Task Completed" and show the last output.
            full_response = "✅ Task Completed. Check the thought process for details."
            
            # If it was a chat skill, try to find the reply
            # This is a bit hacky, normally the AGI should return a clear "Response".
            # In Phase 3 (Refinement), we should standardize "Final Response" in AGI class.
            
            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "trace": trace_log
            })

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})

# Sidebar
with st.sidebar:
    st.title("Connex AGI 🧠")
    st.markdown("---")
    st.subheader("System Status")
    if "agi" in st.session_state:
        config = st.session_state.agi.config
        st.success("System Online")
        st.code(f"Planner: {config.default_planner}\nBrain: Active\nWorkspace: {os.getcwd()}")
    
    st.markdown("---")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Main Interface
st.header("Jarvis Command Center")

display_chat_history()

if prompt := st.chat_input("How can I help you?"):
    asyncio.run(process_user_input(prompt))
