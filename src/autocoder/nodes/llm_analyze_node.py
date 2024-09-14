from typing import Dict
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
from anthropic import HUMAN_PROMPT, AI_PROMPT
from functools import partial
from langchain_core.messages import AIMessage  # Import AIMessage
from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from anthropic import Anthropic

class LLMAnalyzeArgs(BaseModel):
    pass  # No additional arguments needed; state contains necessary info

def create_llm_analyze_node(claude_api):
    def llm_analyze(state: Dict, args: LLMAnalyzeArgs) -> Dict:
        try:
            # Use Claude API to analyze the context
            analysis = claude_api.completions.create(
                model="claude-3-opus-20240229",
                prompt=f"Analyze the following project context:\n\n{args.context}",
                max_tokens=1000
            ).completion

            state['analysis_result'] = analysis
            state['messages'] = state.get('messages', []) + [AIMessage(content="Analysis completed.")]
            return state
        except Exception as e:
            state['error'] = str(e)
            state['messages'] = state.get('messages', []) + [AIMessage(content=f"Error during analysis: {str(e)}")]
            return state

    llm_analyze_tools = [
        Tool.from_function(
            func=llm_analyze,
            name="llm_analyze",
            description="Analyze project context using LLM",
            args_schema=LLMAnalyzeArgs
        )
    ]

    return ToolNode(llm_analyze_tools)

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


def create_llm_analyze_node(claude_client: Anthropic):
    def llm_analyze(state: Dict[str, Any]) -> Dict[str, Any]:
        try:
            project_files = state.get('project_files', [])
            context = state.get('context', '')

            prompt = f"""Analyze the following project structure and provide insights:

Project Files:
{', '.join(project_files)}

Context:
{context}

Please provide a comprehensive analysis of the project structure, including:
1. Overall project organization
2. Key components and their purposes
3. Potential areas for improvement or refactoring
4. Any best practices that are being followed or could be implemented
"""

            response = claude_client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis_result = response.content[0].text

            # Ensure we're returning an AIMessage
            return {
                "messages": [AIMessage(content=analysis_result)],
                "analysis_result": analysis_result
            }
        except Exception as e:
            return {"error": f"An error occurred during analysis: {str(e)}"}

    return llm_analyze
