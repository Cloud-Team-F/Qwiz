import logging


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

    # todo:: convert file to text

    return "This is a sample text"
