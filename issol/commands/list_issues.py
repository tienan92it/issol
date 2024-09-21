def run(repo):
    print("Open issues:")
    for issue in repo.get_issues(state='open'):
        print(f"#{issue.number}: {issue.title}")