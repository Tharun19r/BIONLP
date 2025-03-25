import re
import fitz  # PyMuPDF
import spacy
from config import (
    keywords,
    numeric_regex,
    exclude_brackets_regex,
    date_regex,
    table_regex,
    gender_regex,
    age_regex,
    author_pattern,
    exclude_words,
    key_sections,
    follow_up
)
import sys

# Load spaCy's English model
nlp = spacy.load("en_core_web_sm")

def normalize_text(text):
    """Normalize text by removing extra whitespace."""
    return " ".join(line.strip() for line in text.splitlines())

def extract_sentences(text):
    """Split text into sentences."""
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', text)

def contains_valid_numeric(sentence):
    """Check if a sentence contains valid numeric values."""
    matches = numeric_regex.findall(sentence)
    bracketed_numbers = exclude_brackets_regex.findall(sentence)
    return bool(matches) and len(matches) != len(bracketed_numbers)

def matches_criteria(sentence, check_time_duration=False):
    """Check if a sentence matches any of the defined keyword criteria."""
    if date_regex.search(sentence) or table_regex.match(sentence):
        return False

    # Gender: Whole-word match only
    contains_gender = bool(gender_regex.search(sentence))

    # Age: Must contain numeric + age-related keyword as a whole word
    contains_age_and_numeric = bool(re.search(
        r"\b(?:\d{1,3}(?:–\d{1,3})?)\s*(?:years?|year-old|year olds?|aged\b|ages\b)\b",
        sentence, re.IGNORECASE
    ))

    # Patients: Must contain numeric + patients
    contains_patients_and_numeric = bool(re.search(
        r"\b(\d+)\s*(?:patient|patients|case|cases|subject|subjects)\b",
        sentence, re.IGNORECASE
    ))

    # Participants: Must contain numeric + participants
    contains_participants_and_numeric = bool(re.search(
        r"\b(\d+)\s*(?:participant|participants|attendee|respondent|volunteer)\b",
        sentence, re.IGNORECASE
    ))

    # Inclusion and Exclusion: Must contain numeric + keyword
    contains_inclusion_and_numeric = bool(re.search(
        r"\b(\d+)\s*(?:inclusion|eligibility criteria|study inclusion)\b",
        sentence, re.IGNORECASE
    ))
    contains_exclusion_and_numeric = bool(re.search(
        r"\b(\d+)\s*(?:exclusion|study exclusion|not eligible)\b",
        sentence, re.IGNORECASE
    ))

    # Co-morbidities: Matches keyword only
    contains_comorbidities = any(kw in sentence.lower() for kw in keywords["Co-morbidities"])

    # Time durations: Matches numeric + time unit
    time_duration_regex = re.compile(
        r'\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*'
        + r"(?:years|year|weeks|week|months|month|days|day)\b",
        re.IGNORECASE
    )
    contains_time_duration = bool(time_duration_regex.search(sentence))

    # Ensure the sentence contains valid numeric values
    contains_valid_numeric_value = contains_valid_numeric(sentence)

    # Additional criteria based on Remark and Intervention Groups
    contains_remark = any(kw in sentence.lower() for kw in keywords["Remark"])
    contains_intervention = any(kw in sentence.lower() for kw in keywords["Intervention Groups"])
    contains_study_type = any(kw in sentence.lower() for kw in keywords["Study Types"])
    contains_country = any(kw in sentence.lower() for kw in keywords["Country"])
    contains_race = any(kw in sentence.lower() for kw in keywords["Race/Ethnicity"])

    if check_time_duration:
        return contains_time_duration

    return (
        contains_valid_numeric_value and (
            contains_gender
            or contains_age_and_numeric
            or contains_patients_and_numeric
            or contains_participants_and_numeric
            or contains_inclusion_and_numeric
            or contains_exclusion_and_numeric
            or contains_comorbidities
            or contains_time_duration
            or contains_remark
            or contains_intervention
            or contains_study_type
            or contains_country
        )
    )

def matches_keyword(sentence, user_keywords):
    """Check if a sentence contains any of the user-specified keywords."""
    return any(keyword.lower() in sentence.lower() for keyword in user_keywords)

def extract_authors(page):
    """Extract authors' names from the text above specified headers."""
    full_text = page.get_text()

    # Find the position of key sections
    section_positions = {section: full_text.find(section) for section in key_sections}
    # Filter out sections not found
    section_positions = {k: v for k, v in section_positions.items() if v != -1}

    # Determine the closest section and extract text above it
    if section_positions:
        closest_section = min(section_positions, key=section_positions.get)
        cutoff_position = section_positions[closest_section]
        text_to_search = full_text[:cutoff_position]  # Extract text above the section
    else:
        text_to_search = full_text

    # Find author names using regex
    author_matches = re.findall(author_pattern, text_to_search)

    # Use NLP to further refine author name extraction
    doc = nlp(text_to_search)
    nlp_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

    # Combine regex and NLP results, filtering out unwanted words
    combined_names = set(author_matches + nlp_names)
    filtered_authors = [name for name in combined_names if name.lower() not in exclude_words]

    return list(set(filtered_authors))

def highlight_keywords(sentence, user_keywords):
    """Highlight user_keywords in the sentence using <mark> tags."""
    if not user_keywords:
        return sentence

    # Separate single-word and multi-word keywords
    single_words = [kw for kw in user_keywords if ' ' not in kw]
    phrases = [kw for kw in user_keywords if ' ' in kw]

    # Escape keywords for regex
    escaped_single_words = [re.escape(kw) for kw in single_words]
    escaped_phrases = [re.escape(kw) for kw in phrases]

    # Build regex patterns
    patterns = []
    if escaped_single_words:
        single_word_pattern = r'\b(?:' + '|'.join(escaped_single_words) + r')\b'
        patterns.append(single_word_pattern)
    if escaped_phrases:
        phrase_pattern = r'(?:' + '|'.join(escaped_phrases) + r')'
        patterns.append(phrase_pattern)

    # Combine patterns into a single regex
    if patterns:
        combined_pattern = re.compile('|'.join(patterns), re.IGNORECASE)
    else:
        return sentence

    # Function to add <mark> tags
    def replacer(match):
        return f"<mark>{match.group(0)}</mark>"

    # Substitute matched keywords with highlighted version
    highlighted_sentence = combined_pattern.sub(replacer, sentence)
    return highlighted_sentence

def process_file(file_path, user_keywords, output_file, check_time_duration=False):
    """
    Process the PDF file and extract sentences based on criteria,
    then filter by user keywords and highlight them.
    """
    doc = fitz.open(file_path)
    first_page = doc[0]
    author_names = extract_authors(first_page)
    authors_str = ', '.join(author_names)

    all_extracted_sentences = []

    for page in doc:
        text = normalize_text(page.get_text())
        sentences = extract_sentences(text)
        extracted = [sentence.strip() for sentence in sentences if matches_criteria(sentence, check_time_duration)]
        all_extracted_sentences.extend(extracted)

    # Filter sentences based on custom keywords
    filtered_sentences = [sentence for sentence in all_extracted_sentences if matches_keyword(sentence, user_keywords)]

    # Highlight keywords in the filtered sentences
    highlighted_sentences = [highlight_keywords(sentence, user_keywords) for sentence in filtered_sentences]

    doc.close()

    # Save output to a file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Authors: {authors_str}\n")
        for sentence in highlighted_sentences:
            # Remove HTML tags before writing to file
            clean_sentence = re.sub(r'<[^>]+>', '', sentence)
            f.write(f"{clean_sentence}\n")

    # Print the keywords that satisfy the constraints
    print("Extracted Keywords:")
    for kw in user_keywords:
        print(kw)

def process_text(input_text, user_keywords, output_file, check_time_duration=False):
    """
    Process the input text and extract sentences based on criteria,
    then filter by user keywords and highlight them.
    """
    refined_text = normalize_text(input_text)
    sentences = extract_sentences(refined_text)
    extracted_sentences = [sentence.strip() for sentence in sentences if matches_criteria(sentence, check_time_duration)]

    # Filter sentences based on custom keywords
    filtered_sentences = [sentence for sentence in extracted_sentences if matches_keyword(sentence, user_keywords)]

    # Highlight keywords in the filtered sentences
    highlighted_sentences = [highlight_keywords(sentence, user_keywords) for sentence in filtered_sentences]

    # Save output to a file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Authors not extracted from text input.\n")
        for sentence in highlighted_sentences:
            # Remove HTML tags before writing to file
            clean_sentence = re.sub(r'<[^>]+>', '', sentence)
            f.write(f"{clean_sentence}\n")

    # Print the keywords that satisfy the constraints
    print("Extracted Keywords:")
    for kw in user_keywords:
        print(kw)

def handle_input(file_path=None, input_text=None, keyword_group=None, custom_keywords=None, output_file='output.txt', time_duration=False):
    """
    Handle user input, process the file or text, and save highlighted sentences with authors to a file.
    """
    # Decide on which keywords to use
    user_keywords = []
    if keyword_group:
        user_keywords = keywords.get(keyword_group, [])
    if custom_keywords:
        user_keywords.extend(kw.strip() for kw in custom_keywords.split(",") if kw.strip())

    if not user_keywords and not time_duration:
        print("No keyword provided.")
        sys.exit()

    if file_path:
        process_file(file_path, user_keywords, output_file, time_duration)
    elif input_text:
        process_text(input_text, user_keywords, output_file, time_duration)
    else:
        print("No input provided.")
        sys.exit()

    print(f"Processing complete. Output saved to {output_file}")

if __name__ == "__main__":
    # Example usage:
    # python script.py --file_path input.pdf --keyword_group "Co-morbidities" --custom_keywords "migraine, headache" --output_file output.txt
    import argparse

    parser = argparse.ArgumentParser(description='BioMedical Information Extraction')

    parser.add_argument('--file_path', type=str, help='Path to PDF or text file.')
    parser.add_argument('--input_text', type=str, help='Input text as a string.')
    parser.add_argument('--keyword_group', type=str, choices=list(keywords.keys()), help='Keyword group to use.')
    parser.add_argument('--custom_keywords', type=str, help='Custom keywords, comma-separated.')
    parser.add_argument('--output_file', type=str, default='output.txt', help='File to save the output.')
    parser.add_argument('--time_duration', action='store_true', help='Check Time Duration Criteria.')

    args = parser.parse_args()

    handle_input(
        file_path=args.file_path,
        input_text=args.input_text,
        keyword_group=args.keyword_group,
        custom_keywords=args.custom_keywords,
        output_file=args.output_file,
        time_duration=args.time_duration
    )