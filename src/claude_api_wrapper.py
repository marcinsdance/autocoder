from anthropic import Anthropic


class ClaudeAPIWrapper:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)

    def generate_response(self, prompt):
        response = self.client.completions.create(
            model="claude-3-opus-20240229",
            prompt=prompt,
            max_tokens_to_sample=1000
        )
        return response.completion
