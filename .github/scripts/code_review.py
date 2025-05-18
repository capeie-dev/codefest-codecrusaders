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

    # Filter out non-code files
    filtered = {f:v for f,v in files.items() if not f.startswith('.github/')}

    # Build Change Summary table using base filenames
    summary_rows = []
    total_adds = total_removes = 0
    for full_path, stats in filtered.items():
        base = os.path.basename(full_path)
        adds = stats['adds']
        removes = stats['removes']
        total = adds + removes
        total_adds += adds
        total_removes += removes
        summary_rows.append(f"| `{base}` | {adds} | {removes} | {total} |")
    summary_table = (
        "| File | +Adds | -Removes | ΔTotal |\n"
        "|:-----|:-----:|:--------:|:------:|\n"
        + "\n".join(summary_rows)
        + f"\n| **Total** | {total_adds} | {total_removes} | {total_adds + total_removes} |"
    )

    # Construct per-file sections with diff snippet and classifications
    sections = []
    for full_path, stats in filtered.items():
        base = os.path.basename(full_path)
        # extract first hunk snippet
        snippet = []
        for idx, l in enumerate(stats['hunks']):
            if l.startswith('@@'):
                snippet = stats['hunks'][idx:idx+6]
                break
        snippet_text = "\n".join(snippet) if snippet else "*(no snippet available)*"
        section = f"""
<details>
  <summary>📄 `{base}`</summary>

  ```diff
{snippet_text}
  ```

  **Change Classification**
  - 🆕 Additions: ...
  - 🗑️ Deletions: ...
  - ✏️ Modifications: ...
  - 🔄 Renames: ...

  **❌ Null Safety & Validation**
  - ...

  **❌ Documentation & Comments**
  - ...

  **❌ Code Quality & Patterns**
  - ...

  **✅ Test & Coverage Notes**
  - ...

  **💡 Suggestions**
  - ...
</details>"""
        sections.append(section)

    # Build final LLM prompt
    prompt = f"""As an AI pull request reviewer bot, your tasks:

1) **Change Summary**: Provide a markdown table of file changes:

{summary_table}

2) **High-Level Change Categories**: Based on the diff below, list:
   - 🆕 New files
   - 🗑️ Removed files
   - 🔧 Refactorings (method renames, class extractions)
   - 🐞 Bug fixes (null checks added, off-by-one fixes)
   - 📝 Docs & comments (Javadoc or README updates)
   - 🔒 Security (input validation, guard clauses)

3) **Risk & Impact Summary**:
   - ⚠️ Risk areas (potential breaking changes)
   - ✅ Covered by tests

4) **Per-File Details**: For each file, include:
   - Tiny diff snippet (first hunk)
   - Change Classification
   - Null Safety & Validation
   - Documentation & Comments
   - Code Quality & Patterns
   - Test & Coverage Notes
   - 💡 Suggestions

Here is the full diff:

```diff
{diff_text}
```

{"".join(sections)}

5) **Summary of Findings**: Conclude with a table:

| Category            | Observation                                                 |
|:--------------------|:------------------------------------------------------------|
| ❌ Null Safety      | ...                                                         |
| ❌ Missing Docs     | ...                                                         |
| ❌ Code Quality     | ...                                                         |
| 💡 Suggestions      | ...                                                         |"""

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
    comment = f"## 🤖 Code Review Summary\n\n{analysis}\n\n*This comment was generated automatically.*"
    post_pr_comment(pr_number, comment)

if __name__ == "__main__":
    main()
