"""Minimal chat call through Hugging Face Inference Providers (OpenAI-compatible API).

Needs HF_TOKEN in .env, a Hugging Face token allowed to make calls to Inference Providers.
The token is only ever sent to Hugging Face. Calls are billed to that account.

Optional settings:
    LLM_MODEL     model to use (default: openai/gpt-oss-120b)
    LLM_BASE_URL  another OpenAI-compatible endpoint you trust; it then needs its own
                  key in LLM_API_KEY (HF_TOKEN is never sent anywhere else)
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

HF_ROUTER = "https://router.huggingface.co/v1"
base_url = os.getenv("LLM_BASE_URL", HF_ROUTER)

if base_url == HF_ROUTER:
    api_key = os.getenv("HF_TOKEN")
    if not api_key:
        raise ValueError("Missing HF_TOKEN. Add a Hugging Face token to your .env file (see .env.example).")
else:
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_BASE_URL is set, so LLM_API_KEY must hold that endpoint's own key.")

client = OpenAI(base_url=base_url, api_key=api_key)

stream = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
    messages=[{"role": "user", "content": "Write a haiku about APIs"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
print()
