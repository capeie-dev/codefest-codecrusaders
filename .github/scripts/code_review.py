import os
import json
import requests
from openai import OpenAI
import re

def get_pr_diff(pr_number):
    """Fetch the unified diff for the given PR number."""
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    url = f'https://api.github.com/repos/{repo}/pulls/{pr_number}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def analyze_code_changes(diff_text):
    """
    Build a prompt that:
    - Generates a Change Summary table with additions/removals per file
    - Embeds a small diff snippet for each file
    - Includes per-file issue sections and a final Summary of Findings table
    """
    # Parse diff into per-file hunks
    files = {}
    current_file = None
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split()
            path_b = parts[2][2:]
            current_file = path_b
            files[current_file] = {'hunks': [], 'adds': 0, 'removes': 0}
        elif current_file is not None:
            files[current_file].setdefault('hunks', []).append(line)
            if line.startswith('+') and not line.startswith('+++'):
                files[current_file]['adds'] += 1
            elif line.startswith('-') and not line.startswith('---'):
                files[current_file]['removes'] += 1

    # Filter out non-code files if desired
    filtered_files = {f:v for f,v in files.items() if not f.startswith('.github/')}

    # Build summary table rows
    total_adds = sum(v['adds'] for v in filtered_files.values())
    total_removes = sum(v['removes'] for v in filtered_files.values())
    summary_rows = []
    for fname, stats in filtered_files.items():
        total = stats['adds'] + stats['removes']
        summary_rows.append(f"| `{fname}` | {stats['adds']} | {stats['removes']} | {total} |")
    summary_table = (
    "| File | +Adds | -Removes | ΔTotal |
"
    "|:----|:-----:|:--------:|:------:|
" +
        "|:----|:-----:|:--------:|:------:|
" +
        "
".join(summary_rows) + "
" +
        f"| **Total** | {total_adds} | {total_removes} | {total_adds + total_removes} |"
    )

    # Create the detailed diff snippets
    file_sections = []
    for fname, stats in filtered_files.items():
        # find first hunk snippet
        lines = stats['hunks']
        snippet = []
        for i, l in enumerate(lines):
            if l.startswith('@@'):
                snippet = lines[i:i+6]
                break
                snippet_text = "
".join(snippet) if snippet else "*(no snippet available)*"
".join(snippet) if snippet else "*(no snippet available)*"
        section = f"""
<details>
  <summary>📄 `{fname}`</summary>

  ```diff
{snippet_text}
  ```

  **❌ Null Safety Risks**
  - …

  **❌ Documentation Gaps**
  - …

  **❌ Code Quality Observations**
  - …

  **💡 Suggestions for Improvement**
  - …
</details>
"""
        file_sections.append(section)

    # Build the final prompt for the LLM
    prompt = f"""As an AI pull request reviewer bot, your task is to:

1. Generate a **Change Summary** table for the PR diff:

{summary_table}

2. For each file, include:
   - A small diff snippet (first hunk)
   - Sections on Null Safety, Documentation Gaps, Code Quality, and Suggestions (fill in based on the diff)

3. Conclude with a **Summary of Findings** table summarizing:
   - ❌ Null Safety
   - ❌ Missing Docs
   - ❌ Code Quality
   - 💡 Suggestions

Here is the full diff:

```diff
{diff_text}
```

{"".join(file_sections)}

And then your **Summary of Findings** table below."""

    # Debug log
    print("PROMPT:
", prompt[:1000], "...
")

    # Call the OpenAI API
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a precise, concise pull request summarizer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def post_pr_comment(pr_number, comment):
    """Post the generated comment to the pull request."""
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f'https://api.github.com/repos/{repo}/issues/{pr_number}/comments'
    data = {'body': comment}
    resp = requests.post(url, headers=headers, json=data)
    resp.raise_for_status()
    return resp.json()

def main():
    # Load the PR event to get the number
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)
    pr_number = event['pull_request']['number']

    diff = get_pr_diff(pr_number)
    analysis = analyze_code_changes(diff)

    comment = f"## 🤖 Code Review Summary\n\n{analysis}\n\n*This comment was generated automatically.*"
    post_pr_comment(pr_number, comment)

if __name__ == "__main__":
    main()
