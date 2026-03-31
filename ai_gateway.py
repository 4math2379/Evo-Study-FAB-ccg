import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "Missing OPENAI_API_KEY environment variable. Ensure it is defined in your .env file."
    )

client = OpenAI(
    base_url="https://aliza-potent-aimee.ngrok-free.dev",
    api_key=api_key
)

stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a haiku about APIs"}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")