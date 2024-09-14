import os
from autocoder.file_listing.file_listing_node import FileListingNode
from autocoder.claude_api_wrapper import ClaudeAPIWrapper

def test_file_listing_node():
    project_root = os.getcwd()  # Or specify the path to your project
    api_key = 'your_api_key_here'  # Replace with your actual API key
    claude_api = ClaudeAPIWrapper(api_key)
    file_lister = FileListingNode(project_root, claude_api)

    state = {"project_root": project_root, "claude_api": claude_api}
    updated_state = file_lister.process(state)

    if 'error' in updated_state:
        print(f"Error: {updated_state['error']}")
    else:
        print("Project Files:")
        for file in updated_state['project_files']:
            print(file)
        print("\nContext:")
        print(updated_state['context'][:500])  # Print first 500 characters of context

if __name__ == "__main__":
    test_file_listing_node()
