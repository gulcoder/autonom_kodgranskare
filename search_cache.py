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

def cosine_similarity(vec1, vec2):
    import math
    dot = sum(a*b for a,b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a*a for a in vec1))
    norm2 = math.sqrt(sum(b*b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)

def search_cache(query, top_k=3):
    if not os.path.exists(CACHE_FILE):
        print(f"Ingen cachefil {CACHE_FILE} hittades.")
        return []

    with open(CACHE_FILE, "r") as f:
        cache = json.load(f)

    query_emb = get_embedding(query)

    scores = []
    for sha, emb in cache.items():
        score = cosine_similarity(query_emb, emb)
        scores.append((sha, score))

    scores.sort(key=lambda x: x[1], reverse=True)

    return scores[:top_k]

if __name__ == "__main__":
    query = input("Skriv din sökfråga: ")
    results = search_cache(query)
    print("Top matchande commits:")
    for sha, score in results:
        print(f"{sha} (similaritet: {score:.4f})")
