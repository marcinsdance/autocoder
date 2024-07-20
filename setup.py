from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="claude_automated_coding",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An automated coding system using Claude API and LangGraph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/claude_automated_coding",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    install_requires=[
        "python-dotenv",
        "requests",
        "openai",
        "anthropic",
        "langgraph",
    ],
    entry_points={
        "console_scripts": [
            "claude-automated-coding=main:main",
        ],
    },
)
