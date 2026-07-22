# Foundry Local model names (must match models pulled/available locally)
embedding_model_name = "qwen3-embedding-0.6b"
chat_model_name = "qwen3-4b"

# How many chunks to actually pass to the LLM as context
top_k = 3
# How many candidates to pull before filtering/re-ranking down to top_k
retrieval_candidate_k = 10

# Minimum combined (BM25 + semantic) score for a chunk to be considered relevant
min_score_threshold = 0.55
# Minimum confidence before the assistant treats an answer as reliable
min_confidence_score = 0.60
# Used to compare a chunk's score relative to the top result's score
relative_score_ratio = 0.90

# Hybrid search weighting: must sum to 1.0 (50/50 keyword vs meaning-based matching)
bm25_weight = 0.5
semantic_weight = 0.5

# Cross-encoder re-ranking (using a public model for re-ranking)
enable_reranker = True
cross_encoder_model = "cross-encoder/qnli-distilroberta-base"