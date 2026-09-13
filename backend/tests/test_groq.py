import os
from dotenv import load_dotenv
from groq import Groq
from app.core.security import decrypt_data

load_dotenv("data/.env")
groq_api_key = decrypt_data(os.getenv("GROQ_API_KEY", ""))

client = Groq(api_key=groq_api_key)
audio_path = "../test_audio.mp3"

with open(audio_path, "rb") as file:
    transcription = client.audio.transcriptions.create(
        file=(os.path.basename(audio_path), file.read()),
        model="whisper-large-v3",
        response_format="verbose_json",
        timeout=300
    )

print(transcription.text[:100])
print("Success!")
