from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

Gemini_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key= Gemini_API_KEY)

prompt = ("genrate a image of banana in a bowl with 3d art style")

response = client.models.generate_content(
    model="gemini-2.5-flash-image-preview",
    contents=[prompt],
)

for part in response.candidates[0].content.parts:
    if part.text is not None:
        print(part.text)
    elif part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save("src/linkedin_automation/tools/data/ai_post.png")