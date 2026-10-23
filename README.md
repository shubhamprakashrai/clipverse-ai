# 🎬 ClipVerse-AI — Next-Gen AI Video Studio & SaaS Engine

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Google Gemini](https://img.shields.io/badge/Gemini_3.5_Flash-Auto_Failover-orange.svg)](https://ai.google.dev/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-GPU_Accelerated-green.svg)](https://ffmpeg.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ClipVerse-AI** is a commercial-grade, multi-modal automated video generation studio and SaaS backend. It automates high-retention vertical reels (9:16), YouTube long-form content (16:9), commercial ads, and 3D animated stories in **under 45–60 seconds**.

---

## 🌟 Key Features & Production Modes

### 1. 🎬 Viral Text-to-Video Engine
- Generates high-retention viral shorts, facts, and mystery stories from a single prompt.
- **Zero-Tofu Subtitle Rendering:** Bundled Devanagari fonts (NotoSansDevanagari-Bold.ttf & Nirmala.ttc) with Alex Hormozi-style glowing yellow highlight (&H0000FFFF), thick black stroke, and drop shadow. No missing glyphs or [ ][ ][ ] tofu boxes.
- Language auto-pairing (Hindi, Hinglish, English) with natural neural voices (hi-IN-MadhurNeural, en-US-ChristopherNeural).

### 2. 📸 Personal Creator Reel (3D Ken Burns Motion)
- Transforms everyday user gallery photos into cinematic reels.
- Applies smooth 3D camera pan, tilt, and zoom effects synced to ambient music and emotional narration.

### 3. 🏷️ Brand & Product Ad (Hybrid Gap-Filling)
- Upload product photos and a transparent brand logo.
- **Smart Gap-Filling:** Seamlessly interleaves product photos with relevant lifestyle B-roll footage from Pixabay, ending with a high-converting call-to-action (CTA) outro card.

### 4. 💌 Royal Digital Video Invitation
- Generates luxury Indian video invitations for Weddings, Birthdays, Housewarming (Griha Pravesh), and Anniversaries.
- Features traditional shlokas, royal animations, and festive Shehnai/Dhol background scoring.

### 5. 🧚 AI 3D Cartoon Storyteller (Pixar/Disney Kahaniyan)
- Creates animated 3D moral tales and children's stories.
- Multi-chapter storyboards with scene art prompts, dramatic sound FX, and expressive storytelling voice.

---

## ⚡ Additional Value Additions
- 📱 **WhatsApp Status HD Optimizer:** Automatically generates a separate < 15MB high-clarity export optimized for WhatsApp status limits.
- 🔥 **1-Click Viral Social Media Pack:** Automatically produces hook titles, engaging descriptions, and 15 targeted hashtags.
- 🎙️ **Custom Voice-Note Upload:** Users can upload their own WhatsApp audio note or MP3 to bypass AI TTS.
- 🔒 **Freemium & Watermark Protection:** Free tier renders a subtle watermark; paid subscribers receive pristine, watermark-free videos.

---

## 🛠️ Architecture

`mermaid
graph TD
    UI[Web Studio Dashboard / React] -->|REST API| API[FastAPI Gateway /api/v1]
    API --> TM[Task Manager Queue]
    TM --> SB[Gemini 3.5 AI Storyboarder]
    TM --> TTS[Edge-TTS Voice Engine]
    TM --> MS[Pixabay & Media Gap-Filler]
    TM --> FF[FFmpeg Renderer Engine]
    FF --> SUB[Zero-Tofu Devanagari Subtitle Burner]
    FF --> DUCK[Smart BGM Audio Ducking]
    FF --> WM[Watermark Engine]
    FF --> WA[WhatsApp Status Optimizer <15MB]
    FF --> OUT[1080p Master Output]
`

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- FFmpeg installed and accessible on PATH

### 1. Clone the Repository
`ash
git clone https://github.com/shubhamprakashrai/clipverse-ai.git
cd clipverse-ai
`

### 2. Install Dependencies
`ash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
`

### 3. Configure Environment Variables
Copy .env.example to .env and insert your API keys:
`env
GEMINI_API_KEY="your_google_gemini_api_key_here"
GEMINI_MODEL="gemini-3.5-flash"
PIXABAY_API_KEY="your_pixabay_api_key_here"

HOST="0.0.0.0"
PORT=8000
`

### 4. Run the Studio Dashboard
`ash
# Windows 1-Click
start_studio.bat

# Or via CLI
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
`
Navigate to **http://localhost:8000** in your browser to launch the Web Studio.
Interactive Swagger API documentation is available at **http://localhost:8000/docs**.

---

## 📜 License
MIT License. Feel free to use and contribute!
