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
    Generate the PR summary with dynamic sections:
    1️⃣ Change Summary (table)
    2️⃣ PR Overview (dynamic narrative based on diff)
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
            # path_b is after a/ and b/
            path_b = parts[2][2:]
            current = path_b
            files[current] = {'adds': 0, 'removes': 0, 'hunks': []}
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

    # 1️⃣ Build Change Summary table
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

    # 2️⃣ Prepare dynamic prompt for the remaining sections
    prompt = (
        "## 🤖 Code Review Summary\n\n"
        "### 2️⃣ PR Overview\n"
        "Analyze the diff above and provide a concise summary of the PR’s objectives, including any added, deleted, or modified files, and the overall impact on functionality, performance, and maintainability.\n\n"
        "### 3️⃣ File-level Changes\n"
        "For each file listed in the Change Summary, detail the main modifications, additions, and deletions in bullet points. Include short code snippets from the diff to illustrate key changes.\n\n"
        "### 4️⃣ Recommendations / Improvements\n"
        "Based on the diff, suggest actionable improvements such as adding missing null checks, enhancing validation, refactoring repeated logic, and updating documentation or tests.\n\n"
        "### Full Diff\n"
        f"```diff\n{diff_text}\n```"
    )

    # Call OpenAI API
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a concise, structured PR reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    llm_output = response.choices[0].message.content

    # Prepend header and Change Summary table
    combined = (
        "## 🤖 Code Review Summary\n\n"
        "### 1️⃣ Change Summary\n"
        f"{change_summary}\n\n"
        + llm_output
    )
    return combined


def post_pr_comment(pr_number, comment):
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    response = requests.post(url, headers=headers, json={'body': comment})
    response.raise_for_status()
    return response.json()


def main():
    # Load event data and get PR number
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)
    pr_number = event['pull_request']['number']

    # Get diff and analyze
    diff_text = get_pr_diff(pr_number)
    summary = analyze_code_changes(diff_text)

    # Post comment
    post_pr_comment(pr_number, summary)

if __name__ == "__main__":
    main()
