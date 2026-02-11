import asyncio
from dotenv import load_dotenv
from langgraph.types import Command
from graph import app

load_dotenv()

async def run_agent():
    config = {"configurable": {"thread_id": "dynamic-session-1"}}
    initial_state = {"user_prompt": "I want to generate some test cases"}

    print("--- Starting QA Agent (Async Mode) ---")

    # Initial run using ainvoke
    result = await app.ainvoke(initial_state, config=config)

    # Dynamic Loop: While the graph is waiting for an interrupt
    while True:
        state_info = await app.aget_state(config)
        
        # If there are no more nodes to run, break the loop
        if not state_info.next:
            break
            
        # Check if we are at an interrupt (Clarification Node)
        if state_info.tasks and state_info.tasks[0].interrupts:
            question = state_info.tasks[0].interrupts[0].value
            
            print(f"\n[Agent]: {question}")
            user_response = input("[User]: ")
            
            # Resume the graph using ainvoke and Command(resume=...)
            result = await app.ainvoke(Command(resume=user_response), config=config)
        else:
            # If it's not an interrupt but the graph isn't finished, 
            # we simply let it continue (though usually .next handles this)
            break

    # Final output retrieval
    final_state = await app.aget_state(config)
    print("\n--- FINAL OUTPUT ---\n", final_state.values.get("final_output"))

if __name__ == "__main__":
    # Use asyncio.run to execute the async flow
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")