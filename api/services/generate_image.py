from PIL import Image
import requests
from io import BytesIO

from openai import OpenAI

def generate_image(prompt):
    secret_key = "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"

    client = OpenAI(api_key=secret_key)

    response = client.images.generate(
    model="dall-e-3",
    prompt=prompt,
    size="1024x1024",
    quality="standard",
    n=1,
    )

    image_url = response.data[0].url
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    return img