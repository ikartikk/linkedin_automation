import requests
import os
from crewai.tools import tool

STABLE_DIFFUSION_API = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

@tool("image_generator_tool")
def image_generator_tool(prompt: str) -> str:
    """
    Generate an AI image using Stability AI (Stable Diffusion).
    Requires STABILITY_API_KEY in environment variables.
    """
    api_key = os.getenv("STABILITY_API_KEY")
    if not api_key:
        return "Error: STABILITY_API_KEY not set in environment."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    files = {
        "prompt": (None, prompt),
        "output_format": (None, "png")
    }

    response = requests.post(STABLE_DIFFUSION_API, headers=headers, files=files)

    if response.status_code == 200:
        image_path = "./ai_post.png"
        with open(image_path, "wb") as f:
            f.write(response.content)
        return image_path
    else:
        return f"Image generation failed: {response.text}"
