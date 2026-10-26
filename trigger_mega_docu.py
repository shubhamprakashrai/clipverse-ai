import sys
import uuid
from app.models.request import DocumentaryRequest, DocumentaryTheme, VideoDurationMode, VideoAspect
from app.services import task_manager

# Force UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

req = DocumentaryRequest(
    topic="India-China Arunachal Pradesh & Tawang Border Conflict: 1914 McMahon Line, 1962 War, 2022 Yangtse Clash, and Indian Army Sela Tunnel Defense",
    theme=DocumentaryTheme.GEOPOLITICAL,
    duration_mode=VideoDurationMode.LONG_10MIN,
    aspect_ratio=VideoAspect.LANDSCAPE_16_9,
    language="hi",
    voice_name="hi-IN-MadhurNeural",
    include_newspaper_clippings=True,
    subtitles_enabled=False,
    auto_upload_youtube=True,
    youtube_privacy="public",
    watermark_enabled=False,
    generate_social_pack=True
)

job_id = f"arunachal_docu_{uuid.uuid4().hex[:8]}"
print("=" * 65)
print(f"🎬 EXECUTING MEGA DOCUMENTARY JOB: {job_id}")
print(f"📌 Topic: {req.topic}")
print("=" * 65)

task_manager.run_documentary_video(job_id, req)

job = task_manager.get_job(job_id)
print("\n" + "=" * 65)
print("FINAL JOB STATUS:", job.status.value if job else "N/A")
if job and job.youtube_upload:
    print("🎉 YOUTUBE UPLOAD RESULT:", job.youtube_upload)
    print("📺 VIDEO URL:", job.youtube_upload.get("video_url"))
print("=" * 65)
