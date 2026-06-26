def generate_document_embeddings(docs, embedding_client):

    embeddings=[]

    for doc in docs:
        text= doc["text"].strip()
        if not text:
            continue

        response = embedding_client.generate_embedding(text)
        embeddings.append(response.data[0].embedding)
    
    return embeddings

def generate_query_embedding(query, embedding_client):

    response = embedding_client.generate_embedding(query)

    return response.data[0].embedding

