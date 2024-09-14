from anthropic import Anthropic
from typing import Dict, Any, List
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

class GenerateResponseArgs(BaseModel):
    messages: List[Dict[str, str]] = Field(..., description="List of messages in the conversation")
    max_tokens: int = Field(1000, description="Maximum number of tokens in the response")
    system_prompt: str = Field("You are a helpful AI assistant.", description="System prompt to guide the model's behavior")

class ClaudeAPIWrapper:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"

    def generate_response(self, state: Dict[str, Any], args: GenerateResponseArgs) -> Dict[str, Any]:
        try:
            messages = [{"role": "system", "content": args.system_prompt}] + args.messages

            response = self.client.messages.create(
                model=self.model,
                max_tokens=args.max_tokens,
                messages=messages
            )
            return {"response": response.content[0].text}
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}

claude_api_tools = [
    Tool.from_function(
        func=ClaudeAPIWrapper.generate_response,
        name="generate_response",
        description="Generate a response using the Claude API",
        args_schema=GenerateResponseArgs
    )
]

claude_api_node = ToolNode(claude_api_tools)
