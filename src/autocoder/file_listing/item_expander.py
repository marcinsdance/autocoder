import os
from typing import List, Set

class ItemExpander:
    def __init__(self, project_root: str, item_filter):
        self.project_root = project_root
        self.item_filter = item_filter

    def expand_approved_items(self, approved_items: List[str]) -> List[str]:
        expanded_items = []
        for item in approved_items:
            full_path = os.path.join(self.project_root, item)
            if os.path.isdir(full_path):
                expanded_items.extend(self._walk_directory(full_path))
                expanded_items.append(item)  # Include the directory itself
            else:
                expanded_items.append(item)  # It's a file, just add it
        return sorted(set(expanded_items))  # Remove duplicates and sort

    def _walk_directory(self, directory: str) -> List[str]:
        items = []
        for root, dirs, files in os.walk(directory):
            rel_root = os.path.relpath(root, self.project_root)
            for dir in dirs[:]:  # Copy the list as we might modify it
                if self.item_filter.should_exclude(dir):
                    self.item_filter.auto_excluded_items.add(os.path.join(rel_root, dir))
                    dirs.remove(dir)  # Don't walk into excluded directories
            for file in files:
                rel_path = os.path.join(rel_root, file)
                if not self.item_filter.should_exclude(file):
                    items.append(rel_path)
                else:
                    self.item_filter.auto_excluded_items.add(rel_path)
        return items

    def get_all_excluded_items(self, user_excluded_items: List[str]) -> List[str]:
        all_excluded = set(user_excluded_items) | self.item_filter.auto_excluded_items
        expanded_excluded = set()

        for item in all_excluded:
            full_path = os.path.join(self.project_root, item)
            if os.path.isdir(full_path):
                expanded_excluded.update(self._walk_directory(full_path))
            expanded_excluded.add(item)

        return sorted(expanded_excluded)
