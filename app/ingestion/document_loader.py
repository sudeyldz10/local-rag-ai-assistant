import os
import fitz
from docx import Document

def load_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return text

def load_pdf(file_path):
    text = ""
    pdf=fitz.open(file_path)
    for page in pdf:
        text += page.get_text()
    return text

def load_docx(file_path):
    doc= Document(file_path)
    parapraghs= [p.text for p in doc.paragraphs if p.text.strip()]
    text="\n".join(parapraghs)
    return text



def load_single_file(file_path):
    if file_path.endswith(".txt"):
        return load_txt(file_path)
    elif file_path.endswith(".pdf"):
        return load_pdf(file_path)
    elif file_path.endswith(".docx"):
        return load_docx(file_path)
    else:
        print(f"unsupported formats: {file_path}")
        return None

def load_documents(data_dir="data"):
    docs=[]

    for file_name in os.listdir(data_dir):
        file_path=os.path.join(data_dir, file_name)

        text= load_single_file(file_path)

        if text:
            docs.append({"text": text, "source": file_name})
            print(f"Downloaded: {file_name}")
    
    print(f"\n Total {len(docs)} is downloaded")
    return docs

                                              