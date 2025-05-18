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
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def analyze_code_changes(diff_text):
    """
    Generate the PR summary with sections:
    1️⃣ Change Summary (table)
    2️⃣ PR Overview (dynamic narrative)
    3️⃣ File-level Changes (dynamic per-file breakdown)
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
            files[path] = {'adds': 0, 'removes': 0, 'hunks': []}
        elif current:
            files[current]['hunks'].append(line)
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
        if path.startswith('.github/'):
            continue
        name = os.path.basename(path)
        adds = stats['adds']
        rem = stats['removes']
        total = adds + rem
        total_adds += adds
        total_removes += rem
        summary_rows.append(f"| `{name}` | {adds:>4} | {rem:>4} | {total:>5} |")
    change_summary = (
        "| File                 | +Adds | -Removes | ΔTotal |\n"
        "|:---------------------|:-----:|:--------:|:------:|\n"
        + "\n".join(summary_rows)
        + f"\n| **Total**            | {total_adds:>4} | {total_removes:>4} | {(total_adds+total_removes):>5} |"
    )

    # Build dynamic prompt lines
    prompt_lines = [
        "## 🤖 Code Review Summary",
        "",
        # Note: Change Summary is prepended later, so omit from prompt_lines
        "### 2️⃣ PR Overview",
        "Analyze the diff above and provide a concise summary of the PR’s objectives, including any added, deleted, or modified files, and the overall impact on functionality, performance, and maintainability.",
        "",
        "### 3️⃣ File-level Changes",
        "For each file listed in the Change Summary, detail the main modifications, additions, and deletions in bullet points. Include short code snippets from the diff to illustrate key changes.",
        "",
        "### 4️⃣ Recommendations / Improvements",
        "Based on the diff, suggest actionable improvements such as adding missing null checks, enhancing validation, refactoring repeated logic, and updating documentation or tests.",
    ]
    prompt = "\n".join(prompt_lines)

    # Call OpenAI API
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a concise, structured PR reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    LLM_output = response.choices[0].message.content

    # Prepend Change Summary table to LLM output
    # Use triple-quoted string for the table
    combined = f"""### 1️⃣ Change Summary
{change_summary}

""" + LLM_output
    return combined


def post_pr_comment(pr_number, comment):
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
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
