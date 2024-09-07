import logging
from typing import Dict
from .item_lister import ItemLister
from .item_filter import ItemFilter
from .llm_categorizer import LLMCategorizer
from .user_interaction import UserInteraction
from .item_expander import ItemExpander
from .file_saver import FileSaver

logger = logging.getLogger(__name__)

class FileListingNode:
    def __init__(self, project_root: str, claude_api):
        self.project_root = project_root
        self.claude_api = claude_api
        self.item_lister = ItemLister(project_root)
        self.item_filter = ItemFilter()
        self.llm_categorizer = LLMCategorizer(claude_api)
        self.user_interaction = UserInteraction(self.llm_categorizer)
        self.item_expander = ItemExpander(project_root, self.item_filter)
        self.file_saver = FileSaver(project_root)

    def process(self, state: Dict) -> Dict:
        logger.info("Starting file listing process")

        root_items = self.item_lister.list_root_items()
        filtered_items = self.item_filter.filter_common_excludes(root_items)
        generated_lists = self.llm_categorizer.generate_lists(filtered_items)

        if generated_lists is None:
            return self._update_state_with_error(state, "Failed to categorize items using LLM")

        approved_lists = self.user_interaction.get_user_approval(generated_lists, self.item_filter.auto_excluded_items)

        if approved_lists is None:
            return self._update_state_with_error(state, "User aborted the approval process")

        if approved_lists:
            project_items = self.item_expander.expand_approved_items(approved_lists['project_items'])
            excluded_items = self.item_expander.get_all_excluded_items(approved_lists['excluded_items'])

            self.file_saver.save_item_lists(project_items, excluded_items)
            state['project_items'] = project_items
            state['excluded_items'] = excluded_items
            logger.info("File and directory listing process completed successfully")
        else:
            logger.error("User did not approve item lists. Process aborted.")
            return self._update_state_with_error(state, "User did not approve item lists")

        return state

    def _update_state_with_error(self, state: Dict, error_message: str) -> Dict:
        state['error'] = error_message
        return state
