import os
from typing import List

class FileSaver:
    def __init__(self, project_root: str):
        self.project_root = project_root

    def save_item_lists(self, project_items: List[str], excluded_items: List[str]):
        autocoder_dir = os.path.join(self.project_root, '.autocoder')
        os.makedirs(autocoder_dir, exist_ok=True)

        with open(os.path.join(autocoder_dir, 'project_items'), 'w') as f:
            f.write('\n'.join(project_items))

        with open(os.path.join(autocoder_dir, 'excluded_items'), 'w') as f:
            f.write('\n'.join(excluded_items))
