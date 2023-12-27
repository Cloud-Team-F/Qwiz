import json

from azure.functions import HttpRequest, HttpResponse


def create_error_response(error_message: str, status_code: int) -> HttpResponse:
    """
    Creates an error response with the given error message and status code.

    Args:
        error_message (str): The error message to include in the response.
        status_code (int): The HTTP status code to set for the response.

    Returns:
        HttpResponse: The error response object.
    """
    return HttpResponse(
        body=json.dumps({"error": error_message}),
        status_code=status_code,
        mimetype="application/json",
    )
