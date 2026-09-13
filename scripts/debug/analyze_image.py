import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

img_path = "/app/data/templates/tiktok snap 88.jpg"
if not os.path.exists(img_path):
    print("Image not found:", img_path)
    exit()

sample_file = client.files.upload(file=img_path)

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[
        sample_file,
        "Analyze this TikTok camera screen. Where exactly is the gallery/upload button located? What exact Vietnamese or English text is written under or on it? Is it on the bottom left or bottom right?"
    ]
)
print("GEMINI ANALYSIS:")
print(response.text)
