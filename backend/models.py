# -*- coding: UTF-8 -*-

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum


class ProcessingMode(str, Enum):
    AUDIO = "audio"
    AUDIO_VIDEO = "audio_video"


class MessageModel(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[MessageModel]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int]
    timeout: Optional[int]
    target_language: Optional[str] = None


class TranslationRequest(BaseModel):
    text: str
    target_language: str
    max_tokens: Optional[int] = 8192
    timeout: Optional[int] = 120


class FileNameRequest(BaseModel):
    filename: str
    processing_mode: ProcessingMode = ProcessingMode.AUDIO
    original_name: Optional[str] = None
    keep_source_media: bool = False


class VideoLinkRequest(BaseModel):
    url: str
    processing_mode: ProcessingMode = ProcessingMode.AUDIO
    keep_source_media: bool = False


class OutputRecordRequest(BaseModel):
    processing_mode: ProcessingMode = ProcessingMode.AUDIO
    transcript: Any
    generated_content: str
    metadata: Dict[str, Any]
    visual_analysis: Optional[Dict[str, Any]] = None
    screenshots: List[Dict[str, Any]] = Field(default_factory=list)
    title: Optional[str] = None
    publish: bool = False


class PublishOutputRequest(BaseModel):
    title: str
    files: Dict[str, Any]


class EnvResponse(BaseModel):
    code: int = 200
    success: bool = True
    message: str = "operation successful"
    data: Optional[Any] = None
