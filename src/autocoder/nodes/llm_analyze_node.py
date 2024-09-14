# File: src/autocoder/nodes/llm_analyze_node.py

from typing import Dict
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from anthropic import HUMAN_PROMPT, AI_PROMPT
from functools import partial

class LLMAnalyzeArgs(BaseModel):
    pass  # No additional arguments needed; state contains necessary info

def llm_analyze(state: Dict, args: LLMAnalyzeArgs, claude_api) -> Dict:
    try:
        context = state['context']

        prompt = f"{HUMAN_PROMPT} Please analyze the following project code and provide a detailed analysis:\n{context}{AI_PROMPT}"

        response = claude_api.completions.create(
            model="claude-instant-v1",  # Adjust the model as needed
            prompt=prompt,
            max_tokens_to_sample=1000,
            stop_sequences=[HUMAN_PROMPT]
        )

        state['analysis_result'] = response.completion.strip()
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
