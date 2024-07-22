import os
from .manifest_processor import ManifestProcessor

class FileManager:
   def __init__(self, project_directory):
       self.project_directory = project_directory
       self.manifest_processor = ManifestProcessor(project_directory)

   def read_file(self, file_path):
       full_path = os.path.join(self.project_directory, file_path)
       with open(full_path, 'r') as file:
           return file.read()

   def write_file(self, file_path, content):
       full_path = os.path.join(self.project_directory, file_path)
       with open(full_path, 'w') as file:
           file.write(content)

   def list_files(self):
       files = self.manifest_processor.process_manifest()
       return [os.path.relpath(f, self.project_directory) for f in files]

   def get_file_contents(self):
       files = self.list_files()
       return {file: self.read_file(file) for file in files}
