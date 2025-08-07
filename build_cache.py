import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CACHE_FILE = "embedding_cache.json"

def get_embedding(text, model="text-embedding-3-small"):
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding

def build_embedding_cache():
    # Exempel: Läs commits eller textbitar från fil eller repo-historik
    commits = [
        {"sha": "0287623", "message": "Fixade bugg i funktion X"},
        {"sha": "a3f8d1e", "message": "La till ny feature Y"},
        {"sha": "9b7f3cd", "message": "Refaktorering av modul Z"},
    ]

    cache = {}
    for commit in commits:
        print(f"Embedding commit {commit['sha']}...")
        emb = get_embedding(commit["message"])
        cache[commit["sha"]] = emb

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)
    print(f"Cache byggd och sparad i {CACHE_FILE}")

if __name__ == "__main__":
    build_embedding_cache()
