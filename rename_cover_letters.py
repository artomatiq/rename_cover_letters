import spacy
import re
import logging
from pathlib import Path
from PyPDF2 import PdfReader
from docx import Document
from watchdog.events import FileSystemEventHandler
import time
import os
from watchdog.observers import Observer
import unicodedata

nlp = spacy.load("en_core_web_sm")

DOWNLOADS_FOLDER = str(Path.home() / "Downloads")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def extract_company_and_role(text):
    company = None
    role = None

    snippet = text[:300]
    doc = nlp(snippet)

    for ent in doc.ents:
        if ent.label_ == "ORG":
            company = ent.text.strip()
            break

    if company:
        stop_words = ['Dear Recipient', 'To Whom It May Concern', 'Dear Sir', 'Dear Madam', 'Team']
        for stop in stop_words:
            pattern = re.compile(re.escape(stop), re.IGNORECASE)
            company = pattern.sub('', company)
        company = company.strip()
    else:
        company = None

    role_match = re.search(
        r"\b(?:apply(?:ing)?\s+(?:for|to)|interest(?:ed)?\s+in|seeking)?\s*(?:the)?\s*([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*){0,5})\s+(?:position|role|job)\b",
        text,
    )

    if role_match:
        role = role_match.group(1).strip()

    return company or "Unknown Company", role or "Unknown Role"


def read_pdf(path):
    try:
        with open(path, "rb") as file:
            reader = PdfReader(file)
            if len(reader.pages) > 3:
                print(f"Skipped (too long): {path}")
                return None
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            text = unicodedata.normalize("NFKC", text).replace('\xa0', ' ')
            text = re.sub(r'\s+', ' ', text).strip()
            return text
    except Exception as e:
        print(f"Failed to read PDF: {e}")
        return None


def read_docx(path):
    try:
        doc = Document(path)
        full_text = "\n".join([para.text for para in doc.paragraphs])
        full_text = unicodedata.normalize("NFKC", full_text).strip()
        return full_text
    except Exception as e:
        print(f"Failed to read DOCX: {e}")
        return None


def process_and_rename(path):
    if not path.endswith((".pdf", ".docx")):
        return

    time.sleep(1)
    logging.info(f"Processing file: {path}")
    
    if path.endswith(".pdf"):
        text = read_pdf(path)
        ext = ".pdf"
    elif path.endswith(".docx"):
        text = read_docx(path)
        ext = ".docx"
    else:
        return

    if text is None:
        return
    

    company, role = extract_company_and_role(text)
    new_name = f"CvrLtr_{company}-{role}{ext}"
    sanitized_new_name = re.sub(r"[^a-zA-Z0-9 _.-]", "-", new_name).strip(" .")

    if len(sanitized_new_name) > 255:
        base, ext = os.path.splitext(sanitized_new_name)
        sanitized_new_name = base[: 255 - len(ext)] + ext
        
    new_path = os.path.join(DOWNLOADS_FOLDER, sanitized_new_name)
    
    if os.path.exists(new_path):
        logging.warning(f"File already exists: {new_path}")
        return

    try:
        os.rename(path, new_path)
        print(f"Renamed to: {new_path}")
    except Exception as e:
        print(f"Rename failed: {e}")


class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        process_and_rename(event.src_path)

def scan_existing_files():
    for filename in os.listdir(DOWNLOADS_FOLDER):
        if "cvrltr" in filename.lower():
            full_path = os.path.join(DOWNLOADS_FOLDER, filename)
            if os.path.isfile(full_path):
                process_and_rename(full_path)


if __name__ == "__main__":
    scan_existing_files()
    observer = Observer()
    event_handler = PDFHandler()
    observer.schedule(event_handler, DOWNLOADS_FOLDER, recursive=False)
    observer.start()
    print(f"Watching folder: {DOWNLOADS_FOLDER}")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
