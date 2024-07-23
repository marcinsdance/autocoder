# Claude Automated Coding

Claude Automated Coding is an innovative tool that leverages the power of AI to automate coding tasks. It uses the Claude API and LangGraph to interpret coding tasks, modify code, and run tests automatically.

## Features

- Task interpretation using natural language processing
- Automated code modification based on task description
- Context-aware code changes
- Automatic test running after modifications
- Detailed error handling and reporting

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.7 or higher
- An Anthropic API key (for Claude API access)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/claude_automated_coding.git
   cd claude_automated_coding
   ```

2. Install the package:
   ```
   pip install .
   ```
   
   If you want to install it for development:
   ```
   pip install -e .
   ```

3. Verify the installation:
   ```
   which autocoder
   ```

4. You can now use the `autocoder` command from any location.
     ```
     autocoder "Your task description here"
     ```

Note: If you're using a virtual environment, make sure to activate it before installation and usage.
For system-wide installation (requires root privileges):
```
sudo pip install .
```
The tool will interpret the task, make the necessary code changes, run tests, and provide you with the results.

## Contributing

Contributions to Claude Automated Coding are welcome. Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- This project uses the Claude API by Anthropic
- LangGraph is used for workflow management

## Contact

If you have any questions or feedback, please open an issue on the GitHub repository.
