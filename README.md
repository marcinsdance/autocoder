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

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   ```
   
   On Windows, activate the virtual environment with:
   ```
   .venv\Scripts\activate
   ```
   
   On macOS and Linux, use:
   ```
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   - Copy the `.env.example` file to `.env`
   - Open the `.env` file and add your Anthropic API key:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```

## Usage

To use Claude Automated Coding, ensure your virtual environment is activated, then run the following command:

```
python src/autocoder.py "Your task description here"
```

For example:

```
python src/autocoder.py "Add a new function to calculate the factorial of a number in the math_utils.py file"
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
