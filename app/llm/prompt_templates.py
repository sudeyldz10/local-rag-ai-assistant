def built_rag_prompt(context):
    return (
        "You are a concise assistant.\n"
        "NEVER output reasoning.\n"
        "NEVER output <think>, </think>, <thinking>, or reasoning tags.\n"
        "Answer ONLY with the final answer.\n"
        "Answer in maximum 3 sentences. Do not repeat yourself.\n"
        "Use ONLY the provided context.\n"
        "If the answer is not in the context, say: "
        "'The provided context does not contain enough information.'\n\n"
        f"Context:\n{context}"
    )


    