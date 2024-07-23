from anthropic import Anthropic

class ClaudeAPIWrapper:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)

    def generate_response(self, prompt):
        try:
            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return None
