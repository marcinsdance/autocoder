class ContextBuilder:
    def __init__(self):
        self.context = {}

    def build_context(self, file_manager):
        context = file_manager.get_context()
        self.context['built_context'] = context
        return context

    def get_full_context(self):
        return self.context

    def add_context(self, key, value):
        self.context[key] = value

    def get_context(self, key):
        if key in self.context:
            return self.context[key]
        else:
            raise KeyError(f"Key '{key}' not found in context")

    def update_context(self, key, value):
        if key in self.context:
            self.context[key] = value
        else:
            raise KeyError(f"Key '{key}' not found in context")

    def remove_context(self, key):
        if key in self.context:
            del self.context[key]
        else:
            raise KeyError(f"Key '{key}' not found in context")

    def clear_context(self):
        self.context.clear()

    def context_exists(self, key):
        return key in self.context

    def get_size(self):
        return len(self.context)

    def add_multiple_context(self, context_dict):
        self.context.update(context_dict)
