import sys
import time
from pathlib import Path

# Enable UTF-8 for Hindi characters on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from app.models.request import TextToVideoRequest, VideoAspect, VideoDurationMode
from app.services import task_manager

def main():
    print("==================================================")
    print("Testing ReelCraft-AI Fast Engine (Phase 1 Verifier)")
    print("==================================================")
    
    start_time = time.time()
    job_id = "test_verification_01"
    
    req = TextToVideoRequest(
        topic="जंगल के जादुई झरने का रहस्य",
        language="hi",
        aspect_ratio=VideoAspect.PORTRAIT_9_16,
        duration_mode=VideoDurationMode.REEL_30S,
        watermark_enabled=True,
        include_bgm=False,
        generate_social_pack=True
    )
    
    print(f"Starting test job: {job_id}...")
    task_manager.run_text_to_video(job_id, req)
    
    elapsed = time.time() - start_time
    job = task_manager.get_job(job_id)
    
    print("--------------------------------------------------")
    print(f"Status: {job.status}")
    print(f"Total Elapsed Time: {elapsed:.2f} seconds")
    print(f"Progress: {job.progress}%")
    print(f"Video URL: {job.video_url}")
    print(f"WhatsApp URL: {job.whatsapp_video_url}")
    print(f"Script: {job.script}")
    if job.social_pack:
        print(f"Viral Title: {job.social_pack.get('title')}")
        print(f"Hashtags: {' '.join(job.social_pack.get('hashtags', [])[:6])}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
