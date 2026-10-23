from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class VideoAspect(str, Enum):
    PORTRAIT_9_16 = "9:16"      # Shorts, Reels, TikTok (1080x1920)
    LANDSCAPE_16_9 = "16:9"     # YouTube Standard (1920x1080)
    SQUARE_1_1 = "1:1"          # Instagram Square (1080x1080)

class VideoDurationMode(str, Enum):
    REEL_30S = "30s"            # Quick 30-sec viral reel
    REEL_60S = "60s"            # Standard 60-sec story
    LONG_3MIN = "3min"          # 3-minute YouTube long story
    LONG_4MIN = "4min"          # 4-minute YouTube episode

class CreationMode(str, Enum):
    TEXT_TO_VIDEO = "text_to_video"
    PERSONAL_REEL = "personal_reel"
    PRODUCT_AD = "product_ad"
    DIGITAL_INVITATION = "digital_invitation"
    CARTOON_STORY = "cartoon_story"

class TextToVideoRequest(BaseModel):
    topic: str = Field(..., description="Topic or prompt for the video", example="3 Incredible facts about Mars")
    language: str = Field("hi", description="Script language: 'hi' (Hindi/Hinglish) or 'en' (English)", example="hi")
    aspect_ratio: VideoAspect = Field(VideoAspect.PORTRAIT_9_16, description="Video aspect ratio")
    voice_name: Optional[str] = Field(None, description="Optional TTS Voice. If None, auto-detected from language")
    duration_mode: VideoDurationMode = Field(VideoDurationMode.REEL_30S, description="Target video duration")
    watermark_enabled: bool = Field(True, description="False for paid subscribers (removes watermark)")
    custom_audio_path: Optional[str] = Field(None, description="Optional user voice note or MP3 file to bypass TTS")
    generate_social_pack: bool = Field(True, description="Generate viral title, description and 15 hashtags")
    include_bgm: bool = Field(True, description="Whether to include background music")

class PersonalReelRequest(BaseModel):
    idea_prompt: str = Field(..., description="Context or story behind the photos", example="Our family vacation in Goa")
    image_paths: List[str] = Field(..., description="List of local uploaded image file paths", min_length=1)
    language: str = Field("hi", description="Script language: 'hi' or 'en'")
    aspect_ratio: VideoAspect = Field(VideoAspect.PORTRAIT_9_16, description="Video aspect ratio")
    voice_name: Optional[str] = Field(None, description="TTS Voice name. If None, auto-detected")
    watermark_enabled: bool = Field(True, description="False for paid subscribers")
    custom_audio_path: Optional[str] = Field(None, description="Optional user voice-note")
    generate_social_pack: bool = Field(True, description="Generate title and hashtags")
    include_bgm: bool = Field(True, description="Whether to include background music")

class ProductAdRequest(BaseModel):
    product_name: str = Field(..., description="Name of the product or brand", example="Royal Oud Luxury Perfume")
    product_description: str = Field(..., description="Key features or benefits", example="Long lasting 24hr fragrance for party and work")
    offer_text: Optional[str] = Field("FLAT 20% OFF | LIMITED TIME", description="Promotional discount or offer headline")
    call_to_action: str = Field("Order Now | Link in Bio", description="Call to action text for the outro card")
    product_image_paths: List[str] = Field(..., description="Product photo file paths", min_length=1)
    logo_path: Optional[str] = Field(None, description="Optional transparent brand logo file path")
    auto_fill_online: bool = Field(True, description="Fill missing scenes with matching Pixabay B-roll footage")
    language: str = Field("hi", description="Script language: 'hi' or 'en'")
    aspect_ratio: VideoAspect = Field(VideoAspect.PORTRAIT_9_16, description="Video aspect ratio")
    voice_name: Optional[str] = Field(None, description="TTS Voice name")
    watermark_enabled: bool = Field(True, description="False for paid subscribers")
    custom_audio_path: Optional[str] = Field(None, description="Optional audio voice note")
    generate_social_pack: bool = Field(True, description="Generate title and hashtags")

class DigitalInvitationRequest(BaseModel):
    event_type: str = Field(..., description="Type of event: wedding, birthday, housewarming, opening", example="wedding")
    host_names: str = Field(..., description="Hosts or Couple names", example="Aman & Priya")
    event_date: str = Field(..., description="Date & Time of the event", example="25th December 2026, 7:00 PM onwards")
    venue: str = Field(..., description="Venue details", example="The Grand Palace Hotel, Jaipur")
    rsvp: Optional[str] = Field("Sharma & Verma Family - 9876543210", description="RSVP contact details")
    photo_paths: List[str] = Field([], description="Optional 1-2 photos of couple or celebrant")
    music_theme: str = Field("royal_shehnai", description="Music vibe: royal_shehnai, celebration, acoustic")
    language: str = Field("hi", description="Invitation language: 'hi' or 'en'")
    aspect_ratio: VideoAspect = Field(VideoAspect.PORTRAIT_9_16, description="Video aspect ratio")
    watermark_enabled: bool = Field(True, description="False for paid subscribers")
    generate_social_pack: bool = Field(True, description="Generate WhatsApp message copy")

class CartoonStoryRequest(BaseModel):
    story_topic: str = Field(..., description="Story concept or plot", example="Jungle me jaadui jharne ka rahasya - Rohan aur bimar maa")
    character_style: str = Field("3d_pixar", description="Visual style: '3d_pixar', 'anime', '2d_disney'")
    duration_mode: VideoDurationMode = Field(VideoDurationMode.REEL_60S, description="Target duration: 30s, 60s, 3min, 4min")
    language: str = Field("hi", description="Language: 'hi' (Hinglish/Hindi) or 'en'")
    aspect_ratio: VideoAspect = Field(VideoAspect.PORTRAIT_9_16, description="Video aspect ratio (9:16 for Reels, 16:9 for YouTube)")
    voice_name: Optional[str] = Field(None, description="Voice: auto-detected or specific character voice")
    watermark_enabled: bool = Field(True, description="False for paid subscribers")
    include_sfx: bool = Field(True, description="Include ambient sound effects and dramatic scoring")
    generate_social_pack: bool = Field(True, description="Generate viral title, description and 15 hashtags")
