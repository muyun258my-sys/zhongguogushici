from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="用户问题")
    session_id: str = Field(default="default", description="会话 ID")


class SourceItem(BaseModel):
    title: str
    author: str
    dynasty: str
    source: str


class ChatResponse(BaseModel):
    answer: str
    question_type: str
    used_llm: bool
    sources: list[SourceItem]
    contexts: list[dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    llm_enabled: bool
    vector_store_ready: bool

