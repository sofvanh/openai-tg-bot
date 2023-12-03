import io
from openai import OpenAI


class SpeechGenerator:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client

    def text_to_speech(self, text):
        try:
            # Split the text into chunks of 4096 characters each (OpenAI limit)
            chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]
            fp = io.BytesIO()

            for chunk in chunks:
                response = self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice="onyx",
                    input=chunk
                )
                for audio_chunk in response.iter_bytes():
                    fp.write(audio_chunk)

            fp.seek(0)
            return {"mp3_fp": fp}
        except Exception as e:
            return {"error": str(e)}
