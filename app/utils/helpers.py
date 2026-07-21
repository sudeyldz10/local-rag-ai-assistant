import re

def clean_answer(full_answer):
    """Remove <think>, <thinking>, and other thinking tags from LLM output."""
    # Convert to string if needed
    full_answer = str(full_answer) if full_answer else ""
    
    # Remove incomplete think tags at the start
    if "<think>" in full_answer and "</think>" not in full_answer:
        full_answer = full_answer.split("<think>")[0]
    if "<thinking>" in full_answer and "</thinking>" not in full_answer:
        full_answer = full_answer.split("<thinking>")[0]
    
    # Remove complete think/thinking blocks (case-insensitive)
    full_answer = re.sub(r"<\s*think\s*>.*?<\s*/\s*think\s*>", "", full_answer, flags=re.DOTALL | re.IGNORECASE)
    full_answer = re.sub(r"<\s*thinking\s*>.*?<\s*/\s*thinking\s*>", "", full_answer, flags=re.DOTALL | re.IGNORECASE)

    # Remove any remaining standalone think/thinking tags (e.g. stray <think>, </think>)
    full_answer = re.sub(r"<\s*/?\s*(think|thinking)\s*>", "", full_answer, flags=re.IGNORECASE)

    # Remove lines that start with 'Thought:' or 'Thoughts:' (common internal reasoning prefixes)
    full_answer = re.sub(r"(?im)^\s*thoughts?:.*$", "", full_answer)
    
    # Remove any other thought/analysis tags
    full_answer = re.sub(r"<\s*analysis\s*>.*?<\s*/\s*analysis\s*>", "", full_answer, flags=re.DOTALL | re.IGNORECASE)
    full_answer = re.sub(r"<\s*reflection\s*>.*?<\s*/\s*reflection\s*>", "", full_answer, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up extra whitespace and newlines
    full_answer = re.sub(r"\n\s*\n+", "\n", full_answer)
    full_answer = re.sub(r"^\s+|\s+$", "", full_answer, flags=re.MULTILINE)
    
    return full_answer.strip()

