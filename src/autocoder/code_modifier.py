import re
import ast
import astor


class CodeModifier:
    def __init__(self):
        pass

    def modify_code(self, original_code, modifications):
        try:
            # Parse the original code into an AST
            tree = ast.parse(original_code)

            # Apply modifications
            modified_tree = self.apply_modifications(tree, modifications)

            # Generate the modified code
            modified_code = astor.to_source(modified_tree)

            return modified_code
        except SyntaxError:
            # If parsing fails, fall back to simple string replacement
            return self.simple_modify(original_code, modifications)

    def apply_modifications(self, tree, modifications):
        # TODO: Implement more sophisticated AST transformations here
        # For now, we'll just add a comment at the top of the file
        new_node = ast.Expr(ast.Str(f"# Modified by AutoCoder: {modifications}"))
        tree.body.insert(0, new_node)
        return tree

    def simple_modify(self, original_code, modifications):
        # Simple string-based modifications
        # This is a fallback method and should be improved
        modified_code = f"# Modified by AutoCoder: {modifications}\n\n{original_code}"

        # Apply simple replacements based on the modifications string
        # This is a very basic implementation and should be enhanced
        replacements = re.findall(r'replace "([^"]*)" with "([^"]*)"', modifications)
        for old, new in replacements:
            modified_code = modified_code.replace(old, new)

        return modified_code
