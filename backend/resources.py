from pypdf import PdfReader
import json

import os

# Read LinkedIn PDF
pdf_path = "./data/linkedin.pdf"
if not os.path.exists(pdf_path):
    if os.path.exists("./data/LinkedIn.pdf"):
        pdf_path = "./data/LinkedIn.pdf"

try:
    reader = PdfReader(pdf_path)
    linkedin = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            linkedin += text
except FileNotFoundError:
    linkedin = "LinkedIn profile not available"

# Read other data files
with open("./data/summary.txt", "r", encoding="utf-8") as f:
    summary = f.read()

with open("./data/style.txt", "r", encoding="utf-8") as f:
    style = f.read()

with open("./data/facts.json", "r", encoding="utf-8") as f:
    facts = json.load(f)