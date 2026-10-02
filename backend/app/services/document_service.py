from pathlib import Path
from pypdf import PdfReader
from docx import Document as DocxDocument

def extract_text(path: str, suffix: str):
    if suffix == ".pdf":
        reader = PdfReader(path)
        return [(i+1, page.extract_text() or "") for i,page in enumerate(reader.pages)]
    if suffix == ".docx":
        doc = DocxDocument(path)
        return [(1, "\n".join(p.text for p in doc.paragraphs))]
    if suffix == ".txt":
        return [(1, Path(path).read_text(encoding="utf-8", errors="ignore"))]
    raise ValueError("Unsupported file type")

def chunk_text(text: str, size=1200, overlap=180):
    out=[]
    start=0
    while start < len(text):
        out.append(text[start:start+size])
        start += size-overlap
    return out
