import re


def split_text(text, chunk_size=1000, overlap=100):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            for i in range(0, len(sentence), chunk_size):
                chunks.append(sentence[i:i + chunk_size])
            continue

        if len(current_chunk) + len(sentence) + 1 <= chunk_size:
            current_chunk = (current_chunk + " " + sentence).strip()
        else:
            chunks.append(current_chunk)

            overlap_text = current_chunk[-overlap:] if overlap else ""
            current_chunk = (overlap_text + " " + sentence).strip()

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def split_documents(documents):
    all_chunks = []

    for doc in documents:
        chunks = split_text(doc["text"])

        for chunk in chunks:
            if len(chunk.strip()) > 50:
                all_chunks.append({"text": chunk, "source": doc["source"]})

    print(f"total {len(all_chunks)} chunk is created")
    return all_chunks


