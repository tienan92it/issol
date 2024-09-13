# issol - AI-Powered GitHub Issue Solver

issol (Issue Solver) is a command-line tool that uses AI to automatically generate code solutions for GitHub issues. It integrates with GitHub repositories and leverages the power of large language models to propose code changes based on issue descriptions.

## Short Description

issol streamlines the process of addressing GitHub issues by:
1. Reading issue details from a specified GitHub repository
2. Using AI to generate code solutions
3. Creating pull requests with the proposed changes

This tool is designed to assist developers in quickly addressing simple to moderate complexity issues, reducing development time and increasing productivity.

## Installation

To install issol, follow these steps:

1. Ensure you have Python 3.6 or higher installed on your system.

2. Clone the repository:
   ```
   git clone https://github.com/yourusername/issol.git
   cd issol
   ```

3. Install the required dependencies:
   ```
   pip install -e .
   ```

4. Set up your environment variables:
   ```
   export GITHUB_TOKEN=your_github_token
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

   Note: You'll need to obtain a GitHub personal access token and an Anthropic API key to use this tool.

## How It Works

issol operates in the following steps:

1. **Issue Selection**: 
   - Run `issol -l` to list all open issues in the repository.
   - Choose an issue to resolve by its number.

2. **Issue Processing**:
   - The tool reads the selected issue's details, including the problem description, desired outcome, and affected files.
   - It also scans the repository's codebase (focusing on README.md and codebase.md) to provide context to the AI.

3. **AI Code Generation**:
   - The issue details and codebase context are sent to the AI (Claude model) as a prompt.
   - The AI generates code changes for each affected file.

4. **Code Cleaning**:
   - The generated code is cleaned to remove any non-code content, ensuring only actual code changes remain.

5. **Pull Request Creation**:
   - A new branch is created based on the issue title.
   - The cleaned code changes are applied to the affected files in this new branch.
   - A pull request is created with the changes, including a description of the problem and the desired outcome.

6. **Review and Merge**:
   - Developers can review the generated pull request, make any necessary adjustments, and merge the changes if satisfactory.

## Usage

To use issol, navigate to your GitHub repository's directory and run:

```
issol -r <issue_number> [-b <branch_name>]
```

Options:
- `-r, --resolve`: Specify the issue number to resolve.
- `-b, --branch`: (Optional) Specify the base branch to work from (default is 'main').
- `-l, --list`: List all open issues in the repository.
- `-d, --debug`: Enable debug mode for more detailed output.

Example:
```
issol -r 5 -b feature-branch
```

This command will attempt to resolve issue #5, creating a new branch based on 'feature-branch'.

## Notes

- The AI-generated code should always be reviewed before merging.
- The tool works best with well-described issues that clearly state the problem and desired outcome.
- Ensure your GitHub token has the necessary permissions to create branches and pull requests.

## Troubleshooting

If you encounter any issues:
1. Ensure your environment variables are correctly set.
2. Check that your GitHub token has the required permissions.
3. Verify that the issue description follows the expected format (Problem Description, Desired Outcome, Affected Files).
4. Run the command with the `-d` flag for more detailed debug information.

For any persistent issues or feature requests, please open an issue in the issol repository.