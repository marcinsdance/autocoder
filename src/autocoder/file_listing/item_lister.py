import os
from typing import List, Tuple

class ItemLister:
    def __init__(self, project_root: str):
        self.project_root = project_root

    def list_root_items(self) -> List[Tuple[str, str]]:
        root_items = []
        for item in os.listdir(self.project_root):
            full_path = os.path.join(self.project_root, item)
            item_type = 'directory' if os.path.isdir(full_path) else 'file'
            root_items.append((item, item_type))
        return root_items
