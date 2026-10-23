import time
import socket

# Force IPv4 to prevent 120s Windows IPv6 timeout
orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4(host, port, family=0, type=0, proto=0, flags=0):
    return orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
socket.getaddrinfo = getaddrinfo_ipv4

from app.core.config import settings
from google import genai

t0 = time.time()
print("Connecting via IPv4...", flush=True)
with genai.Client(api_key=settings.GEMINI_API_KEY) as client:
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents="Say 'Hello world' in 2 words",
    )
    print(f"Response in {time.time()-t0:.2f}s: {response.text.strip()}", flush=True)
