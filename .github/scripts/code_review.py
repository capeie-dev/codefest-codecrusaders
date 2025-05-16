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
    
    prompt = f"""You are a code review assistant helping with GitHub pull requests.
    
    You are provided a unified diff of code changes. Analyze the changes and provide a structured, professional review grouped by file. Focus on clarity and actionable insights.
    
    ### Format your output like this:
    
    <details>
    <summary>📄 <FileName></summary>

    <br>
    
    **❌ Null Safety Issues**
    - Describe any null-related risks (write “None” if no issues)
    
    **❌ Documentation Gaps**
    - Mention missing or incomplete JavaDocs (e.g., @return, @param)
    
    **❌ Code Quality Observations**
    - Flag duplicated logic, bad naming, log misuse, poor patterns
    
    **💡 Suggestions for Improvement**
    - Recommend code simplifications, naming improvements, response handling fixes, or log formatting
    
    </details>
    
    Repeat this for each file.
    
    ---
    
    <details>
    <summary>📊 Summary of Changes</summary>
    
    - Files changed: {', '.join(sorted(changed_files)) or "None"}
    - Total lines added / removed: +{added_lines} / -{removed_lines}
    - Common changes may include: logging, validation, method structure, or documentation edits (adjust based on the analysis)
    - Impact area: Describe based on file types (e.g., Controller, Service, etc.)
    
    </details>
    
    <details>
    <summary>🧾 Summary of Findings</summary>
    
    **✅ Files Reviewed**: {', '.join(sorted(changed_files)) or "None"}  
    **❌ Null Issues**: For each file, summarize NPE-related risks  
    **❌ Missing Docs**: Which files/methods are missing JavaDocs  
    **❌ Code Quality**: Notable violations or risky changes  
    **💡 Suggestions**: Final optimization tips, naming clarifications, or logic improvements
    
    </details>
    
    Keep it professional and avoid repeating issues in multiple sections unless critical.
    
    Here is the diff to review:
    
    ```diff
    {filtered_diff}

    ```"""
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
