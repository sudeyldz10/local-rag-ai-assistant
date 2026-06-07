from app.retrieval.vector_store import cosine_similarity
from app.config import top_k 




def find_relevant(query_embedding, doc_embeddings):
        scores = []

        for i, doc_emb in enumerate(doc_embeddings):
            score = cosine_similarity(query_embedding, doc_emb)

            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_k]