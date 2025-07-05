import spacy
import re
from pathlib import Path
from PyPDF2 import PdfReader

nlp = spacy.load("en_core_web_sm")

DOWNLOADS_FOLDER = str(Path.home() / "Downloads")

def extract_company_and_role(text):
    company = None
    role = None

    company_match = re.search(r'\b(?:at|with)\s+([A-Z][a-zA-Z0-9&\-\.]+)', text)
    if company_match:
        company = company_match.group(1).strip()

    role_match = re.search(r'\b(?:position|role|job)\s+(?:of|as)?\s*([A-Z][a-zA-Z\s]+)', text)
    if role_match:
        role = role_match.group(1).strip()

    return company or "Unknown Company", role or "Unknown Role"

def read_pdf(path):
    try:
        with open(path, 'rb') as file:
            reader = PdfReader(file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        print(f"Failed to read PDF: {e}")
        return ""
    
