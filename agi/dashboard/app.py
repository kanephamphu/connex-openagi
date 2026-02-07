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
        # UI Structure: Thinking (Collapsed), Plan (Expanded), Execution (Collapsed)
        reasoning_expander = st.expander("Thinking Process", expanded=False)
        plan_expander = st.expander("Execution Plan", expanded=True)
        execution_expander = st.expander("Execution Log", expanded=False)
        final_answer = st.empty()
        
        full_response = ""
        trace_log = []
        
        # Placeholders for streaming content
        with reasoning_expander:
            reasoning_placeholder = st.empty()
        
        try:
            async for update in st.session_state.agi.execute_with_streaming(prompt):
                
                # --- PLANNING PHASE ---
                if update["phase"] == "planning":
                    # Handle Reasoning (Streaming)
                    if "partial_content" in update:
                        reasoning_placeholder.markdown(update["partial_content"])
                    
                    # Handle Plan Generation
                    text = format_thought_process(update)
                    if text and "Plan Generated" in text:
                        with plan_expander:
                            st.markdown(text)
                        trace_log.append(text)
                    elif text and update.get("type") not in ["reasoning_token", "reasoning_chunk"]:
                        # Other planning events (e.g. goal started)
                        with reasoning_expander:
                            st.write(text)
                        trace_log.append(text)
                            
                # --- EXECUTION PHASE ---
                elif update["phase"] == "execution":
                    with execution_expander:
                        text = format_execution_step(update)
                        if text:
                            st.markdown(text)
                            trace_log.append(text)
                    
            # Completion
            full_response = "✅ **Task Completed**"
            final_answer.markdown(full_response)
            
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
