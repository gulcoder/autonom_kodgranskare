from git_utils import clone_repo
from analyzer import get_python_files, analyze_complexity, run_bandit
from openai_utils import analyze_code_with_gpt
from radon.complexity import cc_rank

def main():
    repo_url = "https://github.com/gulcoder/code-review-bot.git"
    pr_branch = "main"

    repo = clone_repo(repo_url, pr_branch)
    repo_path = repo.working_dir

    python_files = get_python_files(repo_path)

    for file in python_files:
        with open(file, "r") as f:
            code = f.read()

        print(f"\nAnalyserar {file}...")

        # GPT-4 feedback
        feedback = analyze_code_with_gpt(code, file)
        print("--- GPT-4 Feedback ---")
        print(feedback)

        # Komplexitet
        print("--- Komplexitet (Radon) ---")
        complexity = analyze_complexity(file)
        for item in complexity:
            print(f"{item.name}: {item.complexity} ({cc_rank(item.complexity)})")

        # Säkerhetsproblem
        print("--- Säkerhet (Bandit) ---")
        issues = run_bandit(file)
        for issue in issues:
            print(f"{issue.test_id} - {issue.text}")

if __name__ == "__main__":
    main()
