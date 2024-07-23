from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="autocoder",
    version="0.0.5",  # Updated to match version.txt
    author="Marcin Dancewicz",
    author_email="mdancewicz@gmail.com",
    description="An automated coding system using Claude API and LangGraph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/marcinsdance/autocoder",
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
            "autocoder=src.autocoder.autocoder:main",
        ],
    },
    scripts=['bin/autocoder'],  # Add this line to include the bin/autocoder script
)
