import os
import json
import subprocess
from openai import OpenAI
from dotenv import load_dotenv
import ast

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_unit_tests(code_text, filename, feedback):
    feedback_note = ""
    if filename in feedback:
        if feedback[filename]:
            feedback_note = "Föregående version av testen fick 👍."
        else:
            feedback_note = "Föregående version av testen fick 👎, förbättra testkvaliteten."

    prompt = (
        f"Du är en senior Python-utvecklare. Skriv ENBART fungerande Python-enhetstester "
        f"för filen `{os.path.basename(filename)}` med `unittest`. "
        f"Täck de viktigaste funktionerna. Ingen förklaring, ingen markdown. "
        f"{feedback_note}\n\nKod:\n{code_text}\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Du skriver enhetstester i Python."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Fel vid generering av test med GPT: {e}")
        return ""

def save_test_file(test_code, original_filename):
    try:
        ast.parse(test_code)
    except SyntaxError as e:
        print(f"Fel i genererad testkod för {original_filename}: {e}")
        print("Hoppar över denna fil.")
        return False

    test_dir = os.path.join("temp_repo", "tests")
    os.makedirs(test_dir, exist_ok=True)
    test_filename = f"test_{os.path.basename(original_filename)}"
    test_path = os.path.join(test_dir, test_filename)

    with open(test_path, "w") as f:
        f.write(test_code)

    print(f"✅ Sparade testfil: {test_path}")
    return True

def ensure_tests_package():
    test_dir = os.path.join("temp_repo", "tests")
    os.makedirs(test_dir, exist_ok=True)
    init_path = os.path.join(test_dir, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w") as f:
            f.write("# Init file for tests package\n")

def get_uncovered_files(threshold=75.0):
    repo_path = "temp_repo"
    original_cwd = os.getcwd()
    os.chdir(repo_path)

    print("🔄 Kör tester med coverage...")
    result = subprocess.run(
        ["coverage", "run", "-m", "unittest", "discover", "-s", "tests"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("❌ Fel vid testkörning med coverage:")
        print(result.stderr)
        os.chdir(original_cwd)
        return []

    print("🔄 Skapar coverage JSON-rapport...")
    result = subprocess.run(
        ["coverage", "json", "-o", "coverage.json"],
        capture_output=True, text=True
    )
    if result.returncode != 0 or not os.path.exists("coverage.json"):
        print("❌ Coverage.json hittades inte - inga tester körda eller coverage kunde inte samlas in.")
        os.chdir(original_cwd)
        return []

    try:
        with open("coverage.json", "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Kunde inte läsa coverage.json: {e}")
        os.chdir(original_cwd)
        return []

    uncovered = []
    for file, info in data.get("files", {}).items():
        percent = info.get("summary", {}).get("percent_covered", 100.0)
        if percent < threshold and file.endswith(".py"):
            uncovered.append((os.path.join(repo_path, file), percent))

    os.chdir(original_cwd)
    return uncovered

def load_feedback(filename="feedback.json"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_feedback(feedback_dict, filename="feedback.json"):
    with open(filename, "w") as f:
        json.dump(feedback_dict, f, indent=2)

def ask_for_feedback(test_file_path):
    while True:
        feedback = input(f"Tycker du att testet för {test_file_path} är bra? (👍/👎): ").strip()
        if feedback in ["👍", "👎"]:
            return feedback == "👍"
        else:
            print("Skriv '👍' för tumme-upp eller '👎' för tumme-ned.")

def auto_generate_tests_if_low_coverage(threshold=75.0):
    uncovered_files = get_uncovered_files(threshold)
    if not uncovered_files:
        print("✅ Coverage är tillräcklig. Inga tester behöver genereras.")
        return False, []

    feedback = load_feedback()
    changed_files = []

    for filepath, percent in uncovered_files:
        print(f"🔍 Genererar tester för {filepath} ({percent:.1f}%)")
        with open(filepath, "r") as f:
            code = f.read()

        test_code = generate_unit_tests(code, filepath, feedback)
        if save_test_file(test_code, filepath):
            print(f"Ber om feedback för {filepath}")
            is_good = ask_for_feedback(filepath)
            feedback[filepath] = is_good
            changed_files.append(filepath)

    save_feedback(feedback)

    print("🔁 Kör om coverage efter genererade tester...")
    subprocess.run(["coverage", "run", "-m", "unittest", "discover", "-s", "tests"])
    subprocess.run(["coverage", "report"], cwd="temp_repo")

    return True, changed_files

def main():
    print("🚀 Kör GPT-baserad testgenerator...")
    ensure_tests_package()
    generated, affected = auto_generate_tests_if_low_coverage()
    if generated:
        print("🧪 Genererade tester för:")
        for file in affected:
            print(f" - {file}")
    else:
        print("✅ Coverage OK – inga tester behövde genereras.")

if __name__ == "__main__":
    main()
