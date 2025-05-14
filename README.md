# Code Review Bot

A GitHub Action-based code review bot that automatically analyzes pull requests using OpenAI's GPT-4 and provides a concise 5-point summary of the changes.

## Setup

1. Add the following secrets to your GitHub repository:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `GITHUB_TOKEN`: This is automatically provided by GitHub Actions

2. The bot will automatically run on all pull request events (when opened or synchronized).

## How it Works

1. When a pull request is created or updated, the GitHub Action is triggered
2. The bot fetches the PR diff using GitHub's API
3. The diff is analyzed using OpenAI's GPT-4
4. A 5-point summary is generated and posted as a comment on the PR

## Test Application

The repository includes a simple Python hello world application (`main.py`) that you can use to test the code review bot:

```python
from main import greet
print(greet("Your Name"))  # Will output: Hello, Your Name!
```

## Requirements

- Python 3.10 or higher
- Dependencies are listed in `requirements.txt`
