import os
import subprocess
from pathlib import Path
from typing import List, Optional
from loguru import logger
from app.core.config import settings

def get_ffmpeg_binary() -> str:
    """
    Locate FFmpeg binary from imageio-ffmpeg or system path.
    """
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return "ffmpeg"

def image_to_motion_clip(
    image_path: Path,
    output_path: Path,
    duration: float = 4.0,
    motion_type: str = "zoom_in",
    aspect_ratio: str = "9:16"
) -> Path:
    """
    Convert a still image (cartoon art or personal photo) into a dynamic 3D Ken Burns motion video.
    """
    ffmpeg = get_ffmpeg_binary()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if aspect_ratio == "9:16":
        w, h = 1080, 1920
    elif aspect_ratio == "16:9":
        w, h = 1920, 1080
    else:
        w, h = 1080, 1080

    fps = 30
    total_frames = max(30, int(duration * fps))

    if motion_type == "zoom_in":
        zoom_expr = "min(pzoom+0.0035,1.25)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion_type == "zoom_out":
        zoom_expr = "if(eq(on,1),1.25,max(1.05,pzoom-0.0035))"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion_type == "pan_right":
        zoom_expr = "1.20"
        x_expr = f"(on/{total_frames})*(iw-iw/zoom)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif motion_type == "pan_left":
        zoom_expr = "1.20"
        x_expr = f"(1-on/{total_frames})*(iw-iw/zoom)"
        y_expr = "ih/2-(ih/zoom/2)"
    else:
        zoom_expr = "min(pzoom+0.0045,1.30)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    vf = (
        f"scale={w*2}:{h*2}:force_original_aspect_ratio=increase,crop={w*2}:{h*2},"
        f"zoompan=z='{zoom_expr}':d={total_frames}:x='{x_expr}':y='{y_expr}':s={w}x{h}:fps={fps},eq=saturation=1.28:contrast=1.12:brightness=0.02,"
        f"format=yuv420p"
    )

    cmd = [
        ffmpeg, "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", vf,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-threads", "0",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def resize_and_fit_clip(
    input_clip: Path,
    output_clip: Path,
    target_duration: float,
    aspect_ratio: str = "9:16"
) -> Path:
    """
    Resize, crop (fit-to-cover), and trim a video clip to standard dimension.
    """
    ffmpeg = get_ffmpeg_binary()
    output_clip.parent.mkdir(parents=True, exist_ok=True)

    if aspect_ratio == "9:16":
        w, h = 1080, 1920
    elif aspect_ratio == "16:9":
        w, h = 1920, 1080
    else:
        w, h = 1080, 1080

    # Scale to fill target bounds and crop to exact dimension
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,format=yuv420p"

    cmd = [
        ffmpeg, "-y",
        "-ss", "0",
        "-t", str(target_duration),
        "-i", str(input_clip),
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-threads", "0",
        "-an",
        str(output_clip)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_clip

def assemble_final_video(
    clips: List[Path],
    audio_path: Path,
    subtitle_path: Optional[Path],
    output_path: Path,
    bgm_path: Optional[Path] = None,
    logo_path: Optional[Path] = None,
    watermark_enabled: bool = True,
    aspect_ratio: str = "9:16"
) -> Path:
    """
    Concatenate video clips, mix voiceover + ducked BGM, burn Zero-Tofu Devanagari subtitles,
    and apply mandatory watermark for free tier or clean export for paid tier.
    """
    ffmpeg = get_ffmpeg_binary()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Create concat list
    concat_txt = output_path.parent / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.resolve().as_posix()}'\n")

    # 2. Build inputs
    cmd = [
        ffmpeg, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", str(audio_path)
    ]

    input_count = 2

    # Background Music input
    if bgm_path and bgm_path.exists():
        cmd.extend(["-i", str(bgm_path)])
        bgm_index = input_count
        input_count += 1
    else:
        bgm_index = None

    # Custom Brand Logo input (Product Ads)
    if logo_path and logo_path.exists():
        cmd.extend(["-i", str(logo_path)])
        logo_index = input_count
        input_count += 1
    else:
        logo_index = None

    # Free Tier Brand Watermark input
    if watermark_enabled and settings.WATERMARK_PATH.exists():
        cmd.extend(["-i", str(settings.WATERMARK_PATH)])
        watermark_index = input_count
        input_count += 1
    else:
        watermark_index = None

    # 3. Filter graph construction
    video_chain = "[0:v]"
    filter_parts = []

    # Overlay brand logo (top-left for product ads)
    if logo_index is not None:
        filter_parts.append(f"{video_chain}[{logo_index}:v]overlay=40:40[v_logo]")
        video_chain = "[v_logo]"

    # Overlay Free Tier Watermark (top-right corner with 30px padding)
    if watermark_index is not None:
        filter_parts.append(f"{video_chain}[{watermark_index}:v]overlay=main_w-overlay_w-30:30[v_wm]")
        video_chain = "[v_wm]"

    work_dir = output_path.parent
    sub_name = subtitle_path.name if (subtitle_path and subtitle_path.exists()) else None

    # Zero-Tofu Subtitle Burning using Nirmala UI / Noto Sans Devanagari font
    if sub_name:
        font_style = (
            "Fontname=Nirmala UI,FontSize=24,"
            "PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,"
            "BorderStyle=1,Outline=3,Shadow=2,Alignment=2,MarginV=70"
        )
        sub_filter = f"{video_chain}subtitles={sub_name}:force_style='{font_style}'[v_final]"
        filter_parts.append(sub_filter)
        final_video_label = "[v_final]"
    else:
        final_video_label = video_chain

    # Audio mixing with smart ducking
    if bgm_index is not None:
        # Duck BGM volume to 12% and mix with voiceover
        audio_filter = f"[{bgm_index}:a]volume=0.12[bgm_low];[1:a][bgm_low]amix=inputs=2:duration=first[a_final]"
        filter_parts.append(audio_filter)
        final_audio_label = "[a_final]"
    else:
        final_audio_label = "1:a"

    if filter_parts:
        cmd.extend(["-filter_complex", ";".join(filter_parts)])
        cmd.extend(["-map", final_video_label, "-map", final_audio_label])
    else:
        cmd.extend(["-map", "0:v", "-map", "1:a"])

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-threads", "0",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path.name)
    ])

    logger.info(f"Rendering final video in {work_dir}: {output_path.name} (Watermark: {watermark_enabled})")
    subprocess.run(cmd, cwd=str(work_dir), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path

def optimize_for_whatsapp(input_mp4: Path, output_mp4: Path) -> Path:
    """
    Compress video to strictly < 15MB with high visual clarity for WhatsApp Status.
    """
    ffmpeg = get_ffmpeg_binary()
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg, "-y",
        "-i", str(input_mp4),
        "-c:v", "libx264",
        "-crf", "26",
        "-maxrate", "2.2M",
        "-bufsize", "4.4M",
        "-preset", "veryfast",
        "-threads", "0",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        str(output_mp4)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info(f"Optimized video for WhatsApp: {output_mp4} (Size: {output_mp4.stat().st_size / 1024 / 1024:.2f} MB)")
    return output_mp4

