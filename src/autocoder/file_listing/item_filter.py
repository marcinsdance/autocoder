import os
from typing import List, Tuple, Set

class ItemFilter:
    def __init__(self):
        self.common_excludes = {
            '__pycache__', '*.pyc', '*.pyo', '*.pyd',
            '.git', '.idea', '.vscode', '*.egg-info',
            'build', 'dist', '.tox', '.pytest_cache',
            '*.log', '*.sqlite3', '*.db', '*.swp',
            '.DS_Store', 'Thumbs.db'
        }
        self.auto_excluded_items: Set[str] = set()

    def filter_common_excludes(self, items: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        filtered_items = []
        for item, item_type in items:
            if not self.should_exclude(item):
                filtered_items.append((item, item_type))
            else:
                self.auto_excluded_items.add(item)
        return filtered_items

    def should_exclude(self, item: str) -> bool:
        return any(self.match_pattern(os.path.basename(item), pattern) for pattern in self.common_excludes)

    def match_pattern(self, item: str, pattern: str) -> bool:
        if pattern.startswith('*'):
            return item.endswith(pattern[1:])
        return item == pattern
