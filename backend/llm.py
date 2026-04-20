# backend/llm.py
# ─────────────────────────────────────────────
# LLM Engine — the ONLY file that talks to Ollama.
#
# WHY ISOLATED:
# If you swap Ollama for another engine later,
# you only change THIS file. Nothing else breaks.
# ─────────────────────────────────────────────

import httpx
import json
from typing import AsyncGenerator
from config import OLLAMA_URL, MODEL_NAME


async def stream_response(messages: list) -> AsyncGenerator[str, None]:
    """
    Sends the full conversation history to Ollama.
    Streams back tokens one by one as they are generated.

    WHY STREAMING:
    - User sees response immediately (feels fast)
    - No waiting for full response to complete
    - Same pattern used by ChatGPT, Claude, etc.

    messages format:
    [
      {"role": "system",    "content": "..."},
      {"role": "user",      "content": "..."},
      {"role": "assistant", "content": "..."},
      ...
    ]
    """

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True          # tells Ollama to stream tokens
    }

    # async with = non-blocking HTTP — won't freeze the server
    # timeout=120 = allow up to 2 min for slow CPU responses
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", OLLAMA_URL, json=payload) as response:

            # Ollama streams newline-delimited JSON objects
            # Each line looks like: {"message":{"content":"Hello"},"done":false}
            async for line in response.aiter_lines():

                if not line.strip():
                    continue  # skip empty lines

                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue  # skip malformed lines

                # Extract the token text
                token = chunk.get("message", {}).get("content", "")

                if token:
                    yield token  # send token to conversation manager

                # When done=True, Ollama signals the stream is finished
                if chunk.get("done", False):
                    break