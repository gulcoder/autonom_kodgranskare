import os
from radon.complexity import cc_visit
from bandit.core import config, manager

def get_python_files(repo_path):
    python_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def analyze_complexity(filepath):
    with open(filepath, "r") as f:
        code = f.read()
    return cc_visit(code)

def run_bandit(filepath):
    b_conf = config.BanditConfig()
    m = manager.BanditManager(b_conf, "file", True)
    m.discover_files([filepath])
    m.run_tests()
    return m.get_issue_list()
