import logging
import os
import re
import string
import tempfile

import fitz
import requests
import textract


def convert_to_text(file_url: str, mime: str) -> str:
    """
    Converts a file to text.

    Args:
        file_url (str): The URL of the file to be converted. Example: https://a.blob.core.windows.net/blobs/1.pdf
        mime (str): The MIME type of the file. Example: application/pdf

    Returns:
        str: The converted text.
    """
    logging.info(f"Converting file to text: {file_url}, {mime}")

    try:
        response = requests.get(file_url)  # http request to get the file
        response.raise_for_status()  # check if successful before continuing
        file = response.content  # retrieve raw content of the file

        # Determine file extension based on MIME type
        match mime.lower():
            case "application/pdf":
                file_extension = "pdf"
            case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                file_extension = "docx"
            case "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                file_extension = "pptx"
            case _:
                logging.error(f"Unknown MIME type: {mime}")
                return ""

        # Create temporary file to store the file
        with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as temp_file:
            # Write file to temporary file
            temp_file.write(file)
            temp_file.seek(0)
            logging.info(f"File successfully saved path: {temp_file.name}")

            # specific functions for PDF as they don't work with textract
            if file_extension == "pdf":
                text = text_pdf(temp_file.name)
            else:
                # textract library works flawlessly with DOCX and PPTX
                text = textract.process(temp_file.name).decode("utf-8")

            # remove all unnecessary characters
            cleaned_text = clean_text(text)
            logging.info(f"Text successfully extracted from '{file_url}")

            # Clean up
            temp_file.close()
            os.remove(temp_file.name)
            logging.info(f"Temporary file '{temp_file.name}' deleted")

            return cleaned_text

    except Exception as e:
        logging.error(f"Error converting file to text: {e}")
        return ""


def text_pdf(file):
    # Initialise list of text
    text = ""
    pdf_document = fitz.open(file)

    # for every page of the pdf
    for page_number in range(pdf_document.page_count):
        page = pdf_document[page_number]
        text += page.get_text()  # add the page text to the running list

    # Clean up
    pdf_document.close()
    return text


def clean_text(raw_text):
    # Remove special characters (except from punctuation), whitespaces, line breaks
    cleaned_text = re.sub(r"[^a-zA-Z0-9\s" + re.escape(string.punctuation) + "]", "", raw_text)

    # Remove conseuctive whitespaces
    cleaned_text = re.sub(r"\s+", " ", cleaned_text)

    # Remove leading/trailing white space
    return cleaned_text.strip()
