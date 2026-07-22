def generate_document_embeddings(docs, embedding_client):
    # Generates one embedding vector per document chunk (used once at ingestion time)
    embeddings = []
    total = len(docs)

    for i, doc in enumerate(docs, start=1):
        text = doc["text"].strip()
        if not text:
            # Skip empty chunks, nothing useful to embed
            continue

        response = embedding_client.generate_embedding(text)
        embeddings.append(response.data[0].embedding)

        # Print progress every 50 chunks so long ingestion runs aren't silent
        if i % 50 == 0 or i == total:
            print(f"Embedding progress: {i}/{total} chunks")

    return embeddings


def generate_query_embedding(query, embedding_client):
    # Embeds a single user query at search time (same model as document embeddings)
    response = embedding_client.generate_embedding(query)
    return response.data[0].embedding