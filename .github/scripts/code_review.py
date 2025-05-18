import os
import json
import requests
from openai import OpenAI

def get_pr_diff(pr_number):
    """Fetch the unified diff for the given pull request."""
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text


def analyze_code_changes(diff_text):
    """
    Generate the PR summary with sections:
    1️⃣ Change Summary (table)
    2️⃣ PR Overview (detailed narrative)
    3️⃣ File-level Changes (in-depth per-file breakdown)
    4️⃣ Recommendations/Improvements
    """
    # Parse diff into file stats
    files = {}
    added, deleted = set(), set()
    current = None
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split()
            path = parts[2][2:]
            current = path
            files[path] = {'adds': 0, 'removes': 0}
        elif current:
            if line.startswith('+') and not line.startswith('+++'):
                files[current]['adds'] += 1
            elif line.startswith('-') and not line.startswith('---'):
                files[current]['removes'] += 1
        if line.startswith('new file mode') and current:
            added.add(current)
        if line.startswith('deleted file mode') and current:
            deleted.add(current)

    # 1️⃣ Change Summary table
    summary_rows = []
    total_adds = total_removes = 0
    for path, stats in files.items():
        if path.startswith('.github/'): continue
        name = os.path.basename(path)
        adds, rem = stats['adds'], stats['removes']
        total = adds + rem
        total_adds += adds; total_removes += rem
        summary_rows.append(f"| `{name}` | {adds:>4} | {rem:>4} | {total:>5} |")
    change_summary = (
        "| File                 | +Adds | -Removes | ΔTotal |\n"
        "|:---------------------|:-----:|:--------:|:------:|\n"
        + "\n".join(summary_rows)
        + f"\n| **Total**            | {total_adds:>4} | {total_removes:>4} | {(total_adds+total_removes):>5} |"
    )

    # 2️⃣-4️⃣ Build prompt for LLM to elaborate overview and file details
    prompt = f"""## 🤖 Code Review Summary

### 1️⃣ Change Summary
{change_summary}

### 2️⃣ PR Overview
Based on the Change Summary above, write a detailed narrative covering:
- The primary goals of this PR, including refactoring aims, performance or security enhancements.
- The overall impact on code readability, maintainability, and potential breaking changes.
- Any additions or deletions of files and their significance.

### 3️⃣ File-level Changes
For each file listed above, provide an in-depth breakdown of specific changes, including:
- Method signature changes, renames, or extractions.
- Javadoc or comment additions/edits/removals.
- Null-safety or validation logic inserted or removed.
- Logging improvements or refactoring choices.
- ResponseEntity or other API contract adjustments.

### 4️⃣ Recommendations / Improvements
List actionable suggestions for further enhancement, such as:
- Adding null checks or guard clauses.
- Enhancing or adding unit tests targeting refactored code.
- Consolidating duplicated code into helper utilities.
- Updating documentation to reflect code changes.
"""

    # Debug preview
    print("PROMPT PREVIEW:\n", prompt[:1000], "...")

    # Call OpenAI API for elaboration
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a detailed, structured pull request reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def post_pr_comment(pr_number, comment):
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = { 'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json' }
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    resp = requests.post(url, headers=headers, json={'body': comment})
    resp.raise_for_status()
    return resp.json()


def main():
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)
    pr_number = event['pull_request']['number']
    diff_text = get_pr_diff(pr_number)
    summary = analyze_code_changes(diff_text)
    post_pr_comment(pr_number, summary)

if __name__ == "__main__":
    main()
