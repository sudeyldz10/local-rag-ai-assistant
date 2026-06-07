import re

def clean_answer(full_answer):
    full_answer = re.sub(r"<think>.*?</think>", "", full_answer, flags=re.DOTALL)
    full_answer = re.sub(r"<thinking>.*?</thinking>", "", full_answer, flags=re.DOTALL)
    return full_answer.strip()
