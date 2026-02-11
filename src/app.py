import streamlit as st
import asyncio
from langgraph.types import Command
from graph import app  # Import your compiled graph
import uuid

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI QA Test Case Generator", layout="wide")
st.title(" QA Test Case Agent")
st.markdown("Provide a URL or HTML to generate test cases.")

# --- SESSION STATE INITIALIZATION ---
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Helper to run async logic in Streamlit's sync environment
def run_async(coro):
    return asyncio.run(coro)

# --- DISPLAY CHAT HISTORY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- INPUT HANDLING ---
user_input = st.chat_input("Enter URL, HTML, or Format...")

if user_input:
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Processing (Browser may take a moment)..."):
            
            # 2. Define the Async Execution Logic
            async def process_input():
                # Check current state asynchronously
                state = await app.aget_state(config)
                
                if state.next:
                    # Resume with async ainvoke
                    return await app.ainvoke(Command(resume=user_input), config=config)
                else:
                    # Start fresh with async ainvoke
                    initial_input = {
                        "user_prompt": user_input,
                        "url": None,
                        "raw_html": None,
                        "output_format": None,
                        "decision": None,
                        "reason": None
                    }
                    return await app.ainvoke(initial_input, config=config)

            # 3. Execute the async function
            final_state_values = run_async(process_input())

            # 4. Check for Interrupts or Final Output (Async state check)
            new_state = run_async(app.aget_state(config))
            
            if new_state.next:
                # Get the question from the interrupt
                interrupt_msg = new_state.tasks[0].interrupts[0].value
                st.markdown(interrupt_msg)
                st.session_state.messages.append({"role": "assistant", "content": interrupt_msg})
            
            elif "final_output" in final_state_values and final_state_values["final_output"]:
                output = final_state_values["final_output"]
                st.markdown("### Final Test Cases")
                st.code(output, language="gherkin" if "gherkin" in str(output).lower() else "json")
                st.session_state.messages.append({"role": "assistant", "content": f"Generated output:\n{output}"})

# --- SIDEBAR STATE VIEWER ---
with st.sidebar:
    st.header("Graph State")
    # Async state retrieval for the sidebar
    state_for_sidebar = run_async(app.aget_state(config))
    current_values = state_for_sidebar.values
    
    if current_values:
        st.json({
            "URL": current_values.get("url"),
            "Format": current_values.get("output_format"),
            "Last Decision": current_values.get("decision"),
            "Reason": current_values.get("reason")
        })
    
    if st.button("Reset Session"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()