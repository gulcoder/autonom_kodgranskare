import subprocess

def get_git_commits():
    result = subprocess.run(["git", "rev-list", "--reverse", "HEAD"], capture_output=True, text=True)
    return result.stdout.strip().split('\n')

def get_commit_message(commit_hash):
    result = subprocess.run(["git", "log", "-1", "--pretty=%B", commit_hash], capture_output=True, text=True)
    return result.stdout.strip()

def get_commit_diff(commit_hash):
    result = subprocess.run(["git", "show", commit_hash, "--unified=0", "--pretty=format:"], capture_output=True, text=True)
    return result.stdout.strip()

def extract_commit_texts():
    commits = get_git_commits()
    commit_texts = []
    for c in commits:
        msg = get_commit_message(c)
        diff = get_commit_diff(c)
        combined_text = f"Commit message:\n{msg}\n\nDiff:\n{diff}"
        commit_texts.append((c, combined_text))
    return commit_texts

if __name__ == "__main__":
    commits_data = extract_commit_texts()
    print(f"Extracted {len(commits_data)} commits")
    # Skriv ut första commit för test
    print(commits_data[0][1])
