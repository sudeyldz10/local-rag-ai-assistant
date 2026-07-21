def generate_document_embeddings(docs, embedding_client):
    embeddings = []
    total = len(docs)

    for i, doc in enumerate(docs, start=1):
        text = doc["text"].strip()
        if not text:
            continue

        response = embedding_client.generate_embedding(text)
        embeddings.append(response.data[0].embedding)

        if i % 50 == 0 or i == total:
            print(f"Embedding progress: {i}/{total} chunks")

    return embeddings

def generate_query_embedding(query, embedding_client):

    response = embedding_client.generate_embedding(query)

    return response.data[0].embedding

