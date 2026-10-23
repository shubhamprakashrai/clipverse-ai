import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.generate import router as api_router
from app.models.response import JobResponse, JobStatus
from app.services import task_manager

app = FastAPI(
    title="ReelCraft-AI Video Creation Studio",
    description="Commercial-grade AI Video Studio & SaaS Engine supporting 5 production modes: Text-to-Video, Personal Reels, Brand Ads with Gap-Filling, Digital Invitations, and 3D Cartoon Kahaniyan.",
    version="1.0.0"
)

# Enable CORS for Next.js Studio and Mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed verified test reel so Studio has instant playback
task_manager.jobs_db["test_verification_01"] = JobResponse(
    job_id="test_verification_01",
    status=JobStatus.COMPLETED,
    progress=100,
    current_stage="Video completed!",
    video_url="/static/output/test_verification_01/final_reel.mp4",
    whatsapp_video_url="/static/output/test_verification_01/final_reel_whatsapp.mp4",
    duration=13.9,
    watermark_applied=True,
    script="Mars yaani Lal Grah ke 3 hairatangez rahasya. Pehla: Mars par suryast neela dikhta hai. Doosra: Mars par hamare solar system ka sabse bada jwalamukhi Olympus Mons maujood hai. Teesra: Mars ka ek saal dharti ke 687 dinon ke barabar hota hai.",
    social_pack={
        "title": "Mars Ke 3 Aise Rahasya Jo Scientists Ko Hairan Kar Dete Hain 🔴🚀",
        "description": "Kyu Mars ka ek saal dharti se dugna hota hai? Jaaniye Lal Grah ke 3 hairatangez rahasya is video me. Like aur Subscribe zaroor karein!",
        "hashtags": ["#mars", "#spacefacts", "#sciencefacts", "#solarsystem", "#reels", "#viralshorts", "#hindifacts", "#universe", "#chandrayaan", "#isro", "#nasa", "#astronomy", "#amazingfacts", "#knowledge", "#reelcraft"]
    }
)

# Mount static file directories for streaming and downloading generated videos
app.mount("/static/output", StaticFiles(directory=str(settings.OUTPUT_DIR)), name="output")
app.mount("/static/uploads", StaticFiles(directory=str(settings.UPLOADS_DIR)), name="uploads")
app.mount("/static/assets", StaticFiles(directory=str(settings.ASSETS_DIR)), name="assets")

# Include API endpoints
app.include_router(api_router)

# Mount web studio dashboard
web_dir = Path(__file__).resolve().parent.parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

