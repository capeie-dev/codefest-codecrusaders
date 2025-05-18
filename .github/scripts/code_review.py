import os
import json
import requests
import re
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
    Sections are collapsible per <details> tag:
    1️⃣ Change Summary (table)
    2️⃣ PR Overview
    3️⃣ File-level Changes
    4️⃣ Recommendations / Improvements
    """
    # Parse diff into per-file stats
    files = {}
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
            files[current]['added'] = True
        if line.startswith('deleted file mode') and current:
            files[current]['deleted'] = True

    # Exclude .github folder changes
    files = {p: stats for p, stats in files.items() if not p.startswith('.github/')}

    # 1️⃣ Change Summary table
    summary_rows = []
    total_adds = total_removes = 0
    for path, stats in files.items():
        name = os.path.basename(path)
        adds, rem = stats['adds'], stats['removes']
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

    # Filter diff for prompt (exclude .github)
    filtered_diff = []
    skip = False
    for line in diff_text.splitlines():
        if line.startswith('diff --git'):
            parts = line.split()
            path_b = parts[2][2:]
            skip = path_b.startswith('.github/')
            if not skip:
                filtered_diff.append(line)
        else:
            if not skip:
                filtered_diff.append(line)
    filtered_diff_text = "\n".join(filtered_diff)

    # Build prompt for sections 2-4
    prompt = (
        "### 2️⃣ PR Overview\n"
        "Analyze the diff above and describe the primary objectives of this PR, noting any file additions or deletions, and summarizing the expected impact on functionality, performance, and maintainability.\n\n"
        "### 3️⃣ File-level Changes\n"
        "For each file in the Change Summary, provide bullet points detailing key modifications, additions, and deletions. Include brief code snippets from the diff for context.\n\n"
        "### 4️⃣ Recommendations / Improvements\n"
        "Based on the diff, suggest actionable recommendations such as adding null checks, improving validation, refactoring duplicated logic, and updating documentation or tests.\n\n"
        "### Full Diff\n"
        f"```diff\n{filtered_diff_text}\n```"
    )

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a concise, structured PR reviewer."},
            {"role": "user", "content": prompt}
        ]
    )
    body = response.choices[0].message.content

    # Split generated sections
    sections = {}
    for m in re.finditer(r"### (\d️⃣ [^\n]+)\n([\s\S]*?)(?=### \d️⃣|\Z)", body):
        sections[m.group(1)] = m.group(2).strip()

    # Build collapsible output
    output = []
    output.append("## 🤖 Code Review Summary")
    output.append("")

    # Section 1
    output.append("<details>")
    output.append("<summary>1️⃣ Change Summary</summary>")
    output.append("")
    output.append(change_summary)
    output.append("</details>")

    # Sections 2-4
    for sec in ["2️⃣ PR Overview", "3️⃣ File-level Changes", "4️⃣ Recommendations / Improvements"]:
        content = sections.get(sec, None)
        if content:
            output.append("")
            output.append("<details>")
            output.append(f"<summary>{sec}</summary>")
            output.append("")
            output.append(content)
            output.append("</details>")

    return "\n".join(output)


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
