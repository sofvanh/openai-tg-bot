import os
import time
import requests
from bot import Assistant
from images import ImageGenerator
from speech import SpeechGenerator
from deta import Base
from openai import OpenAI
from urllib.parse import urlparse
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Template
from pydantic import BaseModel


class New_ID(BaseModel):
    new_id: int


CONFIG = Base("config")
DEBUG_LOGGING_ENABLED = os.getenv(
    "DEBUG_LOGGING_ENABLED", "false").lower() == "true"
BOT_KEY = os.getenv("TELEGRAM")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_URL = f"https://api.telegram.org/bot{BOT_KEY}"
ENV_VARS_MISSING = (not BOT_KEY or BOT_KEY == "enter your key"
                    or not OPENAI_API_KEY or OPENAI_API_KEY == "enter your key")

bot = Assistant()
openai_client = OpenAI()
image_generator = ImageGenerator(openai_client)
speech_generator = SpeechGenerator(openai_client)
app = FastAPI()
app.mount("/public", StaticFiles(directory="public"), name="public")


# API ROUTES


@app.get("/")
def home():
    home_template = Template((open("index.html").read()))

    response = get_webhook_info()

    if ENV_VARS_MISSING:
        return RedirectResponse("/setup")

    if response and "result" in response and not response["result"]["url"]:
        return RedirectResponse("/setup")

    if response and "result" in response and "url" in response["result"]:
        return HTMLResponse(home_template.render(status="READY"))

    return HTMLResponse(home_template.render(status="ERROR"))


def get_webhook_info():
    message_url = f"{BOT_URL}/getWebhookInfo"
    return requests.get(message_url).json()


@app.get("/setup")
def setup():
    home_template = Template((open("index.html").read()))
    blackhole_app_url = f"https://{urlparse(BLACKHOLE_URL).hostname}" if bh_validity else ""
    if ENV_VARS_MISSING:
        return HTMLResponse(home_template.render(status="SETUP_ENVS"))
    return HTMLResponse(home_template.render(status="SETUP_WEBHOOK", blackhole_url=blackhole_app_url))


@app.get("/authorize")
def auth():
    authorized_chat_ids = CONFIG.get("chat_ids")
    home_template = Template((open("index.html").read()))

    if authorized_chat_ids is None:
        return HTMLResponse(home_template.render(status="AUTH", chat_ids=None))

    return HTMLResponse(
        home_template.render(
            status="AUTH", chat_ids=authorized_chat_ids.get("value"))
    )


@app.post("/authorize")
def add_auth(item: New_ID):
    if CONFIG.get("chat_ids") is None:
        CONFIG.put(data=[item.new_id], key="chat_ids")
        return

    CONFIG.update(
        updates={"value": CONFIG.util.append(item.new_id)}, key="chat_ids")
    return


@app.post("/open")
async def http_handler(request: Request, background_tasks: BackgroundTasks):
    incoming_data = await request.json()
    if DEBUG_LOGGING_ENABLED:
        print(incoming_data)
        print(incoming_data["message"])

    prompt = incoming_data["message"]["text"]
    chat_id = incoming_data["message"]["chat"]["id"]
    authorized_chat_ids = CONFIG.get("chat_ids")

    if prompt in ["/chat-id", "/chatid"]:
        bot.send_message(chat_id, f"```{chat_id}```")
        return "ok"
    elif prompt in ["/start", "/help"]:
        print("We here")
        bot.send_message(
            chat_id, "Welcome. Send /image {prompt} to generate a message, or /speech {Text or link to PDF} to generate audio.")
        return "ok"
    elif authorized_chat_ids is None or chat_id not in authorized_chat_ids.get("value"):
        bot.send_message(
            chat_id, "You're not authorized. Contact this bot's admin...")
        return "ok"
    elif prompt.startswith("/image "):
        background_tasks.add_task(
            bot.process_image_request, chat_id, prompt[len("/image "):])
        return "ok"
    elif prompt.startswith("/speech "):
        background_tasks.add_task(
            bot.process_speech_request, chat_id, prompt[len("/speech "):])
        return "ok"
    else:
        bot.send_message(
            chat_id, "Send /image {prompt} to generate an image, or /speech {text or link to PDF} to generate audio.")
        return "ok"


@app.get("/set_webhook")
def url_setter():
    PROG_URL = os.getenv("DETA_SPACE_APP_HOSTNAME")
    set_url = f"{BOT_URL}/setWebHook?url=https://{PROG_URL}/open"
    resp = requests.get(set_url)
    return resp.json()


# LOCAL TESTING


def main():
    choice = input(
        "Do you want to generate an image or use text-to-speech? (image/tts): ").strip().lower()
    if choice == "image":
        prompt = input("Enter a prompt for image generation: ")
        image = image_generator.generate(prompt)
        print("decoding...")
        with open(f"{time.time()}-{prompt[0:3]}.png", "wb") as file:
            file.write(image)
        print("Image saved successfully!")
    elif choice == "tts":
        prompt = input("Enter a prompt to turn into speech: ")
        speech_io = speech_generator.text_to_speech(prompt)
        filename = f"{time.time()}-speech.ogg"
        with open(filename, "wb") as file:
            file.write(speech_io.read())
        print(f"Audio saved successfully at {filename}")
    else:
        print("Invalid choice. Please type 'image' or 'tts'.")


if __name__ == "__main__":
    main()
