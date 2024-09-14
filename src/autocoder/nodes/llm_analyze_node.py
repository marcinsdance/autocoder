from typing import Dict
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from anthropic import HUMAN_PROMPT, AI_PROMPT
from functools import partial
from langchain_core.messages import AIMessage  # Import AIMessage

class LLMAnalyzeArgs(BaseModel):
    pass  # No additional arguments needed; state contains necessary info

def llm_analyze(state: Dict, args: LLMAnalyzeArgs, claude_api) -> Dict:
    try:
        context = state['context']

        prompt = f"{HUMAN_PROMPT} Please analyze the following project code and provide a detailed analysis:\n{context}{AI_PROMPT}"

        response = claude_api.completions.create(
            model="claude-instant-v1",
            prompt=prompt,
            max_tokens_to_sample=1000,
            stop_sequences=[HUMAN_PROMPT]
        )

        analysis_result = response.completion.strip()
        state['analysis_result'] = analysis_result

        # Append the LLM's response as an AIMessage
        state['messages'].append(AIMessage(content=analysis_result))
        return state
    except Exception as e:
        state['error'] = f"Error during LLM analysis: {str(e)}"
        return state

def create_llm_analyze_node(claude_api):
    llm_analyze_partial = partial(llm_analyze, claude_api=claude_api)
    llm_analyze_tools = [
        Tool.from_function(
            func=llm_analyze_partial,
            name="llm_analyze",
            description="Send project context to LLM for analysis",
            args_schema=LLMAnalyzeArgs
        )
    ]
    return ToolNode(llm_analyze_tools)
