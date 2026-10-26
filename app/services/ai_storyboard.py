import json
from loguru import logger
from google import genai
from google.genai import types
from app.core.config import settings

def _get_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)

def _generate_with_fallback(prompt: str, config: types.GenerateContentConfig) -> str:
    """
    Execute generation with instant model fallback if a model is temporarily unavailable.
    """
    client = _get_client()
    candidate_models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", settings.GEMINI_MODEL, "gemini-3.5-flash"]
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    last_error = None
    for m in models_to_try:
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt,
                config=config
            )
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Model {m} error ({e}), trying fallback...")
            last_error = e

    raise RuntimeError(f"All Gemini model fallbacks failed: {last_error}")

def generate_social_pack(topic: str, script: str, language: str = "hi") -> dict:
    """
    Generate viral Hook Title, Description, and 15 Hashtags in 1 call.
    """
    prompt = f"""Given this video topic: "{topic}" and script: "{script[:400]}"
Generate a viral social media package in valid JSON:
{{
  "title": "Short punchy click-worthy Hook Title",
  "description": "Engaging 2-sentence description with Call to Action",
  "hashtags": ["#reels", "#viral", "#trending", "...15 relevant hashtags"]
}}
Return ONLY JSON."""

    try:
        raw = _generate_with_fallback(
            prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json"
            )
        )
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"Failed to generate social pack: {e}")
        return {
            "title": topic,
            "description": f"Watch this amazing video about {topic}! Like and subscribe.",
            "hashtags": ["#shorts", "#reels", "#viral", "#trending", "#story"]
        }

def generate_text_storyboard(topic: str, language: str = "hi", duration_mode: str = "30s") -> dict:
    """
    Generate structured short-form or long-form video script and visual keywords.
    """
    lang_prompt = "in natural, engaging Hindi/Hinglish (Devanagari script)" if language == "hi" else "in energetic, viral English"

    if duration_mode in ["3min", "4min"]:
        scene_count = "10 to 14"
        length_desc = "3 to 4 minute deep YouTube documentary/story"
    elif duration_mode == "60s":
        scene_count = "6 to 8"
        length_desc = "60-second engaging short story"
    else:
        scene_count = "4 to 6"
        length_desc = "fast-paced 30-second viral reel"

    prompt = f"""You are a master viral video creator.
Create a captivating {length_desc} {lang_prompt} on the topic: "{topic}".

Follow this exact JSON structure:
{{
  "title": "Short title",
  "full_script": "Complete narration text to be spoken by voiceover without any stage directions or brackets",
  "scenes": [
    {{
      "scene_number": 1,
      "visual_search_term": "English keyword to search on stock footage website (e.g. mystical glowing forest)",
      "narration_part": "Corresponding spoken text for this scene"
    }}
  ]
}}
Ensure there are between {scene_count} scenes. Return ONLY the valid JSON object, no markdown, no backticks."""

    raw = _generate_with_fallback(
        prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json"
        )
    )
    data = json.loads(raw)
    data["social_pack"] = generate_social_pack(topic, data.get("full_script", ""), language)
    return data

def generate_cartoon_storyboard(
    topic: str,
    duration_mode: str = "60s",
    character_style: str = "3d_pixar",
    language: str = "hi"
) -> dict:
    """
    Generate structured 3D Cartoon / Animated Kahani storyboard with scene art prompts and sound cues.
    """
    lang_prompt = "in expressive, animated Hindi storytelling tone (jaise jaadui kahaniyan hoti hain)" if language == "hi" else "in vivid, magical English animated story tone"

    if duration_mode in ["3min", "4min"]:
        scene_count = "10 to 15"
        length_desc = "3 to 4 minute long multi-chapter animated YouTube story"
    else:
        scene_count = "5 to 8"
        length_desc = "30 to 60 second animated cartoon reel"

    prompt = f"""You are a top Disney / Pixar story director and writer.
Create a captivating {length_desc} {lang_prompt} based on the plot: "{topic}".

Visual Style: {character_style} (High-budget 3D animated film with vivid magical colors, expressive characters).

Output MUST be valid JSON:
{{
  "title": "Animated Story Title",
  "full_script": "Full spoken voiceover narration without any sound cues or notes",
  "scenes": [
    {{
      "scene_number": 1,
      "scene_title": "Chapter name",
      "visual_image_prompt": "Ultra detailed English prompt for 3D Pixar animation image generator describing the character, action, lighting, and environment (e.g. A kind Indian boy in traditional vest standing in awe before a giant glowing blue crystalline waterfall inside a magical bioluminescent forest, Pixar 3D style, warm volumetric lighting)",
      "visual_search_term": "Short stock fallback keyword (e.g. magical fantasy forest 3d animation)",
      "sound_effect_vibe": "mystical_chime / dramatic_boom / forest_ambience / happy_tune",
      "narration_part": "Spoken line for this scene"
    }}
  ]
}}
Ensure there are between {scene_count} scenes. Return ONLY valid JSON."""

    raw = _generate_with_fallback(
        prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json"
        )
    )
    data = json.loads(raw)
    data["social_pack"] = generate_social_pack(topic, data.get("full_script", ""), language)
    return data

def generate_invitation_storyboard(
    event_type: str,
    host_names: str,
    event_date: str,
    venue: str,
    rsvp: str,
    language: str = "hi"
) -> dict:
    """
    Generate royal wedding, birthday, or event invitation video script and visual themes.
    """
    lang_prompt = "in royal, heart-warming traditional Hindi with shlokas/blessings" if language == "hi" else "in elegant, warm English"

    prompt = f"""You are an elite royal event invitation designer.
Create a 30-40 second video invitation {lang_prompt}.
Event: {event_type}
Hosts/Couple: {host_names}
Date & Time: {event_date}
Venue: {venue}
RSVP: {rsvp}

Output valid JSON:
{{
  "title": "{event_type.capitalize()} Invitation - {host_names}",
  "full_script": "Spoken invitation narration inviting friends and family with warmth and joy",
  "scenes": [
    {{
      "scene_number": 1,
      "visual_search_term": "royal palace celebration golden lights wedding",
      "caption_text": "Welcoming message / Shloka",
      "narration_part": "Spoken welcoming line"
    }},
    {{
      "scene_number": 2,
      "visual_search_term": "indian wedding flowers mandap luxury",
      "caption_text": "{host_names}",
      "narration_part": "Announcing the couple or celebrants"
    }},
    {{
      "scene_number": 3,
      "visual_search_term": "luxury banquet dinner candles evening party",
      "caption_text": "{event_date}\\n{venue}",
      "narration_part": "Date and venue announcement"
    }},
    {{
      "scene_number": 4,
      "visual_search_term": "sparklers fireworks celebration party golden",
      "caption_text": "RSVP: {rsvp}",
      "narration_part": "Warm closing awaiting your presence"
    }}
  ]
}}
Return ONLY valid JSON."""

    raw = _generate_with_fallback(
        prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json"
        )
    )
    return json.loads(raw)

def generate_personal_storyboard(idea: str, num_photos: int, language: str = "hi") -> dict:
    """
    Generate a script tailored to user personal photos.
    """
    lang_prompt = "in emotional, expressive Hindi" if language == "hi" else "in warm, engaging English"

    prompt = f"""You are creating a personal story video narration {lang_prompt} based on the user's idea: "{idea}".
The user has provided exactly {num_photos} photos for this story.

Generate a JSON object with:
{{
  "title": "Personal Story Title",
  "full_script": "Complete narration text",
  "scenes": [
    {{
      "scene_number": 1,
      "narration_part": "Narration accompanying photo 1"
    }}
  ]
}}
Ensure the number of scenes exactly matches {num_photos}. Return ONLY valid JSON."""

    raw = _generate_with_fallback(
        prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json"
        )
    )
    return json.loads(raw)

def generate_product_ad_storyboard(
    product_name: str,
    description: str,
    offer: str,
    cta: str,
    num_product_photos: int,
    language: str = "hi"
) -> dict:
    """
    Generate a high-converting commercial video ad.
    """
    lang_prompt = "in compelling, energetic Hindi/Hinglish tone suitable for Indian customers" if language == "hi" else "in high-converting English sales ad copy"

    prompt = f"""You are an elite marketing copywriter creating a 30-40 second video ad {lang_prompt}.
Product: {product_name}
Description: {description}
Special Offer: {offer}
Call to Action: {cta}

We have {num_product_photos} actual product photos from the client.
Plan a dynamic ad with 6 to 8 scenes:
- Some scenes show the client's actual product (tag: "product_photo")
- Some scenes show lifestyle/context B-roll from online stock (tag: "online_stock", with an English visual search term)
- The final scene is the Call to Action outro (tag: "outro")

Output valid JSON:
{{
  "title": "Ad Title",
  "full_script": "Complete voiceover script",
  "scenes": [
    {{
      "scene_number": 1,
      "type": "online_stock",
      "visual_search_term": "English keyword for stock footage (e.g. elegant luxury lifestyle)",
      "narration_part": "Hook line"
    }},
    {{
      "scene_number": 2,
      "type": "product_photo",
      "narration_part": "Introducing the product"
    }}
  ]
}}
Return ONLY valid JSON."""

    raw = _generate_with_fallback(
        prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            response_mime_type="application/json"
        )
    )
    data = json.loads(raw)
    data["social_pack"] = generate_social_pack(product_name, data.get("full_script", ""), language)
    return data


def generate_documentary_storyboard(
    topic: str,
    duration_mode: str = "5min",
    theme: str = "investigative",
    language: str = "hi"
) -> dict:
    """
    Generate cinematic 5 to 10 minute multi-chapter documentary screenplay,
    complete with chapter timestamps, newspaper clipping headlines, archival B-roll cues, and YouTube SEO pack.
    """
    if duration_mode == "10min":
        scene_count = "28 to 35"
        word_target = "1300 to 1500"
        length_desc = "10-minute deep investigative mega-documentary"
    elif duration_mode == "8min":
        scene_count = "22 to 26"
        word_target = "1000 to 1200"
        length_desc = "8-minute comprehensive documentary explainer"
    else: # 5min default
        scene_count = "16 to 20"
        word_target = "650 to 800"
        length_desc = "5-minute fast-paced cinematic documentary"

    lang_desc = (
        "in deep, serious, authoritative Hindi documentary tone (jaise Johnny Harris, Vox, ya Dhruv Rathee ke deep-dive explainers hote hain)"
        if language == "hi"
        else "in deep, authoritative, gripping English investigative documentary tone (like BBC, Vox, or Frontline)"
    )

    theme_vibe = {
        "investigative": "Dark corporate greed, secret financial loops, dramatic revelations, investigative exposes",
        "historical": "Epic historical grandeur, forgotten wars, ancient empires, lost civilizations, monumental battles",
        "geopolitical": "Global power struggles, espionage, diplomacy, border tensions, intelligence dossiers",
        "tech_business": "Silicon Valley power battles, startup scandals, algorithmic monopolies, billion-dollar gambles",
        "mystery": "Unexplained scientific anomalies, cosmic paradoxes, deep-sea exploration, forbidden discoveries"
    }.get(theme, "Serious investigative journalism")

    prompt = f"""You are an award-winning documentary director and investigative journalist (like Vox, MagnatesMedia, and National Geographic).
Create a {length_desc} {lang_desc} based on the topic: "{topic}".

Theme & Mood: {theme_vibe}.

Output MUST be strictly valid JSON with this exact structure:
{{
  "title": "Gripping, high-CTR YouTube Documentary Title",
  "chapters": [
    {{"timestamp": "00:00", "title": "The Hook"}},
    {{"timestamp": "01:05", "title": "The Hidden Roots"}},
    {{"timestamp": "02:15", "title": "The Escalation"}},
    {{"timestamp": "03:30", "title": "The Fatal Mistake"}},
    {{"timestamp": "04:30", "title": "The Dark Truth"}}
  ],
  "full_script": "Complete uninterrupted spoken voiceover narration ({word_target} words). Gripping narrative flow, no sound cues or markdown symbols in this text.",
  "scenes": [
    {{
      "scene_number": 1,
      "chapter": "The Hook",
      "scene_type": "newspaper_headline",
      "headline_text": "DRAMATIC NEWSPAPER HEADLINE TEXT IN ALL CAPS",
      "visual_search_terms": ["stock market panic", "wall street traders"],
      "ken_burns": "slow_zoom_in",
      "narration_part": "Narration sentence corresponding to this visual"
    }},
    {{
      "scene_number": 2,
      "chapter": "The Hook",
      "scene_type": "stock_footage",
      "headline_text": null,
      "visual_search_terms": ["dark boardroom meeting", "documents shredding"],
      "ken_burns": "slow_pan_right",
      "narration_part": "Next narration sentence"
    }}
  ],
  "social_pack": {{
    "title": "YouTube High-CTR Title",
    "description": "Full YouTube SEO description with summary, chapter timestamps, and call to action",
    "hashtags": ["#documentary", "#investigation", "#history", "#exposed", "#viral"]
  }}
}}

Important Requirements:
1. Provide between {scene_count} distinct scenes.
2. Intersperse 3 to 5 scenes with scene_type="newspaper_headline" for dramatic news clipping reveals.
3. Every scene MUST have 2 clean, simple English visual search keywords for high-definition stock footage (e.g. 'old factory smoke', 'courtroom judge gavel', 'money counting machine').
4. The script must be high-retention with dramatic pacing.
Return ONLY valid JSON.
"""

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.75
    )

    raw = _generate_with_fallback(prompt, config)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        data = json.loads(cleaned)

    return data
