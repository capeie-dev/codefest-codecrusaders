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
    Generate a structured PR summary:
    1️⃣ Change Summary table
    2️⃣ PR Overview (with added/deleted files explanations)
    3️⃣ File-level Changes summaries
    4️⃣ Recommendations/Improvements
    """
    import os

    # Parse diff into file stats and detect additions/deletions
    files = {}
    added, deleted = set(), set()
    current = None
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split()
            path_b = parts[2][2:]
            current = path_b
            files[current] = {'hunks': [], 'adds': 0, 'removes': 0}
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

    # Build Change Summary table (base filenames only)
    summary_rows = []
    total_adds = total_removes = 0
    for path, stats in files.items():
        if path.startswith('.github/'):
            continue
        name = os.path.basename(path)
        adds, removes = stats['adds'], stats['removes']
        total = adds + removes
        total_adds += adds
        total_removes += removes
        summary_rows.append(f"| `{name}` | {adds:>5} | {removes:>7} | {total:>6} |")

    summary_table = (
        "| File                 | +Adds  | -Removes  | ΔTotal  |\n"
        "|:---------------------|:------:|:---------:|:-------:|\n"
        + "\n".join(summary_rows)
        + f"\n| **Total**            | {total_adds:>5} | {total_removes:>7} | {(total_adds+total_removes):>6} |"
    )

    # PR Overview bullets
    overview = []
    if added:
        files_added = ', '.join(f"`{os.path.basename(p)}`" for p in sorted(added))
        overview.append(f"🆕 Added files: {files_added} (new functionality or modules)")
    if deleted:
        files_deleted = ', '.join(f"`{os.path.basename(p)}`" for p in sorted(deleted))
        overview.append(f"🗑️ Deleted files: {files_deleted} (removed obsolete or refactored code)")
    modified = [p for p in files if p not in added and p not in deleted and not p.startswith('.github/')]
    if modified:
        files_mod = ', '.join(f"`{os.path.basename(p)}`" for p in sorted(modified))
        overview.append(f"🔧 Modified files: {files_mod}")

    # File-level summaries
    file_changes = []
    for path, stats in files.items():
        if path.startswith('.github/'):
            continue
        name = os.path.basename(path)
        adds, removes = stats['adds'], stats['removes']
        file_changes.append(f"- **{name}**: +{adds} / -{removes}. Summary of key changes...")

    # Recommendations
    recs = [
        "• Add null checks to guard service responses.",
        "• Reinstate or improve input validation where removed.",
        "• Update Javadoc for all modified public methods.",
        "• Consolidate duplicated logic into shared utilities.",
        "• Add or extend unit tests to cover new and changed logic."
    ]

    # Compose prompt
    prompt = f"""## 🤖 Code Review Summary

### 1️⃣ Change Summary
{summary_table}

### 2️⃣ PR Overview
" + "\n".join(overview) + "

### 3️⃣ File-level Changes
" + "\n".join(file_changes) + "

### 4️⃣ Recommendations / Improvements
" + "\n".join(recs) + """  

    # Debug
    print("PROMPT PREVIEW:\n", prompt)

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a concise PR review assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


def post_pr_comment(pr_number, comment):
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    resp = requests.post(url, headers=headers, json={'body': comment})
    resp.raise_for_status()
    return resp.json()


def main():
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)
    pr_number = event['pull_request']['number']
    diff = get_pr_diff(pr_number)
    comment = analyze_code_changes(diff)
    post_pr_comment(pr_number, comment)

if __name__ == "__main__":
    main()
