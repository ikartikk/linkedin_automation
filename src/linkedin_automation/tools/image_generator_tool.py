from crewai.tools import tool
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
import time

load_dotenv()

@tool("image_generator_tool")
def image_generator_tool(prompt: str) -> str:
    """
    Generate an image using Google's Gemini multimodal model.
    Requires GEMINI_API_KEY in environment variables.
    """
    try:
        api_key_image = os.getenv("GEMINI_API_KEY_IMAGE")
        if not api_key_image:
            return "Error: GEMINI_API_KEY not set in environment."
        print("Using api_key_image")

        client = genai.Client(api_key=api_key_image)

        time.sleep(60)

        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[prompt],
        )

        # Loop through parts, check for image data
        for part in response.candidates[0].content.parts:
            if getattr(part, "inline_data", None) is not None:
                image = Image.open(BytesIO(part.inline_data.data))
                image_path = "src/linkedin_automation/tools/data/ai_post.png"
                image.save(image_path)
                return image_path

        return "Error: No image returned from Gemini."

    except Exception as e:
        return f"❌ Gemini image generation failed: {str(e)}"
