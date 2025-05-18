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
    2️⃣ PR Overview (elaborate paragraph)
    3️⃣ File-level Changes (detailed summaries)
    4️⃣ Recommendations / Improvements
    """
    import os
    # Parse diff to compute additions/removals per file
    files, added, deleted = {}, set(), set()
    current = None
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split(); path = parts[2][2:]
            current = path; files[path] = {'adds': 0, 'removes': 0}
        elif current:
            if line.startswith('+') and not line.startswith('+++'):
                files[current]['adds'] += 1
            if line.startswith('-') and not line.startswith('---'):
                files[current]['removes'] += 1
        if line.startswith('new file mode') and current:
            added.add(current)
        if line.startswith('deleted file mode') and current:
            deleted.add(current)

    # Build Change Summary table
    rows = []
    total_adds = total_removes = 0
    for path, stats in files.items():
        if path.startswith('.github/'): continue
        name = os.path.basename(path)
        adds, rem = stats['adds'], stats['removes']
        total = adds + rem
        total_adds += adds; total_removes += rem
        rows.append(f"| `{name}` | {adds:>5} | {rem:>7} | {total:>6} |")
    change_summary = (
        "| File                 | +Adds  | -Removes  | ΔTotal  |\n"
        "|:---------------------|:------:|:---------:|:-------:|\n"
        + "\n".join(rows)
        + f"\n| **Total**            | {total_adds:>5} | {total_removes:>7} | {(total_adds+total_removes):>6} |"
    )

        # Prepare LLM prompt to elaborate sections 2 & 3 based on diff
    prompt = f"""## 🤖 Code Review Summary

1️⃣ Change Summary
{change_summary}

2️⃣ PR Overview
Provide a detailed summary of the overall purpose and impact of these changes across all modified files. Explain why these changes were made and how they improve code quality, readability, and maintainability.

3️⃣ File-level Changes
For each file in the Change Summary, describe the specific modifications, additions, and deletions. Include concrete examples (e.g., method renames, Javadoc edits, null-safety fixes, validation logic changes).

4️⃣ Recommendations / Improvements
List actionable suggestions for further improvements, such as adding null checks, enhancing tests, consolidating duplicated logic, and updating documentation.

---
### Full Diff
```diff
{diff_text}
```
"""

    # Call OpenAI
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a detailed, structured pull request reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content[0].message.content


def post_pr_comment(pr_number, comment):
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    res = requests.post(url, headers=headers, json={'body': comment})
    res.raise_for_status()
    return res.json()


def main():
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)
    pr_number = event['pull_request']['number']
    diff = get_pr_diff(pr_number)
    summary = analyze_code_changes(diff)
    post_pr_comment(pr_number, summary)

if __name__ == "__main__":
    main()
