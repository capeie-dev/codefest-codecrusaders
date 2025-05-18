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
    Build and return a formatted summary comment including:
      1) Change Summary table (base filenames only)
      2) High-Level Change Categories
      3) Risk & Impact Summary table
      4) Per-file details with diff snippets
      5) Summary of Findings table
    """
    # Parse diff into per-file statistics
    files = {}
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

    # Filter out tooling or GitHub workflow files
    filtered = {f: stats for f, stats in files.items() if not f.startswith('.github/')}

    # Build Change Summary table with base filenames
    summary_rows = []
    total_adds = total_removes = 0
    for full_path, stats in filtered.items():
        base = os.path.basename(full_path)
        adds = stats['adds']
        removes = stats['removes']
        total = adds + removes
        total_adds += adds
        total_removes += removes
        summary_rows.append(f"| `{base}`{' ' * (26 - len(base))}| {adds:>4} | {removes:>7} | {total:>6} |")

    summary_table = (
        "| File                      | +Adds | -Removes | ΔTotal  |\n"
        "|:--------------------------|:-----:|:--------:|:-------:|\n"
        + "\n".join(summary_rows)
        + f"\n| **Total**{' ' * 17}| {total_adds:>4} | {total_removes:>7} | {(total_adds+total_removes):>6} |"
    )

    # High-Level Change Categories (placeholders to fill)
    categories = (
        "- **🗑️ Removed files**: file deletion notices\n"
        "- **🔄 Refactorings**: method renames or logic cleanup\n"
        "- **🐞 Bug fixes**: null checks added, logic corrections\n"
        "- **📝 Docs**: Javadoc or comment updates\n"
        "- **🔒 Security**: validation or permission enhancements"
    )

    # Risk & Impact Summary table
    risk_table = (
        "| ⚠️ Risk Areas          | Potential breaking changes               |\n"
        "| ✅ Test Coverage       | Covered by existing tests? (yes/no)      |"
    )

    # Per-file detailed sections
    file_sections = []
    for full_path, stats in filtered.items():
        base = os.path.basename(full_path)
        # Extract first diff hunk snippet
        snippet = []
        for idx, l in enumerate(stats['hunks']):
            if l.startswith('@@'):
                snippet = stats['hunks'][idx:idx+5]
                break
        snippet_text = "\n".join(snippet) if snippet else "*(no snippet available)*"

        section = f"""
<details>
<summary>📄 `{base}`</summary>

```diff
{snippet_text}
```

- **🆕 Additions**: describe new code added
- **🗑️ Deletions**: describe code removed
- **✏️ Modifications**: describe changes made
- **🔄 Renames**: describe renamed elements

- **❌ Null Safety**: note potential NPE risks or guards
- **❌ Docs**: note missing or incomplete comments
- **❌ Code Quality**: note duplication or poor patterns
- **✅ Tests**: note test coverage or missing tests
- **💡 Suggestions**: recommended improvements
</details>"""
        file_sections.append(section)

    # Summary of Findings table
    findings_table = (
        "| Category            | Observation                                  |\n"
        "|:--------------------|:---------------------------------------------|\n"
        "| ❌ Null Safety      | missing null checks or potential NPEs         |\n"
        "| ❌ Missing Docs     | removed or incomplete Javadoc comments        |\n"
        "| ❌ Code Quality     | duplication, naming issues, or removed logic  |\n"
        "| 💡 Suggestions      | summary recommendations                      |"
    )

    # Compile full prompt
    prompt = f"""## 🤖 Code Review Summary

### 1️⃣ Change Summary
{summary_table}

### 2️⃣ High-Level Change Categories
{categories}

### 3️⃣ Risk & Impact Summary
{risk_table}

### 4️⃣ Per-File Details
{''.join(file_sections)}

### 5️⃣ Summary of Findings
{findings_table}
"""

    # Debug: print prompt preview
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
    diff_text = get_pr_diff(pr_number)
    comment = analyze_code_changes(diff_text)
    post_pr_comment(pr_number, comment)

if __name__ == "__main__":
    main()
