import os


def create_llm_txt(files_list_path, output_file_path):
    # Read the list of file names
    with open(files_list_path, 'r') as f:
        files = f.read().splitlines()

    # Open the output file for writing
    with open(output_file_path, 'w') as out_f:
        for file_name in files:
            # Check for empty or invalid file names
            if not file_name.strip():
                print("Encountered an empty or invalid file name")
                continue

            # Check if the file exists
            if os.path.exists(file_name):
                # Read the content of the file
                with open(file_name, 'r') as file_f:
                    content = file_f.read()
                # Write the file name and content to the output file
                out_f.write(f"#File {file_name}:\n{content}\n\n\n\n\n\n\n")
            else:
                print(f"File not found: {file_name}")


# Paths to the input files
files_list_path = 'files'  # This should be the path to your "files" document
output_file_path = 'llm.txt'  # This is the path to the output file

# Create the llm.txt file with the specified content
create_llm_txt(files_list_path, output_file_path)
