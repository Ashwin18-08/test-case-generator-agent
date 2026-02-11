import re
import requests
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import interrupt
from langchain_mcp_adapters.client import MultiServerMCPClient
from state import QAState
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
URL_REGEX = r"https?://[^\s]+"


def extractor_node(state: QAState):
    # Use the current user_prompt which contains the resume value
    prompt = state.get("user_prompt", "")
    print(f"[Extractor] Current input: {prompt}")
    
    # 1. Extract URL
    url_match = re.search(URL_REGEX, prompt)
    # CRITICAL: We only update if a new URL is found, otherwise keep the old one
    url = url_match.group(0) if url_match else state.get("url")
    
    # 2. Detect HTML
    raw_html = state.get("raw_html")
    if "<html>" in prompt.lower() or "</div>" in prompt.lower():
        raw_html = prompt

    # 3. Detect Format
    output_format = state.get("output_format")
    if "json" in prompt.lower(): output_format = "json"
    elif "gherkin" in prompt.lower(): output_format = "gherkin"
    
    print(f"[Extractor] State Updated -> URL: {url}, HTML: {bool(raw_html)}, Format: {output_format}")
    return {**state, "url": url, "raw_html": raw_html, "output_format": output_format}


def analyst_node(state: QAState):
    print("[Analyst] Analyzing requirements...")
    
    # We use explicit True/False for the LLM to make it easier to parse
    has_url = state.get("url") is not None
    has_html = state.get("raw_html") is not None
    has_format = state.get("output_format") is not None

    system_prompt = """
    You are a workflow controller. You must choose the NEXT ACTION based on these STRICT rules:
    
    1. If URL is False AND HTML is False -> ACTION: ASK_CLARIFICATION | REASON: I need a URL or HTML content to start.
    2. If URL is True AND HTML is False -> ACTION: FETCH_URL | REASON: Scrape the content from the URL.
    3. If HTML is True AND Format is False -> ACTION: ASK_CLARIFICATION | REASON: I need to know the output format (JSON/Gherkin).
    4. If HTML is True AND Format is True -> ACTION: PROCEED | REASON: All data ready.

    Output format: ACTION: <ACTION_NAME> | REASON: <REASON_TEXT>
    """
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"State: URL_Exists={has_url}, HTML_Exists={has_html}, Format_Exists={has_format}")
    ])
    
    content = response.content.strip()
    action = re.search(r"ACTION:\s*(\w+)", content).group(1)
    reason = re.search(r"REASON:\s*(.*)", content).group(1)
    
    print(f"[Analyst] Decision: {action}")
    return {**state, "decision": action, "reason": reason}


async def fetch_url_node(state: QAState):
    url = state["url"]
    mcp_config = {
        "playwright": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"],
            "transport": "stdio",
        }
    }

    print(f"[Fetch] Session active for: {url}")
    
    try:
        client = MultiServerMCPClient(mcp_config)
        
        async with client.session("playwright") as session:
            mcp_tools = await client.get_tools()
            llm_with_tools = llm.bind_tools(mcp_tools)
            
            # 1. Ask the LLM to browse
            # We explicitly mention "snapshot" to nudge the LLM toward the right tool
            messages = [HumanMessage(content=f"Navigate to {url} and get the HTML.")]
            
            response = await llm_with_tools.ainvoke(messages)

            
            final_html = ""
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    print(f"Executing: {tool_call['name']}...")
                    result = await session.call_tool(tool_call['name'], tool_call['args'])
                    
                    # Capture the content from the snapshot tool
                    # browser_snapshot usually returns the full HTML string
                    if "snapshot" in tool_call["name"]:
                        final_html = result.content[0].text if result.content else ""

            # 2. Safety Fallback: Use the exact name from your log
            if not final_html:
                print("Fallback: Forcing 'browser_snapshot'...")
                res = await session.call_tool("browser_snapshot", {})
                final_html = res.content[0].text if res.content else ""

            # 3. Clean the result (Remove any AI "thought" text)
            clean_html = str(final_html)
            if "<html>" in clean_html.lower():
                # Ensure we only keep the actual HTML block
                import re
                match = re.search(r"<html.*</html>", clean_html, re.DOTALL | re.IGNORECASE)
                if match:
                    clean_html = match.group(0)

            return {
                **state,
                "raw_html": clean_html,
                "decision": "ANALYZE"
            }

    except Exception as e:
        print(f"Fetch Failed: {e}")
        return {**state, "decision": "ASK_CLARIFICATION", "reason": str(e)}
    


def clarification_node(state: QAState):
    print("[Clarification] Asking user...")
    reason = state.get("reason", "I need more info.")
    
    # LLM creates a natural question based on the analyst's reason
    question = llm.invoke([
        SystemMessage(content="Ask a polite question to get the missing info."),
        HumanMessage(content=f"Reason for pause: {reason}")
    ])
    
    user_input = interrupt(question.content)
    return {**state, "user_prompt": user_input}



def generator_node(state: QAState):
    print(f"[Generator] Creating {state['output_format']}...")
    print(state["raw_html"])
    
    # We explicitly tell the LLM to ignore tool logs and focus on the HTML structure
    system_msg = f"You are a Senior QA Engineer. Generate functional test cases in {state['output_format']} format."
    user_msg = f"""Analyze the following HTML source code and generate comprehensive test cases:
    
    SOURCE HTML:
    {state['raw_html']}
    
    IMPORTANT: Do not write tests about the browser tools. Write tests for the actual website features visible in the HTML code above."""

    response = llm.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=user_msg)
    ])
    return {**state, "final_output": response.content}