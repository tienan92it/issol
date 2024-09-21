import argparse
import os
import logging
from .commands import list_issues, resolve_issue, generate_codebase_context
from .utils.github_utils import get_repo_info, github_client
from .utils.config_utils import setup_tokens
from .utils.codebase_utils import summarize_codebase

__version__ = "0.3.2"

def setup_logging(debug):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Setup tokens before parsing arguments
    github_token, anthropic_token = setup_tokens()

    parser = argparse.ArgumentParser(description="GitHub Claude Bot CLI Tool")
    parser.add_argument("-l", "--list", action="store_true", help="List all open issues")
    parser.add_argument("-r", "--resolve", type=int, help="Resolve a specific issue by number")
    parser.add_argument("-b", "--branch", default="main", help="Specify the branch to read code from (default: main)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-c", "--codebase-context", action="store_true", help="Generate codebase context")
    parser.add_argument("-v", "--version", action="store_true", help="Show the current version of issol")
    parser.add_argument("-s", "--summarize", action="store_true", help="Summarize the codebase")
    
    args = parser.parse_args()

    setup_logging(args.debug)

    if args.version:
        print(f"issol version {__version__}")
        return

    if args.codebase_context:
        generate_codebase_context.run()
        return

    repo_name = get_repo_info()
    logging.debug(f"Determined repo name: {repo_name}")
    logging.debug(f"GitHub token: {'Set' if github_token else 'Not set'}")
    logging.debug(f"Anthropic API key: {'Set' if anthropic_token else 'Not set'}")
    logging.debug(f"Using branch: {args.branch}")

    try:
        repo = github_client.get_repo(repo_name)
        logging.debug(f"Successfully accessed repository: {repo.full_name}")
    except Exception as e:
        logging.error(f"Error accessing repository: {str(e)}")
        if args.debug:
            logging.debug(f"Full error: {repr(e)}")
        return

    if args.list:
        list_issues.run(repo)
    elif args.resolve:
        resolve_issue.run(repo, args.resolve, args.branch)
    elif args.summarize:
        summary = summarize_codebase()
        print(summary)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()