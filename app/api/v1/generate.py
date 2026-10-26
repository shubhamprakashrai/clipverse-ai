import uuid
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException
from app.core.config import settings
from app.models.request import (
    TextToVideoRequest,
    PersonalReelRequest,
    ProductAdRequest,
    DigitalInvitationRequest,
    CartoonStoryRequest,
    DocumentaryRequest
)
from app.models.response import JobResponse, JobStatus
from app.services import task_manager

router = APIRouter(prefix="/api/v1", tags=["Video Generation & Studio API"])

@router.post("/upload", summary="Upload images, logos or voice notes")
async def upload_asset(file: UploadFile = File(...)):
    """
    Upload an image (photo/logo) or audio (voice-note) to server storage.
    """
    file_id = str(uuid.uuid4())[:8]
    ext = Path(file.filename).suffix.lower()
    dest_path = settings.UPLOADS_DIR / f"upload_{file_id}{ext}"

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "success",
        "filename": file.filename,
        "local_path": str(dest_path.resolve()),
        "url": f"/static/uploads/{dest_path.name}"
    }

@router.post("/generate/text-to-video", response_model=JobResponse, summary="Mode 1: Text to Viral Reel/Short")
def generate_text_video(req: TextToVideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = JobResponse(job_id=job_id, status=JobStatus.PROCESSING, progress=5, current_stage="Job queued...")
    task_manager.jobs_db[job_id] = job
    background_tasks.add_task(task_manager.run_text_to_video, job_id, req)
    return job

@router.post("/generate/personal-reel", response_model=JobResponse, summary="Mode 2: Personal Photos to 3D Ken Burns Reel")
def generate_personal_reel(req: PersonalReelRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = JobResponse(job_id=job_id, status=JobStatus.PROCESSING, progress=5, current_stage="Job queued...")
    task_manager.jobs_db[job_id] = job
    background_tasks.add_task(task_manager.run_personal_reel, job_id, req)
    return job

@router.post("/generate/product-ad", response_model=JobResponse, summary="Mode 3: Brand & Product Ad with Auto Gap-Filling")
def generate_product_ad(req: ProductAdRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = JobResponse(job_id=job_id, status=JobStatus.PROCESSING, progress=5, current_stage="Job queued...")
    task_manager.jobs_db[job_id] = job
    background_tasks.add_task(task_manager.run_product_ad, job_id, req)
    return job

@router.post("/generate/digital-invitation", response_model=JobResponse, summary="Mode 4: Digital Video Invitation Card")
def generate_invitation(req: DigitalInvitationRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = JobResponse(job_id=job_id, status=JobStatus.PROCESSING, progress=5, current_stage="Job queued...")
    task_manager.jobs_db[job_id] = job
    background_tasks.add_task(task_manager.run_digital_invitation, job_id, req)
    return job

@router.post("/generate/cartoon-story", response_model=JobResponse, summary="Mode 5: AI 3D Cartoon Story (Pixar/Disney Kahaniyan)")
def generate_cartoon_story(req: CartoonStoryRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    job = JobResponse(job_id=job_id, status=JobStatus.PROCESSING, progress=5, current_stage="Job queued...")
    task_manager.jobs_db[job_id] = job
    background_tasks.add_task(task_manager.run_cartoon_story, job_id, req)
    return job

@router.get("/jobs", response_model=List[JobResponse], summary="List all recent jobs")
def list_jobs():
    return list(task_manager.jobs_db.values())

@router.get("/jobs/{job_id}", response_model=JobResponse, summary="Get Job Status, Video & WhatsApp URLs")
def get_job_status(job_id: str):
    job = task_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return job



@router.post("/generate/documentary", response_model=JobResponse, summary="Mode 6: Long-Form Cinematic Documentary (5-10 Min)")
def generate_documentary(req: DocumentaryRequest, background_tasks: BackgroundTasks):
    """
    Mode 6: Long-form Vox / MagnatesMedia / Dhruv Rathee style investigative documentary.
    Supports 5-min, 8-min, and 10-min formats with newspaper headline clippings, archival B-roll, and optional YouTube upload.
    """
    job_id = str(uuid.uuid4())
    job = JobResponse(job_id=job_id, status=JobStatus.PROCESSING, progress=5, current_stage="Documentary job queued...")
    task_manager.jobs_db[job_id] = job
    background_tasks.add_task(task_manager.run_documentary_video, job_id, req)
    return job

@router.get("/youtube/status", summary="Check YouTube Data API credentials & connection")
def get_yt_status():
    from app.services import youtube_uploader
    return youtube_uploader.get_youtube_auth_status()

@router.post("/youtube/upload", summary="Manually publish an existing job to YouTube")
def publish_to_youtube(job_id: str, privacy: str = "unlisted"):
    job = task_manager.get_job(job_id)
    if not job or not job.video_url:
        raise HTTPException(status_code=400, detail="Job has no completed video")

    from app.services import youtube_uploader
    video_path = settings.OUTPUT_DIR / job_id / "final_reel.mp4"
    title = (job.social_pack or {}).get("title", f"Documentary - {job_id[:8]}")
    desc = (job.social_pack or {}).get("description", job.script or "")
    tags = (job.social_pack or {}).get("hashtags", ["documentary", "history"])

    res = youtube_uploader.upload_video_to_youtube(
        video_path=video_path,
        title=title,
        description=desc,
        tags=tags,
        privacy_status=privacy
    )
    return res
