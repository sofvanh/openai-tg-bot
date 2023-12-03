import os
import time
import requests
from urllib.parse import urlparse
from deta import Drive


BLACKHOLE_URL = os.getenv("BLACKHOLE")
PHOTOS = Drive("generations")


def is_valid_url(url):
    parsed_url = urlparse(url)
    return bool(parsed_url.scheme and parsed_url.netloc)


def store_image(image):
    if is_valid_url(BLACKHOLE_URL):
        requests.post(BLACKHOLE_URL, files={"photo": image})
    else:
        current_time = time.time()
        filename = f"{current_time}.png"
        PHOTOS.put(filename, image)
