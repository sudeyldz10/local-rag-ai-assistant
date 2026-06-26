import json
import os

def save_embeddings(chunks, embeddings, path="vector/embeddings.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "chunks": chunks,
        "embeddings": embeddings
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"Embeddings is saved: {path}")

def load_embeddings(path="vector/embeddings.json"):
    if not os.path.exists(path):
        return None, None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Embeddings are downloaded: {path}")
    return data["chunks"], data["embeddings"]