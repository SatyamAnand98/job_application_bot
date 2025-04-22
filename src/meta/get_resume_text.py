import os
import fitz  # PyMuPDF
from dotenv import load_dotenv
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    text = ""
    with fitz.open(pdf_path) as doc:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += page.get_text()
    return text

def get_resume_text():
    load_dotenv(override=True)
    # PROJECT_ROOT = Path(__file__).resolve().parent
    PROJECT_ROOT = Path().resolve()
    print("PROJECT_ROOT: ", PROJECT_ROOT)
    pdf_path = str(PROJECT_ROOT / os.getenv("UPLOAD_RESUME", ""))
    return extract_text_from_pdf(pdf_path)