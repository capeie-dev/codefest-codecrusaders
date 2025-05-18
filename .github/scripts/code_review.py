import os
import json
import requests
from openai import OpenAI

def get_pr_diff(pr_number):
    """Fetch the unified diff for the pull request."""
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
    Generate a review summary with:
    1) Change Summary table
    2) High-Level PR overview (including file additions/deletions)
    3) Per-file change summaries
    4) Recommendations/Improvements
    """
    import os

    # Parse diff into file stats
    files = {}
    added_files = []
    deleted_files = []
    current_file = None
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split()
            path_b = parts[2][2:]
            current_file = path_b
            files[current_file] = {'hunks': [], 'adds': 0, 'removes': 0}
        elif current_file:
            files[current_file]['hunks'].append(line)
            if line.startswith('+') and not line.startswith('+++'):
                files[current_file]['adds'] += 1
            elif line.startswith('-') and not line.startswith('---'):
                files[current_file]['removes'] += 1
        if line.startswith('new file mode') and current_file:
            added_files.append(current_file)
        if line.startswith('deleted file mode') and current_file:
            deleted_files.append(current_file)

    # Filter and compute summary rows
    summary_rows = []
    total_adds = total_removes = 0
    for full_path, stats in files.items():
        if full_path.startswith('.github/'):  # skip tooling
            continue
        base = os.path.basename(full_path)
        adds = stats['adds']; removes = stats['removes']
        total = adds + removes
        total_adds += adds; total_removes += removes
        summary_rows.append(f"| `{base}` | {adds:>4} | {removes:>4} | {total:>5} |")

    summary_table = (
        "| File | +Adds | -Removes | ΔTotal |\n"
        "|:-----|:-----:|:--------:|:------:|\n"
        + "\n".join(summary_rows)
        + f"\n| **Total** | {total_adds:>4} | {total_removes:>4} | {(total_adds+total_removes):>5} |"
    )

    # High-Level PR overview
    overview = []
    if added_files:
        names = ', '.join(os.path.basename(f) for f in added_files)
        overview.append(f"🆕 Added files: {names}")
    if deleted_files:
        names = ', '.join(os.path.basename(f) for f in deleted_files)
        overview.append(f"🗑️ Deleted files: {names}")
    overview.append("🔧 Modified files: " + ', '.join(os.path.basename(f) for f in files if f not in added_files + deleted_files))

    # Per-file summaries
    file_summaries = []
    for full_path, stats in files.items():
        if full_path.startswith('.github/'): continue
        base = os.path.basename(full_path)
        # summarize changes
        adds = stats['adds']; removes = stats['removes']
        summary = f"`{base}`: +{adds} / -{removes}."
        file_summaries.append(f"- {summary}")

    # Recommendations/Improvements placeholder
    recommendations = [
        "• Add null checks where service calls may return null.",
        "• Reinstate or enhance validation logic removed in refactor.",
        "• Update Javadoc comments for all public endpoints.",
        "• Consolidate duplicate logic into utility methods.",
        "• Add or update unit tests to cover modified logic."
    ]

    # Build prompt
    prompt = f"""## 🤖 Code Review Summary

**1️⃣ Change Summary**
{summary_table}

**2️⃣ PR Overview**
" + "\n".join(overview) + "\n
" +
"**3️⃣ File-level Changes**
" + "\n".join(file_summaries) + "\n
" +
"**4️⃣ Recommendations / Improvements**
" + "\n".join(recommendations) + """ 

    # Debug print
    print("PROMPT PREVIEW:\n", prompt)

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are a concise PR review bot."},
                  {"role": "user", "content": prompt}]
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
