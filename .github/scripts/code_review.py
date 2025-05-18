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
    2️⃣ PR Overview (elaborate paragraph)
    3️⃣ File-level Changes (detailed summaries)
    4️⃣ Recommendations / Improvements
    """
    # Parse diff to compute additions/removals per file
    files = {}
    added, deleted = set(), set()
    current = None
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split()
            path = parts[2][2:]
            current = path
            files[path] = {'hunks': [], 'adds': 0, 'removes': 0}
        elif current:
            # collect hunk lines for diff snippets
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
        removes = stats['removes']
        total = adds + removes
        total_adds += adds
        total_removes += removes
        summary_rows.append(f"| `{name}` | {adds:>4} | {removes:>4} | {total:>5} |")

    change_summary = (
        "| File                 | +Adds | -Removes | ΔTotal |\n"
        "|:---------------------|:-----:|:--------:|:------:|\n"
        + "\n".join(summary_rows)
        + f"\n| **Total**            | {total_adds:>4} | {total_removes:>4} | {(total_adds+total_removes):>5} |"
    )

    # 2️⃣ PR Overview
    overview = []
    if added:
        overview.append(
            f"🆕 Added: {', '.join(os.path.basename(p) for p in sorted(added))}"
        )
    if deleted:
        overview.append(
            f"🗑️ Deleted: {', '.join(os.path.basename(p) for p in sorted(deleted))}"
        )
    modified = [p for p in files if p not in added and p not in deleted and not p.startswith('.github/')]
    if modified:
        overview.append(
            f"🔧 Modified: {', '.join(os.path.basename(p) for p in sorted(modified))}"
        )
    overview.append(
        "This PR simplifies controller logic, improves maintainability, and reduces redundant operations."
    )

    # 3️⃣ File-level Changes
    file_changes = []
    for path, stats in files.items():
        if path.startswith('.github/'): 
            continue
        name = os.path.basename(path)
        adds = stats['adds']
        removes = stats['removes']
        # extract first diff hunk snippet
        snippet = []
        for i, l in enumerate(stats['hunks']):
            if l.startswith('@@'):
                snippet = stats['hunks'][i:i+5]
                break
        snippet_text = "\n".join(snippet) if snippet else ""
        file_changes.append(
            f"- **{name}** (+{adds}/-{removes}): key changes below.\n```diff\n{snippet_text}\n```"
        )

    # 4️⃣ Recommendations / Improvements
    recommendations = [
        "• Add null checks for potential null returns.",
        "• Restore or enhance validation where removed.",
        "• Update Javadoc for all modified endpoints.",
        "• Consolidate duplicated logic into helper methods.",
        "• Add or update unit tests for refactored code paths."
    ]

    # Assemble comment
    comment = (
        "## 🤖 Code Review Summary\n\n"
        "### 1️⃣ Change Summary\n" + change_summary + "\n\n"
        "### 2️⃣ PR Overview\n" + "\n".join(overview) + "\n\n"
        "### 3️⃣ File-level Changes\n" + "\n".join(file_changes) + "\n\n"
        "### 4️⃣ Recommendations / Improvements\n" + "\n".join(recommendations)
    )

    # Debug preview
    print("PROMPT PREVIEW:\n", comment[:500], "...")

    # Call OpenAI API
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a detailed, structured PR reviewer."},
            {"role": "user", "content": comment}
        ]
    )
    return response.choices[0].message.content


def post_pr_comment(pr_number, comment):
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    res = requests.post(url, headers=headers, json={'body': comment})
    res.raise_for_status()
    return res.json()


def main():
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)
    pr_number = event['pull_request']['number']
    diff_text = get_pr_diff(pr_number)
    summary = analyze_code_changes(diff_text)
    post_pr_comment(pr_number, summary)

if __name__ == "__main__":
    main()
