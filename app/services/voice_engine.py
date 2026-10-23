import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Optional
import edge_tts
from loguru import logger

def detect_language(text: str, default_lang: str = "hi") -> str:
    """
    Detect if text contains Devanagari (Hindi) or English/Hinglish.
    """
    if any('\u0900' <= char <= '\u097f' for char in text):
        return "hi"
    if default_lang in ["hi", "hinglish"]:
        return "hi"
    return "en"

def get_optimal_voice(text: str, requested_voice: Optional[str] = None, language: str = "hi") -> str:
    """
    Resolve the best voice to prevent any TTS language-voice mismatch errors.
    """
    if requested_voice and requested_voice.strip():
        # Sanity check: If text is Hindi script but voice is English, auto-correct to Hindi
        is_hindi = detect_language(text, language) == "hi"
        if is_hindi and not requested_voice.startswith("hi-"):
            logger.warning(f"Voice {requested_voice} does not support Hindi script. Auto-switching to hi-IN-MadhurNeural")
            return "hi-IN-MadhurNeural"
        return requested_voice

    lang = detect_language(text, language)
    if lang == "hi":
        return "hi-IN-MadhurNeural"
    return "en-US-ChristopherNeural"

def get_audio_duration(audio_path: Path) -> float:
    """
    Get duration in seconds of any audio file using ffprobe.
    """
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        logger.warning(f"Failed to get audio duration with ffprobe: {e}, falling back to file estimate")
        # Rough estimate: 16KB per sec for 128kbps MP3
        return max(5.0, audio_path.stat().st_size / 16000.0)

async def generate_speech_and_subtitles(
    text: str,
    voice: Optional[str] = None,
    output_audio_path: Path = None,
    output_srt_path: Path = None,
    language: str = "hi",
    rate: str = "+0%"
) -> Tuple[Path, Path]:
    """
    Generate audio and synced SRT subtitles using Edge-TTS with auto-language pairing.
    """
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_voice = get_optimal_voice(text, requested_voice=voice, language=language)

    communicate = edge_tts.Communicate(text, resolved_voice, rate=rate)
    sub_maker = edge_tts.SubMaker()

    with open(output_audio_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] in ["WordBoundary", "SentenceBoundary"]:
                sub_maker.feed(chunk)

    srt_content = sub_maker.get_srt().strip()
    if not srt_content:
        # Fallback subtitle timing generator so FFmpeg never crashes on empty srt
        duration = get_audio_duration(output_audio_path)
        words = text.split()
        chunk_size = 7
        num_chunks = max(1, (len(words) + chunk_size - 1) // chunk_size)
        sec_per_chunk = duration / num_chunks
        lines = []
        for idx in range(num_chunks):
            start_sec = idx * sec_per_chunk
            end_sec = min(duration, (idx + 1) * sec_per_chunk)
            chunk_text = " ".join(words[idx * chunk_size:(idx + 1) * chunk_size])
            s_m, s_s = divmod(start_sec, 60)
            s_h, s_m = divmod(s_m, 60)
            e_m, e_s = divmod(end_sec, 60)
            e_h, e_m = divmod(e_m, 60)
            lines.append(f"{idx+1}\n{int(s_h):02d}:{int(s_m):02d}:{int(s_s):02d},000 --> {int(e_h):02d}:{int(e_m):02d}:{int(e_s):02d},000\n{chunk_text}\n")
        srt_content = "\n".join(lines)

    # Write SRT subtitles with UTF-8 encoding
    with open(output_srt_path, "w", encoding="utf-8") as srt_file:
        srt_file.write(srt_content)

    logger.info(f"Generated voiceover: {output_audio_path} using {resolved_voice} and subtitles: {output_srt_path}")
    return output_audio_path, output_srt_path

def process_custom_voice_note(
    input_audio_path: Path,
    output_audio_path: Path,
    output_srt_path: Path,
    fallback_text: str = ""
) -> Tuple[Path, Path]:
    """
    Process user-uploaded voice note / audio file (bypasses Edge-TTS).
    """
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(input_audio_path, output_audio_path)
    duration = get_audio_duration(output_audio_path)

    # Generate timing-aligned subtitle from fallback text if provided
    with open(output_srt_path, "w", encoding="utf-8") as srt:
        if fallback_text:
            srt.write(f"1\n00:00:00,500 --> 00:00:{int(duration):02d},000\n{fallback_text}\n\n")
        else:
            srt.write(f"1\n00:00:00,500 --> 00:00:{int(duration):02d},000\n \n\n")

    logger.info(f"Processed custom voice note: {output_audio_path} (Duration: {duration:.2f}s)")
    return output_audio_path, output_srt_path

def synthesize_voice(
    text: str,
    voice: Optional[str],
    output_audio_path: Path,
    output_srt_path: Path,
    language: str = "hi"
) -> Tuple[Path, Path]:
    """
    Synchronous wrapper for FastAPI and background workers.
    """
    return asyncio.run(generate_speech_and_subtitles(
        text=text,
        voice=voice,
        output_audio_path=output_audio_path,
        output_srt_path=output_srt_path,
        language=language
    ))
