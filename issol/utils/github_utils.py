import os
import sys
import fnmatch
import re
from github import Github, GithubException
from git import Repo
from git.exc import InvalidGitRepositoryError
from .config_utils import get_or_prompt_token
from .ignore_patterns import IGNORE_PATTERNS

def get_github_client():
    github_token = get_or_prompt_token('GITHUB_TOKEN', "Please enter your GitHub Personal Access Token")
    if github_token:
        return Github(github_token)
    else:
        print("Failed to obtain GitHub token. Exiting.")
        sys.exit(1)

github_client = get_github_client()

def get_repo_info():
    try:
        repo = Repo(os.getcwd(), search_parent_directories=True)
        remote_url = repo.remotes.origin.url
        if remote_url.startswith('https://'):
            parts = remote_url.split('/')
            repo_name = f"{parts[-2]}/{parts[-1].rstrip('.git')}"
        else:
            parts = remote_url.split(':')
            repo_name = parts[-1].rstrip('.git')
        
        current_branch = repo.active_branch.name
        print(f"Repository: {repo_name}")
        print(f"Current branch: {current_branch}")
        
        return repo_name, current_branch
    except InvalidGitRepositoryError:
        print("Error: Not a git repository. Please run this command from within a git repository.")
        sys.exit(1)
    except Exception as e:
        print(f"Error determining repository info: {str(e)}")
        sys.exit(1)

def parse_gitignore():
    gitignore_patterns = IGNORE_PATTERNS.copy()
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    gitignore_patterns.append(line)
    return gitignore_patterns

def should_ignore(path, gitignore_patterns):
    path = os.path.normpath(path)
    
    path_parts = path.split(os.sep)
    for i in range(len(path_parts)):
        partial_path = os.sep.join(path_parts[:i+1])
        if any(fnmatch.fnmatch(partial_path, pattern) for pattern in gitignore_patterns):
            return True
        
        if any(fnmatch.fnmatch(path_parts[i], pattern) for pattern in gitignore_patterns):
            return True
    
    return False

def get_file_content(file_path, gitignore_patterns):
    if should_ignore(file_path, gitignore_patterns):
        print(f"Ignoring file: {file_path}")
        return ""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return ""
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return ""

def scan_codebase(repo, branch):
    context = ""
    gitignore_patterns = parse_gitignore()
    
    print("Gitignore patterns:", gitignore_patterns)
    print(f"Scanning branch: {branch}")
    
    for root, dirs, files in os.walk('.', topdown=True):
        dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d), gitignore_patterns)]
        
        for file in files:
            file_path = os.path.join(root, file)
            if not should_ignore(file_path, gitignore_patterns):
                file_content = get_file_content(file_path, gitignore_patterns)
                if file_content:
                    context += f"File: {file_path} (branch: {branch})\n\n{file_content}\n\n"
            else:
                print(f"Ignoring file: {file_path}")
    
    return context

def extract_issue_content(body):
    print("Extracting issue content...")
    print(f"Raw issue body:\n{body}")
    
    content = {
        'problem_description': '',
        'desired_outcome': '',
        'affected_files': []
    }
    
    lines = body.split('\n')
    
    headers = {
        'problem_description': ['problem description', 'problem', 'description'],
        'desired_outcome': ['desired outcome', 'outcome', 'goal'],
        'affected_files': ['affected files', 'files']
    }
    
    current_section = None
    for line in lines:
        line = line.strip().lower()
        
        for section, possible_headers in headers.items():
            if any(header in line for header in possible_headers):
                current_section = section
                break
        
        if current_section:
            if current_section == 'affected_files':
                if ':' in line:
                    continue
                if line and not any(header in line for header in sum(headers.values(), [])):
                    content[current_section].append(line)
            else:
                if ':' in line:
                    continue
                content[current_section] += line + ' '
    
    content['problem_description'] = content['problem_description'].strip()
    content['desired_outcome'] = content['desired_outcome'].strip()
    
    print("Extracted content:")
    print(content)
    
    return content

def create_branch_name(title):
    name = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
    name = re.sub(r'\s+', '-', name)
    return name[:50]

def clean_generated_code(content):
    # Remove any lines that start with '#' (comments)
    content = re.sub(r'(?m)^#.*$', '', content)
    
    # Remove any markdown formatting
    content = re.sub(r'```[\w\s]*\n', '', content)
    content = content.replace('```', '')
    
    # Remove any lines that don't look like code (e.g., explanations)
    content = '\n'.join(line for line in content.split('\n') if re.match(r'^\s*[\w\(\)\{\}\[\]=\+\-\*/:<>!&|]+', line))
    
    # Remove empty lines
    content = '\n'.join(line for line in content.split('\n') if line.strip())
    
    return content

def create_pull_request(repo, issue, generated_code, base_branch, issue_content):
    print(f"Starting create_pull_request function for issue #{issue.number}")
    base_branch_name = f"fix-{issue.number}-{create_branch_name(issue.title)}"
    new_branch_name = base_branch_name
    counter = 1

    while True:
        try:
            repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=repo.get_branch(base_branch).commit.sha)
            print(f"Created new branch: {new_branch_name}")
            break
        except GithubException as e:
            if e.status == 422:
                print(f"Branch {new_branch_name} already exists. Trying a new name...")
                new_branch_name = f"{base_branch_name}-{counter}"
                counter += 1
            else:
                print(f"Error creating branch: {str(e)}")
                raise

    file_contents = {}
    print("Processing generated code:")
    print(generated_code)
    
    file_sections = re.split(r'# File: ', generated_code)
    for section in file_sections[1:]:
        lines = section.split('\n')
        file_path = lines[0].strip()
        content = '\n'.join(lines[1:])
        file_contents[file_path] = clean_generated_code(content)  # Apply cleaning here

    if not file_contents:
        print("Error: No file contents were extracted from the generated code.")
        return

    pr_description = f"""This pull request addresses issue #{issue.number}.

Problem Description:
{issue_content['problem_description']}

Desired Outcome:
{issue_content['desired_outcome']}

Changes made:
"""

    changes_made = False
    gitignore_patterns = parse_gitignore()
    print(f"Processing {len(file_contents)} files...")
    for file_path, new_content in file_contents.items():
        if should_ignore(file_path, gitignore_patterns):
            print(f"\nSkipping ignored file: {file_path}")
            continue
        
        print(f"\nProcessing file: {file_path}")
        original_content = get_file_content(file_path, gitignore_patterns)
        
        print("AI suggested content:")
        print(new_content)
        print("\nExisting content:")
        print(original_content)
        
        if new_content.strip() != original_content.strip():
            changes_made = True
            print(f"Changes detected for {file_path}")
            
            try:
                if original_content:
                    current_file = repo.get_contents(file_path, ref=new_branch_name)
                    repo.update_file(file_path, f"Fix #{issue.number}: Update {file_path}", new_content, current_file.sha, branch=new_branch_name)
                else:
                    repo.create_file(file_path, f"Fix #{issue.number}: Create {file_path}", new_content, branch=new_branch_name)
                print(f"Successfully updated/created {file_path}")
            except GithubException as e:
                print(f"Error updating/creating file {file_path}: {str(e)}")
                raise

            import difflib
            diff = list(difflib.unified_diff(original_content.splitlines(), new_content.splitlines(), lineterm=''))
            pr_description += f"\nChanges in {file_path}:\n```diff\n" + '\n'.join(diff) + "\n```\n"
        else:
            print(f"No changes detected for {file_path}")

    if not changes_made:
        print("\nNo changes were made to any files. Skipping pull request creation.")
        try:
            repo.get_git_ref(f"heads/{new_branch_name}").delete()
            print(f"Deleted branch {new_branch_name} as it contained no changes.")
        except GithubException:
            print(f"Failed to delete branch {new_branch_name}. You may want to delete it manually.")
        return

    pr_description += "\nThis code was generated automatically by an AI assistant. Please review carefully before merging."

    try:
        pr = repo.create_pull(
            title=f"Fix #{issue.number}: {issue.title}",
            body=pr_description,
            head=new_branch_name,
            base=base_branch
        )
        print(f"Created Pull Request: {pr.html_url}")
    except GithubException as e:
        print(f"Error creating pull request: {str(e)}")
        if e.status == 422:
            print("Possible reasons for this error:")
            print("  - A pull request between these branches already exists")
            print("  - The branch you're trying to create the PR from doesn't exist")
            print("  - There are no differences between the branches")
        raise