import io
from openai import OpenAI


class SpeechGenerator:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client

    def text_to_speech(self, text):
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="onyx",
                input=text
            )
            fp = io.BytesIO()
            for chunk in response.iter_bytes():
                fp.write(chunk)
            fp.seek(0)
            return {"mp3_fp": fp}
        except Exception as e:
            return {"error": str(e)}
