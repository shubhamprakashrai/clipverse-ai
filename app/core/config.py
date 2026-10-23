from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "ReelCraft-AI"
    APP_ENV: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # AI Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # Stock Media
    PIXABAY_API_KEY: str = ""

    # Storage Paths
    STORAGE_DIR: Path = BASE_DIR / "storage"
    UPLOADS_DIR: Path = BASE_DIR / "storage" / "uploads"
    OUTPUT_DIR: Path = BASE_DIR / "storage" / "output"
    CACHE_DIR: Path = BASE_DIR / "storage" / "cache"
    BGM_DIR: Path = BASE_DIR / "storage" / "bgm"

    # Assets Paths
    ASSETS_DIR: Path = BASE_DIR / "assets"
    FONTS_DIR: Path = BASE_DIR / "assets" / "fonts"
    DEFAULT_FONT_PATH: Path = BASE_DIR / "assets" / "fonts" / "NotoSansDevanagari-Bold.ttf"
    FALLBACK_FONT_PATH: Path = BASE_DIR / "assets" / "fonts" / "Nirmala.ttc"
    WATERMARK_PATH: Path = BASE_DIR / "assets" / "watermark" / "reelcraft_watermark.png"
    FRAMES_DIR: Path = BASE_DIR / "assets" / "frames"
    SFX_DIR: Path = BASE_DIR / "assets" / "sfx"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
for path in [
    settings.STORAGE_DIR,
    settings.UPLOADS_DIR,
    settings.OUTPUT_DIR,
    settings.CACHE_DIR,
    settings.BGM_DIR,
    settings.ASSETS_DIR,
    settings.FONTS_DIR,
    settings.FRAMES_DIR,
    settings.SFX_DIR,
    settings.WATERMARK_PATH.parent
]:
    path.mkdir(parents=True, exist_ok=True)
