import time
from pathlib import Path
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
            fp = Path(__file__).parent / f"{time.time()}.mp3"
            response.stream_to_file(fp)
            return {"mp3_fp": fp}
        except Exception as e:
            return {"error": str(e)}