#!/usr/bin/env python3

import os
import glob
import fnmatch

def is_excluded(path):
    # List of directories and patterns to always exclude
    exclude_patterns = [
        '.venv', '__pycache__', '*.pyc', '*.pyo', '*.pyd',
        '.git', '.idea', '.vscode', '*.egg-info',
        'build', 'dist', '.tox', '.pytest_cache'
    ]
    
    # Convert relative path to absolute path
    abs_path = os.path.abspath(path)
    
    # Check if the path or any of its parents match any exclude pattern
    path_parts = abs_path.split(os.sep)
    for i in range(len(path_parts)):
        current_path = os.sep.join(path_parts[:i+1])
        if any(fnmatch.fnmatch(os.path.basename(current_path), pattern) for pattern in exclude_patterns):
            return True
    
    return False

def process_manifest_in(manifest_file='MANIFEST.in'):
    print(f"Current working directory: {os.getcwd()}")
    print(f"Processing file: {manifest_file}")

    if not os.path.exists(manifest_file):
        print(f"Error: {manifest_file} not found in the current directory.")
        return

    included_files = set()
    excluded_files = set()

    with open(manifest_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            command = parts[0].lower()
            patterns = parts[1:]

            if command in ('include', 'recursive-include'):
                for pattern in patterns:
                    if command == 'include':
                        included_files.update(f for f in glob.glob(pattern) if not is_excluded(f))
                    else:  # recursive-include
                        for root, _, filenames in os.walk('.'):
                            if not is_excluded(root):
                                for filename in fnmatch.filter(filenames, pattern):
                                    path = os.path.join(root, filename)
                                    if not is_excluded(path):
                                        included_files.add(path)

            elif command in ('exclude', 'recursive-exclude'):
                for pattern in patterns:
                    if command == 'exclude':
                        excluded_files.update(glob.glob(pattern))
                    else:  # recursive-exclude
                        for root, _, filenames in os.walk('.'):
                            for filename in fnmatch.filter(filenames, pattern):
                                excluded_files.add(os.path.join(root, filename))

            elif command == 'global-include':
                for pattern in patterns:
                    for root, _, filenames in os.walk('.'):
                        if not is_excluded(root):
                            included_files.update(
                                os.path.join(root, f) for f in fnmatch.filter(filenames, pattern)
                                if not is_excluded(os.path.join(root, f))
                            )

            elif command == 'global-exclude':
                for pattern in patterns:
                    for root, _, filenames in os.walk('.'):
                        excluded_files.update(
                            os.path.join(root, f) for f in fnmatch.filter(filenames, pattern)
                        )

    final_files = sorted(included_files - excluded_files)

    print("\nFiles included based on MANIFEST.in:")
    for file in final_files:
        print(file)

    print(f"\nTotal files: {len(final_files)}")

if __name__ == "__main__":
    process_manifest_in()
