import requests
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()
HF_API_KEY = os.getenv("HF_TOKEN")

def generate_image_hf(prompt, model_name="black-forest-labs/FLUX.1-schnell", output_path="src/linkedin_automation/tools/data/ai_post.png"):
    """
    Generate image using Hugging Face Inference API
    
    Args:
        prompt (str): Text prompt for image generation
        model_name (str): Hugging Face model to use
        output_path (str): Path to save the generated image
    
    Popular models:
    - "black-forest-labs/FLUX.1-schnell" (fast, free tier friendly)
    - "black-forest-labs/FLUX.1-dev" (higher quality, may have limits)
    - "ByteDance/SDXL-Lightning" (fast SDXL)
    - "stabilityai/stable-diffusion-xl-base-1.0" (classic SDXL)
    """
    
    # Hugging Face Inference API URL
    API_URL = f"https://api-inference.huggingface.co/models/{model_name}"
    
    headers = {
        "Authorization": f"Bearer {HF_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "guidance_scale": 7.5,  # How closely to follow the prompt
            "num_inference_steps": 20,  # Quality vs speed tradeoff
            "width": 1024,
            "height": 1024
        }
    }
    
    try:
        print(f"Generating image with prompt: '{prompt}'")
        print(f"Using model: {model_name}")
        
        response = requests.post(API_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            # The response content is the image bytes
            image = Image.open(BytesIO(response.content))
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the image
            image.save(output_path)
            print(f"Image saved successfully to: {output_path}")
            
            return image
            
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

# def generate_image_hf_alternative(prompt, model_name="stabilityai/stable-diffusion-xl-base-1.0", output_path="src/linkedin_automation/tools/data/ai_post.png"):
#     """
#     Alternative method using the client library approach (requires huggingface_hub)
#     """
#     try:
#         from huggingface_hub import InferenceClient
        
#         client = InferenceClient(api_key=HF_API_KEY)
        
#         print(f"Generating image with prompt: '{prompt}'")
#         print(f"Using model: {model_name}")
        
#         # Generate image
#         image = client.text_to_image(
#             prompt, 
#             model=model_name,
#             guidance_scale=7.5,
#             num_inference_steps=20,
#             width=1024,
#             height=1024
#         )
        
#         # Create directory if it doesn't exist
#         os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
#         # Save the image
#         image.save(output_path)
#         print(f"Image saved successfully to: {output_path}")
        
#         return image
        
#     except ImportError:
#         print("huggingface_hub library not installed. Install with: pip install huggingface_hub")
#         return None
#     except Exception as e:
#         print(f"An error occurred: {str(e)}")
#         return None

# Main execution
if __name__ == "__main__":
    # Your prompt
    prompt = """ generate an attractive image matching the AI topic to make the LinkedIn post stand out.
        You are a visual storyteller who creates effective images using AI image generation tools.
    Based on the finalized LinkedIn post text, generate a visually appealing image which is proffesional
    that represents the main idea. 
    The post text will be provided to you as context. 
    Use it to guide the imagery
**Unlock the Power of LLMs with LangChain**                                                                                                              │
│                                                                                                                                                           │
│  Curious how to build sophisticated AI applications beyond basic prompts? LangChain is an open-source framework that simplifies developing powerful       │
│  LLM-driven tools. It lets you chain LLM calls, connect to external data, and manage conversational context, abstracting complexity so you can focus on   │
│  innovation.                                                                                                                                              │
│                                                                                                                                                           │
│  By mastering LangChain, you can develop custom chatbots, RAG systems, and data-aware AI applications. This skill is invaluable for AI/ML professionals   │
│  looking to build robust, scalable, and intelligent solutions efficiently, opening doors to roles in AI development and prompt engineering.               │
│                                                                                                                                                           │
│  What are your favorite LangChain components for building complex AI applications?                                                                        │
│                                                                                                                                                           │
│  #AI #MachineLearning #LangChain #LLMs #Developer #TechSkills                                                                                             │
│  Reference: [https://python.langchain.com/docs/tutorials/](https://python.langchain.com/docs/tutorials/)   
"""
    
    # Method 1: Using requests (recommended)
    image = generate_image_hf(
        prompt=prompt,
        model_name="black-forest-labs/FLUX.1-schnell",  # Fast and free-tier friendly
        output_path="src/linkedin_automation/tools/data/ai_post.png"
    )
    
    # Method 2: Using huggingface_hub client (alternative)
    # Uncomment the line below to try the alternative method
    # image = generate_image_hf_alternative(prompt=prompt)
    
    if image:
        print("Image generation completed successfully!")
        # Optionally display the image
        # image.show()
    else:
        print("Image generation failed!")