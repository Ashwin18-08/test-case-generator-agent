from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import QAState
from nodes import analyst_node, fetch_url_node, clarification_node, generator_node, extractor_node

def route_after_analyst(state: QAState):
    decision = state["decision"]
    if decision == "FETCH_URL": return "fetch"
    if decision == "ASK_CLARIFICATION": return "clarify"
    if decision == "PROCEED": return "generate"
    return "clarify"

graph = StateGraph(QAState)

graph.add_node("extractor", extractor_node)
graph.add_node("analyst", analyst_node)
graph.add_node("fetch", fetch_url_node)
graph.add_node("clarify", clarification_node)
graph.add_node("generate", generator_node)

graph.add_edge(START, "extractor")
graph.add_edge("extractor", "analyst")
graph.add_conditional_edges("analyst", route_after_analyst)
graph.add_edge("fetch", "extractor") # Re-extract in case fetch fails or redirects
graph.add_edge("clarify", "extractor") # Loop back to parse user's new answer
graph.add_edge("generate", END)

app = graph.compile(checkpointer=MemorySaver())