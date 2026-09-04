<h1 align="center">
  <p>
  <img src="docs/images/logo.jpeg" alt="logo" width="50" height="50" style="border-radius: 50%;">
 </p>
  AI Media2Doc Assistant
</h1>

<p align="center">
    <em>Based on AI large models, convert videos and audios to various document styles like Xiaohongshu/WeChat Official Account/Knowledge Notes/Mind Maps with one click.</em>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/Platform-Web-orange" alt="Web Platform">
</p>

<p align="center">
    <img src="docs/images/index.jpg" alt="index" width="80%">
</p>

[中文文档](./README.md)

### 📖 Introduction

AI Media2Doc Assistant is a web tool based on AI large models that converts videos and audios to various document styles with one click. No login or registration required, with both frontend and backend supporting local deployment. Experience AI video/audio to styled document conversion services at an extremely low cost - I spent just five dollars for a month of development and testing.

### ✨ Core Features

- ✅ **Fully Open Source**: Licensed under MIT, supports local deployment.
- 🔒 **Privacy Protection**: No login or registration required, task records saved locally.
- 💻 **Frontend Processing**: Uses ffmpeg wasm technology, no need to install ffmpeg locally.
- � **Multilingual Transcription**: The spoken language is auto-detected and transcribed in that same language.
- 🌐 **Target-Language Translation**: Pick an output language in Settings to translate the transcript and generated document.
- 🗣️ **Interface Language Switch**: Toggle the whole UI between English and Simplified Chinese.
- 🔗 **Video Link Transcription**: Paste a video or web page link (e.g. Xiaohongshu, YouTube, Facebook) to transcribe it.
- �🎯 **Multiple Style Support**: Supports various document styles like Xiaohongshu/WeChat Official Account/Knowledge Notes/Mind Maps/Content Summaries.
- 🤖 **AI Conversation**: Supports secondary Q&A based on video content.
- 🤖 **Local Deployment Friendly**: With basic development knowledge, you can get it running in no time.
- 🐳 **One-Click Deployment**: Supports one-click deployment with Docker.

### 🔜 Future Plans

- 📷 Support intelligent extraction of video key frames, achieving true integration of text and images
- 🎙️ Support audio recognition using fast-whisper local large model processing to further reduce costs
- 🎨 Completely rebuild the frontend page using React for a smoother experience

### 📦 Installation Guide

1) Download `docker-compose.yaml` and `variables_template.env` from the project root.

2) Please refer to the [Backend Deployment Guide / Configuration Instructions](./backend/README.md) to complete the `variables.env` file in the root directory.

3) Run the Project:

```shell
$ make run
```

### LLM & ASR Configuration: Gemini with OpenRouter Fallback

Both transcription and document generation call Google Gemini first. If that request fails, OpenRouter is tried when configured. Both providers use OpenAI-compatible Chat Completions APIs. Volcengine Ark and Volcengine AUC are no longer used.

Set these values in `variables.env`:

```dotenv
# Primary provider: Google Gemini
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL_ID=gemini-3.6-flash
GEMINI_API_KEY=your-gemini-api-key

# Optional fallback provider: OpenRouter
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL_ID=openai/gpt-4o-mini
OPENROUTER_API_KEY=your-openrouter-api-key

# S3-compatible object storage (e.g. Cloudflare R2)
STORAGE_ACCESS_KEY=your-access-key
STORAGE_SECRET_KEY=your-secret-key
STORAGE_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
STORAGE_REGION=auto
STORAGE_BUCKET=your-bucket
```

Setup steps:

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/) and copy it into `GEMINI_API_KEY`. Pick an audio-capable model for `GEMINI_MODEL_ID`.
2. Optionally create an [OpenRouter](https://openrouter.ai/) key for `OPENROUTER_API_KEY`. Note that `openai/gpt-4o-mini` is a paid model; use a `:free`-suffixed model to stay on the free tier.
3. Create an S3-compatible bucket (Cloudflare R2 works well) and add a CORS rule allowing `http://localhost:5173`.
4. Run `docker compose up -d`, then open `http://localhost:5173`.

### Features

- **Multilingual transcription** – the spoken language is auto-detected and the transcript is produced in that same language.
- **Target-language translation** – pick an output language under **Settings → Language** to translate the transcript and generated document.
- **Interface language** – switch the whole UI between English and Simplified Chinese under **Settings → Language**.
- **File upload** – MP4, MOV, AVI, MKV, WebM and MP3 are supported.
- **Video link transcription** – paste a video or web page link on the upload screen. Success depends on platform restrictions; some sites block downloads.

### 👾 Developer's Note

The AI Media2Doc Assistant originated from an idea I had at the beginning of the year. As someone who enjoys reading, I prefer to convert video content into text for easier re-reading, thinking, and note-taking. However, I couldn't find a good tool to achieve this - most tools required login and payment. I didn't want to register too many accounts on the internet, nor did I want to upload my content to third-party platforms other than cloud providers. Therefore, I developed this small application under the MIT license, allowing anyone to experience audio/video to text conversion at a minimal cost.

### Project Screenshots

#### Support AI Q&A based on video content
<p align="center">
<img src="docs/images/details.png" alt="task details" width="80%">
</p>

#### Support mind map generation

Generated mind maps can be exported to third-party platforms for editing and optimization
<p align="center">
<img src="docs/images/mindmap.jpg" alt="mindmap" width="80%">
</p>

### 🔄 Processing Flow

<p align="center">
<img src="docs/images/process_flow.jpg" alt="architecture" width="80%">
</p>

### 🔧 Local Development Guide

- [Backend Local Deployment](./backend/README.md)
- [Frontend Local Deployment](./frontend/README.md)

### 📄 License

This project is licensed under the [MIT License](./LICENSE)

### 🔗 Related Links

- [volcengine-ai-app-lab](https://github.com/volcengine/ai-app-lab)
- [throttled-py](https://github.com/ZhuoZhuoCrayon/throttled-py): ✨Python rate-limiting library, reasonably limits and smooths cloud resource usage.


[韩数的开发笔记： 致力于分享 Github 上那些好玩、有趣、免费、实用的高质量项目](https://www.xiaohongshu.com/user/profile/5e2992b000000000010064a4)

### 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=hanshuaikang/AI-Media2Doc&type=Date)](https://www.star-history.com/#hanshuaikang/AI-Media2Doc&Date)