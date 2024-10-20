import logging
from typing import Dict, Any, List
from anthropic import Anthropic
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)

class ClaudeAPIWrapper:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"

    def generate_response(self, state: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            messages = args.get('messages', [])
            max_tokens = args.get('max_tokens', 10000)

            anthropic_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    anthropic_messages.append(msg)
                elif isinstance(msg, HumanMessage):
                    anthropic_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    anthropic_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, SystemMessage):
                    anthropic_messages.append({"role": "system", "content": msg.content})

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=anthropic_messages
            )

            return {"response": response.content[0].text}
        except Exception as e:
            logger.error(f"An error occurred in generate_response: {str(e)}")
            return {"error": f"An error occurred: {str(e)}"}
