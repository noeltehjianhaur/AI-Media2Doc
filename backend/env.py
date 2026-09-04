# -*- coding: UTF-8 -*-

import os

# Primary provider: Google Gemini. OpenRouter acts as the fallback provider.
GEMINI_BASE_URL = os.getenv(
	"GEMINI_BASE_URL",
	"https://generativelanguage.googleapis.com/v1beta/openai/",
)
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_BASE_URL = os.getenv(
	"OPENROUTER_BASE_URL",
	"https://openrouter.ai/api/v1",
)
OPENROUTER_MODEL_ID = os.getenv("OPENROUTER_MODEL_ID")
OPENROUTER_ASR_MODEL_ID = os.getenv("OPENROUTER_ASR_MODEL_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
STORAGE_ACCESS_KEY = os.getenv("STORAGE_ACCESS_KEY")
STORAGE_SECRET_KEY = os.getenv("STORAGE_SECRET_KEY")
STORAGE_ENDPOINT = os.getenv("STORAGE_ENDPOINT")
STORAGE_REGION = os.getenv("STORAGE_REGION")
STORAGE_BUCKET = os.getenv("STORAGE_BUCKET")
WEB_ACCESS_PASSWORD = os.getenv("WEB_ACCESS_PASSWORD", None)
