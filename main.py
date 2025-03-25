# import gradio as gr
# import re
# import fitz  # PyMuPDF
# import spacy
# from config import (
#     keywords,
#     numeric_regex,
#     exclude_brackets_regex,
#     date_regex,
#     table_regex,
#     gender_regex,
#     age_regex,
#     author_pattern,
#     exclude_words,
#     key_sections,
#     follow_up
# )

# # Load spaCy's English model
# nlp = spacy.load("en_core_web_sm")

# def normalize_text(text):
#     """Normalize text by removing extra whitespace."""
#     return " ".join(line.strip() for line in text.splitlines())

# def extract_sentences(text):
#     """Split text into sentences."""
#     return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s', text)

# def contains_valid_numeric(sentence):
#     """Check if a sentence contains valid numeric values."""
#     matches = numeric_regex.findall(sentence)
#     bracketed_numbers = exclude_brackets_regex.findall(sentence)
#     return bool(matches) and len(matches) != len(bracketed_numbers)

# def matches_criteria(sentence, check_time_duration=False):
#     """Check if a sentence matches any of the defined keyword criteria."""
#     if date_regex.search(sentence) or table_regex.match(sentence):
#         return False

#     # Gender: Whole-word match only
#     contains_gender = bool(gender_regex.search(sentence))
    
#     # Age: Must contain numeric + age-related keyword as a whole word
#     contains_age_and_numeric = bool(re.search(r"\b(\d{1,3})\s*(?:years? old|year-old|year olds?|aged|age|young|elderly)\b", sentence, re.IGNORECASE))
    
#     # Patients: Must contain numeric + patients
#     contains_patients_and_numeric = bool(re.search(r"\b(\d+)\s*(?:patient|patients|case|cases|subject|subjects)\b", sentence, re.IGNORECASE))
    
#     # Participants: Must contain numeric + participants
#     contains_participants_and_numeric = bool(re.search(r"\b(\d+)\s*(?:participant|participants|attendee|respondent|volunteer)\b", sentence, re.IGNORECASE))
    
#     # Inclusion and Exclusion: Must contain numeric + keyword
#     contains_inclusion_and_numeric = bool(re.search(r"\b(\d+)\s*(?:inclusion|eligibility criteria|study inclusion)\b", sentence, re.IGNORECASE))
#     contains_exclusion_and_numeric = bool(re.search(r"\b(\d+)\s*(?:exclusion|study exclusion|not eligible)\b", sentence, re.IGNORECASE))
    
#     # Co-morbidities: Matches keyword only
#     contains_comorbidities = any(kw in sentence.lower() for kw in keywords["Co-morbidities"])

#     # Time durations: Matches numeric + time unit
#     time_duration_regex = re.compile(keywords["Follow-Up"][0], re.IGNORECASE)
#     contains_time_duration = bool(time_duration_regex.search(sentence))

#     # Ensure the sentence contains valid numeric values
#     contains_valid_numeric_value = contains_valid_numeric(sentence)

#     contains_remark = any(kw in sentence.lower() for kw in keywords["Remark"])

#     contains_intervention = any(kw in sentence.lower() for kw in keywords["Intervention Groups"])

#     if check_time_duration:
#         return contains_time_duration

#     return (
#         contains_valid_numeric_value and (
#             contains_gender
#             or contains_age_and_numeric
#             or contains_patients_and_numeric
#             or contains_participants_and_numeric
#             or contains_inclusion_and_numeric
#             or contains_exclusion_and_numeric
#             or contains_comorbidities
#             or contains_time_duration
#             or contains_remark
#             or contains_intervention
#         )
#     )

# def matches_keyword(sentence, user_keywords):
#     """Check if a sentence contains any of the user-specified keywords."""
#     return any(keyword.lower() in sentence.lower() for keyword in user_keywords)

# def extract_authors(page):
#     """Extract authors' names from the text above specified headers."""
#     full_text = page.get_text()

#     # Find the position of key sections
#     section_positions = {section: full_text.find(section) for section in key_sections}
#     section_positions = {k: v for k, v in section_positions.items() if v != -1}

#     # Determine the closest section and extract text above it
#     if section_positions:
#         closest_section = min(section_positions, key=section_positions.get)
#         cutoff_position = section_positions[closest_section]
#         text_to_search = full_text[:cutoff_position]  # Extract text above the section
#     else:
#         text_to_search = full_text

#     # Find author names using regex
#     author_matches = re.findall(author_pattern, text_to_search)

#     # Use NLP to further refine author name extraction
#     doc = nlp(text_to_search)
#     nlp_names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

#     # Combine regex and NLP results, filtering out unwanted words
#     combined_names = set(author_matches + nlp_names)
#     filtered_authors = [name for name in combined_names if name.lower() not in exclude_words]

#     return list(set(filtered_authors))

# def process_file(file_path, user_keywords, check_time_duration=False):
#     """Process the PDF file and extract sentences based on criteria, then filter by user keywords."""
#     doc = fitz.open(file_path)
#     first_page = doc[0]
#     author_names = extract_authors(first_page)
#     authors_str = ', '.join(author_names)

#     all_extracted_sentences = []
#     filtered_sentences = []

#     for page in doc:
#         text = normalize_text(page.get_text())
#         sentences = extract_sentences(text)
#         extracted = [sentence.strip() for sentence in sentences if matches_criteria(sentence, check_time_duration)]
#         all_extracted_sentences.extend(extracted)

#     if not check_time_duration:
#         filtered_sentences = [sentence for sentence in all_extracted_sentences if matches_keyword(sentence, user_keywords)]
#     else:
#         filtered_sentences = all_extracted_sentences

#     doc.close()
#     return filtered_sentences, authors_str

# def process_text(input_text, user_keywords, check_time_duration=False):
#     """Process the input text and extract sentences based on criteria, then filter by user keywords."""
#     refined_text = normalize_text(input_text)
#     sentences = extract_sentences(refined_text)
#     extracted_sentences = [sentence.strip() for sentence in sentences if matches_criteria(sentence, check_time_duration)]
    
#     if not check_time_duration:
#         filtered_sentences = [sentence for sentence in extracted_sentences if matches_keyword(sentence, user_keywords)]
#     else:
#         filtered_sentences = extracted_sentences

#     return filtered_sentences, "Authors not extracted from text input."

# def handle_input(file_path=None, input_text=None, keyword_group=None, custom_keywords=None, time_duration=False):
#     # Decide on which keywords to use
#     user_keywords = []
#     if keyword_group:
#         user_keywords = keywords[keyword_group]
#     if custom_keywords:
#         user_keywords.extend(kw.strip() for kw in custom_keywords.split(",") if kw.strip())

#     if not user_keywords and not time_duration:
#         return "No keyword provided."

#     if file_path:
#         extracted_sentences, authors_str = process_file(file_path, user_keywords, time_duration)
#     elif input_text:
#         extracted_sentences, authors_str = process_text(input_text, user_keywords, time_duration)
#     else:
#         return "No input provided."

#     if extracted_sentences:
#         return f"<p><b>Authors:</b> {authors_str}</p>" + "<br>".join(f"<p>{sentence}</p>" for sentence in extracted_sentences)
#     return "No matching sentences found."

# # Gradio Interface
# iface = gr.Interface(
#     fn=handle_input,
#     inputs=[
#         gr.File(label="Upload PDF or Text File", type="filepath"),
#         gr.Textbox(label="Enter Text", placeholder="Type or paste text here..."),
#         gr.Radio(list(keywords.keys()), label="Information related to..."),
#         # gr.Radio(label="Time Duration Criteria", value=False),
#         gr.Textbox(label="Enter Custom Keywords", placeholder="e.g., migraine, headache")
#     ],
#     outputs=gr.HTML(label="Processed Output"),
#     title="BioMedical Information Extraction",
#     description="""
#         <div style='text-align: left;'>
#             Made by: Sumit Kumar (2311006), Ramavath Tharun(21219) <br>
#             Supervisor: Dr. Tanmay Basu<br>
#             Indian Institute of Science Education and Research<br>
#         <div style='text-align: center;'>
#             <b>Upload a PDF file or enter text, then select a keyword group or enter custom keywords to extract relevant sentences.</b>
#         </div>
#     """,
#     cache_examples=True
# )

# iface.launch(share=True)




# prac.py

import gradio as gr
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
    # contains_age_and_numeric = bool(re.search(
    #     r"\b(\d{1,3})\s*(?:years? old|year-old|year olds?|aged|age|young|elderly)\b",
    #     sentence, re.IGNORECASE
    # ))
    

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

def process_file(file_path, user_keywords, check_time_duration=False):
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

    if not check_time_duration:
        filtered_sentences = [sentence for sentence in all_extracted_sentences if matches_keyword(sentence, user_keywords)]
    else:
        filtered_sentences = all_extracted_sentences

    # Highlight keywords in the filtered sentences
    highlighted_sentences = [highlight_keywords(sentence, user_keywords) for sentence in filtered_sentences]

    doc.close()
    return highlighted_sentences, authors_str

def process_text(input_text, user_keywords, check_time_duration=False):
    """
    Process the input text and extract sentences based on criteria,
    then filter by user keywords and highlight them.
    """
    refined_text = normalize_text(input_text)
    sentences = extract_sentences(refined_text)
    extracted_sentences = [sentence.strip() for sentence in sentences if matches_criteria(sentence, check_time_duration)]

    if not check_time_duration:
        filtered_sentences = [sentence for sentence in extracted_sentences if matches_keyword(sentence, user_keywords)]
    else:
        filtered_sentences = extracted_sentences

    # Highlight keywords in the filtered sentences
    highlighted_sentences = [highlight_keywords(sentence, user_keywords) for sentence in filtered_sentences]

    return highlighted_sentences, "Authors not extracted from text input."

def handle_input(file_path=None, input_text=None, keyword_group=None, custom_keywords=None, time_duration=False):
    """
    Handle user input from the Gradio interface,
    process the file or text, and return highlighted sentences with authors.
    """
    # Decide on which keywords to use
    user_keywords = []
    if keyword_group:
        user_keywords = keywords.get(keyword_group, [])
    if custom_keywords:
        user_keywords.extend(kw.strip() for kw in custom_keywords.split(",") if kw.strip())

    if not user_keywords and not time_duration:
        return "No keyword provided."

    if file_path:
        extracted_sentences, authors_str = process_file(file_path, user_keywords, time_duration)
    elif input_text:
        extracted_sentences, authors_str = process_text(input_text, user_keywords, time_duration)
    else:
        return "No input provided."

    if extracted_sentences:
        # Combine authors and highlighted sentences into HTML
        highlighted_html = f"<p><b>Authors:</b> {authors_str}</p>"
        for sentence in extracted_sentences:
            highlighted_html += f"<p>{sentence}</p>"
        return highlighted_html

    return "No matching sentences found."

# Gradio Interface
iface = gr.Interface(
    fn=handle_input,
    inputs=[
        gr.File(label="Upload PDF or Text File", type="filepath"),
        gr.Textbox(label="Enter Text", placeholder="Type or paste text here..."),
        gr.Radio(
            choices=list(keywords.keys()),
            label="Information related to..."
        ),
        gr.Textbox(
            label="Enter Custom Keywords",
            placeholder="e.g., migraine, headache"
        ),
        # gr.Checkbox(
        #     label="Check Time Duration Criteria",
        #     value=False
        # )
    ],
    outputs=gr.HTML(label="Processed Output"),
    title="BioMedical Information Extraction",
    description="""
        <div style='text-align: left;'>
            Made by: Sumit Kumar (2311006), Ramavath Tharun (21219) <br>
            Supervisor: Dr. Tanmay Basu<br>
            Indian Institute of Science Education and Research<br>
        </div>
        <div style='text-align: center; margin-top: 10px;'>
            <b>Upload a PDF file or enter text, then select a keyword group or enter custom keywords to extract and highlight relevant sentences.</b>
        </div>
    """,
    examples=None,  # You can add example files or texts if desired
    allow_flagging="never",
    cache_examples=True,
    # Add custom CSS to style the <mark> tag if necessary
    css="""
        mark {
            background-color: blue;
            padding: 0;
            border-radius: 2px;
        }
        /* Optional: Adjust paragraph spacing */
        p {
            margin-bottom: 10px;
        }
    """
)

iface.launch(share=True)



