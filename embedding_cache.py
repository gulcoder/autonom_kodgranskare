import sqlite3
import json

def create_db(db_path="embedding_cache.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS commit_embeddings (
            commit_hash TEXT PRIMARY KEY,
            text TEXT,
            embedding TEXT
        )
    ''')
    conn.commit()
    return conn

def save_embedding(conn, commit_hash, text, embedding):
    c = conn.cursor()
    embedding_json = json.dumps(embedding)
    c.execute('''
        INSERT OR REPLACE INTO commit_embeddings (commit_hash, text, embedding)
        VALUES (?, ?, ?)
    ''', (commit_hash, text, embedding_json))
    conn.commit()

def load_all_embeddings(conn):
    c = conn.cursor()
    c.execute("SELECT commit_hash, text, embedding FROM commit_embeddings")
    rows = c.fetchall()
    return [(h, t, json.loads(e)) for h, t, e in rows]
