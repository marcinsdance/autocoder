from typing import Dict, Any
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
from functools import partial
from langchain_core.messages import AIMessage, HumanMessage

class LLMAnalyzeArgs(BaseModel):
    pass  # No additional arguments needed; state contains necessary info

def llm_analyze(state: Dict[str, Any], args: LLMAnalyzeArgs, claude_client: Anthropic) -> Dict[str, Any]:
    try:
        project_files = state.get('project_files', [])
        context = state.get('context', '')

        prompt = f"""{HUMAN_PROMPT} Analyze the following project structure and provide insights:

Project Files:
{', '.join(project_files)}

Context:
{context}

Please provide a comprehensive analysis of the project structure, including:
1. Overall project organization
2. Key components and their purposes
3. Potential areas for improvement or refactoring
4. Any best practices that are being followed or could be implemented
{AI_PROMPT}"""

        response = claude_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        analysis_result = response.content[0].text

        state['analysis_result'] = analysis_result
        state['messages'] = state.get('messages', []) + [AIMessage(content=analysis_result)]
        return state
    except Exception as e:
        state['error'] = f"Error during LLM analysis: {str(e)}"
        state['messages'] = state.get('messages', []) + [AIMessage(content=f"Error during analysis: {str(e)}")]
        return state

def create_llm_analyze_node(claude_client: Anthropic):
    llm_analyze_partial = partial(llm_analyze, claude_client=claude_client)

    llm_analyze_tools = [
        Tool.from_function(
            func=llm_analyze_partial,
            name="llm_analyze",
            description="Analyze project context using LLM",
            args_schema=LLMAnalyzeArgs
        )
    ]

    return ToolNode(llm_analyze_tools)
