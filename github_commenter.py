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

def agent_commit_logic_with_responses(repo_path, branch):
    from openai import OpenAI
    client = OpenAI()

    commit_prompt = (
        "Du är en Git-agent som skriver ett tydligt och kortfattat commit-meddelande "
        "för en fixup-commit baserat på ändringar i Python-kod."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": commit_prompt},
            {"role": "user", "content": "fixup commit changes"}
        ],
        temperature=0.1
    )

    commit_msg = response.choices[0].message.content.strip()

    repo = Repo(repo_path)
    git = repo.git

    try:
        git.commit("--fixup", "HEAD", m=commit_msg)
        git.push("origin", branch)
        print("✅ Fixup commit pushad med meddelande:", commit_msg)
    except GitCommandError as e:
        print("❌ Fel vid commit eller push:", e)

def post_pr_comment(repo_owner, repo_name, pr_number, message, github_token):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"body": message}
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        print("📝 Kommentar publicerad på PR.")
    else:
        print(f"❌ Kunde inte posta kommentar: {response.status_code} {response.text}")



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


def extract_diff_from_analysis(analysis_text):
    """
    Extraherar kodblock från analys, tex Python
    """
    code_blocks = re.findall(r"```diff\n(.*?)\n```", analysis_text, re.DOTALL)
    return code_blocks

def apply_diff_to_code(original_code, diff_text):
    """
    Enkel diff-applikation:
    För tillfället hanterar vi endast ett vanligt scenario: 
    ersätt 'print(' med 'logging.info(' om diffen innehåller det.
    """
    if "print(" in original_code and "logging.info(" in diff_text:
        return original_code.replace("print(", "logging.info(")
    return original_code

def agent_diff_generation(original_code, analysis):
    print("===ANALYSIS FROM GPT===")
    print(analysis)

    # Försök extrahera ny kod från analysen
    code_blocks = extract_diff_from_analysis(analysis)
    print(f"[DEBUG] Extracted code blocks: {code_blocks}")

    if code_blocks:
        new_code = code_blocks[0].strip()
        if new_code != original_code.strip():
            print("[DEBUG] Förbättrad kod extraherad och skiljer sig från originalet.")
            return "[FULL FILE REPLACEMENT]", new_code
        else:
            print("[DEBUG] Förbättrad kod är identisk med originalet.")
            return None, original_code

    # Fallback
    print("[DEBUG] Inga kodblock hittades. Försöker fallback...")
    if "byt ut print(" in analysis.lower():
        new_code = original_code.replace("print(", "logging.info(")
        return "[fallback]", new_code

    return None, original_code



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

        changed_any_files = False
        
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

            diff, new_code= agent_diff_generation(code, analysis)
            print(f"Genererad diff för {filename}:\n{diff}\n")

            if new_code and new_code != code:
                with open(full_path, "w") as f:
                    f.write(new_code)
                print(f"✏️ Uppdaterade {filename} med föreslagna ändringar.")
                changed_any_files = True
            else:
                print(f"Inga ändringar för {filename}.")
        if changed_any_files:
            print("\n Utför fixup-commit och push..")
            commit_msg = agent_commit_logic_with_responses(repo_path, pr_branch)

            post_pr_comment(
                repo_owner,
                repo_name,
                pr["number"],
                f"Fixup-commit skapad med meddelande:\n\n```{commit_msg}",
                GITHUB_TOKEN
            )
        else:
            print("Ingen fil ändrades - ingen fixup-commit behövs")

    else:
        print("💬 Ingen refactor-signoff hittad, lägger till inline-kommentarer.")
        for file in files:
            analyze_patch_and_comment(pr, file)

if __name__ == "__main__":
    main()

