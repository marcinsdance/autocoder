import os


class FileManager:
    def __init__(self, project_directory):
        self.project_directory = project_directory

    def read_file(self, file_path):
        full_path = os.path.join(self.project_directory, file_path)
        with open(full_path, 'r') as file:
            return file.read()

    def write_file(self, file_path, content):
        full_path = os.path.join(self.project_directory, file_path)
        with open(full_path, 'w') as file:
            file.write(content)

    def list_files(self):
        return [f for f in os.listdir(self.project_directory) if os.path.isfile(os.path.join(self.project_directory, f))]
