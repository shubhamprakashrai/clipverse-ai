import os
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

TOKEN_FILE = Path("D:/ReelCraft-AI/storage/youtube_token.pickle")
CLIENT_SECRETS_FILE = Path("D:/ReelCraft-AI/storage/client_secrets.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]

def get_youtube_auth_status() -> Dict[str, Any]:
    """
    Check if YouTube Data API credentials and OAuth token are active.
    """
    has_secrets = CLIENT_SECRETS_FILE.exists()
    has_token = TOKEN_FILE.exists()

    channel_name = None
    if has_token:
        try:
            with open(TOKEN_FILE, "rb") as f:
                creds = pickle.load(f)
            if creds and creds.valid:
                from googleapiclient.discovery import build
                yt = build("youtube", "v3", credentials=creds)
                resp = yt.channels().list(mine=True, part="snippet").execute()
                items = resp.get("items", [])
                if items:
                    channel_name = items[0]["snippet"]["title"]
        except Exception as e:
            logger.warning(f"Failed to query YouTube channel: {e}")

    return {
        "configured": has_secrets,
        "authenticated": has_token and channel_name is not None,
        "channel_name": channel_name,
        "client_secrets_path": str(CLIENT_SECRETS_FILE),
        "instructions": (
            "1. Create a free OAuth 2.0 Client ID in Google Cloud Console.\\n"
            "2. Download client_secrets.json and save to D:\\ReelCraft-AI\\storage\\client_secrets.json\\n"
            "3. Run authentication to link your YouTube Channel."
        )
    }

def get_authenticated_service():
    """
    Get authorized YouTube API service using saved OAuth credentials.
    """
    if not TOKEN_FILE.exists():
        logger.warning("No YouTube OAuth token found at storage/youtube_token.pickle")
        return None

    try:
        from google.auth.transport.requests import Request
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(TOKEN_FILE, "wb") as f:
                    pickle.dump(creds, f)

        from googleapiclient.discovery import build
        return build("youtube", "v3", credentials=creds)
    except Exception as e:
        logger.error(f"Error loading YouTube service: {e}")
        return None

def upload_video_to_youtube(
    video_path: Path,
    title: str,
    description: str,
    tags: Optional[list] = None,
    privacy_status: str = "unlisted",
    category_id: str = "27"
) -> Dict[str, Any]:
    """
    Upload a rendered documentary video to YouTube via YouTube Data API v3.
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    youtube = get_authenticated_service()
    if not youtube:
        logger.warning(f"YouTube not authenticated. Skipping direct upload for: {video_path.name}")
        return {
            "success": False,
            "status": "NOT_AUTHENTICATED",
            "message": "YouTube OAuth credentials not configured. Video saved locally in storage/output."
        }

    from googleapiclient.http import MediaFileUpload

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or ["documentary", "explainer", "history", "news"],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)

    logger.info(f"Starting YouTube upload for: '{title[:40]}' ({video_path.stat().st_size / (1024*1024):.1f} MB)")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"YouTube upload progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    video_url = f"https://youtu.be/{video_id}"
    logger.info(f"YouTube upload complete! Video URL: {video_url}")

    return {
        "success": True,
        "video_id": video_id,
        "video_url": video_url,
        "privacy": privacy_status
    }
