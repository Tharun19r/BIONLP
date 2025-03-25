import re
import fitz  # PyMuPDF
import pandas as pd
import sys
import os

# Import configuration from config.py
from config import (
    keywords,
    numeric_regex,
    exclude_brackets_regex,
    date_regex,
    table_regex,
    gender_regex,
    author_pattern,
    key_sections
)

import openpyxl

def text_refinement(text):
    """Clean and refine extracted text to improve matching accuracy."""
    text = re.sub(r'([a-z])([\.])([\s]*)([a-z])', r'\1 \3\4', text)  # Remove '.' between two lowercase letters
    text = re.sub(r'([0-9]+)([\.]+)([0-9]+)([\.]+)([0-9]+)', r'\1-\3-\5', text)  # Remove '.' between decimal numbers
    text = re.sub(r'(\s)([a-z0-9]+)([A-Z])([\w]+)', r'\1\2. \3\4', text)  # Insert '.' before uppercase words
    text = re.sub(r'(\.)([\s]*)([\.]+)', r'\1', text)  # Remove duplicate dots
    text = re.sub(r'([a-zA-Z0-9])([\s]*)([-])([\s]*)([a-zA-Z0-9])', r'\1\3\5', text)  # Remove spaces around hyphens
    return text

def remove_illegal_chars(text):
    """Remove characters that cannot be stored in an Excel worksheet."""
    return "".join(c for c in text if c.isprintable())

def normalize_text(text):
    """Normalize text by removing extra whitespace."""
    return " ".join(line.strip() for line in text.splitlines())

def extract_sentences(text):
    """Split text into sentences using punctuation-based segmentation."""
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', text)

def extract_title_and_authors(text):
    """Extracts study title and authors from the document text."""
    lines = text.split("\n")
    title = lines[0].strip() if lines else "Unknown Title"
    authors = re.findall(author_pattern, text)
    author_names = ", ".join(authors) if authors else "Unknown Authors"
    return title, author_names

def extract_sentences_from_pdf(pdf_path):
    """Extract and categorize sentences from a PDF file."""
    doc = fitz.open(pdf_path)
    filename = os.path.basename(pdf_path)
    
    categories = [
        "Filename", "Title", "Authors", "Gender", "Age", "Patients", "Participants", "Inclusion Criteria",
        "Exclusion Criteria", "Co-morbidities", "Time Duration", "Remarks", "Intervention Groups",
        "Study Types", "Country", "Race/Ethnicity"
    ]
    extracted_data = {category: [] for category in categories}
    extracted_data["Filename"].append(filename)

    # Extract full text for title and author extraction
    full_text = "\n".join([normalize_text(page.get_text()) for page in doc])
    title, authors = extract_title_and_authors(full_text)
    extracted_data["Title"].append(title)
    extracted_data["Authors"].append(authors)

    for page in doc:
        text = normalize_text(page.get_text())
        sentences = extract_sentences(text)

        for sentence in sentences:
            refined_sentence = text_refinement(sentence)
            matched_categories = matches_criteria(refined_sentence)
            if matched_categories:
                for category in matched_categories:
                    extracted_data[category].append(refined_sentence)

    doc.close()
    
    # Convert lists to comma-separated strings for Excel storage
    for category in categories:
        extracted_data[category] = [", ".join(extracted_data[category]) if extracted_data[category] else ""]

    return extracted_data

def matches_criteria(sentence):
    """Check if a sentence matches predefined keyword-based categories."""
    if date_regex.search(sentence) or table_regex.match(sentence):
        return None  # Skip sentences containing dates or table patterns

    contains_valid_numeric_value = bool(numeric_regex.findall(sentence))

    # Check against keyword patterns
    criteria_match = {
        "Gender": bool(gender_regex.search(sentence)),
        "Age": bool(re.search(r"\b(?:\d{1,3}(?:–\d{1,3})?)\s*(?:years?|year-old|aged|ages)\b", sentence, re.IGNORECASE)),
        "Patients": bool(re.search(r"\b(\d+)\s*(?:patient|patients|case|cases|subject|subjects)\b", sentence, re.IGNORECASE)),
        "Participants": bool(re.search(r"\b(\d+)\s*(?:participant|participants|attendee|respondent|volunteer)\b", sentence, re.IGNORECASE)),
        "Inclusion Criteria": any(kw in sentence.lower() for kw in keywords["Inclusion Criteria"]),
        "Exclusion Criteria": any(kw in sentence.lower() for kw in keywords["Exclusion Criteria"]),
        "Co-morbidities": any(kw in sentence.lower() for kw in keywords["Co-morbidities"]),
        "Time Duration": bool(re.search(r'\b(?:\d+|one|two|three)\s*(?:years?|weeks?|months?|days?)\b', sentence, re.IGNORECASE)),
        "Remarks": any(kw in sentence.lower() for kw in keywords["Remark"]),
        "Intervention Groups": any(kw in sentence.lower() for kw in keywords["Intervention Groups"]),
        "Study Types": any(kw in sentence.lower() for kw in keywords["Study Types"]),
        "Country": any(kw in sentence.lower() for kw in keywords["Country"]),
        "Race/Ethnicity": any(kw in sentence.lower() for kw in keywords["Race/Ethnicity"]),
    }

    matched_criteria = [key for key, value in criteria_match.items() if value]
    return matched_criteria if contains_valid_numeric_value and matched_criteria else None

def process_directory(pdf_dir, output_excel):
    """Process multiple PDFs in a directory and save results in a single Excel file."""
    all_data = []
    for file in os.listdir(pdf_dir):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, file)
            extracted_data = extract_sentences_from_pdf(pdf_path)
            all_data.append(extracted_data)
    
    # Convert list of dicts to DataFrame
    df = pd.DataFrame(all_data)
    df = df.applymap(lambda x: remove_illegal_chars(x) if isinstance(x, str) else x)
    
    # Save results to Excel
    df.to_excel(output_excel, index=False, engine="openpyxl")
    print(f"Processing complete. Results saved to {output_excel}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <pdf_directory> <output_excel>")
        sys.exit(1)

    pdf_directory = sys.argv[1]
    output_excel = sys.argv[2]

    process_directory(pdf_directory, output_excel)