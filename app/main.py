from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.models import ChatRequest, ChatResponse, HealthResponse
from app.services.poetry_assistant import PoetryAssistantService


load_dotenv()

settings = get_settings()
service = PoetryAssistantService(settings)

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

web_dir = Path(__file__).resolve().parent / "web"
app.mount("/assets", StaticFiles(directory=web_dir), name="assets")


@app.on_event("startup")
def startup_event() -> None:
    if settings.auto_ingest_on_start and not service.vector_store_ready():
        service.auto_ingest()


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(web_dir / "index.html")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        llm_enabled=settings.llm_enabled,
        vector_store_ready=service.vector_store_ready(),
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = service.answer(request.question, request.session_id)
    return ChatResponse(**result)

