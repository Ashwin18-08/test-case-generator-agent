import asyncio
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

async def check_setup():
    print("Starting Setup Check...")
    
    # 1. Check Groq Connection
    try:
        llm = ChatGroq(model="llama-3.1-8b-instant") 
        res = llm.invoke("Are you online?")
        print("Groq Connection: Success")
    except Exception as e:
        print(f"Groq Connection: Failed ({e})")
        return

    mcp_config = {
            "playwright": {
                "command": "npx",
                "args": ["-y", "@playwright/mcp@latest"],
                "transport": "stdio",
            }
        }

    try:
        print("📡 Connecting to Playwright MCP Server...")
        client = MultiServerMCPClient(mcp_config)
        
        tools = await client.get_tools()
        
        if not tools:
            print("Connected, but no tools were returned.")
        else:
            print(f"Playwright MCP Connection: Success")
            print(f"Available Tools ({len(tools)}):")
            for tool in tools[:5]: # Print first 5
                print(f"   - {tool.name}")
    except Exception as e:
        print(f"MCP Connection: Failed.")
        print(f"Error Details: {e}")

if __name__ == "__main__":
    asyncio.run(check_setup())