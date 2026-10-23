import hashlib
import random
import urllib.parse
from pathlib import Path
from typing import List, Optional
import requests
from loguru import logger
from app.core.config import settings

def search_pixabay_videos(query: str, orientation: str = "vertical", per_page: int = 5) -> List[dict]:
    """
    Search Pixabay for HD stock videos.
    """
    if not settings.PIXABAY_API_KEY:
        logger.warning("Pixabay API key not configured")
        return []

    url = "https://pixabay.com/api/videos/"
    params = {
        "key": settings.PIXABAY_API_KEY,
        "q": query,
        "video_type": "all",
        "per_page": per_page
    }
    if orientation in ["vertical", "horizontal"]:
        params["orientation"] = orientation

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            return hits
        else:
            logger.error(f"Pixabay video search error {resp.status_code}: {resp.text}")
            return []
    except Exception as e:
        logger.error(f"Failed to query Pixabay videos: {e}")
        return []

def search_pixabay_images(query: str, orientation: str = "vertical", per_page: int = 5, image_type: str = "photo") -> List[dict]:
    """
    Search Pixabay for high-res stock photos or illustrations.
    """
    if not settings.PIXABAY_API_KEY:
        return []

    url = "https://pixabay.com/api/"
    params = {
        "key": settings.PIXABAY_API_KEY,
        "q": query,
        "image_type": image_type,
        "per_page": per_page,
        "orientation": orientation if orientation in ["vertical", "horizontal"] else "all"
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("hits", [])
        return []
    except Exception as e:
        logger.error(f"Failed to query Pixabay images: {e}")
        return []

def download_file(url: str, dest_folder: Path, suffix: str = ".mp4") -> Path:
    """
    Download a remote media file and cache locally.
    """
    dest_folder.mkdir(parents=True, exist_ok=True)
    url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
    local_path = dest_folder / f"pixabay_{url_hash}{suffix}"

    if local_path.exists() and local_path.stat().st_size > 1000:
        return local_path

    logger.info(f"Downloading stock asset from: {url}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_path

def get_best_video_download_url(hit: dict) -> Optional[str]:
    """
    Extract best matching video URL (strictly medium/large, avoiding 4K for fast rendering).
    """
    videos = hit.get("videos", {})
    # Prioritize medium (720p/1080p) -> large -> small
    for q in ["medium", "large", "small"]:
        if q in videos and videos[q].get("url"):
            return videos[q]["url"]
    return None

def fetch_media_for_terms(search_terms: List[str], aspect_ratio: str = "9:16", is_cartoon: bool = False) -> List[Path]:
    """
    Fetch matching video clips for a list of visual search terms.
    """
    orientation = "vertical" if aspect_ratio == "9:16" else "horizontal"
    downloaded_paths = []

    for term in search_terms:
        query = f"{term} animation 3d" if is_cartoon else term
        hits = search_pixabay_videos(query, orientation=orientation, per_page=4)
        if not hits:
            # Fallback without orientation or animation tag
            hits = search_pixabay_videos(term, per_page=4)

        if hits:
            video_url = get_best_video_download_url(hits[0])
            if video_url:
                local_file = download_file(video_url, settings.CACHE_DIR, suffix=".mp4")
                downloaded_paths.append(local_file)

    return downloaded_paths

def generate_ai_cartoon_scene_image(
    prompt: str,
    output_path: Path,
    aspect_ratio: str = "9:16",
    style: str = "3d_pixar"
) -> Path:
    """
    Generate or fetch a stunning 3D Pixar/Disney style cartoon scene image.
    Uses Pixabay high-res illustrations or AI Pollinations generator.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 5000:
        return output_path

    # Style prefix
    style_tag = "3D Pixar Disney animated film style, vibrant colors, cinematic volumetric lighting, 8k render, masterpiece"
    full_prompt = f"{prompt}, {style_tag}"

    w, h = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)

    # 1. Try Pollinations AI free generator
    try:
        encoded_prompt = urllib.parse.quote(full_prompt)
        seed = random.randint(1000, 999999)
        poll_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={w}&height={h}&nologo=true&seed={seed}&model=flux"
        logger.info(f"Generating AI Cartoon Scene: {prompt[:60]}...")
        resp = requests.get(poll_url, timeout=6)
        if resp.status_code == 200 and len(resp.content) > 5000:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path
    except Exception as e:
        logger.warning(f"AI image generation timeout/error: {e}, falling back to Pixabay illustration")

    # 2. Fallback: Search Pixabay Illustrations
    try:
        search_q = f"{prompt} cartoon 3d illustration"
        hits = search_pixabay_images(search_q, orientation="vertical" if aspect_ratio == "9:16" else "horizontal", image_type="illustration")
        if hits and hits[0].get("largeImageURL"):
            img_url = hits[0]["largeImageURL"]
            return download_file(img_url, output_path.parent, suffix=".jpg")
    except Exception as e:
        logger.error(f"Fallback illustration search failed: {e}")

    return output_path
