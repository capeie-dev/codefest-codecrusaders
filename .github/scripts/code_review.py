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
    Generate a structured PR summary with dynamic content:
    1️⃣ Change Summary (table of additions/removals per file)
    2️⃣ PR Overview (model-generated narrative based on diff)
    3️⃣ File-level Changes (model-generated breakdown)
    4️⃣ Recommendations/Improvements (model-generated suggestions)
    """
    import os

    # Parse diff into per-file stats, skip .github folder
    files = {}
    current = None
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split()
            path_b = parts[2][2:]
            current = path_b
            files[path_b] = {'adds': 0, 'removes': 0, 'hunks': []}
        elif current:
            files[current]['hunks'].append(line)
            if line.startswith('+') and not line.startswith('+++'):
                files[current]['adds'] += 1
            elif line.startswith('-') and not line.startswith('---'):
                files[current]['removes'] += 1
        if line.startswith('new file mode') and current:
            # track file additions
            files[current]['added'] = True
        if line.startswith('deleted file mode') and current:
            # track file deletions
            files[current]['deleted'] = True

    # Exclude .github paths
    files = {p: stats for p, stats in files.items() if not p.startswith('.github/')}

    # 1️⃣ Build Change Summary table
    summary_rows = []
    total_adds = total_removes = 0
    for path, stats in files.items():
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

    # Prepare dynamic prompt (sections 2-4)
    prompt = (
        "### 2️⃣ PR Overview\n"
        "Analyze the diff above and describe the primary objectives of this PR, noting any file additions or deletions, and summarizing the expected impact on functionality, performance, and maintainability.\n\n"
        "### 3️⃣ File-level Changes\n"
        "For each file in the Change Summary, provide bullet points detailing key modifications, additions, and deletions. Include brief code snippets from the diff for context.\n\n"
        "### 4️⃣ Recommendations / Improvements\n"
        "Based on the diff, suggest actionable recommendations such as adding null checks, improving validation, refactoring duplicated logic, and updating documentation or tests.\n\n"
        "### Full Diff\n"
        f"```diff\n{diff_text}\n```"
    )

    # Call OpenAI to generate sections 2-4
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a concise, structured PR reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    body = response.choices[0].message.content

    # Prepend header and Change Summary table
    combined = (
        "## 🤖 Code Review Summary\n\n"
        "### 1️⃣ Change Summary\n"
        f"{change_summary}\n\n"
        + body
    )
    return combined


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
    pr_num = event['pull_request']['number']
    diff = get_pr_diff(pr_num)
    summary = analyze_code_changes(diff)
    post_pr_comment(pr_num, summary)

if __name__ == "__main__":
    main()
