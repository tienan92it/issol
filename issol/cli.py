import os
import argparse
from github import Github, GithubException
from anthropic import Anthropic
import base64
from git import Repo
from git.exc import InvalidGitRepositoryError
import sys
import re
import difflib

# Initialize GitHub and Anthropic clients
github_client = Github(os.environ.get("GITHUB_TOKEN"))
anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def get_repo_info():
    try:
        repo = Repo(os.getcwd(), search_parent_directories=True)
        remote_url = repo.remotes.origin.url
        if remote_url.startswith('https://'):
            # HTTPS URL format
            parts = remote_url.split('/')
            return f"{parts[-2]}/{parts[-1].rstrip('.git')}"
        else:
            # SSH URL format
            parts = remote_url.split(':')
            return parts[-1].rstrip('.git')
    except InvalidGitRepositoryError:
        print("Error: Not a git repository. Please run this command from within a git repository.")
        sys.exit(1)
    except Exception as e:
        print(f"Error determining repository info: {str(e)}")
        sys.exit(1)

def scan_codebase(repo, branch='main'):
    context = ""
    files_to_read = ["README.md", "codebase.md"]
    
    for file_name in files_to_read:
        try:
            file_content = repo.get_contents(file_name, ref=branch)
            decoded_content = base64.b64decode(file_content.content).decode('utf-8')
            context += f"File: {file_name} (branch: {branch})\n\n{decoded_content}\n\n"
        except Exception as e:
            print(f"Error reading {file_name} from branch {branch}: {str(e)}")
    
    return context

def extract_issue_content(body):
    print("Extracting issue content...")
    print(f"Raw issue body:\n{body}")
    
    # Initialize content dictionary
    content = {
        'problem_description': '',
        'desired_outcome': '',
        'affected_files': []
    }
    
    # Split the body into lines
    lines = body.split('\n')
    
    # Define possible section headers
    headers = {
        'problem_description': ['problem description', 'problem', 'description'],
        'desired_outcome': ['desired outcome', 'outcome', 'goal'],
        'affected_files': ['affected files', 'files']
    }
    
    current_section = None
    for line in lines:
        line = line.strip().lower()
        
        # Check if this line is a header
        for section, possible_headers in headers.items():
            if any(header in line for header in possible_headers):
                current_section = section
                break
        
        # If we're in a section, add content to that section
        if current_section:
            if current_section == 'affected_files':
                if ':' in line:  # Skip the header line
                    continue
                if line and not any(header in line for header in sum(headers.values(), [])):
                    content[current_section].append(line)
            else:
                if ':' in line:  # Skip the header line
                    continue
                content[current_section] += line + ' '
    
    # Strip any extra whitespace
    content['problem_description'] = content['problem_description'].strip()
    content['desired_outcome'] = content['desired_outcome'].strip()
    
    print("Extracted content:")
    print(content)
    
    return content

def process_issue(repo, issue, branch):
    print(f"Processing issue #{issue.number}: {issue.title}")
    print(f"Issue body:\n{issue.body}")
    
    if "AI: Generate Code" not in issue.title:
        print(f"Skipping issue #{issue.number}: Not marked for AI code generation")
        return

    issue_content = extract_issue_content(issue.body)
    
    if not issue_content['problem_description'] and not issue_content['desired_outcome']:
        print("Error: Could not extract problem description or desired outcome from the issue.")
        print("Please ensure the issue contains sections for 'Problem Description' and 'Desired Outcome'.")
        return

    codebase_context = scan_codebase(repo, branch)
    
    system_prompt = """You are an AI assistant tasked with generating code solutions based on GitHub issues. 
    Provide only the code changes required, without any explanations or comments.
    Your response should contain only valid code that can be directly inserted into the relevant files."""
    
    human_prompt = f"""Given the following context and requirements, generate the necessary code changes:

    Problem Description: {issue_content['problem_description']}
    Desired Outcome: {issue_content['desired_outcome']}
    Affected Files: {', '.join(issue_content['affected_files'])}

    Codebase Context (from branch '{branch}'):
    {codebase_context}

    Please provide only the code changes for each affected file. 
    Start each file's code with a line containing the file path, like this:
    # File: path/to/file.py
    [Only the code changes for this file]

    # File: path/to/another_file.py
    [Only the code changes for this file]

    Do not include any explanations, comments, or markdown formatting. 
    Provide only the actual code changes that should be applied to each file."""

    print("Sending prompt to AI:")
    print(human_prompt)

    generated_code = generate_code(system_prompt, human_prompt)
    
    print("Generated code:")
    print(generated_code)

    if not generated_code.strip():
        print("Error: No code was generated by the AI.")
        return

    create_pull_request(repo, issue, generated_code, branch, issue_content)

def create_branch_name(title):
    name = re.sub(r'[^a-zA-Z0-9\s-]', '', title.lower())
    name = re.sub(r'\s+', '-', name)
    return name[:50]

def get_file_content(repo, file_path, branch):
    try:
        file_content = repo.get_contents(file_path, ref=branch)
        return base64.b64decode(file_content.content).decode('utf-8')
    except:
        return ""
    
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
            if e.status == 422:  # Reference already exists
                print(f"Branch {new_branch_name} already exists. Trying a new name...")
                new_branch_name = f"{base_branch_name}-{counter}"
                counter += 1
            else:
                print(f"Error creating branch: {str(e)}")
                raise

    file_contents = {}
    current_file = None
    print("Processing generated code:")
    print(generated_code)
    
    # Split the generated code into sections for each file
    file_sections = re.split(r'# File: ', generated_code)
    for section in file_sections[1:]:  # Skip the first empty section
        lines = section.split('\n')
        file_path = lines[0].strip()
        content = '\n'.join(lines[1:])
        file_contents[file_path] = clean_generated_code(content)

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
    print(f"Processing {len(file_contents)} files...")
    for file_path, new_content in file_contents.items():
        print(f"\nProcessing file: {file_path}")
        original_content = get_file_content(repo, file_path, base_branch)
        
        print("AI suggested content (after cleaning):")
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

            diff = list(difflib.unified_diff(original_content.splitlines(), new_content.splitlines(), lineterm=''))
            pr_description += f"\nChanges in {file_path}:\n```diff\n" + '\n'.join(diff) + "\n```\n"
        else:
            print(f"No changes detected for {file_path}")

    if not changes_made:
        print("\nNo changes were made to any files. Skipping pull request creation.")
        print("Possible reasons:")
        print("1. The AI's suggested code is identical to the existing code.")
        print("2. The AI didn't generate any code changes for the specified files.")
        print("3. The issue description might not have provided enough information for the AI to suggest concrete changes.")
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

def generate_code(system_prompt, human_prompt):
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4000,
            temperature=0.1,
            system=system_prompt,
            messages=[
                {"role": "user", "content": human_prompt}
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error generating code: {str(e)}")
        return ""

def list_issues(repo):
    print("Open issues:")
    for issue in repo.get_issues(state='open'):
        print(f"#{issue.number}: {issue.title}")

def main():
    parser = argparse.ArgumentParser(description="GitHub Claude Bot CLI Tool")
    parser.add_argument("-l", "--list", action="store_true", help="List all open issues")
    parser.add_argument("-r", "--resolve", type=int, help="Resolve a specific issue by number")
    parser.add_argument("-b", "--branch", default="main", help="Specify the branch to read code from (default: main)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()

    repo_name = get_repo_info()
    if args.debug:
        print(f"Debug: Determined repo name: {repo_name}")
        print(f"Debug: GitHub token: {'Set' if os.environ.get('GITHUB_TOKEN') else 'Not set'}")
        print(f"Debug: Anthropic API key: {'Set' if os.environ.get('ANTHROPIC_API_KEY') else 'Not set'}")
        print(f"Debug: Using branch: {args.branch}")
        print(f"Debug: Using Claude model: claude-3-sonnet-20240320")

    try:
        repo = github_client.get_repo(repo_name)
        if args.debug:
            print(f"Debug: Successfully accessed repository: {repo.full_name}")
    except Exception as e:
        print(f"Error accessing repository: {str(e)}")
        if args.debug:
            print(f"Debug: Full error: {repr(e)}")
        return

    if args.list:
        list_issues(repo)
    elif args.resolve:
        try:
            issue = repo.get_issue(number=args.resolve)
            process_issue(repo, issue, args.branch)
        except Exception as e:
            print(f"Error processing issue: {str(e)}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
