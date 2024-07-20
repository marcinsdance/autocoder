class ContextBuilder:
    def __init__(self):
        pass

    def build_context(self, file_contents):
        context = "Project Files:\n\n"
        for filename, content in file_contents.items():
            context += f"File: {filename}\n"
            context += "Content:\n"
            context += content[:500] + "...\n\n" if len(content) > 500 else content + "\n\n"
        return context
