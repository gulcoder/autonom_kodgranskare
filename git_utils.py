from git import Repo
import os
import shutil

def clone_repo(repo_url, branch_name, target_dir="temp_repo"):
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    return Repo.clone_from(repo_url, target_dir, branch=branch_name)
