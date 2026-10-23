import time
import sys
print("Step 1: Importing config", flush=True)
from app.core.config import settings
print(f"Step 2: API key length = {len(settings.GEMINI_API_KEY)}, Model = {settings.GEMINI_MODEL}", flush=True)

print("Step 3: Importing google.genai", flush=True)
from google import genai
from google.genai import types

print("Step 4: Initializing client with context manager", flush=True)
with genai.Client(api_key=settings.GEMINI_API_KEY) as client:
    print("Step 5: Calling generate_content", flush=True)
    t0 = time.time()
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents="Say 'OK' in one word.",
        )
        print(f"Step 6: Got response in {time.time()-t0:.2f}s: {response.text}", flush=True)
    except Exception as e:
        print(f"Step 6: Error occurred: {e}", flush=True)

print("Done!", flush=True)
