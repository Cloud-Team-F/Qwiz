import json

from azure.functions import HttpRequest, HttpResponse


def create_error_response(error_message: str, status_code: int) -> HttpResponse:
    return HttpResponse(
        body=json.dumps({"error": error_message}),
        status_code=status_code,
        mimetype="application/json",
    )
