from anthropic import Anthropic

class ClaudeAPIWrapper:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"  # Using the latest Claude 3 model

    def generate_response(self, prompt):
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return None

    def format_prompt(self, system_prompt, user_prompt):
        return f"{system_prompt}\n\n{user_prompt}"
