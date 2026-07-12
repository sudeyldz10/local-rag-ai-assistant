import re

def clean_answer(full_answer):
    if "<think>" in full_answer and "</think>" not in full_answer:
        full_answer = full_answer.split("<think>")[0]
    if "<thinking>" in full_answer and "</thinking>" not in full_answer:
        full_answer = full_answer.split("<thinking>")[0]

    full_answer = re.sub(r"<think>.*?</think>", "", full_answer, flags=re.DOTALL)
    full_answer = re.sub(r"<thinking>.*?</thinking>", "", full_answer, flags=re.DOTALL)
    return full_answer.strip()
