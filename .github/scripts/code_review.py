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
    Generate a structured PR summary:
    1️⃣ Change Summary table
    2️⃣ Detailed PR Overview
    3️⃣ File-level Change Summaries
    4️⃣ Recommendations / Improvements
    """
    import os

    # Parse diff into per-file stats
    files, added, deleted = {}, set(), set()
    current = None
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split(); path = parts[2][2:]
            current = path; files[path] = {'hunks': [], 'adds': 0, 'removes': 0}
        elif current:
            files[current]['hunks'].append(line)
            if line.startswith('+') and not line.startswith('+++'):
                files[current]['adds'] += 1
            if line.startswith('-') and not line.startswith('---'):
                files[current]['removes'] += 1
        if line.startswith('new file mode') and current:
            added.add(current)
        if line.startswith('deleted file mode') and current:
            deleted.add(current)

    # 1️⃣ Change Summary table (base names)
    summary_rows, total_adds, total_removes = [], 0, 0
    for path, stats in files.items():
        if path.startswith('.github/'): continue
        name = os.path.basename(path)
        adds, rem = stats['adds'], stats['removes']
        total = adds + rem
        total_adds += adds; total_removes += rem
        summary_rows.append(f"| `{name}` | {adds:>4} | {rem:>4} | {total:>5} |")
    summary_table = (
        "| File | +Adds | -Removes | ΔTotal |\n"
        "|:-----|:-----:|:--------:|:------:|\n"
        + "\n".join(summary_rows)
        + f"\n| **Total** | {total_adds:>4} | {total_removes:>4} | {(total_adds+total_removes):>5} |"
    )

    # 2️⃣ Detailed PR Overview
    overview_lines = []
    if added:
        overview_lines.append(f"🆕 Added: {', '.join(os.path.basename(p) for p in sorted(added))}")
    if deleted:
        overview_lines.append(f"🗑️ Deleted: {', '.join(os.path.basename(p) for p in sorted(deleted))}")
    modified = [p for p in files if p not in added and p not in deleted and not p.startswith('.github/')]
    if modified:
        overview_lines.append(f"🔧 Modified: {', '.join(os.path.basename(p) for p in sorted(modified))}")
    overview_lines.append(f"This PR simplifies controller logic, improves maintainability, and removes redundant code.")

    # 3️⃣ File-level Change Summaries
    file_summaries = []
    for path, stats in files.items():
        if path.startswith('.github/'): continue
        name = os.path.basename(path)
        adds, rem = stats['adds'], stats['removes']
        # extract first hunk for context
        hunk = next((stats['hunks'][i:i+5] for i,l in enumerate(stats['hunks']) if l.startswith('@@')), [])
        snippet = '\n'.join(hunk) if hunk else ''
        file_summaries.append(
            f"- **{name}** (+{adds}/-{rem}): Summary of key changes.\n```diff\n{snippet}\n```"
        )

    # 4️⃣ Recommendations / Improvements
    recs = [
        "• Add null checks around service calls.",
        "• Reinstate input validations where removed.",
        "• Update Javadoc for public endpoints.",
        "• Consolidate duplicate logic into helper methods.",
        "• Enhance or add unit tests for changed code paths."
    ]

    # Assemble full comment
    comment = (
        "## 🤖 Code Review Summary\n\n"
        "### 1️⃣ Change Summary\n" + summary_table + "\n\n"
        "### 2️⃣ PR Overview\n" + "\n".join(overview_lines) + "\n\n"
        "### 3️⃣ File-level Changes\n" + "\n".join(file_summaries) + "\n\n"
        "### 4️⃣ Recommendations / Improvements\n" + "\n".join(recs)
    )

    # Debug logging
    print("PROMPT PREVIEW:\n", comment[:1000], "...)\n")

    # Call OpenAI
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a concise, structured PR reviewer."},
            {"role": "user", "content": comment}
        ]
    )
    return resp.choices[0].message.content


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
