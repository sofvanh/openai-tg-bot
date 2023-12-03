import os
import fitz
import requests
from speech import SpeechGenerator
from images import ImageGenerator
from helpers import store_image, is_valid_url
from openai import OpenAI


BOT_KEY = os.getenv("TELEGRAM")
BOT_URL = f"https://api.telegram.org/bot{BOT_KEY}"


class Assistant:
    def __init__(self):
        self.openai = OpenAI()
        self.images = ImageGenerator(self.openai)
        self.speech = SpeechGenerator(self.openai)

    def save_and_send_img(self, image, chat_id, prompt):
        photo_payload = {"photo": image}
        message_url = f"{BOT_URL}/sendPhoto?chat_id={chat_id}&caption={prompt}"
        requests.post(message_url, files=photo_payload)
        store_image(image)

    def send_voice(self, chat_id, ogg_io, title):
        message_url = f"{BOT_URL}/sendVoice?chat_id={chat_id}"
        files = {'voice': (title + '.ogg', ogg_io, 'audio/ogg')}
        requests.post(message_url, files=files)

    def send_audio(self, chat_id, audio_fp, title):
        message_url = f"{BOT_URL}/sendAudio?chat_id={chat_id}"
        audio_filename = f"{title}.mp3"
        files = {'audio': (audio_filename, audio_fp, 'audio/mp3')}
        requests.post(message_url, files=files)

    def send_message(self, chat_id, msg, parse_mode="Markdown"):
        message_url = f"{BOT_URL}/sendMessage"
        payload = {"text": msg, "chat_id": chat_id, "parse_mode": parse_mode}
        requests.post(message_url, json=payload)

    def process_image_request(self, chat_id, prompt):
        self.send_message(chat_id, "Generating 🎨")
        image = self.images.generate(prompt)
        self.save_and_send_img(image, chat_id, prompt)

    def process_speech_request(self, chat_id, prompt):
        self.send_message(chat_id, "Processing... ⏳")
        text = ""
        title = "audio"
        if is_valid_url(prompt):
            content_res = requests.get(prompt)
            if content_res.headers['Content-Type'] == 'application/pdf':
                try:
                    with fitz.open(stream=content_res.content, filetype="pdf") as doc:
                        title = doc.metadata['title'] if doc.metadata['title'] else "audio"
                        for page in doc:
                            text += page.get_text()
                except Exception as e:
                    return self.send_message(chat_id, f"Error processing PDF: {e}")
            else:
                return self.send_message(chat_id, "The URL must be a direct link to a PDF.")
        else:
            text = prompt
            # TODO Add LessWrong API / Graphql support
            # TODO Add BeautifulSoup / general article scraping support?

        speech_io = self.speech.text_to_speech(text)
        return self.send_voice(chat_id, speech_io, title)
