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
        page_text = page.get_text()
        lines = [line.strip() for line in page_text.split("\n") if len(line.strip()) > 20]
        text += "\n".join(lines) + "\n"
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
    supported={".txt", ".pdf", ".docx"}
    all_docs=[]


    for root, dirs, files in os.walk(data_dir):
        for file_name in files:
            file_path=os.path.join(root, file_name)
            ext=os.path.splitext(file_name)[1].lower()
            
            if ext not in supported:
                print(f"unsuppoted formats: {file_path}")
                continue

            try:
                text=load_single_file(file_path)
                if text:
                    all_docs.append({"text": text, "source": file_path})
                    print(f"Downloaded: {file_path}")
            
            except Exception as e:
                print(f"Error: {file_name} - {e}")

    print(f"\nTotal {len(all_docs)} is downloaded")
    return all_docs

                                              