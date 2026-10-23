import json
import shutil
import uuid
from pathlib import Path
from typing import Dict
from loguru import logger
from app.core.config import settings
from app.models.request import (
    TextToVideoRequest,
    PersonalReelRequest,
    ProductAdRequest,
    DigitalInvitationRequest,
    CartoonStoryRequest
)
from app.models.response import JobResponse, JobStatus
from app.services import ai_storyboard, voice_engine, media_service, ffmpeg_renderer

# In-memory job repository (ready to connect to Redis / PostgreSQL in Phase 4)
jobs_db: Dict[str, JobResponse] = {}

def get_job(job_id: str) -> JobResponse:
    return jobs_db.get(job_id, JobResponse(job_id=job_id, status=JobStatus.FAILED, error="Job not found"))

def update_job(job_id: str, status: JobStatus, progress: int, current_stage: str, **kwargs):
    if job_id not in jobs_db:
        jobs_db[job_id] = JobResponse(job_id=job_id, status=status, progress=progress, current_stage=current_stage)
    else:
        jobs_db[job_id].status = status
        jobs_db[job_id].progress = progress
        jobs_db[job_id].current_stage = current_stage
    for k, v in kwargs.items():
        if hasattr(jobs_db[job_id], k):
            setattr(jobs_db[job_id], k, v)

def run_text_to_video(job_id: str, req: TextToVideoRequest):
    """
    Mode 1: Text-to-Video Engine (Shorts, Facts, Stories).
    """
    job_dir = settings.OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Storyboard
        update_job(job_id, JobStatus.PROCESSING, 15, "AI writing script & visual keywords...")
        storyboard = ai_storyboard.generate_text_storyboard(
            req.topic, language=req.language, duration_mode=req.duration_mode.value
        )
        script_text = storyboard.get("full_script", "")
        scenes = storyboard.get("scenes", [])
        social_pack = storyboard.get("social_pack", {})

        # Step 2: Voiceover or Custom Audio
        update_job(job_id, JobStatus.PROCESSING, 35, "Generating voiceover & synced subtitles...")
        audio_path = job_dir / "voiceover.mp3"
        srt_path = job_dir / "subtitles.srt"

        if req.custom_audio_path and Path(req.custom_audio_path).exists():
            voice_engine.process_custom_voice_note(Path(req.custom_audio_path), audio_path, srt_path, script_text)
        else:
            voice_engine.synthesize_voice(script_text, req.voice_name, audio_path, srt_path, language=req.language)

        # Step 3: Fetch Stock Media
        update_job(job_id, JobStatus.PROCESSING, 60, "Downloading HD stock clips from Pixabay...")
        search_terms = [s.get("visual_search_term", req.topic) for s in scenes]
        raw_clips = media_service.fetch_media_for_terms(search_terms, aspect_ratio=req.aspect_ratio.value)

        if not raw_clips:
            raw_clips = media_service.fetch_media_for_terms([req.topic], aspect_ratio=req.aspect_ratio.value)

        # Step 4: Fit & Resize Clips
        update_job(job_id, JobStatus.PROCESSING, 80, "Formatting and cropping video clips...")
        processed_clips = []
        clip_duration = 3.5
        for i, clip in enumerate(raw_clips):
            out_clip = job_dir / f"clip_{i}.mp4"
            fitted = ffmpeg_renderer.resize_and_fit_clip(clip, out_clip, clip_duration, req.aspect_ratio.value)
            processed_clips.append(fitted)

        # Step 5: Final Assembly
        update_job(job_id, JobStatus.PROCESSING, 90, "Assembling video with subtitles & music...")
        final_mp4 = job_dir / "final_reel.mp4"
        bgm_files = list(settings.BGM_DIR.glob("*.mp3"))
        bgm_path = bgm_files[0] if (req.include_bgm and bgm_files) else None

        ffmpeg_renderer.assemble_final_video(
            clips=processed_clips,
            audio_path=audio_path,
            subtitle_path=srt_path,
            output_path=final_mp4,
            bgm_path=bgm_path,
            watermark_enabled=req.watermark_enabled,
            aspect_ratio=req.aspect_ratio.value
        )

        # Step 6: WhatsApp Status Optimizer (<15MB)
        whatsapp_mp4 = job_dir / "final_reel_whatsapp.mp4"
        ffmpeg_renderer.optimize_for_whatsapp(final_mp4, whatsapp_mp4)

        duration = voice_engine.get_audio_duration(audio_path)
        update_job(
            job_id,
            JobStatus.COMPLETED,
            100,
            "Video completed!",
            video_url=f"/static/output/{job_id}/final_reel.mp4",
            whatsapp_video_url=f"/static/output/{job_id}/final_reel_whatsapp.mp4",
            script=script_text,
            social_pack=social_pack,
            duration=duration,
            watermark_applied=req.watermark_enabled
        )

    except Exception as e:
        logger.error(f"[{job_id}] Text-to-video task failed: {e}")
        update_job(job_id, JobStatus.FAILED, 0, "Failed", error=str(e))

def run_personal_reel(job_id: str, req: PersonalReelRequest):
    """
    Mode 2: Personal Creator Mode with Ken Burns Motion.
    """
    job_dir = settings.OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Storyboard
        update_job(job_id, JobStatus.PROCESSING, 15, "AI crafting narration for your photos...")
        storyboard = ai_storyboard.generate_personal_storyboard(req.idea_prompt, len(req.image_paths), req.language)
        script_text = storyboard.get("full_script", "")

        # Step 2: Audio
        update_job(job_id, JobStatus.PROCESSING, 35, "Generating emotional narration...")
        audio_path = job_dir / "voiceover.mp3"
        srt_path = job_dir / "subtitles.srt"

        if req.custom_audio_path and Path(req.custom_audio_path).exists():
            voice_engine.process_custom_voice_note(Path(req.custom_audio_path), audio_path, srt_path, script_text)
        else:
            voice_engine.synthesize_voice(script_text, req.voice_name, audio_path, srt_path, language=req.language)

        # Step 3: 3D Ken Burns Motion
        update_job(job_id, JobStatus.PROCESSING, 65, "Applying 3D camera pan & zoom to photos...")
        processed_clips = []
        clip_duration = 4.0
        for i, img_path_str in enumerate(req.image_paths):
            img_path = Path(img_path_str)
            out_clip = job_dir / f"motion_photo_{i}.mp4"
            motion_clip = ffmpeg_renderer.image_to_motion_clip(img_path, out_clip, clip_duration, req.aspect_ratio.value)
            processed_clips.append(motion_clip)

        # Step 4: Final Assembly
        update_job(job_id, JobStatus.PROCESSING, 90, "Merging music, motion photos & subtitles...")
        final_mp4 = job_dir / "final_reel.mp4"
        bgm_files = list(settings.BGM_DIR.glob("*.mp3"))
        bgm_path = bgm_files[0] if (req.include_bgm and bgm_files) else None

        ffmpeg_renderer.assemble_final_video(
            clips=processed_clips,
            audio_path=audio_path,
            subtitle_path=srt_path,
            output_path=final_mp4,
            bgm_path=bgm_path,
            watermark_enabled=req.watermark_enabled,
            aspect_ratio=req.aspect_ratio.value
        )

        whatsapp_mp4 = job_dir / "final_reel_whatsapp.mp4"
        ffmpeg_renderer.optimize_for_whatsapp(final_mp4, whatsapp_mp4)

        duration = voice_engine.get_audio_duration(audio_path)
        update_job(
            job_id,
            JobStatus.COMPLETED,
            100,
            "Personal reel completed!",
            video_url=f"/static/output/{job_id}/final_reel.mp4",
            whatsapp_video_url=f"/static/output/{job_id}/final_reel_whatsapp.mp4",
            script=script_text,
            duration=duration,
            watermark_applied=req.watermark_enabled
        )

    except Exception as e:
        logger.error(f"[{job_id}] Personal reel failed: {e}")
        update_job(job_id, JobStatus.FAILED, 0, "Failed", error=str(e))

def run_product_ad(job_id: str, req: ProductAdRequest):
    """
    Mode 3: Brand & Product Ad with Gap-Filling.
    """
    job_dir = settings.OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Copy Brand Logo
        logo_file = None
        if req.logo_path and Path(req.logo_path).exists():
            logo_file = job_dir / f"brand_logo{Path(req.logo_path).suffix}"
            shutil.copy(req.logo_path, logo_file)

        # Step 2: Commercial Script
        update_job(job_id, JobStatus.PROCESSING, 15, "AI writing high-converting ad copy...")
        storyboard = ai_storyboard.generate_product_ad_storyboard(
            req.product_name, req.product_description, req.offer_text or "", req.call_to_action,
            len(req.product_image_paths), req.language
        )
        script_text = storyboard.get("full_script", "")
        scenes = storyboard.get("scenes", [])
        social_pack = storyboard.get("social_pack", {})

        # Step 3: Audio
        update_job(job_id, JobStatus.PROCESSING, 35, "Generating energetic voiceover...")
        audio_path = job_dir / "voiceover.mp3"
        srt_path = job_dir / "subtitles.srt"

        if req.custom_audio_path and Path(req.custom_audio_path).exists():
            voice_engine.process_custom_voice_note(Path(req.custom_audio_path), audio_path, srt_path, script_text)
        else:
            voice_engine.synthesize_voice(script_text, req.voice_name, audio_path, srt_path, language=req.language)

        # Step 4: Hybrid Gap-Filling Media
        update_job(job_id, JobStatus.PROCESSING, 65, "Blending product photos & lifestyle B-roll...")
        processed_clips = []
        product_photo_idx = 0

        for i, scene in enumerate(scenes):
            scene_type = scene.get("type", "online_stock")
            out_clip = job_dir / f"scene_{i}.mp4"

            if scene_type == "product_photo" and product_photo_idx < len(req.product_image_paths):
                img_path = Path(req.product_image_paths[product_photo_idx])
                product_photo_idx += 1
                ffmpeg_renderer.image_to_motion_clip(img_path, out_clip, duration=3.5, aspect_ratio=req.aspect_ratio.value)
                processed_clips.append(out_clip)
            else:
                term = scene.get("visual_search_term", req.product_name)
                stock_clips = media_service.fetch_media_for_terms([term], aspect_ratio=req.aspect_ratio.value)
                if stock_clips:
                    fitted = ffmpeg_renderer.resize_and_fit_clip(stock_clips[0], out_clip, 3.5, req.aspect_ratio.value)
                    processed_clips.append(fitted)
                elif product_photo_idx > 0:
                    img_path = Path(req.product_image_paths[0])
                    ffmpeg_renderer.image_to_motion_clip(img_path, out_clip, duration=3.5, aspect_ratio=req.aspect_ratio.value)
                    processed_clips.append(out_clip)

        # Step 5: Assembly
        update_job(job_id, JobStatus.PROCESSING, 90, "Applying brand logo, captions & music...")
        final_mp4 = job_dir / "final_reel.mp4"
        bgm_files = list(settings.BGM_DIR.glob("*.mp3"))
        bgm_path = bgm_files[0] if bgm_files else None

        ffmpeg_renderer.assemble_final_video(
            clips=processed_clips,
            audio_path=audio_path,
            subtitle_path=srt_path,
            output_path=final_mp4,
            bgm_path=bgm_path,
            logo_path=logo_file,
            watermark_enabled=req.watermark_enabled,
            aspect_ratio=req.aspect_ratio.value
        )

        whatsapp_mp4 = job_dir / "final_reel_whatsapp.mp4"
        ffmpeg_renderer.optimize_for_whatsapp(final_mp4, whatsapp_mp4)

        duration = voice_engine.get_audio_duration(audio_path)
        update_job(
            job_id,
            JobStatus.COMPLETED,
            100,
            "Commercial ad completed!",
            video_url=f"/static/output/{job_id}/final_reel.mp4",
            whatsapp_video_url=f"/static/output/{job_id}/final_reel_whatsapp.mp4",
            script=script_text,
            social_pack=social_pack,
            duration=duration,
            watermark_applied=req.watermark_enabled
        )

    except Exception as e:
        logger.error(f"[{job_id}] Product ad failed: {e}")
        update_job(job_id, JobStatus.FAILED, 0, "Failed", error=str(e))

def run_digital_invitation(job_id: str, req: DigitalInvitationRequest):
    """
    Mode 4: Digital Video Invitation (Weddings, Birthdays, Royal Events).
    """
    job_dir = settings.OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Royal Script
        update_job(job_id, JobStatus.PROCESSING, 15, "AI designing royal invitation storyboard...")
        storyboard = ai_storyboard.generate_invitation_storyboard(
            req.event_type, req.host_names, req.event_date, req.venue, req.rsvp or "", req.language
        )
        script_text = storyboard.get("full_script", "")
        scenes = storyboard.get("scenes", [])

        # Step 2: Voiceover
        update_job(job_id, JobStatus.PROCESSING, 35, "Generating warm invitation narration...")
        audio_path = job_dir / "voiceover.mp3"
        srt_path = job_dir / "subtitles.srt"
        voice_engine.synthesize_voice(script_text, "hi-IN-MadhurNeural", audio_path, srt_path, language=req.language)

        # Step 3: Visuals & Motion Clips
        update_job(job_id, JobStatus.PROCESSING, 65, "Preparing royal festive visuals...")
        processed_clips = []
        clip_duration = 4.0

        for i, scene in enumerate(scenes):
            out_clip = job_dir / f"scene_{i}.mp4"
            term = scene.get("visual_search_term", "royal wedding celebration palace")
            clips = media_service.fetch_media_for_terms([term], aspect_ratio=req.aspect_ratio.value)
            if clips:
                fitted = ffmpeg_renderer.resize_and_fit_clip(clips[0], out_clip, clip_duration, req.aspect_ratio.value)
                processed_clips.append(fitted)
            elif req.photo_paths:
                # Use celebrant's photo with 3D zoom
                p = Path(req.photo_paths[i % len(req.photo_paths)])
                motion = ffmpeg_renderer.image_to_motion_clip(p, out_clip, clip_duration, req.aspect_ratio.value)
                processed_clips.append(motion)

        # Step 4: Final Montage
        update_job(job_id, JobStatus.PROCESSING, 90, "Adding traditional shehnai music & gold titles...")
        final_mp4 = job_dir / "final_reel.mp4"
        bgm_files = list(settings.BGM_DIR.glob("*.mp3"))
        bgm_path = bgm_files[0] if bgm_files else None

        ffmpeg_renderer.assemble_final_video(
            clips=processed_clips,
            audio_path=audio_path,
            subtitle_path=srt_path,
            output_path=final_mp4,
            bgm_path=bgm_path,
            watermark_enabled=req.watermark_enabled,
            aspect_ratio=req.aspect_ratio.value
        )

        whatsapp_mp4 = job_dir / "final_reel_whatsapp.mp4"
        ffmpeg_renderer.optimize_for_whatsapp(final_mp4, whatsapp_mp4)

        duration = voice_engine.get_audio_duration(audio_path)
        update_job(
            job_id,
            JobStatus.COMPLETED,
            100,
            "Digital invitation completed!",
            video_url=f"/static/output/{job_id}/final_reel.mp4",
            whatsapp_video_url=f"/static/output/{job_id}/final_reel_whatsapp.mp4",
            script=script_text,
            duration=duration,
            watermark_applied=req.watermark_enabled
        )

    except Exception as e:
        logger.error(f"[{job_id}] Digital invitation failed: {e}")
        update_job(job_id, JobStatus.FAILED, 0, "Failed", error=str(e))

def run_cartoon_story(job_id: str, req: CartoonStoryRequest):
    """
    Mode 5: AI 3D Cartoon Storyteller (Pixar/Disney 3D Animated Kahaniyan).
    """
    job_dir = settings.OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Cartoon Storyboard with Scene Art Prompts
        update_job(job_id, JobStatus.PROCESSING, 15, "AI writing 3D cartoon screenplay & scenes...")
        storyboard = ai_storyboard.generate_cartoon_storyboard(
            req.story_topic, duration_mode=req.duration_mode.value,
            character_style=req.character_style, language=req.language
        )
        script_text = storyboard.get("full_script", "")
        scenes = storyboard.get("scenes", [])
        social_pack = storyboard.get("social_pack", {})

        # Step 2: Animated Storyteller Voiceover
        update_job(job_id, JobStatus.PROCESSING, 35, "Generating animated storyteller narration...")
        audio_path = job_dir / "voiceover.mp3"
        srt_path = job_dir / "subtitles.srt"
        voice_engine.synthesize_voice(script_text, req.voice_name, audio_path, srt_path, language=req.language)

        # Step 3: Generate 3D Cartoon Scene Artwork & Motion
        update_job(job_id, JobStatus.PROCESSING, 65, "Creating 3D Pixar-style scene artwork & camera motion...")
        processed_clips = []
        clip_duration = 4.0

        for i, scene in enumerate(scenes):
            img_prompt = scene.get("visual_image_prompt", req.story_topic)
            scene_img_path = job_dir / f"cartoon_art_{i}.jpg"
            out_clip = job_dir / f"scene_{i}.mp4"

            # Generate or fetch 3D cartoon scene image
            media_service.generate_ai_cartoon_scene_image(
                img_prompt, scene_img_path, aspect_ratio=req.aspect_ratio.value, style=req.character_style
            )

            if scene_img_path.exists() and scene_img_path.stat().st_size > 1000:
                # Apply 3D Ken Burns Camera Pan & Zoom motion
                motion = ffmpeg_renderer.image_to_motion_clip(
                    scene_img_path, out_clip, duration=clip_duration, aspect_ratio=req.aspect_ratio.value
                )
                processed_clips.append(motion)
            else:
                # Fallback to animated stock video
                term = scene.get("visual_search_term", "3d cartoon animation")
                clips = media_service.fetch_media_for_terms([term], aspect_ratio=req.aspect_ratio.value, is_cartoon=True)
                if clips:
                    fitted = ffmpeg_renderer.resize_and_fit_clip(clips[0], out_clip, clip_duration, req.aspect_ratio.value)
                    processed_clips.append(fitted)

        # Step 4: Final Assembly with Ambient Scoring & Subtitles
        update_job(job_id, JobStatus.PROCESSING, 90, "Final rendering with magical music & subtitles...")
        final_mp4 = job_dir / "final_reel.mp4"
        bgm_files = list(settings.BGM_DIR.glob("*.mp3"))
        bgm_path = bgm_files[0] if bgm_files else None

        ffmpeg_renderer.assemble_final_video(
            clips=processed_clips,
            audio_path=audio_path,
            subtitle_path=srt_path,
            output_path=final_mp4,
            bgm_path=bgm_path,
            watermark_enabled=req.watermark_enabled,
            aspect_ratio=req.aspect_ratio.value
        )

        whatsapp_mp4 = job_dir / "final_reel_whatsapp.mp4"
        ffmpeg_renderer.optimize_for_whatsapp(final_mp4, whatsapp_mp4)

        duration = voice_engine.get_audio_duration(audio_path)
        update_job(
            job_id,
            JobStatus.COMPLETED,
            100,
            "Cartoon animated story completed!",
            video_url=f"/static/output/{job_id}/final_reel.mp4",
            whatsapp_video_url=f"/static/output/{job_id}/final_reel_whatsapp.mp4",
            script=script_text,
            social_pack=social_pack,
            duration=duration,
            watermark_applied=req.watermark_enabled
        )

    except Exception as e:
        logger.error(f"[{job_id}] Cartoon story task failed: {e}")
        update_job(job_id, JobStatus.FAILED, 0, "Failed", error=str(e))
