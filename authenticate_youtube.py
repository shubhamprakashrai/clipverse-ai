import sys
import os
from pathlib import Path

# Force UTF-8 stdout on Windows terminal so emojis and symbols do not crash cp1252
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CLIENT_SECRETS_FILE = Path("D:/ReelCraft-AI/storage/client_secrets.json")
TOKEN_FILE = Path("D:/ReelCraft-AI/storage/youtube_token.pickle")
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def authenticate():
    print("=" * 65)
    print("  [ReelCraft-AI] YouTube Channel 1-Click Authenticator")
    print("=" * 65)

    if not CLIENT_SECRETS_FILE.exists():
        print("\n[!] ERROR: client_secrets.json file nahi mili!")
        print(f"Target location:\n   {CLIENT_SECRETS_FILE.resolve()}")
        print("\n" + "-" * 65)
        print("--- KAISE SETUP KAREIN (100% Free - 3 Minutes) ---")
        print("-" * 65)
        print("1. Google Cloud Console kholein: https://console.cloud.google.com")
        print("2. Upar naya Project banayein (e.g. 'ReelCraft Auto') ya existing chunein.")
        print("3. Left menu -> 'APIs & Services' -> 'Library' me jayein:")
        print("   - 'YouTube Data API v3' search karein aur 'ENABLE' button dabayein.")
        print("4. 'OAuth consent screen' me jayein:")
        print("   - User type: 'External' select karein aur Create karein.")
        print("   - App name me 'ReelCraft' likhein, apna email daalein.")
        print("   - 'Test users' section me apna wahi Gmail daalein jis par YouTube channel hai.")
        print("5. 'Credentials' tab me jayein:")
        print("   - 'Create Credentials' -> 'OAuth client ID' select karein.")
        print("   - Application type: 'Desktop App' chunein.")
        print("   - Name: 'ReelCraft App' likh kar Create dabayein.")
        print("6. 'Download JSON' icon par click karein.")
        print("7. Us file ka naam badal kar 'client_secrets.json' kar dein aur yahan paste karein:")
        print(f"   {CLIENT_SECRETS_FILE.resolve()}")
        print("-" * 65)
        print("Iske baad dubara yeh command chalayein: python authenticate_youtube.py")
        print("=" * 65)
        sys.exit(1)

    try:
        import pickle
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        print("\n[INFO] Opening your default browser for YouTube authorization...")
        print("[INFO] Browser me apna YouTube account chunein aur permission 'Allow' karein.")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
        creds = flow.run_local_server(port=8090, prompt="consent")

        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

        yt = build("youtube", "v3", credentials=creds)
        resp = yt.channels().list(mine=True, part="snippet").execute()
        items = resp.get("items", [])
        if items:
            channel_name = items[0]["snippet"]["title"]
            print("\n" + "=" * 65)
            print(f"[SUCCESS] YouTube Channel Connected: {channel_name}")
            print(f"[SAVED] Credentials saved to: {TOKEN_FILE}")
            print("Ab aap Web Studio (http://localhost:8000) me jakar 'Auto-Publish to YouTube' tick kar sakte hain!")
            print("=" * 65)
        else:
            print("\n[CONNECTED] Account jud gaya hai, lekin is email par koi active YouTube channel nahi mila.")

    except Exception as e:
        print(f"\n[ERROR] Authentication failed: {e}")

if __name__ == "__main__":
    authenticate()
