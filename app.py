import re
import tempfile
import time

import streamlit as st
from deep_translator import GoogleTranslator
from docx import Document


def is_url_or_link(text):
    """Check if text is a URL or link that should not be translated."""
    # Common URL patterns
    url_patterns = [
        r"https?://[^\s]+",  # HTTP/HTTPS URLs
        r"www\.[^\s]+",  # www URLs
        r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Domain names
        r"ftp://[^\s]+",  # FTP URLs
        r"mailto:[^\s]+",  # Email links
        r"file://[^\s]+",  # File URLs
    ]

    # Check if text matches any URL pattern
    for pattern in url_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    # Check for common link indicators
    link_indicators = ["http://", "https://", "www.", "mailto:", "ftp://", "file://"]
    text_lower = text.lower()
    for indicator in link_indicators:
        if indicator in text_lower:
            return True

    return False


def translate_text_safely(text, src_lang, dest_lang, max_retries=3):
    """Safely translate text with retry logic and error handling."""
    # Skip translation if text is a URL or link
    if is_url_or_link(text):
        return text

    # Skip translation if text is too short or empty
    if len(text.strip()) < 2:
        return text

    for attempt in range(max_retries):
        try:
            translator = GoogleTranslator(source=src_lang, target=dest_lang)
            result = translator.translate(text)
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retrying
                continue
            else:
                st.warning(f"Failed to translate: '{text[:50]}...' - {str(e)}")
                return text  # Return original text if translation fails
    return text


def translate_docx(file, src_lang, dest_lang):
    doc = Document(file)

    # Progress tracking
    total_paragraphs = len([p for p in doc.paragraphs if p.text.strip()])
    total_cells = sum(
        len([c for c in row.cells if c.text.strip()])
        for table in doc.tables
        for row in table.rows
    )
    total_items = total_paragraphs + total_cells

    progress_bar = st.progress(0)
    status_text = st.empty()

    current_item = 0

    # Translate paragraphs
    for para in doc.paragraphs:
        if para.text.strip():
            try:
                status_text.text(
                    f"Translating paragraph {current_item + 1}/{total_items}..."
                )
                translated_text = translate_text_safely(para.text, src_lang, dest_lang)
                para.text = translated_text
                current_item += 1
                progress_bar.progress(current_item / total_items)
            except Exception as e:
                st.error(f"Error translating paragraph: {str(e)}")
                current_item += 1
                progress_bar.progress(current_item / total_items)
                continue

    # Translate tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    try:
                        status_text.text(
                            f"Translating table cell {current_item + 1}/{total_items}..."
                        )
                        translated_text = translate_text_safely(
                            cell.text, src_lang, dest_lang
                        )
                        cell.text = translated_text
                        current_item += 1
                        progress_bar.progress(current_item / total_items)
                    except Exception as e:
                        st.error(f"Error translating table cell: {str(e)}")
                        current_item += 1
                        progress_bar.progress(current_item / total_items)
                        continue

    progress_bar.empty()
    status_text.empty()
    return doc


st.title("📄 DOCX Translator Tool")

# Language codes reference
with st.expander("ℹ️ Language Codes Reference"):
    st.markdown(
        """
    **Common Language Codes:**
    - `en` - English
    - `de` - German  
    - `es` - Spanish
    - `fr` - French
    - `it` - Italian
    - `pt` - Portuguese
    - `ru` - Russian
    - `ja` - Japanese
    - `ko` - Korean
    - `zh` - Chinese
    - `ar` - Arabic
    - `hi` - Hindi
    
    Use 2-letter ISO codes, not full language names!
    
    **Note:** URLs and links will be preserved and not translated.
    """
    )

uploaded_file = st.file_uploader("Upload your .docx file", type=["docx"])
src_lang = st.text_input(
    "Source language code",
    placeholder="e.g., en, de, es",
    help="Enter the 2-letter language code of your source document",
)
dest_lang = st.text_input(
    "Destination language code",
    placeholder="e.g., es, fr, de",
    help="Enter the 2-letter language code for translation",
)

if uploaded_file and src_lang and dest_lang:
    if st.button("Translate"):
        try:
            with st.spinner("Preparing translation..."):
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".docx"
                ) as tmp_input:
                    tmp_input.write(uploaded_file.read())
                    tmp_input_path = tmp_input.name

                doc = translate_docx(tmp_input_path, src_lang, dest_lang)

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".docx"
                ) as tmp_output:
                    doc.save(tmp_output.name)
                    tmp_output_path = tmp_output.name

                with open(tmp_output_path, "rb") as f:
                    st.success("✅ Translation complete!")
                    st.download_button(
                        label="Download Translated DOCX",
                        data=f,
                        file_name=f"translated_{uploaded_file.name}",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
        except Exception as e:
            st.error(f"An error occurred during translation: {str(e)}")
            st.info("Please try again or check your language codes.")
