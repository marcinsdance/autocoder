from typing import Dict, List, Set
import logging

logger = logging.getLogger(__name__)

class UserInteraction:
    def __init__(self, llm_categorizer):
        self.llm_categorizer = llm_categorizer

    def get_user_approval(self, item_lists: Dict[str, List[str]], auto_excluded_items: Set[str]) -> Dict[str, List[str]] | None:
        while True:
            if item_lists is None or 'project_items' not in item_lists or 'excluded_items' not in item_lists:
                logger.error("Invalid item lists. Unable to proceed with approval.")
                return None

            print("\nProject Items:")
            for item in item_lists['project_items']:
                print(f"  {item}")

            print("\nExcluded Items:")
            for item in item_lists['excluded_items']:
                print(f"  {item}")

            print("\nAutomatically Excluded Items:")
            for item in sorted(auto_excluded_items):
                print(f"  {item}")

            approval = input("\nDo you approve these item lists? (yes/no/quit): ").lower()

            if approval == 'yes':
                return item_lists
            elif approval == 'no':
                print("Please describe the changes you want to make:")
                changes = input("Your changes: ")
                updated_lists = self._update_lists_with_llm(item_lists, changes, auto_excluded_items)
                if updated_lists is None:
                    logger.error("Failed to update lists. Please try again.")
                else:
                    item_lists = updated_lists
            elif approval == 'quit':
                logger.info("Process aborted by user.")
                return None
            else:
                print("Invalid input. Please enter 'yes', 'no', or 'quit'.")

    def _update_lists_with_llm(self, current_lists: Dict[str, List[str]], user_changes: str, auto_excluded_items: Set[str]) -> Dict[str, List[str]] | None:
        try:
            # Prepare the prompt for the LLM
            prompt = f"""Given the current project structure and user requested changes, update the project and excluded items lists.

Current Project Items:
{', '.join(current_lists['project_items'])}

Current Excluded Items:
{', '.join(current_lists['excluded_items'])}

Automatically Excluded Items:
{', '.join(sorted(auto_excluded_items))}

User Requested Changes:
{user_changes}

Please provide the updated lists in the following format:

Project Items:
- [List of updated project items]

Excluded Items:
- [List of updated excluded items]

Ensure all items from the original lists are accounted for, either by including them in one of the lists or explicitly mentioning their removal."""

            # Get response from LLM
            response = self.llm_categorizer.claude_api.generate_response(prompt)

            if response is None:
                logger.error("Failed to get response from LLM")
                return None

            # Parse the response
            updated_lists = self.llm_categorizer._parse_response(response)

            if updated_lists is None or 'project_items' not in updated_lists or 'excluded_items' not in updated_lists:
                logger.error("Invalid response from LLM")
                return None

            return updated_lists

        except Exception as e:
            logger.error(f"Error in updating lists with LLM: {str(e)}")
            return None
