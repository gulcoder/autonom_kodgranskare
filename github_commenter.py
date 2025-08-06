import os
import requests
from dotenv import load_dotenv
from git import Repo, GitCommandError
import tempfile
from openai import OpenAI
import re


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
API_BASE = "https://api.github.com"

def get_pull_request(repo_owner, repo_name, head_branch):
    url = f"{API_BASE}/repos/{repo_owner}/{repo_name}/pulls"
    params = {"head": f"{repo_owner}:{head_branch}", "state": "open"}
    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    prs = response.json()
    if prs:
        print(f"Found PR #{prs[0]['number']} for branch {head_branch}")
        return prs[0]
    else:
        print("No open PR found for this branch.")
        return None

def get_changed_files(pr):
    files_url = pr["url"] + "/files"
    response = requests.get(files_url, headers=HEADERS)
    response.raise_for_status()
    files = response.json()
    print(f"Found {len(files)} changed files in PR.")
    return files

def post_inline_comment(pr, file_path, body, line_position):
    comments_url = pr["comments_url"]
    comment = {
        "body": body,
        "path": file_path,
        "position": line_position,
        "commit_id": pr["head"]["sha"]
    }
    response = requests.post(comments_url, headers=HEADERS, json=comment)
    response.raise_for_status()
    print(f"Posted comment on {file_path} at position {line_position}")
    return response.json()

def analyze_patch_and_comment(pr, file):
    patch = file.get("patch")
    if not patch:
        return

    lines = patch.split("\n")
    diff_position = 0

    for i, line in enumerate(lines):
        diff_position += 1

        if line.startswith("+") and "print(" in line:
            suggestion = line.replace("print(", "logging.info(")
            diff_patch = f"```diff\n- {line[1:]}\n+ {suggestion[1:]}\n```"

            comment_body = (
                "Förslag: Byt ut `print` mot `logging.info` för bättre loggning.\n\n"
                f"{diff_patch}"
            )
            post_inline_comment(pr, file["filename"], comment_body, diff_position)

def get_pr_comments(pr):
    comments_url = pr["comments_url"]
    response = requests.get(comments_url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def check_for_refactor_signoff(pr):
    comments = get_pr_comments(pr)
    for comment in comments:
        if '/refactor sign-off' in comment["body"].lower():
            print("Trigger '/refactor sign-off' hittad i kommentar!")
            return True
    return False

def apply_fixup_commit(repo_path, pr_branch):
    """
    Går igenom alla .py-filer i repo, byter print() till logging.info(),
    gör en fixup-commit och pushar.
    """
    repo = Repo(repo_path)
    git = repo.git

    changed_files = []

    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                with open(full_path, "r") as f:
                    content = f.read()

                if "print(" in content:
                    print(f"Refaktorerar {file}...")
                    new_content = content.replace("print(", "logging.info(")
                    with open(full_path, "w") as f:
                        f.write(new_content)
                    rel_path = os.path.relpath(full_path, repo_path)
                    repo.git.add(rel_path)
                    changed_files.append(rel_path)


    if changed_files:
        try:
            git.commit("--fixup", "HEAD")
            git.push("origin", pr_branch)
            print("Fixup commit pushad!")
        except GitCommandError as e:
            print("Fel vid commit eller push:", e)
    else:
        print("Ingen kod att refaktorera.")


def analyze_code_with_responses_api(code_text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Du är en senior Python-granskare. Ge konkreta förbättringsförslag, gärna med diff-exempel."},
            {"role": "user", "content": f"Analysera denna Python-fil:\n\n{code_text}"}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content

def agent_static_analysis(code):
    return analyze_code_with_responses_api(code)  # Din funktion som använder chat.completions

def generate_diff_from_analysis(original_code, analysis):
    # Om analysen innehåller förslag att byta print() till logging.info()
    if "byt ut print(" in analysis.lower():
        new_code = original_code.replace("print(", "logging.info(")
        # Skapa diff-text (kan vara enklare form)
        diff = f"--- original\n+++ fixed\n@@ -1 +1 @@\n-{original_code}\n+{new_code}\n"
        return diff
    return ""


def agent_diff_generation(original_code, analysis):
    return generate_diff_from_analysis(original_code, analysis)



def main():
    repo_owner = "gulcoder"
    repo_name = "code-review-bot"
    pr_branch = "test-pr2"

    pr = get_pull_request(repo_owner, repo_name, pr_branch)
    if not pr:
        return
    
    files= get_changed_files(pr)


    if check_for_refactor_signoff(pr):
        repo_url = f"https://github.com/{repo_owner}/{repo_name}.git"
        repo_path = "./temp_repo"

        if not os.path.exists(repo_path):
            print("Klonar repo för fixup...")
            Repo.clone_from(repo_url, repo_path, branch=pr_branch)
        else:
            repo = Repo(repo_path)
            repo.git.checkout(pr_branch)
            repo.remotes.origin.pull()
        
        # Här läser vi in varje fil från det klonade repot och anropar Responses API
        for file in files:
            filename = file["filename"]
            full_path = os.path.join(repo_path, filename)

            if not os.path.exists(full_path):
                print(f"Filen {filename} finns inte i klonat repo, hoppar över.")
                continue

            with open(full_path, "r") as f:
                code = f.read()

            # Anropa Responses API med koden
            #analysis = analyze_code_with_responses_api(code)
            analysis = agent_static_analysis(code)
            print(f"Response från Responses API för {filename}:\n{analysis}\n")

            diff = agent_diff_generation(code, analysis)
            print(f"Genererad diff för {filename}:\n{diff}\n")

            if diff:
                # Enkel tillämpning av diff: ersätt print med logging.info
                new_code = code.replace("print(", "logging.info(")
                with open(full_path, "w") as f:
                    f.write(new_code)

            # TODO: Parsning och applicering av diff från 'analysis' till filen (kan vara nästa steg)

        
        apply_fixup_commit(repo_path, pr_branch)
    else:
        print("Ingen refactor sign-off, fortsätter med kommentarer...")

    
    for file in files:
        analyze_patch_and_comment(pr, file)

if __name__ == "__main__":
    main()


