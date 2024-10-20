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

            # Extract system message if present
            system_message = None
            anthropic_messages = []
            for msg in messages:
                if isinstance(msg, SystemMessage) or (isinstance(msg, dict) and msg.get('role') == 'system'):
                    system_message = msg.content if isinstance(msg, SystemMessage) else msg.get('content')
                elif isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('role') == 'user'):
                    anthropic_messages.append({"role": "user",
                                               "content": msg.content if isinstance(msg, HumanMessage) else msg.get(
                                                   'content')})
                elif isinstance(msg, AIMessage) or (isinstance(msg, dict) and msg.get('role') == 'assistant'):
                    anthropic_messages.append({"role": "assistant",
                                               "content": msg.content if isinstance(msg, AIMessage) else msg.get(
                                                   'content')})

            # Prepare the request
            request = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": anthropic_messages
            }

            # Add system message if present
            if system_message:
                request["system"] = system_message

            response = self.client.messages.create(**request)

            return {"response": response.content[0].text}
        except Exception as e:
            logger.error(f"An error occurred in generate_response: {str(e)}")
            return {"error": f"An error occurred: {str(e)}"}
