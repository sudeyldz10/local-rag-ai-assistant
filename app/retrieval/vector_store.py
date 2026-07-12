import math
import numpy as np

def cosine_similarity(A, B):
        dot_product = sum(x * y for x, y in zip(A, B))
        norm_A = math.sqrt(sum(x * x for x in A))
        norm_B = math.sqrt(sum(x * x for x in B))

        if norm_A == 0 or norm_B == 0:
             return 0.0
        return dot_product / (norm_A * norm_B)


def cosine_similarity_all(query_embedding, doc_embeddings):
    """
    Same math as cosine_similarity, but calculates the score against
    ALL documents in one go using NumPy instead of a Python loop.
    Returns a plain list of scores, in the same order as doc_embeddings.
    """
    query = np.array(query_embedding)
    docs = np.array(doc_embeddings)

    dot_products = docs @ query

    query_norm = np.linalg.norm(query)
    doc_norms = np.linalg.norm(docs, axis=1)

    doc_norms[doc_norms == 0] = 1e-10
    if query_norm == 0:
        query_norm = 1e-10

    scores = dot_products / (doc_norms * query_norm)
    return scores.tolist()