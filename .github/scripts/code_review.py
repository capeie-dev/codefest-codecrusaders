import os
import json
import requests
from openai import OpenAI

def get_pr_diff(pr_number):
    """Fetch the unified diff for the given PR number."""
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
    Build a prompt with:
      1) Change Summary table (base filenames only)
      2) High-Level Change Categories
      3) Risk & Impact Summary
      4) Per-File detailed sections
      5) Summary of Findings table
    """
    import os

    # Parse diff into per-file hunks and stats
    files = {}
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

    # Filter out non-code or tooling files
    filtered = {f: stats for f, stats in files.items() if not f.startswith('.github/')}

    # Build Change Summary table
    summary_rows = []
    total_adds = total_removes = 0
    for path, stats in filtered.items():
        base = os.path.basename(path)
        adds, removes = stats['adds'], stats['removes']
        total = adds + removes
        total_adds += adds
        total_removes += removes
        summary_rows.append(f"| `{base}` | {adds:>3} | {removes:>3} | {total:>3} |")

    summary_table = (
        "| File                      | +Adds | -Removes | ΔTotal |\n"
        "|:--------------------------|:-----:|:--------:|:------:|\n"
        + "\n".join(summary_rows)
        + f"\n| **Total**{' ' * 17}| {total_adds:>3} | {total_removes:>3} | {(total_adds+total_removes):>3} |"
    )

    # High-Level Change Categories (placeholders)
    categories = (
        "- **🗑️ Removed files**: ...\n"
        "- **🔄 Refactorings**: ...\n"
        "- **🐞 Bug fixes**: ...\n"
        "- **📝 Docs**: ...\n"
        "- **🔒 Security**: ..."
    )

    # Risk & Impact Summary
    risk_table = (
        "| ⚠️ Risk areas       | ... potential breaking changes          |\n"
        "| ✅ Test coverage    | ... no direct tests                     |"
    )

    # Per-File Details sections
    sections = []
    for path, stats in filtered.items():
        base = os.path.basename(path)
        # extract first hunk snippet
        snippet = []
        for i, l in enumerate(stats['hunks']):
            if l.startswith('@@'):
                snippet = stats['hunks'][i:i+5]
                break
        snippet_text = "\n".join(snippet) if snippet else "*(no snippet available)*"

        section = f"""
<details>
<summary>📄 `{base}`</summary>

```diff
{snippet_text}
```

- **🆕 Additions**: ...
- **🗑️ Deletions**: ...
- **✏️ Modifications**: ...
- **🔄 Renames**: ...

- **❌ Null Safety**: ...
- **❌ Docs**: ...
- **❌ Code Quality**: ...
- **✅ Tests**: ...
- **💡 Suggestions**: ...
</details>"""
        sections.append(section)

    # Summary of Findings table
    findings_table = (
        "| Category         | Observation                               |\n"
        "|:-----------------|:------------------------------------------|\n"
        "| ❌ Null Safety   | ...                                       |\n"
        "| ❌ Missing Docs  | ...                                       |\n"
        "| ❌ Code Quality  | ...                                       |\n"
        "| 💡 Suggestions   | ...                                       |"
    )

    # Compile final prompt
    prompt = f"""## 🤖 Code Review Summary

### 1️⃣ Change Summary
{summary_table}

### 2️⃣ High-Level Change Categories
{categories}

### 3️⃣ Risk & Impact Summary
{risk_table}

### 4️⃣ Per-File Details
{''.join(sections)}

### 5️⃣ Summary of Findings
{findings_table}
"""

    # Debug output
    print("PROMPT PREVIEW:\n", prompt[:1000], "...")

    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a precise, concise PR summarizer."},
            {"role": "user", "content": prompt}
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
    resp = requests.post(url, headers=headers, json={'body': comment})
    resp.raise_for_status()
    return resp.json()


def main():
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)
    pr_number = event['pull_request']['number']
    diff = get_pr_diff(pr_number)
    analysis = analyze_code_changes(diff)
    post_pr_comment(pr_number, analysis)

if __name__ == "__main__":
    main()
