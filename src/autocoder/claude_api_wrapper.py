from anthropic import Anthropic


class ClaudeAPIWrapper:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)

    def generate_response(self, prompt):
        # Format the prompt to match Claude's expected input format
        formatted_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"

        response = self.client.completions.create(
            model="claude-3-opus-20240229",
            prompt=formatted_prompt,
            max_tokens_to_sample=1000
        )
        return response.completion

    def format_prompt(self, system_prompt, user_prompt):
        # This method can be used for more complex prompt formatting if needed
        return f"{system_prompt}\n\nHuman: {user_prompt}\n\nAssistant:"
