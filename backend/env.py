# -*- coding: UTF-8 -*-

import os

# Primary provider: Volcengine Ark by default. Legacy LLM_* values remain supported.
LLM_BASE_URL = os.getenv(
	"ARK_BASE_URL",
	os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
)
LLM_MODEL_ID = os.getenv("ARK_MODEL_ID") or os.getenv("MODEL_ID")
LLM_API_KEY = (
	os.getenv("ARK_API_KEY")
	or os.getenv("LLM_API_KEY")
)
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
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
STORAGE_ACCESS_KEY = os.getenv("TOS_ACCESS_KEY") or os.getenv("STORAGE_ACCESS_KEY")
STORAGE_SECRET_KEY = os.getenv("TOS_SECRET_KEY") or os.getenv("STORAGE_SECRET_KEY")
STORAGE_ENDPOINT = os.getenv("TOS_ENDPOINT") or os.getenv("STORAGE_ENDPOINT")
STORAGE_REGION = os.getenv("TOS_REGION") or os.getenv("STORAGE_REGION")
STORAGE_BUCKET = os.getenv("TOS_BUCKET") or os.getenv("STORAGE_BUCKET")
AUC_APP_ID = os.getenv("AUC_APP_ID")
AUC_ACCESS_TOKEN = os.getenv("AUC_ACCESS_TOKEN")
AUC_CLUSTER_ID = os.getenv("AUC_CLUSTER_ID", None)
WEB_ACCESS_PASSWORD = os.getenv("WEB_ACCESS_PASSWORD", None)
