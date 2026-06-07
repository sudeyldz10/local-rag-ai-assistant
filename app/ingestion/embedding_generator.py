def generate_document_embedding(docs, embedding_client):

    response = embedding_client.generate_embeddings(docs)
    return [item.embedding for item in response.data]

def generate_query_embedding(query, embedding_client):

    response = embedding_client.generate_embedding(query)

    return response.data[0].embedding

