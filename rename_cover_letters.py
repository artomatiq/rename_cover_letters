import spacy
import re
from pathlib import Path
from PyPDF2 import PdfReader

nlp = spacy.load("en_core_web_sm")

