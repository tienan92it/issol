from ..utils.github_utils import extract_issue_content, create_pull_request, scan_codebase, get_repo_info
from ..utils.ai_utils import generate_code

def run(repo, issue_number, branch):
    try:
        issue = repo.get_issue(number=issue_number)
        process_issue(repo, issue, branch)
    except Exception as e:
        print(f"Error processing issue: {str(e)}")

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