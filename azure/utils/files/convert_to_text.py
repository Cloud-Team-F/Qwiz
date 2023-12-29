import logging
import re
import string
import fitz
import textract
import requests
import tempfile


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
        response = requests.get(file_url) # http request to get the file 
        response.raise_for_status() # check if successful before continuing
        file = response.content # retrieve raw content of the file
        
        # check file extension --> different method for different file type
        # could've used mime type? maybe? perhaps? perchance?
        file_extension = file_url.split('.')[-1].lower() 
        
        
        # saves the file temporarily so that it can be passed into the functions
        # 'file' is raw content so difficult to work with
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            temp_file.write(file)
        
        # specific functions for PDF and DOC files
        # as they don't work with textract because why would they
        if file_extension == 'pdf': 
            text = text_pdf(temp_file.name)
        elif file_extension == 'doc':  # DOC DOES NOT WORK, I'M TOO INCOMPETENT TO MAKE IT WORK
            text = text_doc(temp_file.name)
        else:
            text = textract.process(temp_file.name).decode('utf-8') # textract library works flawlessly with DOCX and PPTX
        
        cleaned_text = clean_text(text) # remove all unnecessary characters
        
        logging.info(f"Text successfully extracted from '{file_url}")
        
        return cleaned_text
    
    
    except Exception as e:
        logging.error(f"Error converting file to text: {e}")
        return ""


def text_doc(file):
    # spent too much time trying to make this work, i think i may be brain dead
    return "" # i hate doc i hate doc i hate doc i hate doc i hate doc

def text_pdf(file):
    text = "" # initialise list of text
    pdf_document = fitz.open(file)
    for page_number in range(pdf_document.page_count): # for every page of the pdf
        page = pdf_document[page_number] 
        text += page.get_text() # add the page text to the running list
    pdf_document.close() # for safety idk
    return text

def clean_text(raw_text):
    # Remove special characters (except from punctuation), whitespaces, line breaks
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s' + re.escape(string.punctuation) + ']', '', raw_text)
    
    # Remove conseuctive whitespaces
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    
    # Remove leading/trailing white space
    return cleaned_text.strip()




#testing code:

# PDF file  : 
#print(convert_to_text("https://www.africau.edu/images/default/sample.pdf","idk"))

# PPTX file : 
#print(convert_to_text("https://www.dickinson.edu/download/downloads/id/1076/sample_powerpoint_slides.pptx","idk"))

# DOCX file : 
#print(convert_to_text("https://calibre-ebook.com/downloads/demos/demo.docx","idk"))
    