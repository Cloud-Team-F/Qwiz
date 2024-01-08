import logging
import os

import azure.cognitiveservices.speech as speechsdk
from azure.functions import HttpRequest, HttpResponse
from utils import create_error_response


def main(req: HttpRequest) -> HttpResponse:
    logging.info("Text to speech function processed a request.")
    try:
        # Parse the request body for the text to synthesize
        body = req.get_json()
        text = body.get("text")

        if not text:
            return create_error_response("Please pass text to synthesize in the request body", 400)

        # Initialize the speech synthesizer with Azure credentials
        speech_config = speechsdk.SpeechConfig(
            subscription=os.environ["SPEECH_SERVICE_KEY"], region="uksouth"
        )
        speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"

        # Create the speech synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=None
        )

        # Synthesize the speech
        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Convert the result to a byte array
            audio_data = result.audio_data
            return HttpResponse(audio_data, status_code=200, headers={"Content-Type": "audio/wav"})

        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_message = f"Speech synthesis canceled: {cancellation_details.reason}"

            # Check if there is a cancellation reason
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    error_message += f" Error details: {cancellation_details.error_details}"

            return create_error_response(error_message, 500)

    except ValueError as e:
        return create_error_response(f"Invalid request, error: {str(e)}", 400)
    except Exception as e:
        return create_error_response(f"An error occurred: {str(e)}", 500)
