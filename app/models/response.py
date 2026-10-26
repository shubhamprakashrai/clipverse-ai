from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SocialMediaPack(BaseModel):
    title: str = Field("", description="Catchy Hook Title")
    description: str = Field("", description="YouTube / Instagram Description")
    hashtags: List[str] = Field([], description="15 Trending Hashtags")

class JobResponse(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(JobStatus.PENDING, description="Current status of the video job")
    progress: int = Field(0, description="Progress percentage (0-100)")
    current_stage: str = Field("queued", description="Human-readable stage description")
    video_url: Optional[str] = Field(None, description="Streamable / downloadable HD video URL")
    whatsapp_video_url: Optional[str] = Field(None, description="WhatsApp-optimized <15MB crystal-clear video URL")
    script: Optional[str] = Field(None, description="Generated narration script")
    social_pack: Optional[Dict[str, Any]] = Field(None, description="Viral Title, Description and Hashtags")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    watermark_applied: bool = Field(True, description="Whether watermark was burned")
    youtube_upload: Optional[Dict[str, Any]] = Field(None, description="YouTube upload response including video URL")
    error: Optional[str] = Field(None, description="Error message if job failed")
