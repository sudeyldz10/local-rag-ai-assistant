import sqlite3
import json
import os


def save_embeddings(chunks, embeddings, path="vector/embeddings.db"):
    # Persist chunks + their embeddings to a local SQLite file (so we don't re-embed on every launch)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    cursor.execute("""
        Create table if not exists documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            source TEXT,
            embedding TEXT
        )
    """)

    # Clear old rows first, this always stores a fresh full snapshot rather than appending
    cursor.execute("delete from documents")

    for chunk, embedding in zip(chunks, embeddings):
        # Embedding is stored as a JSON string since SQLite has no native vector/array type
        cursor.execute(
            "INSERT INTO documents (text, source, embedding) VALUES (?, ?, ?)",
            (chunk["text"], chunk["source"], json.dumps(embedding))
        )

    conn.commit()
    conn.close()
    print(f"embedding saved: {path}")


def load_embeddings(path="vector/embeddings.db"):
    # Load previously saved chunks + embeddings, avoids expensive re-embedding on startup
    if not os.path.exists(path):
        return None, None

    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("select text, source, embedding from documents")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return None, None

    chunks = []
    embeddings = []
    for row in rows:
        chunks.append({"text": row[0], "source": row[1]})
        # Convert the JSON string back into a Python list of floats
        embeddings.append(json.loads(row[2]))

    print(f"Embeddings loaded: {path}")
    return chunks, embeddings