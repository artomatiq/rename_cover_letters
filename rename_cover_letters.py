import spacy
import re
from pathlib import Path
from PyPDF2 import PdfReader
from watchdog.events import FileSystemEventHandler
import time
import os

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
    



class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith((".pdf", ".docx", ".doc")):
            time.sleep(1)
            print(f"New .pdf or .doc(x) detected: {event.src_path}")
            text = read_pdf(event.src_path)
            company, role = extract_company_and_role(text)

            new_name = f"{company} - {role}.pdf"
            sanitized_new_name = re.sub(r'[^a-zA-Z0-9 _.-]', '-', new_name).strip(" .")

            if len(sanitized_new_name) > 255:
                base, ext = os.path.splitext(sanitized_new_name)
                sanitized_new_name = base[:255 - len(ext)] + ext

            new_path = os.path.join(DOWNLOADS_FOLDER, new_name)
            
            try:
                os.rename(event.src_path, new_path)
                print(f"Renamed to: {new_path}")
            except Exception as e:
                print(f"Rename failed: {e}")
                
            
            

