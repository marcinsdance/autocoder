import ast
import astor
from typing import Dict
from langchain_core.tools import Tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

class CodeModifierArgs(BaseModel):
    original_code: str = Field(..., description="The original code to be modified")
    modifications: str = Field(..., description="Description of modifications to be made")

def code_modifier(state: Dict, args: CodeModifierArgs) -> Dict:
    try:
        tree = ast.parse(args.original_code)
        modified_tree = apply_modifications(tree, args.modifications)
        modified_code = astor.to_source(modified_tree)
        return {"modified_code": modified_code}
    except SyntaxError:
        return {"modified_code": simple_modify(args.original_code, args.modifications)}

def apply_modifications(tree, modifications):
    # TODO: Implement more sophisticated AST transformations here
    new_node = ast.Expr(ast.Str(f"# Modified: {modifications}"))
    tree.body.insert(0, new_node)
    return tree

def simple_modify(original_code, modifications):
    return f"# Modified: {modifications}\n\n{original_code}"

code_modifier_tools = [
    Tool.from_function(
        func=code_modifier,
        name="code_modifier",
        description="Modify code based on given instructions",
        args_schema=CodeModifierArgs
    )
]

code_modifier_node = ToolNode(code_modifier_tools)
