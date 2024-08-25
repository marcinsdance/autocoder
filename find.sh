find . -type f ! -name ".env" | grep -vi venv | grep -vi idea | grep -vi llm | grep -vi ".git" | grep -vi pycache | grep -vi attachments | grep -vi processor.db | grep -vi debug
