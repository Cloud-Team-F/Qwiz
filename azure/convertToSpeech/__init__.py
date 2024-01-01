import azure.functions as func
import azure.cognitiveservices.speech as speechsdk
import json
import os


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Parse the request body for the text to synthesize
        body = req.get_json()
        text = body.get('text')

        if not text:
            return func.HttpResponse(
                "Please pass text to synthesize in the request body",
                status_code=400
            )

        # Initialize the speech synthesizer with Azure credentials
        speech_key = '3f64cf27b8ca45d3a99e255c48be1375'
        speech_region = 'uksouth'
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=speech_region)
        speech_config.speech_synthesis_voice_name = 'en-US-JennyNeural'

        # Create the speech synthesizer
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config, audio_config=None)

        # Synthesize the speech
        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Convert the result to a byte array
            audio_data = result.audio_data
            # print(audio_data)
            return func.HttpResponse(audio_data, status_code=200, headers={'Content-Type': 'audio/wav'})
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            error_message = f"Speech synthesis canceled: {cancellation_details.reason}"
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    error_message += f" Error details: {cancellation_details.error_details}"
            return func.HttpResponse(json.dumps({"error": error_message}), status_code=500)

    except ValueError as e:
        return func.HttpResponse(f"Invalid request, error: {str(e)}", status_code=400)
    except Exception as e:
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)
