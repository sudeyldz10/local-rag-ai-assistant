def split_text(text, chunk_size=1000,overlap=100):
    chunks=[]
    start=0

    while start < len(text):
        end =start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start =end - overlap

    return chunks


def split_documents(documents):
    all_chunks = []

    for doc in documents:
        chunks=split_text(doc["text"])

        for chunk in chunks:
            all_chunks.append({"text": chunk, "source": doc["source"]})

    print(f"total {len(all_chunks)} chunk is created")
    return all_chunks


