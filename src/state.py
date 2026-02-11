from typing import TypedDict, Optional

class QAState(TypedDict):
    user_prompt: str
    url: Optional[str]
    raw_html: Optional[str]
    output_format: Optional[str]
    final_output: Optional[str]
    decision: Optional[str]  # Stores: FETCH_URL, ASK_CLARIFICATION, or PROCEED
    reason: Optional[str]    # Stores the LLM's explanation for the next step