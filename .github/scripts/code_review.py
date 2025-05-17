import os
import json
import requests
from openai import OpenAI

def get_pr_diff(pr_number):
    """Get the PR diff from GitHub API"""
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    url = f'https://api.github.com/repos/{repo}/pulls/{pr_number}'
    response = requests.get(url, headers=headers)
    return response.text

def analyze_code_changes(diff_text):
    """Analyze code changes using OpenAI API, excluding .github folder changes"""
    # Filter out changes from .github folder
    filtered_diff_lines = []
    current_file = None
    skip_current = False
    changed_files = set()
    added_lines = 0
    removed_lines = 0

    
    for line in diff_text.split('\n'):
        if line.startswith('diff --git'):
            current_file = line.split()[2][2:]  # Get "b/filename"
            skip_current = current_file.startswith('.github/')
            if not skip_current:
                file_name_only = os.path.basename(current_file)
                changed_files.add(file_name_only)
        elif not skip_current:
            if line.startswith('+') and not line.startswith('+++'):
                added_lines += 1
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines += 1
            filtered_diff_lines.append(line)
    
    filtered_diff = '\n'.join(filtered_diff_lines)
    
    # If there are no changes after filtering, return a message
    if not filtered_diff.strip():
        return "No changes found outside of the .github folder."
    
    # Determine number of points based on changes
    num_points = min(max(2, len(changed_files) + (added_lines + removed_lines) // 10), 8)
    
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    
    prompt = f"""As an AI pull request reviewer bot, your task is to provide a concise summary of the changes introduced in the following pull request diff. Focus on the key modifications, additions, and deletions in the code.

Present the summary clearly and neutrally, highlighting the main purpose and impact of the changes. Avoid providing detailed code reviews, suggestions, or opinions in this initial summary.

The summary should be easy for a human reviewer to quickly understand the scope of the PR.

```diff
{diff_text}
```

### Summary of Changes
1. **Removal or addition of scripts/files**: Describe specific files deleted or added with their paths.
2. **Workflow modifications**: Mention exact sections or steps changed in workflow YML files.
3. **Changes in <FileName>.java**: Under this heading, list exact code changes, such as method renames (e.g., `getAllHotels()` renamed to `fetchAllHotels()`), logging statement updates (e.g., changed `log.info` to `log.debug`), Javadoc modifications (e.g., removed `@return` tags in `getHotelList()`), added or removed parameters in methods, and any validation logic inserted or removed.
4. **Changes in <FileName>.java**: Similarly, for each Java file, specify the precise code differences: updated method signatures, validation checks added/removed, logging message formats changed, Javadoc edits, and any structural refactorings.

After this summary, include per-file sections:

<details>
  <summary>📄 &lt;FileName&gt;</summary>

  <br>

  **❌ Null Safety Issues**
  - Identify any NPE risks based on removed or absent null checks.

  **❌ Documentation Gaps**
  - Highlight Javadoc changes, such as missing `@param` or `@return`.

  **❌ Code Quality Observations**
  - Note duplicate logic, naming issues, or pattern misuse.

  **💡 Suggestions for Improvement**
  - Recommend adding null checks, improving naming, or adjusting logging levels.

</details>

Repeat for each file.

<details>
  <summary>🧾 Summary of Findings</summary>

  **✅ Files Reviewed**: {', '.join(sorted(changed_files)) or "None"}  
  **❌ Null Issues**: Summarize NPE risks across files  
  **❌ Missing Docs**: Summarize Javadoc removals or edits  
  **❌ Code Quality**: Summarize major quality concerns  
  **💡 Suggestions**: Overall improvement advice

</details>

Keep it professional and precise."""
    # ✅ DEBUG: Show prompt preview in GitHub Actions logs
    print("PROMPT PREVIEW START\n" + prompt[:1000] + "\nPROMPT PREVIEW END")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a code review assistant. Provide concise, technical analysis of code changes."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

def post_pr_comment(pr_number, comment):
    """Post a comment on the PR"""
    token = os.environ['GITHUB_TOKEN']
    repo = os.environ['GITHUB_REPOSITORY']
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f'https://api.github.com/repos/{repo}/issues/{pr_number}/comments'
    data = {'body': comment}
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def main():
    # Get PR number from GitHub event
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event = json.load(f)
    pr_number = event['pull_request']['number']

    # Get PR diff
    diff = get_pr_diff(pr_number)
    
    # Analyze changes
    analysis = analyze_code_changes(diff)
    
    # Format comment
    comment = f"""## 🤖 Code Review Bot Analysis

{analysis}

---
*This is an automated code review summary generated by AI.*"""
    
    # Post comment
    post_pr_comment(pr_number, comment)

if __name__ == "__main__":
    main()
